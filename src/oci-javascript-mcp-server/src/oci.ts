/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { createRequire } from "node:module";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import type {
  Json,
  JsonObject,
  OciDiscoverFilter,
  OciInvokePayload,
  ReflectionManifest
} from "./types.ts";

const require = createRequire(import.meta.url);
const packageMetadata = require("../package.json") as { name?: unknown; version?: unknown };
const IDENTIFIER = /^[A-Za-z][A-Za-z0-9_]*$/;
const REGION = /^[a-z][a-z0-9-]*-[a-z0-9-]+-[0-9]+$/;
const SENSITIVE_FIELD = /^(authenticationDetailsProvider|authProvider|signer|privateKey|sessionToken|securityToken)$/i;
const MAX_SANITIZE_DEPTH = 32;

export type SdkBundle = {
  sdk: Record<string, any>;
  common: Record<string, any>;
};

export type SdkLoader = () => SdkBundle;
export type AuthProviderFactory = (bundle: SdkBundle) => any;

export type RequestField = {
  name: string;
  required: boolean;
  type: string;
};

export class OciSdkRuntime {
  readonly #loadSdk: SdkLoader;
  readonly #createAuthProvider: AuthProviderFactory;
  #manifest: ReflectionManifest | undefined;

  constructor(
    loadSdk: SdkLoader = loadDefaultSdk,
    createAuthProvider: AuthProviderFactory = defaultAuthProvider
  ) {
    this.#loadSdk = loadSdk;
    this.#createAuthProvider = createAuthProvider;
  }

  manifest(): ReflectionManifest {
    if (this.#manifest) {
      return this.#manifest;
    }
    const { sdk } = this.#loadSdk();
    const services: ReflectionManifest["services"] = Object.create(null);
    for (const service of Object.keys(sdk).sort()) {
      const serviceModule = sdk[service];
      if (!serviceModule || typeof serviceModule !== "object") {
        continue;
      }
      const clients: ReflectionManifest["services"][string]["clients"] = Object.create(null);
      for (const client of clientNames(serviceModule)) {
        const operations = operationNames(service, serviceModule[client]);
        if (operations.length === 0) {
          continue;
        }
        const requestFields: Record<string, string[]> = Object.create(null);
        for (const operation of operations) {
          requestFields[operation] = operationRequestFields(service, operation).map(field => field.name);
        }
        clients[client] = { operations, requestFields };
      }
      if (Object.keys(clients).length > 0) {
        services[service] = { clients };
      }
    }
    this.#manifest = { services };
    return this.#manifest;
  }

  discover(filter: OciDiscoverFilter): JsonObject {
    assertOnlyFields(filter as Record<string, unknown>, ["service", "client", "operation"], "discovery filter");
    const manifest = this.manifest();
    if (!filter.service) {
      return { type: "index", services: Object.keys(manifest.services) };
    }
    validateIdentifier(filter.service, "service");
    const service = manifest.services[filter.service];
    if (!service) {
      throw new Error(`Unknown OCI SDK service '${filter.service}'`);
    }
    if (!filter.client) {
      return { type: "service", service: filter.service, clients: Object.keys(service.clients) };
    }
    validateIdentifier(filter.client, "client");
    const client = service.clients[filter.client];
    if (!client) {
      throw new Error(`Unknown OCI SDK client '${filter.service}.${filter.client}'`);
    }
    if (!filter.operation) {
      return {
        type: "client",
        service: filter.service,
        client: filter.client,
        operations: client.operations
      };
    }
    validateIdentifier(filter.operation, "operation");
    if (!client.operations.includes(filter.operation)) {
      throw new Error(`Unknown OCI SDK operation '${filter.service}.${filter.client}.${filter.operation}'`);
    }
    const fields = operationRequestFields(filter.service, filter.operation);
    return {
      type: "operation",
      service: filter.service,
      client: filter.client,
      operation: filter.operation,
      requestType: `${pascalCase(filter.operation)}Request`,
      requestFields: fields.map(field => ({
        name: field.name,
        required: field.required,
        fieldType: field.type
      })) as Json,
      response: operationResponseShape(filter.service, filter.operation)
    };
  }

  config(): JsonObject {
    const bundle = this.#loadSdk();
    const provider = this.#createAuthProvider(bundle);
    const userId = optionalCall(provider, "getUserId") ?? optionalCall(provider, "getUser") ?? null;
    const region = optionalCall(provider, "getRegion")?.regionId
      ?? optionalCall(provider, "getRegionId")
      ?? null;
    return sanitizeJson({
      tenancyId: optionalCall(provider, "getTenantId") ?? null,
      userId,
      region,
      principal: typeof userId === "string"
        ? { type: userId.startsWith("ocid1.user.") ? "user" : "unknown", id: userId }
        : null
    }) as JsonObject;
  }

  async invoke(payload: OciInvokePayload, timeoutMs: number, maxRetries = 0): Promise<Json> {
    const { sdk, common } = this.#loadSdk();
    const serviceModule = sdk[payload.service];
    const Client = serviceModule?.[payload.client.name];
    if (typeof Client !== "function") {
      throw new Error(`OCI client '${payload.service}.${payload.client.name}' is unavailable`);
    }
    const provider = this.#createAuthProvider({ sdk, common });
    if (payload.client.options?.region) {
      if (typeof provider?.setRegion !== "function") {
        throw new Error("OCI authentication provider does not support region selection");
      }
      provider.setRegion(payload.client.options.region);
    }
    const configuration: Record<string, unknown> = {};
    if (typeof common.CircuitBreaker === "function") {
      configuration.circuitBreaker = new common.CircuitBreaker({ timeout: Math.max(1, timeoutMs) });
    }
    if (maxRetries === 0 && common.NoRetryConfigurationDetails) {
      configuration.retryConfiguration = common.NoRetryConfigurationDetails;
    } else if (maxRetries > 0 && common.OciSdkDefaultRetryConfiguration
      && typeof common.MaxAttemptsTerminationStrategy === "function") {
      configuration.retryConfiguration = {
        ...common.OciSdkDefaultRetryConfiguration,
        terminationStrategy: new common.MaxAttemptsTerminationStrategy(maxRetries + 1)
      };
    }
    const client = new Client({
      authenticationDetailsProvider: provider,
      additionalUserAgent: additionalUserAgent(packageMetadata)
    }, Object.keys(configuration).length > 0 ? configuration : undefined);
    try {
      const operation = client[payload.operation];
      if (typeof operation !== "function") {
        throw new Error(`OCI operation '${payload.operation}' is unavailable`);
      }
      return sanitizeJson(await operation.call(client, payload.request ?? Object.create(null)));
    } finally {
      if (typeof client.close === "function") {
        client.close();
      }
    }
  }
}

export function validateClientOptions(value: unknown): { region?: string } {
  if (value === undefined) {
    return Object.create(null) as { region?: string };
  }
  if (!isObject(value)) {
    throw new Error("OCI client options must be an object");
  }
  assertOnlyFields(value, ["region"], "OCI client options");
  if (value.region !== undefined && (typeof value.region !== "string" || !REGION.test(value.region))) {
    throw new Error(`Invalid OCI region '${String(value.region)}'`);
  }
  const result = Object.create(null) as { region?: string };
  if (typeof value.region === "string") {
    result.region = value.region;
  }
  return result;
}

export function operationKey(service: string, client: string, operation: string): string {
  return `${service}.${client}.${operation}`;
}

export function isMutationOperation(operation: string): boolean {
  return !/^(get|list|search|head|summarize|retrieve)/i.test(operation);
}

export function sanitizeJson(value: unknown, maxDepth = MAX_SANITIZE_DEPTH): Json {
  const seen = new WeakSet<object>();
  const visit = (item: unknown, depth: number): Json => {
    if (depth > maxDepth) {
      return "[MaxDepth]";
    }
    if (item === null || typeof item === "string" || typeof item === "boolean") {
      return item;
    }
    if (typeof item === "number") {
      return Number.isFinite(item) ? item : String(item);
    }
    if (typeof item === "bigint") {
      return item.toString();
    }
    if (item instanceof Date) {
      return item.toISOString();
    }
    if (item instanceof Uint8Array) {
      return Buffer.from(item).toString("base64");
    }
    if (!item || typeof item !== "object") {
      return String(item);
    }
    if (seen.has(item)) {
      return "[Circular]";
    }
    seen.add(item);
    try {
      if (Array.isArray(item)) {
        return item.map(entry => visit(entry, depth + 1));
      }
      const result = Object.create(null) as JsonObject;
      for (const [key, child] of Object.entries(item)) {
        if (SENSITIVE_FIELD.test(key) || isTransportObject(key, child)) {
          continue;
        }
        result[key] = visit(child, depth + 1);
      }
      return result;
    } finally {
      seen.delete(item);
    }
  };
  return visit(value, 0);
}

function loadDefaultSdk(): SdkBundle {
  return { sdk: require("oci-sdk"), common: require("oci-common") };
}

function defaultAuthProvider(bundle: SdkBundle): any {
  const configFile = process.env.OCI_CONFIG_FILE
    ? resolve(process.env.OCI_CONFIG_FILE)
    : join(homedir(), ".oci", "config");
  const profile = process.env.OCI_CONFIG_PROFILE ?? "DEFAULT";
  const profileValues = readProfile(configFile, profile);
  if (profileValues.security_token_file && typeof bundle.common.SessionAuthDetailProvider === "function") {
    return new bundle.common.SessionAuthDetailProvider(configFile, profile);
  }
  const Provider = bundle.sdk.ConfigFileAuthenticationDetailsProvider
    ?? bundle.common.ConfigFileAuthenticationDetailsProvider;
  if (typeof Provider !== "function") {
    throw new Error("OCI authentication provider is unavailable");
  }
  return new Provider(configFile, profile);
}

function clientNames(service: Record<string, any>): string[] {
  return Object.keys(service)
    .filter(name => name.endsWith("Client") && typeof service[name] === "function")
    .sort();
}

function operationNames(service: string, Client: any): string[] {
  return Object.getOwnPropertyNames(Client.prototype)
    .filter(name => name !== "constructor" && !name.startsWith("_"))
    .filter(name => typeof Client.prototype[name] === "function")
    .filter(name => requestFile(service, name) !== null)
    .sort();
}

function operationRequestFields(service: string, operation: string): RequestField[] {
  const path = requestFile(service, operation);
  if (!path) {
    return [];
  }
  const interfaceName = `${pascalCase(operation)}Request`;
  const body = interfaceBody(readFileSync(path, "utf8"), interfaceName);
  if (!body) {
    return [];
  }
  const fields: RequestField[] = [];
  const pattern = /^\s{4}"([^"]+)"(\?)?:\s*([^;\n]+(?:\n\s{8}[^;\n]+)*);/gm;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(body)) !== null) {
    fields.push({
      name: match[1]!,
      required: match[2] !== "?",
      type: match[3]!.replace(/\s+/g, " ").trim()
    });
  }
  return fields;
}

function operationResponseShape(service: string, operation: string): JsonObject {
  const root = servicePackageRoot(service);
  if (!root) {
    return { description: "OCI SDK response object" };
  }
  const path = join(root, "lib", "client.js");
  if (!existsSync(path)) {
    return { description: "OCI SDK response object" };
  }
  const source = readFileSync(path, "utf8");
  const start = source.indexOf(`    ${operation}(${operation}Request) {`);
  const snippet = start >= 0 ? source.slice(start, start + 12_000) : "";
  const bodyKey = /bodyKey:\s*"([^"]+)"/.exec(snippet)?.[1];
  return {
    description: "Sanitized OCI SDK response object",
    ...(bodyKey ? { bodyField: bodyKey } : {}),
    ...(snippet.includes("opc-next-page")
      ? { pagination: { responseField: "opcNextPage", requestField: "page" } }
      : {})
  };
}

function requestFile(service: string, operation: string): string | null {
  const root = servicePackageRoot(service);
  if (!root) {
    return null;
  }
  const path = join(root, "lib", "request", `${kebabCase(`${pascalCase(operation)}Request`)}.d.ts`);
  return existsSync(path) ? path : null;
}

function servicePackageRoot(service: string): string | null {
  try {
    return dirname(require.resolve(`oci-${service}/package.json`));
  } catch {
    return null;
  }
}

function interfaceBody(source: string, name: string): string | null {
  const match = new RegExp(`export\\s+interface\\s+${name}\\b[^\\{]*\\{`, "m").exec(source);
  if (!match) {
    return null;
  }
  let depth = 1;
  const start = match.index + match[0].length;
  for (let index = start; index < source.length; index += 1) {
    if (source[index] === "{") depth += 1;
    if (source[index] === "}") depth -= 1;
    if (depth === 0) return source.slice(start, index);
  }
  return null;
}

function pascalCase(value: string): string {
  return value.replace(/(^|[_-])([A-Za-z0-9])/g, (_match, _separator, char: string) => char.toUpperCase())
    .replace(/[^A-Za-z0-9]/g, "");
}

function kebabCase(value: string): string {
  return value.replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/([A-Z])([A-Z][a-z])/g, "$1-$2")
    .toLowerCase();
}

function additionalUserAgent(metadata: { name?: unknown; version?: unknown }): string {
  const name = typeof metadata.name === "string" ? metadata.name : "oci-javascript-mcp-server";
  const version = typeof metadata.version === "string" ? metadata.version : "0.0.0";
  return `${name.replace(/^@[^/]+\//, "").replace(/^oracle\./, "").replace(/-server$/, "")}/${version}`;
}

function validateIdentifier(value: unknown, label: string): asserts value is string {
  if (typeof value !== "string" || !IDENTIFIER.test(value)) {
    throw new Error(`Invalid OCI ${label} '${String(value)}'`);
  }
}

function assertOnlyFields(value: Record<string, unknown>, allowed: string[], label: string): void {
  const fields = new Set(allowed);
  for (const key of Object.keys(value)) {
    if (!fields.has(key)) {
      throw new Error(`Unsupported ${label} field '${key}'`);
    }
  }
}

function isObject(value: unknown): value is Record<string, any> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function optionalCall(target: any, name: string): any {
  try {
    return typeof target?.[name] === "function" ? target[name]() : null;
  } catch {
    return null;
  }
}

function readProfile(path: string, profile: string): Record<string, string> {
  if (!existsSync(path)) {
    return {};
  }
  const result: Record<string, string> = {};
  let active = false;
  for (const raw of readFileSync(path, "utf8").split(/\r?\n/)) {
    const line = raw.trim();
    const section = /^\[(.+)]$/.exec(line);
    if (section) {
      active = section[1]!.toUpperCase() === profile.toUpperCase();
    } else if (active && line && !line.startsWith("#") && line.includes("=")) {
      const index = line.indexOf("=");
      result[line.slice(0, index).trim()] = line.slice(index + 1).trim();
    }
  }
  return result;
}

function isTransportObject(key: string, value: unknown): boolean {
  if (!isObject(value)) {
    return false;
  }
  if (key === "httpRequest" || key === "httpResponse") {
    return true;
  }
  const keys = new Set(Object.keys(value).map(field => field.toLowerCase()));
  return (key === "request" || key === "response")
    && keys.has("headers")
    && (["method", "uri", "url", "status", "body"].some(field => keys.has(field)));
}
