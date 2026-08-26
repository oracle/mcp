/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { z } from "zod";
import {
  appendCapped,
  formatError,
  formatPublicOciError,
  isTimeoutError,
  MAX_CODE_BYTES,
  MAX_STDERR_BYTES,
  MAX_STDOUT_BYTES,
  normalizeTimeoutMs,
  positiveIntegerEnv,
  withDeadline
} from "./sandbox-common.ts";
import type {
  HostRpcHandler,
  HostRpcRequest,
  IsolationExecution,
  IsolationProvider,
  Json,
  JsonObject,
  OciReflectionManifest,
  SandboxResult
} from "./types.ts";

const MAX_RESULT_BYTES = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_RESULT_BYTES", 1024 * 1024);
const MAX_HOST_RPC_REQUEST_BYTES = positiveIntegerEnv(
  "OCI_JAVASCRIPT_MAX_HOST_RPC_REQUEST_BYTES",
  1024 * 1024
);
const MAX_HOST_RPC_CALLS = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_HOST_RPC_CALLS", 100);
const MAX_HOST_RPC_IN_FLIGHT = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_HOST_RPC_IN_FLIGHT", 4);
const DEFAULT_PROVIDER_TERMINATION_TIMEOUT_MS = 6000;
const MAX_PROVIDER_TERMINATION_TIMEOUT_MS = 60_000;
const PROVIDER_RESULT_SCHEMA = z.object({
  result: z.unknown(),
  error: z.object({ message: z.string().min(1) }).passthrough().nullable(),
  stdout: z.string(),
  stderr: z.string(),
  exitCode: z.number().int().min(Number.MIN_SAFE_INTEGER).max(Number.MAX_SAFE_INTEGER),
  timedOut: z.boolean()
}).strict();

type RpcRunState = {
  accepting: boolean;
  deadlineMs: number;
  inFlight: number;
  pendingCalls: Set<Promise<Json>>;
  remainingCalls: number;
};

export async function runJavaScript(
  code: string,
  options: {
    timeoutSeconds?: number;
    hostRpc: HostRpcHandler;
    reflectionManifest?: OciReflectionManifest;
    isolationProvider: IsolationProvider;
  }
): Promise<SandboxResult> {
  if (Buffer.byteLength(code, "utf8") > MAX_CODE_BYTES) {
    throw new Error(`JavaScript code exceeds ${MAX_CODE_BYTES} bytes`);
  }

  const timeoutMs = normalizeTimeoutMs(options.timeoutSeconds);
  const deadlineMs = Date.now() + timeoutMs;
  const rpcState: RpcRunState = {
    accepting: true,
    deadlineMs,
    inFlight: 0,
    pendingCalls: new Set(),
    remainingCalls: MAX_HOST_RPC_CALLS
  };
  const abortController = new AbortController();
  const { isolationProvider, reflectionManifest } = options;

  let execution: IsolationExecution | undefined;
  let outcome: SandboxResult | undefined;
  try {
    execution = validateExecution(isolationProvider.run(code, {
      deadlineMs,
      signal: abortController.signal,
      hostRpc: request => invokeHostRpc(
        options.hostRpc,
        rpcState,
        request,
        abortController.signal
      ),
      reflectionManifest
    }));
    const result = await withDeadline(
      execution.result,
      remainingDeadlineMs(deadlineMs)
    );
    outcome = validateProviderResult(result);
  } catch (error) {
    outcome = isTimeoutError(error) || Date.now() >= deadlineMs
      ? timeoutResult()
      : providerFailure(error);
  } finally {
    const completedWithPendingCalls = outcome?.exitCode === 0
      && rpcState.pendingCalls.size > 0;
    rpcState.accepting = false;
    const pendingCalls = [...rpcState.pendingCalls];
    abortController.abort();
    const cleanupDeadlineMs = Date.now() + (
      execution?.terminationTimeoutMs ?? DEFAULT_PROVIDER_TERMINATION_TIMEOUT_MS
    );
    const [cleanupError] = await Promise.all([
      execution
        ? terminateExecution(execution, cleanupDeadlineMs)
        : Promise.resolve(undefined),
      drainPendingCalls(pendingCalls, cleanupDeadlineMs)
    ]);
    if (cleanupError) {
      outcome = providerFailure(cleanupError, "isolation provider cleanup failed");
    }
    if (completedWithPendingCalls && outcome?.exitCode === 0) {
      outcome = workerFailure("JavaScript completed with unawaited OCI calls");
    }
  }

  return outcome ?? providerFailure("isolation provider returned no result");
}

function validateExecution(value: unknown): IsolationExecution {
  if (!value || typeof value !== "object") {
    throw new Error("isolation provider returned an invalid execution handle");
  }
  const record = value as Record<string, unknown>;
  const result = record.result;
  if (
    !result
    || (typeof result !== "object" && typeof result !== "function")
    || typeof (result as { then?: unknown }).then !== "function"
    || typeof record.terminate !== "function"
    || (
      record.terminationTimeoutMs !== undefined
      && (
        !Number.isSafeInteger(record.terminationTimeoutMs)
        || (record.terminationTimeoutMs as number) < 1
        || (record.terminationTimeoutMs as number) > MAX_PROVIDER_TERMINATION_TIMEOUT_MS
      )
    )
  ) {
    throw new Error("isolation provider returned an invalid execution handle");
  }
  return value as IsolationExecution;
}

async function terminateExecution(
  execution: IsolationExecution,
  cleanupDeadlineMs: number
): Promise<unknown | undefined> {
  try {
    await withDeadline(
      Promise.resolve().then(() => execution.terminate()),
      remainingMs(cleanupDeadlineMs)
    );
    return undefined;
  } catch (error) {
    return error;
  }
}

async function drainPendingCalls(
  pendingCalls: Promise<Json>[],
  cleanupDeadlineMs: number
): Promise<void> {
  try {
    await withDeadline(Promise.allSettled(pendingCalls), remainingMs(cleanupDeadlineMs));
  } catch {
    // The individual promises retain rejection observers after the shared tail expires.
  }
}

function validateProviderResult(value: unknown): SandboxResult {
  try {
    const record = PROVIDER_RESULT_SCHEMA.parse(value);
    const result = copyJson(record.result, "result", MAX_RESULT_BYTES);
    const error = record.error === null
      ? null
      : copyJson(record.error, "error", MAX_RESULT_BYTES) as SandboxResult["error"];
    assertByteLimit("stdout", record.stdout, MAX_STDOUT_BYTES);
    assertByteLimit("stderr", record.stderr, MAX_STDERR_BYTES);
    if ((record.exitCode === 0) !== (error === null) || (record.timedOut && !error)) {
      throw new Error("exitCode, error, and timedOut fields are inconsistent");
    }

    return {
      result,
      error,
      stdout: record.stdout,
      stderr: record.stderr,
      exitCode: record.exitCode,
      timedOut: record.timedOut
    };
  } catch (error) {
    throw new Error(
      `isolation provider returned an invalid result: ${formatError(error).message}`
    );
  }
}

function copyJson(value: unknown, label: string, maxBytes: number): Json {
  let encoded: string | undefined;
  try {
    encoded = JSON.stringify(value, (_key, item: unknown) => {
      if (
        item === undefined
        || typeof item === "bigint"
        || typeof item === "function"
        || typeof item === "symbol"
        || (typeof item === "number" && !Number.isFinite(item))
      ) {
        throw new Error(`${label} must be JSON-compatible`);
      }
      return item;
    });
  } catch (error) {
    throw new Error(`${label} must be JSON-compatible: ${formatError(error).message}`);
  }
  if (!encoded) {
    throw new Error(`${label} must be JSON-compatible`);
  }
  const bytes = Buffer.byteLength(encoded, "utf8");
  if (bytes > maxBytes) {
    throw new Error(`${label} was ${bytes} bytes, exceeding limit ${maxBytes} bytes`);
  }
  return JSON.parse(encoded) as Json;
}

function assertByteLimit(label: string, value: string, maxBytes: number): void {
  if (Buffer.byteLength(value, "utf8") > maxBytes) {
    throw new Error(`${label} exceeded ${maxBytes} bytes`);
  }
}

function remainingDeadlineMs(deadlineMs: number): number {
  const value = remainingMs(deadlineMs);
  if (value <= 0) {
    throw new Error("sandbox run deadline exceeded");
  }
  return value;
}

function remainingMs(deadlineMs: number): number {
  return Math.ceil(deadlineMs - Date.now());
}

async function invokeHostRpc(
  hostRpc: HostRpcHandler,
  state: RpcRunState,
  request: unknown,
  signal: AbortSignal
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
      .then(() => hostRpc(request, signal));
    state.pendingCalls.add(hostRpcPromise);
    void hostRpcPromise.then(
      () => state.pendingCalls.delete(hostRpcPromise),
      () => state.pendingCalls.delete(hostRpcPromise)
    );
    const value = await withAbortDeadline(hostRpcPromise, signal, remainingMs);
    if (!state.accepting) {
      return rpcEnvelopeError("sandbox run deadline exceeded");
    }
    return { ok: true, value };
  } catch (error) {
    return rpcEnvelopeError(formatPublicOciError(error));
  } finally {
    state.inFlight -= 1;
  }
}

function withAbortDeadline<T>(
  promise: Promise<T>,
  signal: AbortSignal,
  timeoutMs: number
): Promise<T> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (callback: () => void) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      signal.removeEventListener("abort", abort);
      callback();
    };
    const abort = () => finish(() => reject(new Error("sandbox run deadline exceeded")));
    const timeout = setTimeout(abort, timeoutMs);
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) {
      abort();
      return;
    }
    promise.then(
      value => finish(() => resolve(value)),
      error => finish(() => reject(error))
    );
  });
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

function providerFailure(
  _error: unknown,
  prefix = "isolation provider failed"
): SandboxResult {
  return workerFailure(prefix);
}

function workerFailure(message: string): SandboxResult {
  return {
    result: null,
    error: { message },
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  };
}
