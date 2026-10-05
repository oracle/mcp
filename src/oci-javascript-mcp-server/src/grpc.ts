/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { HostMessage, RunnerMessage } from "./generated/runner.ts";
import { DEFAULT_MAX_FRAME_BYTES, ProtocolError } from "./protocol.ts";
import { MAX_CODE_BYTES, MAX_STDERR_BYTES, MAX_STDOUT_BYTES } from "./sandbox-common.ts";

export { RunnerClient, RunnerService as RUNNER_SERVICE } from "./generated/runner.ts";
export type { HostMessage, RunnerMessage } from "./generated/runner.ts";

// Bound the combined payload; individual JSON/text limits still apply.
export const MAX_GRPC_MESSAGE_BYTES = Math.max(
  DEFAULT_MAX_FRAME_BYTES + 2 * MAX_CODE_BYTES,
  2 * DEFAULT_MAX_FRAME_BYTES + 2 * (MAX_STDOUT_BYTES + MAX_STDERR_BYTES)
) + 64 * 1024;

export function encodeText(text: string, maxUtf8Bytes: number): Buffer {
  if (Buffer.byteLength(text, "utf8") > maxUtf8Bytes) {
    throw new ProtocolError(`text exceeds limit ${maxUtf8Bytes}`);
  }
  return Buffer.from(text, "utf16le");
}

export function decodeText(body: Uint8Array, maxUtf8Bytes: number): string {
  if (body.byteLength % 2 !== 0 || body.byteLength > 2 * maxUtf8Bytes) {
    throw new ProtocolError(`invalid bounded UTF-16LE text`);
  }
  const text = Buffer.from(body).toString("utf16le");
  if (Buffer.byteLength(text, "utf8") > maxUtf8Bytes) {
    throw new ProtocolError(`text exceeds limit ${maxUtf8Bytes}`);
  }
  return text;
}

// Protobuf decoding alone does not require a oneof to be present. Also reject
// multiple known variants. Keep flat oneof fields in the generated codecs so
// decoding preserves conflicting variants instead of silently keeping the last.
export function validateEnvelope(message: HostMessage | RunnerMessage): void {
  const variants = Object.values(message).filter(value => value !== undefined);
  if (variants.length !== 1) {
    throw new ProtocolError("expected exactly one protocol message body");
  }
}
