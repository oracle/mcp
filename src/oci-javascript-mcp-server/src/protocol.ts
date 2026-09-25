/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { TextDecoder } from "node:util";
import type { Json } from "./types.ts";

export const DEFAULT_MAX_FRAME_BYTES = 2 * 1024 * 1024;

export type DecodeLimits = Readonly<{
  maxFrameBytes: number;
  maxDepth: number;
  maxStringBytes: number;
  maxArrayLength: number;
  maxObjectKeys: number;
  maxNodes: number;
}>;

export const DEFAULT_DECODE_LIMITS: DecodeLimits = Object.freeze({
  maxFrameBytes: DEFAULT_MAX_FRAME_BYTES,
  maxDepth: 32,
  maxStringBytes: 1024 * 1024,
  maxArrayLength: 10_000,
  maxObjectKeys: 10_000,
  maxNodes: 50_000
});

const DANGEROUS_KEYS = new Set(["__proto__", "prototype", "constructor"]);

export function encodePayload(message: Json, maxBytes = DEFAULT_MAX_FRAME_BYTES): Buffer {
  const body = Buffer.from(JSON.stringify(message), "utf8");
  if (body.length > maxBytes) {
    throw new ProtocolError(`frame length ${body.length} exceeds limit ${maxBytes}`);
  }
  return body;
}

export function decodeJson(
  body: Uint8Array,
  limits: DecodeLimits = DEFAULT_DECODE_LIMITS
): Json {
  if (body.byteLength > limits.maxFrameBytes) {
    throw new ProtocolError(`frame length ${body.byteLength} exceeds limit ${limits.maxFrameBytes}`);
  }
  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(body);
  } catch {
    throw new ProtocolError("frame is not valid UTF-8");
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(text) as unknown;
  } catch {
    throw new ProtocolError("frame is not valid JSON");
  }
  validateJson(parsed, limits);
  return parsed as Json;
}

export class ProtocolError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProtocolError";
  }
}

// JSON.parse already creates plain data; validate it without rebuilding the tree.
function validateJson(value: unknown, limits: DecodeLimits): void {
  let nodes = 0;
  let keys = 0;
  const visit = (item: unknown, depth: number): void => {
    nodes += 1;
    if (nodes > limits.maxNodes) {
      throw new ProtocolError(`decoded value exceeds node limit ${limits.maxNodes}`);
    }
    if (depth > limits.maxDepth) {
      throw new ProtocolError(`decoded value exceeds depth limit ${limits.maxDepth}`);
    }
    if (item === null || typeof item === "boolean") {
      return;
    }
    if (typeof item === "number") {
      if (!Number.isFinite(item)) {
        throw new ProtocolError("non-finite numbers are not allowed");
      }
      return;
    }
    if (typeof item === "string") {
      if (Buffer.byteLength(item, "utf8") > limits.maxStringBytes) {
        throw new ProtocolError(`string exceeds limit ${limits.maxStringBytes}`);
      }
      return;
    }
    if (Array.isArray(item)) {
      if (item.length > limits.maxArrayLength) {
        throw new ProtocolError(`array exceeds length limit ${limits.maxArrayLength}`);
      }
      for (const entry of item) visit(entry, depth + 1);
      return;
    }
    if (!item || typeof item !== "object") {
      throw new ProtocolError(`unsupported JSON value '${typeof item}'`);
    }
    const entries = Object.entries(item);
    keys += entries.length;
    if (keys > limits.maxObjectKeys) {
      throw new ProtocolError(`decoded value exceeds object-key limit ${limits.maxObjectKeys}`);
    }
    for (const [key, child] of entries) {
      if (DANGEROUS_KEYS.has(key)) {
        throw new ProtocolError(`dangerous key '${key}' is not allowed`);
      }
      if (Buffer.byteLength(key, "utf8") > limits.maxStringBytes) {
        throw new ProtocolError(`object key exceeds limit ${limits.maxStringBytes}`);
      }
      visit(child, depth + 1);
    }
  };
  visit(value, 0);
}
