#!/usr/bin/env -S node --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import vm from "node:vm";
import { inspect } from "node:util";
import { createOciFacade, inferFinalExpression } from "./facade.ts";
import {
  FrameDecoder,
  ProtocolError,
  DEFAULT_DECODE_LIMITS,
  assertExactFields,
  encodeFrame,
  protocolMessage
} from "./protocol.ts";
import { sanitizeJson } from "./oci.ts";
import type { Json, JsonObject, ReflectionManifest, RpcOperation } from "./types.ts";

// The execute frame contains a trusted host-generated SDK manifest. Guest frames
// are decoded by the host with the tighter defaults.
const decoder = new FrameDecoder({
  ...DEFAULT_DECODE_LIMITS,
  maxObjectKeys: 100_000,
  maxNodes: 250_000
});
const pending = new Map<number, { resolve(value: Json): void; reject(error: Error): void }>();
let nextRpcId = 1;
let running = false;

send("health", { status: "ready" });
process.stdin.on("data", chunk => {
  try {
    for (const message of decoder.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk)) {
      void handle(message).catch(fatal);
    }
  } catch (error) {
    fatal(error);
  }
});
process.stdin.on("end", () => {
  try { decoder.end(); } catch (error) { fatal(error); return; }
  rejectPending(new Error("broker channel closed"));
  process.exitCode = 1;
});
process.stdin.resume();

async function handle(message: JsonObject): Promise<void> {
  if (message.type === "execute") {
    assertExactFields(message, [
      "version", "type", "code", "manifest", "timeoutMs", "maxResultBytes", "maxOutputBytes"
    ]);
    if (running) throw new ProtocolError("runner accepts exactly one execution");
    if (typeof message.code !== "string" || !isObject(message.manifest)
      || !Number.isInteger(message.timeoutMs) || !Number.isInteger(message.maxResultBytes)
      || !Number.isInteger(message.maxOutputBytes)) {
      throw new ProtocolError("invalid execute message");
    }
    running = true;
    await execute(
      message.code,
      message.manifest as unknown as ReflectionManifest,
      message.timeoutMs as number,
      message.maxResultBytes as number,
      message.maxOutputBytes as number
    );
    return;
  }
  if (message.type === "rpc_result") {
    assertExactFields(message, ["version", "type", "id", "ok"], ["value", "error"]);
    if (!Number.isInteger(message.id) || typeof message.ok !== "boolean") {
      throw new ProtocolError("invalid rpc_result message");
    }
    const waiter = pending.get(message.id as number);
    if (!waiter) throw new ProtocolError("unknown RPC response id");
    pending.delete(message.id as number);
    if (message.ok) waiter.resolve(message.value ?? null);
    else waiter.reject(new Error(errorMessage(message.error)));
    return;
  }
  if (message.type === "cancel") {
    assertExactFields(message, ["version", "type"], ["reason"]);
    rejectPending(new Error(typeof message.reason === "string" ? message.reason : "execution cancelled"));
    process.exit(124);
  }
  throw new ProtocolError(`unsupported host message type '${String(message.type)}'`);
}

async function execute(
  code: string,
  manifest: ReflectionManifest,
  timeoutMs: number,
  maxResultBytes: number,
  maxOutputBytes: number
): Promise<void> {
  let stdout = "";
  let stderr = "";
  const log = (stream: "stdout" | "stderr", values: unknown[]) => {
    const text = `${values.map(value => typeof value === "string" ? value : inspect(value, { depth: 4 })).join(" ")}\n`;
    const current = stream === "stdout" ? stdout : stderr;
    const remaining = Math.max(0, maxOutputBytes - Buffer.byteLength(current, "utf8"));
    const bounded = Buffer.from(text, "utf8").subarray(0, remaining).toString("utf8");
    if (stream === "stdout") stdout += bounded;
    else stderr += bounded;
    if (bounded) send("log", { stream, text: bounded });
  };
  const facade = createOciFacade(manifest, rpc);
  const sandbox = Object.create(null) as Record<string, unknown>;
  Object.defineProperties(sandbox, {
    oci: { value: facade, enumerable: true, writable: false, configurable: false },
    console: {
      value: Object.freeze({ log: (...values: unknown[]) => log("stdout", values), error: (...values: unknown[]) => log("stderr", values), warn: (...values: unknown[]) => log("stderr", values) }),
      enumerable: true, writable: false, configurable: false
    }
  });
  const context = vm.createContext(sandbox, {
    name: "oci-javascript-runner-context",
    codeGeneration: { strings: false, wasm: false }
  });
  try {
    const wrapped = `"use strict"; (async () => {\n${inferFinalExpression(code)}\n})()`;
    const script = new vm.Script(wrapped, { filename: "agent-code.js" });
    const promise = script.runInContext(context, { timeout: Math.max(1, timeoutMs) });
    const result = sanitizeJson(await promise);
    const bytes = Buffer.byteLength(JSON.stringify(result), "utf8");
    if (bytes > maxResultBytes) throw new Error(`result exceeds ${maxResultBytes} bytes`);
    sendAndExit("result", { result, error: null, exitCode: 0, timedOut: false }, 0);
  } catch (error) {
    sendAndExit("result", {
      result: null,
      error: safeError(error),
      exitCode: 1,
      timedOut: /timed out|deadline/i.test(errorMessage(error))
    }, 1);
  }
}

function rpc(operation: RpcOperation, payload: JsonObject): Promise<Json> {
  const id = nextRpcId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    send("rpc", { id, operation, payload });
  });
}

function send(type: string, fields: JsonObject): void {
  process.stdout.write(encodeFrame(protocolMessage(type, fields)));
}

function sendAndExit(type: string, fields: JsonObject, exitCode: number): void {
  process.stdout.write(encodeFrame(protocolMessage(type, fields)), () => process.exit(exitCode));
}

function fatal(error: unknown): void {
  try { send("protocol_error", { error: safeError(error) }); } catch {}
  rejectPending(new Error("protocol failure"));
  process.exit(70);
}

function rejectPending(error: Error): void {
  for (const waiter of pending.values()) waiter.reject(error);
  pending.clear();
}

function safeError(error: unknown): JsonObject {
  return {
    message: errorMessage(error),
    name: error instanceof Error ? error.name : "Error"
  };
}

function errorMessage(error: unknown): string {
  if (error && typeof error === "object" && typeof (error as { message?: unknown }).message === "string") {
    return (error as { message: string }).message;
  }
  return String(error);
}

function isObject(value: unknown): value is JsonObject {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
