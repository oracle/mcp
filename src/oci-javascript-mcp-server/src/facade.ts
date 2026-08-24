/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { Json, JsonObject, ReflectionManifest, RpcOperation } from "./types.ts";

const IDENTIFIER = /^[A-Za-z][A-Za-z0-9_]*$/;
const REGION = /^[a-z][a-z0-9-]*-[a-z0-9-]+-[0-9]+$/;
const RESERVED = new Set(["then", "catch", "finally", "toJSON"]);

export type FacadeRpc = (operation: RpcOperation, payload: JsonObject) => Promise<Json>;

export function createOciFacade(manifest: ReflectionManifest, rpc: FacadeRpc): object {
  const services = new Map<string, object>();
  const clients = new Map<string, object>();

  const makeClient = (service: string, client: string, options?: unknown): object => {
    validateName(service, "service");
    validateName(client, "client");
    const normalized = normalizeOptions(options);
    const cacheKey = `${service}.${client}.${normalized.region ?? ""}`;
    const cached = clients.get(cacheKey);
    if (cached) return cached;
    const operations = manifest.services[service]?.clients[client]?.operations ?? [];
    const target = Object.create(null) as Record<string, unknown>;
    let proxy!: Record<string, unknown>;
    proxy = new Proxy(target, {
      get(_target, property) {
        if (typeof property !== "string" || property.startsWith("_") || RESERVED.has(property)) {
          return undefined;
        }
        validateName(property, "operation");
        return async (request: JsonObject = {}) => rpc("invoke", {
          service,
          client: Object.keys(normalized).length > 0
            ? { name: client, options: normalized }
            : { name: client },
          operation: property,
          request
        });
      },
      ownKeys() { return [...operations]; },
      getOwnPropertyDescriptor(_target, property) {
        if (typeof property === "string" && operations.includes(property)) {
          return { value: proxy[property], enumerable: true, configurable: true };
        }
        return undefined;
      }
    });
    clients.set(cacheKey, proxy);
    return proxy;
  };

  const makeClientFactory = (service: string, client: string): Function => {
    const operations = manifest.services[service]?.clients[client]?.operations ?? [];
    const target = function OciClient(options?: unknown) {
      return makeClient(service, client, options);
    };
    return new Proxy(target, {
      construct(_target, args) { return makeClient(service, client, args[0]); },
      get(targetValue, property) {
        if (Reflect.has(targetValue, property)) return Reflect.get(targetValue, property);
        if (typeof property !== "string" || RESERVED.has(property)) return undefined;
        return (makeClient(service, client) as Record<string, unknown>)[property];
      },
      ownKeys(targetValue) {
        return mergeKeys(Reflect.ownKeys(targetValue), operations);
      },
      getOwnPropertyDescriptor(targetValue, property) {
        return Reflect.getOwnPropertyDescriptor(targetValue, property)
          ?? (typeof property === "string" && operations.includes(property)
            ? { value: (makeClient(service, client) as Record<string, unknown>)[property], enumerable: true, configurable: true }
            : undefined);
      }
    });
  };

  const makeService = (service: string): object => {
    const cached = services.get(service);
    if (cached) return cached;
    const clientNames = Object.keys(manifest.services[service]?.clients ?? {});
    const target = Object.create(null) as Record<string, unknown>;
    const proxy = new Proxy(target, {
      get(_target, property) {
        if (typeof property !== "string" || property.startsWith("_") || RESERVED.has(property)) {
          return undefined;
        }
        validateName(property, "client");
        return makeClientFactory(service, property);
      },
      ownKeys() { return clientNames; },
      getOwnPropertyDescriptor(_target, property) {
        if (typeof property === "string" && clientNames.includes(property)) {
          return { value: makeClientFactory(service, property), enumerable: true, configurable: true };
        }
        return undefined;
      }
    });
    services.set(service, proxy);
    return proxy;
  };

  const serviceNames = Object.keys(manifest.services);
  const target = Object.create(null) as Record<string, unknown>;
  Object.defineProperty(target, "config", {
    value: async () => rpc("config", {}), enumerable: true, writable: false, configurable: false
  });
  return new Proxy(target, {
    get(targetValue, property) {
      if (Reflect.has(targetValue, property)) return Reflect.get(targetValue, property);
      if (typeof property !== "string" || property.startsWith("_") || RESERVED.has(property)) {
        return undefined;
      }
      return serviceNames.includes(property) ? makeService(property) : undefined;
    },
    ownKeys(targetValue) { return mergeKeys(Reflect.ownKeys(targetValue), serviceNames); },
    getOwnPropertyDescriptor(targetValue, property) {
      return Reflect.getOwnPropertyDescriptor(targetValue, property)
        ?? (typeof property === "string" && serviceNames.includes(property)
          ? { value: makeService(property), enumerable: true, configurable: true }
          : undefined);
    }
  });
}

export function inferFinalExpression(code: string): string {
  const trimmed = code.replace(/[\s;]*$/g, "");
  for (const start of finalExpressionStarts(trimmed)) {
    const expression = trimmed.slice(start).trim();
    if (expression && isExpression(expression)) {
      return `${trimmed.slice(0, start)}\nreturn (${expression});`;
    }
  }
  return code;
}

function finalExpressionStarts(code: string): number[] {
  const starts = [0];
  let depth = 0;
  let quote: string | null = null;
  let escaped = false;
  let lineComment = false;
  let blockComment = false;
  for (let index = 0; index < code.length; index += 1) {
    const char = code[index]!;
    const next = code[index + 1];
    if (lineComment) {
      if (char === "\n") { lineComment = false; starts.push(index + 1); }
      continue;
    }
    if (blockComment) {
      if (char === "*" && next === "/") { blockComment = false; index += 1; }
      continue;
    }
    if (quote) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === quote) quote = null;
      continue;
    }
    if (char === "/" && next === "/") { lineComment = true; index += 1; continue; }
    if (char === "/" && next === "*") { blockComment = true; index += 1; continue; }
    if (char === "\"" || char === "'" || char === "`") { quote = char; continue; }
    if ("([{ ".trim().includes(char)) depth += 1;
    else if (")] }".replace(" ", "").includes(char)) depth = Math.max(0, depth - 1);
    else if (depth === 0 && (char === ";" || char === "\n")) starts.push(index + 1);
  }
  return starts.reverse();
}

function isExpression(source: string): boolean {
  try {
    new Function(`return (async () => (${source}));`);
    return true;
  } catch {
    return false;
  }
}

function normalizeOptions(value: unknown): { region?: string } {
  if (value === undefined || value === null) return {};
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("OCI client options must be a plain object");
  }
  const record = value as Record<string, unknown>;
  for (const key of Object.keys(record)) {
    if (key !== "region") {
      throw new Error(`Unsupported OCI client option '${key}'. Client options only support region.`);
    }
  }
  if (record.region !== undefined && (typeof record.region !== "string" || !REGION.test(record.region))) {
    throw new Error(`Invalid OCI client option region '${String(record.region)}'`);
  }
  return typeof record.region === "string" ? { region: record.region } : {};
}

function validateName(value: string, label: string): void {
  if (!IDENTIFIER.test(value)) throw new Error(`Invalid OCI ${label} '${value}'`);
}

function mergeKeys(first: Array<string | symbol>, second: string[]): Array<string | symbol> {
  return [...new Set([...first, ...second])];
}
