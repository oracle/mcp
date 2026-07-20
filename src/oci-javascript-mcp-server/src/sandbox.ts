/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { fork, type ChildProcess } from "node:child_process";
import { fileURLToPath } from "node:url";
import {
  appendCapped,
  formatError,
  MAX_CODE_BYTES,
  normalizeTimeoutMs,
  positiveIntegerEnv,
  withDeadline
} from "./sandbox-common.ts";
import type {
  HostRpcHandler,
  HostRpcRequest,
  Json,
  JsonObject,
  OciReflectionManifest,
  SandboxResult
} from "./types.ts";

const WORKER_PATH = fileURLToPath(new URL("./sandbox-worker.ts", import.meta.url));
const WORKER_EXEC_ARGV = ["--no-node-snapshot", "--experimental-strip-types"];
const MAX_WORKER_STDERR_BYTES = 64 * 1024;
const MAX_ISOLATE_MEMORY_MB = positiveIntegerEnv("OCI_JAVASCRIPT_ISOLATE_MEMORY_MB", 128);
const MAX_RESULT_BYTES = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_RESULT_BYTES", 1024 * 1024);
const MAX_HOST_RPC_REQUEST_BYTES = positiveIntegerEnv(
  "OCI_JAVASCRIPT_MAX_HOST_RPC_REQUEST_BYTES",
  1024 * 1024
);
const MAX_HOST_RPC_CALLS = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_HOST_RPC_CALLS", 100);
const MAX_HOST_RPC_IN_FLIGHT = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_HOST_RPC_IN_FLIGHT", 4);

type RpcRunState = {
  accepting: boolean;
  deadlineMs: number;
  inFlight: number;
  remainingCalls: number;
};

export async function runJavaScript(
  code: string,
  options: {
    timeoutSeconds?: number;
    hostRpc: HostRpcHandler;
    reflectionManifest?: OciReflectionManifest;
  }
): Promise<SandboxResult> {
  if (Buffer.byteLength(code, "utf8") > MAX_CODE_BYTES) {
    throw new Error(`JavaScript code exceeds ${MAX_CODE_BYTES} bytes`);
  }

  const timeoutMs = normalizeTimeoutMs(options.timeoutSeconds);
  const rpcState: RpcRunState = {
    accepting: true,
    deadlineMs: Date.now() + timeoutMs,
    inFlight: 0,
    remainingCalls: MAX_HOST_RPC_CALLS
  };

  return runWorker(code, options, rpcState, timeoutMs);
}

function runWorker(
  code: string,
  options: {
    timeoutSeconds?: number;
    hostRpc: HostRpcHandler;
    reflectionManifest?: OciReflectionManifest;
  },
  rpcState: RpcRunState,
  timeoutMs: number
): Promise<SandboxResult> {
  return new Promise(resolve => {
    let settled = false;
    let workerResult: SandboxResult | undefined;
    let workerStderr = "";
    const worker = fork(WORKER_PATH, [], {
      env: workerEnv(),
      execArgv: WORKER_EXEC_ARGV,
      stdio: ["ignore", "ignore", "pipe", "ipc"]
    });

    const timer = setTimeout(() => {
      finish(timeoutResult(), true);
    }, timeoutMs);

    worker.stderr?.on("data", chunk => {
      workerStderr = appendCapped(workerStderr, String(chunk), MAX_WORKER_STDERR_BYTES);
    });
    worker.on("message", message => {
      void handleWorkerMessage(
        worker,
        message,
        options.hostRpc,
        rpcState,
        result => {
          workerResult = result;
        },
        finish
      );
    });
    worker.on("error", error => {
      finish(workerFailure(error.message, workerStderr), true);
    });
    worker.once("exit", (code, signal) => {
      if (!settled) {
        finish(
          workerResult ?? workerFailure(workerExitMessage(code, signal), workerStderr),
          false
        );
      }
    });

    sendWorker(worker, {
      type: "run",
      code,
      timeoutSeconds: options.timeoutSeconds,
      reflectionManifest: options.reflectionManifest,
      memoryLimitMb: MAX_ISOLATE_MEMORY_MB,
      maxResultBytes: MAX_RESULT_BYTES
    }, error => finish(workerFailure(error.message, workerStderr), true));

    function finish(result: SandboxResult, killWorker: boolean): void {
      if (settled) {
        return;
      }
      settled = true;
      rpcState.accepting = false;
      clearTimeout(timer);
      worker.removeAllListeners("message");
      if (killWorker && !worker.killed) {
        worker.kill("SIGKILL");
      }
      resolve(result);
    }
  });
}

async function handleWorkerMessage(
  worker: ChildProcess,
  message: unknown,
  hostRpc: HostRpcHandler,
  rpcState: RpcRunState,
  reportResult: (result: SandboxResult) => void,
  finish: (result: SandboxResult, killWorker: boolean) => void
): Promise<void> {
  if (!message || typeof message !== "object") {
    finish(workerFailure("sandbox worker sent invalid message"), true);
    return;
  }

  const record = message as Record<string, unknown>;
  if (record.type === "result") {
    reportResult(record.result as SandboxResult);
    return;
  }
  if (record.type === "fatal") {
    reportResult({
      result: null,
      error: formatError(record.error),
      stdout: "",
      stderr: "",
      exitCode: 1,
      timedOut: false
    });
    return;
  }
  if (record.type !== "rpc" || typeof record.id !== "number") {
    finish(workerFailure("sandbox worker sent invalid message"), true);
    return;
  }

  const result = await invokeHostRpc(hostRpc, rpcState, record.request);
  sendWorker(worker, {
    type: "rpcResult",
    id: record.id,
    result
  }, error => finish(workerFailure(error.message), true));
}

function sendWorker(
  worker: ChildProcess,
  message: Record<string, unknown>,
  onError: (error: Error) => void
): void {
  if (!worker.connected) {
    onError(new Error("sandbox worker disconnected"));
    return;
  }
  worker.send(message, error => {
    if (error) {
      onError(error);
    }
  });
}

async function invokeHostRpc(
  hostRpc: HostRpcHandler,
  state: RpcRunState,
  request: unknown
): Promise<Json> {
  if (!validateRpcRequest(request)) {
    return rpcEnvelopeError("invalid OCI bridge request");
  }

  if (!state.accepting || Date.now() > state.deadlineMs) {
    return rpcEnvelopeError("sandbox run deadline exceeded");
  }
  if (state.remainingCalls <= 0) {
    return rpcEnvelopeError(`OCI call limit exceeded (${MAX_HOST_RPC_CALLS})`);
  }
  if (state.inFlight >= MAX_HOST_RPC_IN_FLIGHT) {
    return rpcEnvelopeError(
      `too many concurrent OCI calls (${MAX_HOST_RPC_IN_FLIGHT})`
    );
  }

  let requestBytes: number;
  try {
    requestBytes = Buffer.byteLength(JSON.stringify(request), "utf8");
  } catch {
    return rpcEnvelopeError("OCI request could not be serialized");
  }
  if (requestBytes > MAX_HOST_RPC_REQUEST_BYTES) {
    return rpcEnvelopeError(
      `OCI request exceeded ${MAX_HOST_RPC_REQUEST_BYTES} bytes`
    );
  }

  state.remainingCalls -= 1;
  state.inFlight += 1;
  try {
    const remainingMs = state.deadlineMs - Date.now();
    if (remainingMs <= 0) {
      throw new Error("sandbox run deadline exceeded");
    }
    const hostRpcPromise = Promise.resolve()
      .then(() => hostRpc(request, remainingMs));
    const value = await withDeadline(hostRpcPromise, remainingMs);
    if (!state.accepting) {
      return rpcEnvelopeError("sandbox run deadline exceeded");
    }
    return { ok: true, value };
  } catch (error) {
    return rpcEnvelopeError(formatError(error));
  } finally {
    state.inFlight -= 1;
  }
}

function rpcEnvelopeError(error: string | JsonObject): Json {
  return { ok: false, error };
}

function validateRpcRequest(value: unknown): value is HostRpcRequest {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const request = value as Record<string, unknown>;
  return request.binding === "oracle"
    && request.namespace === "oci"
    && (request.operation === "invoke"
      || request.operation === "config"
      || request.operation === "discover")
    && !!request.payload
    && typeof request.payload === "object"
    && !Array.isArray(request.payload);
}

function timeoutResult(): SandboxResult {
  return {
    result: null,
    error: { message: "sandbox run deadline exceeded" },
    stdout: "",
    stderr: "",
    exitCode: -1,
    timedOut: true
  };
}

function workerFailure(message: string, stderr = ""): SandboxResult {
  const error: JsonObject = { message };
  if (stderr) {
    error.cause = stderr;
  }
  return {
    result: null,
    error: error as { message: string } & JsonObject,
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  };
}

function workerExitMessage(code: number | null, signal: NodeJS.Signals | null): string {
  if (signal) {
    return `sandbox worker exited unexpectedly with signal ${signal}`;
  }
  return `sandbox worker exited unexpectedly with code ${code ?? "unknown"}`;
}

function workerEnv(): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {};
  for (const key of ["PATH", "TMPDIR", "TEMP", "TMP", "NODE_V8_COVERAGE"]) {
    const value = process.env[key];
    if (value) {
      env[key] = value;
    }
  }
  return env;
}
