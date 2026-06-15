/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { createRequire } from "node:module";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { Buffer } from "node:buffer";
import type {
  HostRpcHandler,
  HostRpcRequest,
  Json,
  JsonObject,
  OciDiscoverPayload,
  OciInvokePayload,
  OciReflectionManifest
} from "./types.ts";
import { fromJson, toJson } from "./json.ts";

const require = createRequire(import.meta.url);
const packageJson = require("../package.json") as { name?: unknown; version?: unknown };

const ADDITIONAL_USER_AGENT = additionalUserAgent(packageJson);
const MAX_HOST_RPC_RESPONSE_BYTES = positiveIntegerEnv(
  "OCI_JAVASCRIPT_MAX_HOST_RPC_RESPONSE_BYTES",
  1024 * 1024
);
const MAX_SANITIZE_DEPTH = 80;
const IDENTIFIER_PATTERN = /^[A-Za-z][A-Za-z0-9_]*$/;
const REGION_ID_PATTERN = /^[a-z][a-z0-9-]*-[a-z0-9-]+-[0-9]+$/;
const LIST_OPERATION_PATTERN = /^(list|search)/i;
const SDK_CREDENTIAL_FIELD_PATTERN =
  /^(authenticationDetailsProvider|authProvider|signer|privateKey|sessionToken|securityToken)$/i;
const MAX_DISCOVERY_MODEL_DEPTH = 2;

type SdkBundle = {
  sdk: Record<string, any>;
  common: Record<string, any>;
};

export type OciSdkLoader = () => SdkBundle;

type OciClientConfiguration = {
  circuitBreaker?: unknown;
};

type FieldDiscovery = {
  name: string;
  required: boolean;
  type: string;
  modelRefs?: string[];
};

type ModelDiscovery = {
  fields: FieldDiscovery[];
};

function additionalUserAgent(metadata: { name?: unknown; version?: unknown }): string {
  const name = typeof metadata.name === "string" && metadata.name
    ? metadata.name
    : "oci-javascript-mcp-server";
  const version = typeof metadata.version === "string" && metadata.version
    ? metadata.version
    : "0.0.0";
  const unscopedName = name.replace(/^@[^/]+\//, "");
  const oracleName = unscopedName.startsWith("oracle.")
    ? unscopedName.slice("oracle.".length)
    : unscopedName;
  return `${oracleName.replace(/-server$/, "")}/${version}`;
}

export function createOciSdkHostRpc(loadSdk: OciSdkLoader = loadDefaultSdk): HostRpcHandler {
  return async (request: HostRpcRequest, timeoutMs?: number): Promise<Json> => {
    if (request.binding !== "oracle" || request.namespace !== "oci") {
      throw new Error(`Unsupported host RPC binding ${request.binding}/${request.namespace}`);
    }

    if (request.operation === "config") {
      return hostConfig(loadSdk);
    }
    if (request.operation === "discover") {
      return discover(loadSdk, request.payload as OciDiscoverPayload);
    }
    if (request.operation === "invoke") {
      return invoke(loadSdk, request.payload as OciInvokePayload, timeoutMs);
    }

    throw new Error(`Unsupported OCI host RPC operation ${request.operation}`);
  };
}

export function createOciReflectionManifest(
  loadSdk: OciSdkLoader = loadDefaultSdk
): OciReflectionManifest {
  const { sdk } = loadSdk();
  const services: OciReflectionManifest["services"] = {};
  for (const serviceName of serviceNames(sdk)) {
    const serviceModule = sdk[serviceName];
    const clients: OciReflectionManifest["services"][string]["clients"] = {};
    for (const clientName of clientNames(serviceModule)) {
      const ClientClass = serviceModule[clientName];
      clients[clientName] = {
        operations: operationNames(serviceName, ClientClass)
      };
    }
    services[serviceName] = { clients };
  }
  return { services };
}

function loadDefaultSdk(): SdkBundle {
  return {
    sdk: require("oci-sdk"),
    common: require("oci-common")
  };
}

function hostConfig(loadSdk: OciSdkLoader): Json {
  const provider = authenticationProvider(loadSdk);
  const userId = providerUserId(provider) ?? sessionTokenSubject(provider);
  return toJson({
    tenancyId: callOptional(provider, "getTenantId"),
    userId,
    fingerprint: callOptional(provider, "getFingerprint"),
    region: callOptional(provider, "getRegion")?.regionId ?? callOptional(provider, "getRegionId") ?? null,
    principal: userId ? {
      type: userId.startsWith("ocid1.user.") ? "user" : "unknown",
      id: userId
    } : null
  });
}

function providerUserId(provider: any): string | null {
  return firstNonEmptyString(
    callOptional(provider, "getUserId"),
    callOptional(provider, "getUser")
  );
}

function sessionTokenSubject(provider: any): string | null {
  const token = typeof provider?.sessionToken === "string" ? provider.sessionToken : null;
  const payload = token ? decodeJwtPayload(token) : null;
  return firstNonEmptyString(payload?.sub);
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const payload = token.trim().split(".")[1];
  if (!payload) {
    return null;
  }
  try {
    const base64 = payload
      .padEnd(payload.length + ((4 - (payload.length % 4)) % 4), "=")
      .replace(/-/g, "+")
      .replace(/_/g, "/");
    return JSON.parse(Buffer.from(base64, "base64").toString("utf8"));
  } catch {
    return null;
  }
}

async function invoke(
  loadSdk: OciSdkLoader,
  payload: OciInvokePayload,
  timeoutMs?: number
): Promise<Json> {
  validateIdentifier(payload.service, "service");
  validateClientPayload(payload.client);
  validateIdentifier(payload.operation, "operation");

  const { sdk, common } = loadSdk();
  const serviceModule = sdk[payload.service];
  if (!serviceModule || typeof serviceModule !== "object") {
    throw new Error(`Unknown OCI SDK service '${payload.service}'`);
  }

  const ClientClass = serviceModule[payload.client.name];
  if (typeof ClientClass !== "function") {
    throw new Error(`Unknown OCI SDK client '${payload.service}.${payload.client.name}'`);
  }
  const operations = operationNames(payload.service, ClientClass);
  if (!operations.includes(payload.operation)) {
    throw new Error(unknownOperationMessage(
      payload.service,
      payload.client.name,
      payload.operation,
      operations
    ));
  }

  const provider = authenticationProvider(loadSdk);
  applyClientOptions(provider, payload.client.options);
  const clientConfiguration = createClientConfiguration(common, timeoutMs);
  const client = new ClientClass({
    authenticationDetailsProvider: provider,
    additionalUserAgent: ADDITIONAL_USER_AGENT
  }, clientConfiguration);
  try {
    const operation = client[payload.operation];
    if (typeof operation !== "function") {
      throw new Error(unknownOperationMessage(
        payload.service,
        payload.client.name,
        payload.operation,
        operations
      ));
    }

    const request = decodeRequest(payload.request ?? {});
    const response = await operation.call(client, request);
    const encoded = toJson(stripHttpTransportArtifacts(response, new WeakSet<object>(), 0));
    const encodedBytes = Buffer.byteLength(JSON.stringify(encoded), "utf8");
    if (encodedBytes > MAX_HOST_RPC_RESPONSE_BYTES) {
      throw new Error(tooLargeMessage(payload, encodedBytes));
    }
    return encoded;
  } finally {
    if (typeof client.close === "function") {
      client.close();
    }
  }
}

function discover(loadSdk: OciSdkLoader, payload: OciDiscoverPayload): Json {
  const { sdk } = loadSdk();

  if (!payload.service) {
    return toJson({ type: "index", services: serviceNames(sdk) });
  }

  validateIdentifier(payload.service, "service");
  const serviceModule = sdk[payload.service];
  if (!serviceModule || typeof serviceModule !== "object") {
    throw new Error(`Unknown OCI SDK service '${payload.service}'`);
  }

  const clients = clientNames(serviceModule);

  if (!payload.client) {
    return toJson({ type: "service", service: payload.service, clients });
  }

  validateIdentifier(payload.client, "client");
  const ClientClass = serviceModule[payload.client];
  if (typeof ClientClass !== "function") {
    throw new Error(`Unknown OCI SDK client '${payload.service}.${payload.client}'`);
  }

  const operations = operationNames(payload.service, ClientClass);

  if (!payload.operation) {
    return toJson({
      type: "client",
      service: payload.service,
      client: payload.client,
      operations
    });
  }

  validateIdentifier(payload.operation, "operation");
  if (!operations.includes(payload.operation)) {
    throw new Error(unknownOperationMessage(
      payload.service,
      payload.client,
      payload.operation,
      operations
    ));
  }

  const operationDetails = discoverOperationShape(
    payload.service,
    payload.operation
  );

  return toJson({
    type: "operation",
    service: payload.service,
    client: payload.client,
    operation: payload.operation,
    requestShape: operationDetails?.requestShape
      ?? "Pass the OCI JavaScript SDK request object as a plain object.",
    ...(operationDetails ?? {})
  });
}

function serviceNames(sdk: Record<string, any>): string[] {
  return Object.keys(sdk)
    .filter(name => sdk[name] && typeof sdk[name] === "object")
    .sort();
}

function clientNames(serviceModule: Record<string, any>): string[] {
  return Object.keys(serviceModule)
    .filter(name => name.endsWith("Client") && typeof serviceModule[name] === "function")
    .sort();
}

function operationNames(service: string, ClientClass: any): string[] {
  const packageRoot = sdkServicePackageRoot(service);
  return Reflect.ownKeys(ClientClass.prototype)
    .filter(name => typeof name === "string")
    .filter(name => name !== "constructor" && !name.startsWith("_"))
    .filter(name => typeof ClientClass.prototype[name] === "function")
    .filter(name => isSdkApiOperation(packageRoot, name))
    .sort();
}

function unknownOperationMessage(
  service: string,
  client: string,
  operation: string,
  operations: string[]
): string {
  const target = `${service}.${client}.${operation}`;
  const paginatedOperation = paginationBaseOperation(operation);
  if (paginatedOperation && operations.includes(paginatedOperation)) {
    return (
      `Unknown OCI SDK operation '${target}'. SDK pagination helpers are not exposed; `
      + `call ${client}.${paginatedOperation} directly and pass response.opcNextPage as request.page.`
    );
  }
  return (
    `Unknown OCI SDK operation '${target}'. Use discover_oci to inspect available `
    + "service, client, operation, and request names."
  );
}

function paginationBaseOperation(operation: string): string | null {
  const listAllMatch = /^listAll([A-Z].*?)(Responses?)?$/.exec(operation);
  if (listAllMatch) {
    return `list${listAllMatch[1]}`;
  }

  const iteratorMatch = /^(list[A-Z].*?)(RecordIterator|ResponseIterator)$/.exec(operation);
  return iteratorMatch ? iteratorMatch[1] : null;
}

function isSdkApiOperation(packageRoot: string | null, operation: string): boolean {
  return !!packageRoot && existsSync(join(
    packageRoot,
    "lib",
    "request",
    `${kebabCase(`${pascalCase(operation)}Request`)}.d.ts`
  ));
}

function discoverOperationShape(
  service: string,
  operation: string
): Record<string, unknown> | null {
  const packageRoot = sdkServicePackageRoot(service);
  if (!packageRoot) {
    return null;
  }

  const requestType = `${pascalCase(operation)}Request`;
  const requestFields = parseInterfaceFile(
    join(packageRoot, "lib", "request", `${kebabCase(requestType)}.d.ts`),
    requestType
  );
  const responseShape = discoverResponseShape(packageRoot, operation);
  if (!requestFields) {
    return responseShape ? { responseShape } : null;
  }

  const models: Record<string, ModelDiscovery> = {};
  for (const field of requestFields) {
    for (const modelRef of field.modelRefs ?? []) {
      discoverModel(packageRoot, modelRef, models, 0);
    }
  }

  return {
    requestType,
    requestShape: "Pass a plain JavaScript object matching requestFields.",
    requestFields,
    models,
    exampleRequest: requestExample(requestFields, models),
    ...(responseShape ? { responseShape } : {})
  };
}

function sdkServicePackageRoot(service: string): string | null {
  try {
    return dirname(require.resolve(`oci-${service}/package.json`));
  } catch {
    return null;
  }
}

function discoverModel(
  packageRoot: string,
  modelName: string,
  models: Record<string, ModelDiscovery>,
  depth: number
): void {
  if (models[modelName] || depth > MAX_DISCOVERY_MODEL_DEPTH) {
    return;
  }
  const fields = parseInterfaceFile(
    join(packageRoot, "lib", "model", `${kebabCase(modelName)}.d.ts`),
    modelName
  );
  if (!fields) {
    return;
  }
  models[modelName] = { fields };

  for (const field of fields) {
    for (const modelRef of field.modelRefs ?? []) {
      discoverModel(packageRoot, modelRef, models, depth + 1);
    }
  }
}

function parseInterfaceFile(filePath: string, interfaceName: string): FieldDiscovery[] | null {
  if (!existsSync(filePath)) {
    return null;
  }
  const source = readFileSync(filePath, "utf8");
  const body = blockBody(
    source,
    new RegExp(`export\\s+interface\\s+${interfaceName}\\b[^\\{]*\\{`, "m")
  );
  if (!body) {
    return null;
  }

  const fields: FieldDiscovery[] = [];
  const fieldPattern = /^\s{4}"([^"]+)"(\?)?:\s*([^;\n]+(?:\n\s{8}[^;\n]+)*);/gm;
  let match: RegExpExecArray | null;
  while ((match = fieldPattern.exec(body)) !== null) {
    const type = normalizeType(match[3]);
    const modelRefs = Array.from(type.matchAll(/\bmodel\.([A-Za-z][A-Za-z0-9_]*)/g))
      .map(refMatch => refMatch[1]);
    fields.push({
      name: match[1],
      required: match[2] !== "?",
      type,
      ...(modelRefs.length > 0 ? { modelRefs } : {})
    });
  }
  return fields;
}

function blockBody(source: string, startPattern: RegExp): string | null {
  const match = startPattern.exec(source);
  if (!match) {
    return null;
  }

  let depth = 1;
  let index = match.index + match[0].length;
  const bodyStart = index;
  for (; index < source.length; index += 1) {
    const char = source[index];
    if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) {
        return source.slice(bodyStart, index);
      }
    }
  }
  return null;
}

function discoverResponseShape(packageRoot: string, operation: string): Record<string, unknown> | null {
  const clientSourcePath = join(packageRoot, "lib", "client.js");
  if (!existsSync(clientSourcePath)) {
    return null;
  }
  const source = readFileSync(clientSourcePath, "utf8");
  const operationSource = blockBody(
    source,
    new RegExp(`\\n\\s{4}${operation}\\(${operation}Request\\)\\s*\\{`)
  );
  if (!operationSource) {
    return null;
  }

  const bodyKey = /bodyKey:\s*"([^"]+)"/.exec(operationSource)?.[1];
  const bodyModel = /bodyModel:\s*model\.([A-Za-z][A-Za-z0-9_]*)/.exec(operationSource)?.[1];
  const nextPage = operationSource.includes("opc-next-page");
  const requestId = operationSource.includes("opc-request-id");
  if (!bodyKey && !bodyModel && !nextPage && !requestId) {
    return null;
  }
  return {
    ...(bodyKey ? { bodyKey } : {}),
    ...(bodyModel ? { bodyModel } : {}),
    ...(nextPage ? { pagination: { nextPageField: "opcNextPage", requestPageField: "page" } } : {}),
    ...(requestId ? { requestIdField: "opcRequestId" } : {})
  };
}

function requestExample(
  requestFields: FieldDiscovery[],
  models: Record<string, ModelDiscovery>
): Record<string, unknown> {
  const example: Record<string, unknown> = {};
  for (const field of requestFields.filter(field => field.required)) {
    example[field.name] = exampleForField(field, models, 0);
  }
  return example;
}

function exampleForField(
  field: FieldDiscovery,
  models: Record<string, ModelDiscovery>,
  depth: number
): unknown {
  const firstModel = field.modelRefs?.[0];
  if (firstModel && depth < MAX_DISCOVERY_MODEL_DEPTH) {
    const modelFields = models[firstModel]?.fields ?? [];
    const value: Record<string, unknown> = {};
    for (const modelField of modelFields.filter(modelField => modelField.required)) {
      value[modelField.name] = exampleForField(modelField, models, depth + 1);
    }
    return value;
  }
  if (/\bboolean\b/.test(field.type)) {
    return false;
  }
  if (/\bnumber\b/.test(field.type)) {
    return 0;
  }
  if (/\[\]|\bArray</.test(field.type)) {
    return [];
  }
  return `<${field.name}>`;
}

function normalizeType(type: string): string {
  return type
    .replace(/\s+/g, " ")
    .replace(/\s*;\s*$/g, "")
    .trim();
}

function pascalCase(value: string): string {
  return value
    .replace(/(^|[_-])([a-zA-Z0-9])/g, (_match, _separator, char: string) => char.toUpperCase())
    .replace(/[^A-Za-z0-9]/g, "");
}

function kebabCase(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/([A-Z])([A-Z][a-z])/g, "$1-$2")
    .toLowerCase();
}

function authenticationProvider(loadSdk: OciSdkLoader): any {
  const { sdk, common } = loadSdk();
  const configFile = process.env.OCI_CONFIG_FILE
    ? resolve(process.env.OCI_CONFIG_FILE)
    : join(homedir(), ".oci", "config");
  const profile = process.env.OCI_CONFIG_PROFILE ?? "DEFAULT";
  const profileConfig = readProfile(configFile, profile);

  if (profileConfig.security_token_file && typeof common.SessionAuthDetailProvider === "function") {
    return new common.SessionAuthDetailProvider(configFile, profile);
  }

  const Provider = sdk.ConfigFileAuthenticationDetailsProvider
    ?? common.ConfigFileAuthenticationDetailsProvider;
  if (typeof Provider !== "function") {
    throw new Error("OCI JavaScript SDK authentication provider is unavailable");
  }
  return new Provider(configFile, profile);
}

function readProfile(configFile: string, profile: string): Record<string, string> {
  if (!existsSync(configFile)) {
    return {};
  }
  const wanted = profile.toUpperCase();
  const result: Record<string, string> = {};
  let active = false;

  for (const rawLine of readFileSync(configFile, "utf8").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#") || line.startsWith(";")) {
      continue;
    }
    const section = line.match(/^\[(.+)]$/);
    if (section) {
      active = section[1].toUpperCase() === wanted;
      continue;
    }
    if (!active) {
      continue;
    }
    const equalsIndex = line.indexOf("=");
    if (equalsIndex === -1) {
      continue;
    }
    const key = line.slice(0, equalsIndex).trim();
    const value = line.slice(equalsIndex + 1).trim();
    result[key] = value;
  }
  return result;
}

function decodeRequest(request: JsonObject): Record<string, any> {
  const decoded = fromJson(request);
  if (!decoded || typeof decoded !== "object" || Array.isArray(decoded)) {
    throw new Error("OCI request must decode to an object");
  }
  return decoded as Record<string, any>;
}

function callOptional(target: any, method: string): any {
  if (target && typeof target[method] === "function") {
    try {
      return target[method]();
    } catch {
      return null;
    }
  }
  return null;
}

function firstNonEmptyString(...values: unknown[]): string | null {
  for (const value of values) {
    if (typeof value === "string" && value.trim()) {
      return value;
    }
  }
  return null;
}

function validateClientPayload(client: unknown): asserts client is OciInvokePayload["client"] {
  if (!client || typeof client !== "object" || Array.isArray(client)) {
    throw new Error("Invalid OCI client payload");
  }
  const keys = Object.keys(client);
  for (const key of keys) {
    if (key !== "name" && key !== "options") {
      throw new Error(`Unsupported OCI client field '${key}'`);
    }
  }
  validateIdentifier((client as { name?: unknown }).name, "client");
  validateClientOptions((client as { options?: unknown }).options);
}

function validateClientOptions(options: unknown): asserts options is OciInvokePayload["client"]["options"] {
  if (options === undefined) {
    return;
  }
  if (!options || typeof options !== "object" || Array.isArray(options)) {
    throw new Error("OCI client options must be an object");
  }
  for (const key of Object.keys(options)) {
    if (key !== "region") {
      throw new Error(
        `Unsupported OCI client option '${key}'. Client options only support region; `
        + "pass tenancyId, compartmentId, and other OCI values in operation request objects."
      );
    }
  }
  const region = (options as { region?: unknown }).region;
  if (region !== undefined && (typeof region !== "string" || !REGION_ID_PATTERN.test(region))) {
    throw new Error(`Invalid OCI client option region '${String(region)}'`);
  }
}

function applyClientOptions(provider: any, options: OciInvokePayload["client"]["options"]): void {
  if (!options?.region) {
    return;
  }
  if (typeof provider?.setRegion !== "function") {
    throw new Error("OCI authentication provider does not support per-client region selection");
  }
  provider.setRegion(options.region);
}

function createClientConfiguration(
  common: Record<string, any>,
  timeout?: number
): OciClientConfiguration | undefined {
  const configuration: OciClientConfiguration = {};
  if (
    timeout !== undefined
    && Number.isFinite(timeout)
    && timeout > 0
    && typeof common.CircuitBreaker === "function"
  ) {
    configuration.circuitBreaker = new common.CircuitBreaker({
      timeout: Math.max(1, Math.ceil(timeout))
    });
  }
  return Object.keys(configuration).length > 0 ? configuration : undefined;
}

function validateIdentifier(value: unknown, name: string): asserts value is string {
  if (typeof value !== "string" || !IDENTIFIER_PATTERN.test(value)) {
    throw new Error(`Invalid OCI ${name} '${String(value)}'`);
  }
}

function tooLargeMessage(payload: OciInvokePayload, size: number): string {
  const base = (
    `OCI response from ${payload.service}.${payload.client.name}.${payload.operation} was `
    + `${size} bytes, exceeding response limit ${MAX_HOST_RPC_RESPONSE_BYTES} bytes.`
  );
  if (LIST_OPERATION_PATTERN.test(payload.operation)) {
    return `${base} Pass a smaller limit and follow the response page token for additional pages.`;
  }
  return `${base} Narrow the request or return only the fields needed.`;
}

function stripHttpTransportArtifacts(
  value: unknown,
  seen: WeakSet<object>,
  depth: number
): unknown {
  if (depth > MAX_SANITIZE_DEPTH) {
    return "[MaxDepth]";
  }
  if (!value || typeof value !== "object") {
    return value;
  }
  if (
    value instanceof Date
    || value instanceof Uint8Array
    || value instanceof Map
    || value instanceof Set
    || value instanceof Error
  ) {
    return value;
  }
  if (seen.has(value)) {
    return "[Circular]";
  }

  seen.add(value);
  try {
    if (Array.isArray(value)) {
      return value.map(item => stripHttpTransportArtifacts(item, seen, depth + 1));
    }

    const result: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value)) {
      if (SDK_CREDENTIAL_FIELD_PATTERN.test(key) || isSdkTransportField(key, item)) {
        continue;
      }
      result[key] = stripHttpTransportArtifacts(item, seen, depth + 1);
    }
    return result;
  } finally {
    seen.delete(value);
  }
}

function isSdkTransportField(key: string, value: unknown): boolean {
  if (!value || typeof value !== "object") {
    return false;
  }
  if (key === "httpRequest" || key === "httpResponse") {
    return true;
  }
  return (key === "request" || key === "response") && looksLikeHttpTransport(value);
}

function looksLikeHttpTransport(value: object): boolean {
  const keys = new Set(Object.keys(value).map(key => key.toLowerCase()));
  return keys.has("headers")
    && (
      keys.has("method")
      || keys.has("uri")
      || keys.has("url")
      || keys.has("status")
      || keys.has("body")
    );
}

function positiveIntegerEnv(name: string, fallback: number): number {
  const value = integerEnv(name, fallback);
  return value > 0 ? value : fallback;
}

function integerEnv(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined) {
    return fallback;
  }
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) ? value : fallback;
}
