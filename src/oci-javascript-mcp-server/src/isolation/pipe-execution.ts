/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import {
  FrameDecoder,
  ProtocolError,
  assertExactFields,
  encodeFrame,
  protocolMessage
} from "../protocol.ts";
import type {
  ExecutionResult,
  GuestRpcRequest,
  IsolationExecution,
  IsolationProvider,
  Json,
  JsonObject
} from "../types.ts";

export function startPipeExecution(
  child: ChildProcessWithoutNullStreams,
  input: Parameters<IsolationProvider["start"]>[0],
  afterClose?: () => Promise<void>
): IsolationExecution {
  const decoder = new FrameDecoder();
  let stdout = "";
  let stderr = "";
  let settled = false;
  let ready = false;
  let resolveResult!: (value: ExecutionResult) => void;
  const result = new Promise<ExecutionResult>(resolve => { resolveResult = resolve; });
  const close = new Promise<void>(resolve => child.once("close", () => resolve()));
  let cleanup: Promise<void> | undefined;
  const destroy = () => cleanup ??= (async () => {
    killChildTree(child);
    await close;
    await afterClose?.();
  })();

  const finish = (value: ExecutionResult, terminate = false) => {
    if (settled) return;
    settled = true;
    resolveResult({ ...value, stdout, stderr });
    if (terminate) void destroy();
  };
  const fail = (message: string, terminate = true) => finish({
    result: null,
    error: { message: "JavaScript execution failed", category: message },
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  }, terminate);

  child.stdout.on("data", chunk => {
    try {
      for (const message of decoder.push(chunk)) {
        void handleGuestMessage(message, child, input, {
          appendLog(stream, text) {
            if (stream === "stdout") stdout = appendBounded(stdout, text, input.maxOutputBytes);
            else stderr = appendBounded(stderr, text, input.maxOutputBytes);
          },
          ready() {
            if (ready) throw new ProtocolError("runner sent duplicate health message");
            ready = true;
            send(child, "execute", {
              code: input.code,
              manifest: input.manifest as unknown as Json,
              timeoutMs: Math.max(1, input.deadlineMs - Date.now()),
              maxResultBytes: input.maxResultBytes,
              maxOutputBytes: input.maxOutputBytes
            });
          },
          finish
        }).catch(error => fail(`protocol error: ${errorMessage(error)}`));
      }
    } catch (error) {
      fail(`protocol error: ${errorMessage(error)}`);
    }
  });
  child.stderr.on("data", chunk => {
    stderr = appendBounded(stderr, String(chunk), input.maxOutputBytes);
  });
  child.once("error", () => fail("runner process error", false));
  child.once("close", (code, signal) => {
    if (!settled) fail(`runner exited before returning a result (${signal ?? code ?? "unknown"})`, false);
  });
  const timeout = setTimeout(() => {
    finish({
      result: null,
      error: { message: "JavaScript execution timed out" },
      stdout: "",
      stderr: "",
      exitCode: -1,
      timedOut: true
    }, true);
  }, Math.max(1, input.deadlineMs - Date.now()));
  timeout.unref();
  const abort = () => {
    if (child.stdin.writable) {
      try { send(child, "cancel", {}); } catch {}
    }
    finish({
      result: null,
      error: { message: "JavaScript execution cancelled" },
      stdout: "",
      stderr: "",
      exitCode: -1,
      timedOut: false
    }, true);
  };
  input.signal?.addEventListener("abort", abort, { once: true });
  result.finally(() => {
    clearTimeout(timeout);
    input.signal?.removeEventListener("abort", abort);
  });

  return {
    result,
    destroy
  };
}

export function runnerEnvironment(): NodeJS.ProcessEnv {
  const environment: NodeJS.ProcessEnv = {};
  for (const name of ["PATH", "TMPDIR", "TMP", "TEMP", "NODE_V8_COVERAGE"]) {
    if (process.env[name]) environment[name] = process.env[name];
  }
  return environment;
}

export function runCleanupCommand(command: string, args: string[]): Promise<void> {
  return new Promise(resolve => {
    let settled = false;
    const cleanup = spawn(command, args, {
      env: runnerEnvironment(),
      stdio: "ignore"
    });
    const finish = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      resolve();
    };
    cleanup.once("error", finish);
    cleanup.once("close", finish);
    const timeout = setTimeout(() => {
      cleanup.kill("SIGKILL");
      finish();
    }, 5_000);
  });
}

async function handleGuestMessage(
  message: JsonObject,
  child: ChildProcessWithoutNullStreams,
  input: Parameters<IsolationProvider["start"]>[0],
  callbacks: {
    appendLog(stream: "stdout" | "stderr", text: string): void;
    ready(): void;
    finish(result: ExecutionResult, terminate?: boolean): void;
  }
): Promise<void> {
  if (message.type === "health") {
    assertExactFields(message, ["version", "type", "status"]);
    if (message.status !== "ready") throw new ProtocolError("invalid runner health status");
    callbacks.ready();
    return;
  }
  if (message.type === "log") {
    assertExactFields(message, ["version", "type", "stream", "text"]);
    if ((message.stream !== "stdout" && message.stream !== "stderr") || typeof message.text !== "string") {
      throw new ProtocolError("invalid log message");
    }
    callbacks.appendLog(message.stream, message.text);
    return;
  }
  if (message.type === "rpc") {
    assertExactFields(message, ["version", "type", "id", "operation", "payload"]);
    if (!Number.isInteger(message.id) || (message.operation !== "config" && message.operation !== "invoke")
      || !isObject(message.payload)) {
      throw new ProtocolError("invalid RPC message");
    }
    const request: GuestRpcRequest = {
      operation: message.operation,
      payload: message.payload
    };
    try {
      const value = await input.broker(request);
      send(child, "rpc_result", { id: message.id, ok: true, value });
    } catch (error) {
      send(child, "rpc_result", {
        id: message.id,
        ok: false,
        error: { message: publicBrokerError(error) }
      });
    }
    return;
  }
  if (message.type === "result") {
    assertExactFields(message, ["version", "type", "result", "error", "exitCode", "timedOut"]);
    if (!Number.isInteger(message.exitCode) || typeof message.timedOut !== "boolean"
      || (message.error !== null && !isObject(message.error))) {
      throw new ProtocolError("invalid result message");
    }
    if (((message.exitCode as number) === 0) !== (message.error === null)
      || (message.timedOut && message.error === null)) {
      throw new ProtocolError("result status fields are inconsistent");
    }
    const bytes = Buffer.byteLength(JSON.stringify(message.result), "utf8");
    if (bytes > input.maxResultBytes) throw new ProtocolError("runner result exceeds configured limit");
    callbacks.finish({
      result: message.result,
      error: message.error as ExecutionResult["error"],
      stdout: "",
      stderr: "",
      exitCode: message.exitCode as number,
      timedOut: message.timedOut as boolean
    });
    return;
  }
  if (message.type === "protocol_error") {
    assertExactFields(message, ["version", "type", "error"]);
    throw new ProtocolError("runner reported a protocol failure");
  }
  throw new ProtocolError(`unsupported guest message type '${String(message.type)}'`);
}

function send(child: ChildProcessWithoutNullStreams, type: string, fields: JsonObject): void {
  if (!child.stdin.writable) throw new Error("runner channel is closed");
  child.stdin.write(encodeFrame(protocolMessage(type, fields)));
}

function appendBounded(current: string, text: string, maximum: number): string {
  const combined = current + text;
  const bytes = Buffer.from(combined, "utf8");
  return bytes.length <= maximum ? combined : bytes.subarray(0, maximum).toString("utf8");
}

function killChildTree(child: ChildProcessWithoutNullStreams): void {
  if (child.exitCode !== null || child.signalCode !== null) return;
  if (process.platform !== "win32" && child.pid) {
    try { process.kill(-child.pid, "SIGKILL"); return; } catch {}
  }
  child.kill("SIGKILL");
}

function publicBrokerError(error: unknown): string {
  const message = errorMessage(error);
  return /not authorized|limit|deadline|cancelled|Unknown OCI|Invalid OCI|Unsupported OCI/i.test(message)
    ? message
    : "OCI operation failed";
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function isObject(value: Json | undefined): value is JsonObject {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
