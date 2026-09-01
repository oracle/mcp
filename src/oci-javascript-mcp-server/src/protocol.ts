/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { TextDecoder } from "node:util";
import type { Json, JsonObject } from "./types.ts";

export const PROTOCOL_VERSION = 1;
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

export type ProtocolMessage = JsonObject & {
  version: number;
  type: string;
};

export function encodeFrame(message: JsonObject, maxBytes = DEFAULT_MAX_FRAME_BYTES): Buffer {
  const body = Buffer.from(JSON.stringify(message), "utf8");
  if (body.length > maxBytes) {
    throw new ProtocolError(`frame length ${body.length} exceeds limit ${maxBytes}`);
  }
  const header = Buffer.allocUnsafe(4);
  header.writeUInt32BE(body.length, 0);
  return Buffer.concat([header, body]);
}

export function decodePayload(
  body: Uint8Array,
  limits: DecodeLimits = DEFAULT_DECODE_LIMITS
): ProtocolMessage {
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
  const value = canonicalize(parsed, limits);
  if (!isRecord(value)) {
    throw new ProtocolError("protocol message must be an object");
  }
  if (value.version !== PROTOCOL_VERSION) {
    throw new ProtocolError(`unsupported protocol version '${String(value.version)}'`);
  }
  if (typeof value.type !== "string") {
    throw new ProtocolError("protocol message type must be a string");
  }
  return value as ProtocolMessage;
}

export class FrameDecoder {
  readonly #limits: DecodeLimits;
  readonly #header = Buffer.allocUnsafe(4);
  #headerBytes = 0;
  #segments: Buffer[] = [];
  #bodyBytes = 0;
  #expected: number | undefined;
  #active = false;

  constructor(limits: DecodeLimits = DEFAULT_DECODE_LIMITS) {
    this.#limits = limits;
  }

  get queuedBytes(): number {
    return this.#headerBytes + this.#bodyBytes;
  }

  *push(chunk: Uint8Array): IterableIterator<ProtocolMessage> {
    if (this.#active) {
      throw new ProtocolError("frame decoder input cannot be processed concurrently");
    }
    this.#active = true;
    try {
      const input = Buffer.from(chunk.buffer, chunk.byteOffset, chunk.byteLength);
      let offset = 0;
      while (offset < input.length) {
        if (this.#expected === undefined) {
          const headerBytes = Math.min(4 - this.#headerBytes, input.length - offset);
          input.copy(this.#header, this.#headerBytes, offset, offset + headerBytes);
          this.#headerBytes += headerBytes;
          offset += headerBytes;
          if (this.#headerBytes < 4) {
            break;
          }
          this.#expected = this.#header.readUInt32BE(0);
          this.#headerBytes = 0;
          if (this.#expected === 0) {
            throw new ProtocolError("empty frames are not allowed");
          }
          if (this.#expected > this.#limits.maxFrameBytes) {
            throw new ProtocolError(
              `frame length ${this.#expected} exceeds limit ${this.#limits.maxFrameBytes}`
            );
          }
        }

        const bodyBytes = Math.min(
          this.#expected - this.#bodyBytes,
          input.length - offset
        );
        if (bodyBytes > 0) {
          this.#segments.push(input.subarray(offset, offset + bodyBytes));
          this.#bodyBytes += bodyBytes;
          offset += bodyBytes;
        }
        if (this.#bodyBytes < this.#expected) {
          break;
        }

        const body = Buffer.allocUnsafe(this.#expected);
        let bodyOffset = 0;
        for (const segment of this.#segments) {
          segment.copy(body, bodyOffset);
          bodyOffset += segment.length;
        }
        this.#segments = [];
        this.#bodyBytes = 0;
        this.#expected = undefined;
        yield decodePayload(body, this.#limits);
      }
    } finally {
      this.#active = false;
    }
  }

  end(): void {
    if (this.#active || this.#expected !== undefined || this.#headerBytes !== 0) {
      throw new ProtocolError("truncated protocol frame");
    }
  }
}

export function assertExactFields(
  value: JsonObject,
  required: readonly string[],
  optional: readonly string[] = []
): void {
  const allowed = new Set([...required, ...optional]);
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) {
      throw new ProtocolError(`unknown field '${key}' in ${String(value.type ?? "message")}`);
    }
  }
  for (const key of required) {
    if (!Object.hasOwn(value, key)) {
      throw new ProtocolError(`missing field '${key}' in ${String(value.type ?? "message")}`);
    }
  }
}

export function protocolMessage(type: string, fields: JsonObject = {}): JsonObject {
  return { version: PROTOCOL_VERSION, type, ...fields };
}

export class ProtocolError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProtocolError";
  }
}

function canonicalize(value: unknown, limits: DecodeLimits): Json {
  let nodes = 0;
  let keys = 0;
  const visit = (item: unknown, depth: number): Json => {
    nodes += 1;
    if (nodes > limits.maxNodes) {
      throw new ProtocolError(`decoded value exceeds node limit ${limits.maxNodes}`);
    }
    if (depth > limits.maxDepth) {
      throw new ProtocolError(`decoded value exceeds depth limit ${limits.maxDepth}`);
    }
    if (item === null || typeof item === "boolean") {
      return item;
    }
    if (typeof item === "number") {
      if (!Number.isFinite(item)) {
        throw new ProtocolError("non-finite numbers are not allowed");
      }
      return item;
    }
    if (typeof item === "string") {
      if (Buffer.byteLength(item, "utf8") > limits.maxStringBytes) {
        throw new ProtocolError(`string exceeds limit ${limits.maxStringBytes}`);
      }
      return item;
    }
    if (Array.isArray(item)) {
      if (item.length > limits.maxArrayLength) {
        throw new ProtocolError(`array exceeds length limit ${limits.maxArrayLength}`);
      }
      return item.map(entry => visit(entry, depth + 1));
    }
    if (!item || typeof item !== "object") {
      throw new ProtocolError(`unsupported JSON value '${typeof item}'`);
    }
    const entries = Object.entries(item);
    keys += entries.length;
    if (keys > limits.maxObjectKeys) {
      throw new ProtocolError(`decoded value exceeds object-key limit ${limits.maxObjectKeys}`);
    }
    const output = Object.create(null) as JsonObject;
    for (const [key, child] of entries) {
      if (DANGEROUS_KEYS.has(key)) {
        throw new ProtocolError(`dangerous key '${key}' is not allowed`);
      }
      if (Buffer.byteLength(key, "utf8") > limits.maxStringBytes) {
        throw new ProtocolError(`object key exceeds limit ${limits.maxStringBytes}`);
      }
      output[key] = visit(child, depth + 1);
    }
    return output;
  };
  return visit(value, 0);
}

function isRecord(value: Json): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
