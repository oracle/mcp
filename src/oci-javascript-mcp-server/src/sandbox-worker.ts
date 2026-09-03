#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { takeCoverage } from "node:v8";

import {
  DEFAULT_DECODE_LIMITS,
  FrameDecoder,
  ProtocolError,
  assertExactFields,
  encodeFrame,
  protocolMessage
} from "./protocol.ts";
import { runJavaScriptInIsolate } from "./sandbox-isolate.ts";
import type { Json, JsonObject, OciReflectionManifest } from "./types.ts";

type PendingRpc = {
  resolve: (value: Json) => void;
  reject: (error: Error) => void;
};

// The execute frame contains a trusted, host-generated SDK reflection manifest.
// Frames emitted by sandbox code are decoded by the host with tighter defaults.
const decoder = new FrameDecoder({
  ...DEFAULT_DECODE_LIMITS,
  maxObjectKeys: 100_000,
  maxNodes: 250_000
});
const pendingRpc = new Map<number, PendingRpc>();
let nextRpcId = 1;
let running = false;
let terminal = false;

send("health", { status: "ready" });
process.stdin.on("data", chunk => {
  try {
    for (const message of decoder.push(
      typeof chunk === "string" ? Buffer.from(chunk) : chunk
    )) {
      void handleMessage(message).catch(fatal);
    }
  } catch (error) {
    fatal(error);
  }
});
process.stdin.on("end", () => {
  if (terminal) {
    return;
  }
  try {
    decoder.end();
  } catch (error) {
    fatal(error);
    return;
  }
  terminal = true;
  rejectPending(new Error("sandbox host channel closed"));
  process.exitCode = 1;
});
process.stdin.resume();

async function handleMessage(message: JsonObject): Promise<void> {
  if (terminal) {
    return;
  }
  if (message.type === "execute") {
    assertExactFields(message, [
      "version",
      "type",
      "code",
      "timeoutMs",
      "reflectionManifest",
      "memoryLimitMb",
      "maxResultBytes"
    ]);
    if (running) {
      throw new ProtocolError("sandbox worker accepts exactly one execution");
    }
    if (
      typeof message.code !== "string"
      || !isPositiveInteger(message.timeoutMs)
      || !isObject(message.reflectionManifest)
      || !isPositiveInteger(message.memoryLimitMb)
      || !isPositiveInteger(message.maxResultBytes)
    ) {
      throw new ProtocolError("invalid sandbox execute message");
    }
    running = true;
    await execute(
      message.code,
      message.timeoutMs,
      message.reflectionManifest as unknown as OciReflectionManifest,
      message.memoryLimitMb,
      message.maxResultBytes
    );
    return;
  }

  if (message.type === "rpc_result") {
    assertExactFields(message, ["version", "type", "id", "result"]);
    if (!Number.isInteger(message.id)) {
      throw new ProtocolError("invalid sandbox RPC result");
    }
    const pending = pendingRpc.get(message.id as number);
    if (!pending) {
      throw new ProtocolError("unknown sandbox RPC response id");
    }
    pendingRpc.delete(message.id as number);
    pending.resolve(message.result ?? null);
    return;
  }

  if (message.type === "cancel") {
    assertExactFields(message, ["version", "type"]);
    terminal = true;
    rejectPending(new Error("sandbox execution cancelled"));
    exitWorker(124);
    return;
  }

  throw new ProtocolError(`unsupported host message type '${String(message.type)}'`);
}

async function execute(
  code: string,
  timeoutMs: number,
  reflectionManifest: OciReflectionManifest,
  memoryLimitMb: number,
  maxResultBytes: number
): Promise<void> {
  const result = await runJavaScriptInIsolate(code, {
    timeoutSeconds: timeoutMs / 1000,
    hostRpc,
    reflectionManifest,
    memoryLimitMb,
    maxResultBytes
  });
  if (result.stdout) {
    send("log", { stream: "stdout", text: result.stdout });
  }
  if (result.stderr) {
    send("log", { stream: "stderr", text: result.stderr });
  }
  sendAndExit("result", {
    result: result.result,
    error: result.error,
    exitCode: result.exitCode,
    timedOut: result.timedOut
  }, result.exitCode === 0 ? 0 : 1);
}

function hostRpc(request: unknown): Promise<Json> {
  const id = nextRpcId;
  nextRpcId += 1;
  return new Promise((resolve, reject) => {
    pendingRpc.set(id, { resolve, reject });
    try {
      send("rpc", {
        id,
        request: request as Json
      });
    } catch (error) {
      pendingRpc.delete(id);
      reject(error instanceof Error ? error : new Error(String(error)));
    }
  });
}

function send(type: string, fields: JsonObject = {}): void {
  process.stdout.write(encodeFrame(protocolMessage(type, fields)));
}

function sendAndExit(type: string, fields: JsonObject, exitCode: number): void {
  if (terminal) {
    return;
  }
  terminal = true;
  if (process.env.NODE_V8_COVERAGE) {
    try {
      takeCoverage();
    } catch {
      // Coverage collection must never affect the worker protocol result.
    }
  }
  process.stdout.write(
    encodeFrame(protocolMessage(type, fields)),
    () => exitWorker(exitCode)
  );
}

function fatal(_error: unknown): void {
  try {
    sendAndExit(
      "protocol_error",
      { error: { message: "sandbox protocol failure" } },
      70
    );
  } catch {
    // The channel may already be unusable.
    exitWorker(70);
  }
  rejectPending(new Error("sandbox protocol failure"));
}

function exitWorker(exitCode: number): void {
  process.exitCode = exitCode;
  process.stdin.destroy();
}

function rejectPending(error: Error): void {
  for (const pending of pendingRpc.values()) {
    pending.reject(error);
  }
  pendingRpc.clear();
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
