/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { Json } from "./types.ts";

const WIRE_TYPE_KEY = "__oci_wire_type";

export function fromJson(value: Json): unknown {
  return decode(value);
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
