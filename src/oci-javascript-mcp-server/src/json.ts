/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { Json } from "./types.ts";

const WIRE_TYPE_KEY = "__oci_wire_type";
const MAX_DEPTH = 80;

export function toJson(value: unknown): Json {
  return encode(value, 0, new WeakSet<object>());
}

export function fromJson(value: Json): unknown {
  return decode(value);
}

function encode(value: unknown, depth: number, seen: WeakSet<object>): Json {
  if (depth > MAX_DEPTH) {
    return wireValue("repr", { value: "[MaxDepth]" });
  }
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (Number.isFinite(value)) {
      return value;
    }
    if (Number.isNaN(value)) {
      return wireValue("float", { value: "nan" });
    }
    return wireValue("float", { value: value > 0 ? "inf" : "-inf" });
  }
  if (typeof value === "bigint") {
    return wireValue("bigint", { value: value.toString() });
  }
  if (typeof value === "function" || typeof value === "symbol") {
    return wireValue("repr", { value: String(value) });
  }

  if (value instanceof Date) {
    return wireValue("datetime", { value: value.toISOString() });
  }
  if (value instanceof Uint8Array) {
    return wireValue("bytes", {
      encoding: "base64",
      value: Buffer.from(value).toString("base64")
    });
  }

  if (typeof value === "object") {
    if (seen.has(value)) {
      return wireValue("repr", { value: "[Circular]" });
    }
    seen.add(value);
    try {
      if (Array.isArray(value)) {
        return value.map(item => encode(item, depth + 1, seen));
      }
      if (value instanceof Map) {
        return wireValue("map", {
          items: Array.from(value.entries()).map(([key, item]) => [
            encode(key, depth + 1, seen),
            encode(item, depth + 1, seen)
          ])
        });
      }
      if (value instanceof Set) {
        return wireValue("set", {
          items: Array.from(value.values()).map(item => encode(item, depth + 1, seen))
        });
      }
      if (value instanceof Error) {
        return {
          name: value.name,
          message: value.message,
          stack: value.stack ?? null
        };
      }
      const result: Record<string, Json> = {};
      for (const [key, item] of Object.entries(value)) {
        if (item !== undefined) {
          result[key] = encode(item, depth + 1, seen);
        }
      }
      return result;
    } finally {
      seen.delete(value);
    }
  }

  return wireValue("repr", { value: String(value) });
}

function wireValue(typeName: string, fields: Record<string, Json>): Json {
  return { [WIRE_TYPE_KEY]: typeName, ...fields };
}

function decode(value: Json): unknown {
  if (Array.isArray(value)) {
    return value.map(item => decode(item));
  }
  if (!value || typeof value !== "object") {
    return value;
  }

  const wireType = value[WIRE_TYPE_KEY];
  if (wireType === "datetime" || wireType === "date" || wireType === "time") {
    return new Date(String(value.value));
  }
  if (wireType === "bigint") {
    return BigInt(String(value.value));
  }
  if (wireType === "bytes") {
    return Buffer.from(String(value.value ?? ""), "base64");
  }
  if (wireType === "float") {
    return decodeFloat(value.value);
  }
  if (wireType === "map") {
    const items = Array.isArray(value.items) ? value.items : [];
    return new Map(items.map(item => {
      const pair = Array.isArray(item) ? item : [];
      return [decode(pair[0] ?? null), decode(pair[1] ?? null)];
    }));
  }
  if (wireType === "set") {
    const items = Array.isArray(value.items) ? value.items : [];
    return new Set(items.map(item => decode(item)));
  }
  if (wireType === "repr") {
    return value.value;
  }
  if (WIRE_TYPE_KEY in value) {
    throw new Error(`Unknown OCI wire type '${String(wireType)}'`);
  }

  const result: Record<string, unknown> = {};
  for (const [key, item] of Object.entries(value)) {
    result[key] = decode(item);
  }
  return result;
}

function decodeFloat(value: Json | undefined): number {
  if (value === "nan") {
    return Number.NaN;
  }
  if (value === "inf") {
    return Number.POSITIVE_INFINITY;
  }
  if (value === "-inf") {
    return Number.NEGATIVE_INFINITY;
  }
  return Number(value);
}
