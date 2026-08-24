/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type {
  ExecutionPolicy,
  GuestRpcRequest,
  Json,
  JsonObject,
  OciInvokePayload,
  ReflectionManifest
} from "./types.ts";
import {
  OciSdkRuntime,
  isMutationOperation,
  operationKey,
  validateClientOptions
} from "./oci.ts";

const IDENTIFIER = /^[A-Za-z][A-Za-z0-9_]*$/;
const IDENTITY_CLAIMS = new Set([
  "executionId", "execution_id", "policy", "principal", "principalId",
  "credential", "credentials", "auth", "authorization", "signer", "token"
]);

export class HostExecutionBroker {
  readonly #runtime: OciSdkRuntime;
  readonly #policy: ExecutionPolicy;
  #calls = 0;
  #inFlight = 0;
  #cancelled = false;

  constructor(runtime: OciSdkRuntime, policy: ExecutionPolicy) {
    this.#runtime = runtime;
    this.#policy = policy;
  }

  cancel(): void {
    this.#cancelled = true;
  }

  async handle(request: GuestRpcRequest): Promise<Json> {
    this.#assertLive();
    if (request.operation === "config") {
      assertExactObject(request.payload, [], "config payload");
      this.#acquireCall();
      try {
        const response = this.#runtime.config();
        if (jsonBytes(response, "OCI config response") > this.#policy.maxResponseBytes) {
          throw new Error(`OCI config response exceeds ${this.#policy.maxResponseBytes} bytes`);
        }
        return response;
      } finally {
        this.#inFlight -= 1;
      }
    }
    if (request.operation !== "invoke") {
      throw new Error(`Unsupported broker operation '${String(request.operation)}'`);
    }
    const encodedBytes = jsonBytes(request.payload, "OCI request");
    if (encodedBytes > this.#policy.maxRequestBytes) {
      throw new Error(`OCI request exceeds ${this.#policy.maxRequestBytes} bytes`);
    }
    const payload = canonicalInvoke(request.payload, this.#runtime.manifest(), this.#policy);
    this.#acquireCall();
    try {
      this.#assertLive();
      const response = await this.#runtime.invoke(payload, this.#remainingMs(), this.#policy.maxRetries);
      this.#assertLive();
      const responseBytes = jsonBytes(response, "OCI response");
      if (responseBytes > this.#policy.maxResponseBytes) {
        throw new Error(`OCI response exceeds ${this.#policy.maxResponseBytes} bytes`);
      }
      return response;
    } finally {
      this.#inFlight -= 1;
    }
  }

  #remainingMs(): number {
    return Math.max(0, this.#policy.deadlineMs - Date.now());
  }

  #acquireCall(): void {
    if (this.#calls >= this.#policy.maxCalls) {
      throw new Error(`OCI call limit exceeded (${this.#policy.maxCalls})`);
    }
    if (this.#inFlight >= this.#policy.maxConcurrentCalls) {
      throw new Error(`OCI concurrency limit exceeded (${this.#policy.maxConcurrentCalls})`);
    }
    this.#calls += 1;
    this.#inFlight += 1;
  }

  #assertLive(): void {
    if (this.#cancelled) {
      throw new Error("execution was cancelled");
    }
    if (Date.now() >= this.#policy.deadlineMs) {
      throw new Error("execution deadline exceeded");
    }
  }
}

export function developmentPolicy(
  manifest: ReflectionManifest,
  deadlineMs: number,
  overrides: Partial<Omit<ExecutionPolicy, "deadlineMs">> = {}
): ExecutionPolicy {
  const operations = new Set<string>();
  const fields = new Map<string, ReadonlySet<string>>();
  for (const [service, serviceEntry] of Object.entries(manifest.services)) {
    for (const [client, clientEntry] of Object.entries(serviceEntry.clients)) {
      for (const operation of clientEntry.operations) {
        const key = operationKey(service, client, operation);
        operations.add(key);
        fields.set(key, new Set(clientEntry.requestFields?.[operation] ?? []));
      }
    }
  }
  return Object.freeze({
    allowedOperations: operations,
    allowMutations: false,
    allowedRequestFields: fields,
    maxCalls: 32,
    maxConcurrentCalls: 4,
    maxRequestBytes: 256 * 1024,
    maxResponseBytes: 1024 * 1024,
    deadlineMs,
    maxRetries: 0,
    ...overrides
  });
}

export function productionPolicy(deadlineMs: number): ExecutionPolicy {
  return Object.freeze({
    allowedOperations: new Set<string>(),
    allowMutations: false,
    maxCalls: 0,
    maxConcurrentCalls: 0,
    maxRequestBytes: 0,
    maxResponseBytes: 0,
    deadlineMs,
    maxRetries: 0
  });
}

export function canonicalInvoke(
  value: JsonObject,
  manifest: ReflectionManifest,
  policy: ExecutionPolicy
): OciInvokePayload {
  assertExactObject(value, ["service", "client", "operation"], "invoke payload", ["request"]);
  const service = identifier(value.service, "service");
  const clientValue = object(value.client, "client");
  assertExactObject(clientValue, ["name"], "client", ["options"]);
  const client = identifier(clientValue.name, "client");
  const operation = identifier(value.operation, "operation");
  const key = operationKey(service, client, operation);
  const manifestClient = manifest.services[service]?.clients[client];
  if (!manifestClient?.operations.includes(operation)) {
    throw new Error(`Unknown OCI SDK operation '${key}'`);
  }
  if (!policy.allowedOperations.has(key)) {
    throw new Error(`OCI operation '${key}' is not authorized`);
  }
  if (!policy.allowMutations && isMutationOperation(operation)) {
    throw new Error(`OCI mutation '${key}' is not authorized for a read-only execution`);
  }
  const options = validateClientOptions(clientValue.options);
  if (options.region && policy.allowedRegions && !policy.allowedRegions.has(options.region)) {
    throw new Error(`OCI region '${options.region}' is not authorized`);
  }
  const requestValue = value.request === undefined ? Object.create(null) : object(value.request, "request");
  rejectIdentityClaims(requestValue);
  const allowedFields = policy.allowedRequestFields?.get(key)
    ?? new Set(manifestClient.requestFields?.[operation] ?? []);
  const request = Object.create(null) as JsonObject;
  for (const [field, item] of Object.entries(requestValue)) {
    if (!allowedFields.has(field)) {
      throw new Error(`OCI request field '${field}' is not authorized for '${key}'`);
    }
    enforceScope(field, item as Json, policy);
    request[field] = copyJson(item as Json);
  }
  return {
    service,
    client: Object.keys(options).length > 0 ? { name: client, options } : { name: client },
    operation,
    request
  };
}

export function assertExactObject(
  value: Record<string, unknown>,
  required: string[],
  label: string,
  optional: string[] = []
): void {
  const allowed = new Set([...required, ...optional]);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new Error(`Unsupported ${label} field '${key}'`);
    }
  }
  for (const key of required) {
    if (!Object.hasOwn(value, key)) {
      throw new Error(`Missing ${label} field '${key}'`);
    }
  }
}

function rejectIdentityClaims(value: JsonObject): void {
  for (const key of Object.keys(value)) {
    if (IDENTITY_CLAIMS.has(key)) {
      throw new Error(`Guest-supplied identity or policy claim '${key}' is not allowed`);
    }
  }
}

function enforceScope(field: string, value: Json, policy: ExecutionPolicy): void {
  if (field === "tenancyId" && policy.allowedTenancyIds && !policy.allowedTenancyIds.has(String(value))) {
    throw new Error(`tenancy '${String(value)}' is not authorized`);
  }
  if (field === "compartmentId" && policy.allowedCompartmentIds
    && !policy.allowedCompartmentIds.has(String(value))) {
    throw new Error(`compartment '${String(value)}' is not authorized`);
  }
  if (field === "region" && policy.allowedRegions && !policy.allowedRegions.has(String(value))) {
    throw new Error(`region '${String(value)}' is not authorized`);
  }
  if (/Id$/.test(field) && field !== "tenancyId" && field !== "compartmentId"
    && policy.allowedResourceIds && !policy.allowedResourceIds.has(String(value))) {
    throw new Error(`resource '${String(value)}' is not authorized`);
  }
}

function copyJson(value: Json): Json {
  if (Array.isArray(value)) {
    return value.map(copyJson);
  }
  if (value && typeof value === "object") {
    const result = Object.create(null) as JsonObject;
    for (const [key, child] of Object.entries(value)) {
      result[key] = copyJson(child);
    }
    return result;
  }
  return value;
}

function identifier(value: Json | undefined, label: string): string {
  if (typeof value !== "string" || !IDENTIFIER.test(value)) {
    throw new Error(`Invalid OCI ${label} '${String(value)}'`);
  }
  return value;
}

function object(value: Json | undefined, label: string): JsonObject {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`OCI ${label} must be an object`);
  }
  return value;
}

function jsonBytes(value: Json, label: string): number {
  try {
    return Buffer.byteLength(JSON.stringify(value), "utf8");
  } catch {
    throw new Error(`${label} is not valid JSON`);
  }
}
