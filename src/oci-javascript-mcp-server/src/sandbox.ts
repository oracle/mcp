/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import {
  formatPublicOciError,
  isTimeoutError,
  MAX_CODE_BYTES,
  MAX_HOST_RPC_CALLS,
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

const MAX_HOST_RPC_IN_FLIGHT = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_HOST_RPC_IN_FLIGHT", 4);
const PROVIDER_TERMINATION_TIMEOUT_MS = 6000;

type RpcRunState = {
  accepting: boolean;
  deadlineMs: number;
  pendingCalls: Set<Promise<Json>>;
  remainingCalls: number;
};

export async function runJavaScript(
  code: string,
  options: {
    timeoutSeconds?: number;
    signal?: AbortSignal;
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
    pendingCalls: new Set(),
    remainingCalls: MAX_HOST_RPC_CALLS
  };
  const abortController = new AbortController();
  const signal = options.signal
    ? AbortSignal.any([options.signal, abortController.signal])
    : abortController.signal;
  const { isolationProvider, reflectionManifest } = options;

  let execution: IsolationExecution | undefined;
  let outcome: SandboxResult | undefined;
  try {
    signal.throwIfAborted();
    execution = isolationProvider.run(code, {
      deadlineMs,
      signal,
      hostRpc: request => invokeHostRpc(
        options.hostRpc,
        rpcState,
        request,
        signal
      ),
      reflectionManifest
    });
    outcome = await withDeadline(
      execution.result,
      remainingDeadlineMs(deadlineMs),
      signal
    );
  } catch (error) {
    outcome = options.signal?.aborted
      ? workerFailure("sandbox execution cancelled")
      : isTimeoutError(error) || Date.now() >= deadlineMs
      ? timeoutResult()
      : workerFailure("isolation provider failed");
  } finally {
    const completedWithPendingCalls = outcome?.exitCode === 0
      && rpcState.pendingCalls.size > 0;
    rpcState.accepting = false;
    abortController.abort();
    if (execution) {
      const cleanupError = await terminateExecution(execution);
      if (cleanupError) {
        outcome = workerFailure("isolation provider cleanup failed");
      }
    }
    if (rpcState.pendingCalls.size > 0) {
      try {
        await withDeadline(
          Promise.allSettled([...rpcState.pendingCalls]),
          PROVIDER_TERMINATION_TIMEOUT_MS
        );
      } catch {
        outcome = workerFailure("OCI cleanup did not complete");
      }
    }
    if (completedWithPendingCalls && outcome?.exitCode === 0) {
      outcome = workerFailure("JavaScript completed with unawaited OCI calls");
    }
  }

  return outcome ?? workerFailure("isolation provider returned no result");
}

async function terminateExecution(execution: IsolationExecution): Promise<unknown | undefined> {
  try {
    await withDeadline(
      Promise.resolve().then(() => execution.terminate()),
      PROVIDER_TERMINATION_TIMEOUT_MS
    );
    return undefined;
  } catch (error) {
    return error;
  }
}

function remainingDeadlineMs(deadlineMs: number): number {
  const remainingMs = Math.ceil(deadlineMs - Date.now());
  if (remainingMs <= 0) {
    throw new Error("sandbox run deadline exceeded");
  }
  return remainingMs;
}

async function invokeHostRpc(
  hostRpc: HostRpcHandler,
  state: RpcRunState,
  request: HostRpcRequest,
  signal: AbortSignal
): Promise<Json> {
  if (!state.accepting || signal.aborted || Date.now() > state.deadlineMs) {
    return rpcEnvelopeError("sandbox run deadline exceeded");
  }
  if (state.remainingCalls <= 0) {
    return rpcEnvelopeError(`OCI call limit exceeded (${MAX_HOST_RPC_CALLS})`);
  }
  if (state.pendingCalls.size >= MAX_HOST_RPC_IN_FLIGHT) {
    return rpcEnvelopeError(
      `too many concurrent OCI calls (${MAX_HOST_RPC_IN_FLIGHT})`
    );
  }

  state.remainingCalls -= 1;
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
    const value = await withDeadline(hostRpcPromise, remainingMs);
    if (!state.accepting) {
      return rpcEnvelopeError("sandbox run deadline exceeded");
    }
    return { ok: true, value };
  } catch (error) {
    return rpcEnvelopeError(formatPublicOciError(error));
  }
}

function rpcEnvelopeError(error: string | JsonObject): Json {
  return { ok: false, error };
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
