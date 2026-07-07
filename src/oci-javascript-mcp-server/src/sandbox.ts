/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import ivm from "isolated-vm";
import type {
  HostRpcHandler,
  HostRpcRequest,
  Json,
  JsonObject,
  OciReflectionManifest,
  SandboxError,
  SandboxResult
} from "./types.ts";
import { SANDBOX_BOOTSTRAP } from "./sandbox-prelude.ts";

const MAX_CODE_BYTES = 1024 * 1024;
const MAX_STDOUT_BYTES = 1024 * 1024;
const MAX_STDERR_BYTES = 1024 * 1024;
const MAX_ISOLATE_MEMORY_MB = positiveIntegerEnv("OCI_JAVASCRIPT_ISOLATE_MEMORY_MB", 128);
const MAX_HOST_RPC_REQUEST_BYTES = positiveIntegerEnv(
  "OCI_JAVASCRIPT_MAX_HOST_RPC_REQUEST_BYTES",
  1024 * 1024
);
const MAX_HOST_RPC_CALLS = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_HOST_RPC_CALLS", 100);
const MAX_HOST_RPC_IN_FLIGHT = positiveIntegerEnv("OCI_JAVASCRIPT_MAX_HOST_RPC_IN_FLIGHT", 4);
const DEFAULT_TIMEOUT_SECONDS = 30;
const MIN_TIMEOUT_SECONDS = 1;
const MAX_TIMEOUT_SECONDS = 120;

type RpcRunState = {
  accepting: boolean;
  deadlineMs: number;
  inFlight: number;
  remainingCalls: number;
};

type SandboxApi = {
  drain: ivm.Reference<() => Promise<void>>;
  encodeLastResult: ivm.Reference<() => Json>;
  run: ivm.Reference<(code: string) => Promise<void>>;
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
  const output = {
    stdout: "",
    stderr: "",
    exceeded: false
  };

  const isolate = new ivm.Isolate({ memoryLimit: MAX_ISOLATE_MEMORY_MB });
  let api: SandboxApi | undefined;
  try {
    const context = await isolate.createContext();
    const global = context.global;
    await global.set("globalThis", global.derefInto());

    const bootstrap = await context.evalClosure(
      SANDBOX_BOOTSTRAP,
      [
        new ivm.Reference((line: unknown) => {
          output.stdout = appendCapped(output.stdout, String(line), MAX_STDOUT_BYTES);
          if (Buffer.byteLength(output.stdout, "utf8") >= MAX_STDOUT_BYTES) {
            output.exceeded = true;
            throw new Error("Sandbox stdout exceeded limit");
          }
        }),
        new ivm.Reference((line: unknown) => {
          output.stderr = appendCapped(output.stderr, String(line), MAX_STDERR_BYTES);
          if (Buffer.byteLength(output.stderr, "utf8") >= MAX_STDERR_BYTES) {
            output.exceeded = true;
            throw new Error("Sandbox stderr exceeded limit");
          }
        }),
        new ivm.Reference(async (request: unknown) => {
          return invokeHostRpc(options.hostRpc, rpcState, request);
        }),
        new ivm.ExternalCopy(options.reflectionManifest ?? { services: {} }).copyInto()
      ],
      {
        result: { reference: true },
        timeout: timeoutMs
      }
    ) as ivm.Reference<Record<string, unknown>>;

    api = {
      drain: await bootstrap.get("drain", { reference: true }) as ivm.Reference<() => Promise<void>>,
      encodeLastResult: await bootstrap.get("encodeLastResult", {
        reference: true
      }) as ivm.Reference<() => Json>,
      run: await bootstrap.get("run", { reference: true }) as ivm.Reference<
        (code: string) => Promise<void>
      >
    };
    bootstrap.release();

    try {
      const evalTimeoutMs = remainingRunMs(rpcState);
      await withDeadline(
        api.run.apply(undefined, [code], {
          arguments: { copy: true },
          result: { promise: true, copy: true },
          timeout: evalTimeoutMs
        }),
        evalTimeoutMs
      );
      await drainHostRpc(api, rpcState);
      const resultTimeoutMs = remainingRunMs(rpcState);
      const result = await withDeadline(
        api.encodeLastResult.apply(undefined, [], {
          result: { copy: true },
          timeout: resultTimeoutMs
        }),
        resultTimeoutMs
      ) as Json;
      await drainHostRpc(api, rpcState);
      return {
        result,
        error: null,
        stdout: output.stdout,
        stderr: output.stderr,
        exitCode: output.exceeded ? 1 : 0,
        timedOut: false
      };
    } catch (error) {
      rpcState.accepting = false;
      const timedOut = isTimeoutError(error);
      return {
        result: null,
        error: formatError(error),
        stdout: output.stdout,
        stderr: output.stderr,
        exitCode: timedOut ? -1 : 1,
        timedOut
      };
    }
  } finally {
    rpcState.accepting = false;
    api?.drain.release();
    api?.encodeLastResult.release();
    api?.run.release();
    isolate.dispose();
  }
}

async function drainHostRpc(
  api: SandboxApi,
  rpcState: RpcRunState
): Promise<void> {
  const remainingMs = remainingRunMs(rpcState);
  await withDeadline(
    api.drain.apply(undefined, [], {
      result: { promise: true, copy: true },
      timeout: remainingMs
    }),
    remainingMs
  );
}

function remainingRunMs(rpcState: RpcRunState): number {
  const remainingMs = rpcState.deadlineMs - Date.now();
  if (remainingMs <= 0) {
    throw new Error("sandbox run deadline exceeded");
  }
  return remainingMs;
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

function withDeadline<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
  if (timeoutMs <= 0) {
    return Promise.reject(new Error("sandbox run deadline exceeded"));
  }
  let timeout: NodeJS.Timeout;
  return new Promise((resolve, reject) => {
    timeout = setTimeout(
      () => reject(new Error("sandbox run deadline exceeded")),
      timeoutMs
    );
    promise.then(resolve, reject).finally(() => clearTimeout(timeout));
  });
}

function positiveIntegerEnv(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined) {
    return fallback;
  }
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function normalizeTimeoutMs(timeoutSeconds: number | undefined): number {
  const raw = timeoutSeconds ?? DEFAULT_TIMEOUT_SECONDS;
  if (!Number.isFinite(raw)) {
    throw new Error("timeout must be a finite number");
  }
  const clamped = Math.min(MAX_TIMEOUT_SECONDS, Math.max(MIN_TIMEOUT_SECONDS, raw));
  return Math.ceil(clamped * 1000);
}

function isTimeoutError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error);
  return /timed out|deadline exceeded|Script execution timed out/i.test(message);
}

function formatError(error: unknown): SandboxError {
  const response = readObjectField(error, "response");
  const body = readField(error, "body") ?? readField(response, "body") ?? readField(response, "data");
  const details: SandboxError = {
    message: errorMessage(error)
  };
  for (const key of [
    "name",
    "code",
    "status",
    "statusCode",
    "serviceCode",
    "opcRequestId",
    "requestId",
    "targetService",
    "operationName",
    "timestamp",
    "requestEndpoint"
  ]) {
    const value = jsonScalar(readField(error, key));
    if (value !== undefined) {
      details[key] = value;
    }
  }

  const responseStatusCode = jsonScalar(
    readField(response, "statusCode") ?? readField(response, "status")
  );
  if (responseStatusCode !== undefined) {
    details.responseStatusCode = responseStatusCode;
  }

  const responseRequestId = headerValue(readField(response, "headers"), "opc-request-id");
  if (responseRequestId && details.opcRequestId === undefined) {
    details.opcRequestId = responseRequestId;
  }

  const bodyValue = jsonErrorBody(body);
  if (bodyValue !== undefined) {
    details.responseBody = bodyValue;
  }

  const cause = readField(error, "cause");
  if (cause !== undefined && cause !== error) {
    details.cause = cause instanceof Error
      ? formatError(cause)
      : jsonErrorBody(cause) ?? errorMessage(cause);
  }

  return details;
}

function errorMessage(error: unknown): string {
  const message = readField(error, "message");
  if (typeof message === "string" && message) {
    return message;
  }
  const name = readField(error, "name");
  if (typeof name === "string" && name) {
    return name;
  }
  if (!error || typeof error !== "object") {
    return String(error);
  }
  const rendered = String(error);
  return rendered === "[object Object]" ? "OCI call failed" : rendered;
}

function readField(value: unknown, key: string): unknown {
  if (!value || typeof value !== "object") {
    return undefined;
  }
  try {
    return (value as Record<string, unknown>)[key];
  } catch {
    return undefined;
  }
}

function readObjectField(value: unknown, key: string): Record<string, unknown> | undefined {
  const field = readField(value, key);
  return field && typeof field === "object" && !Array.isArray(field)
    ? field as Record<string, unknown>
    : undefined;
}

function jsonScalar(value: unknown): Json | undefined {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : String(value);
  }
  if (typeof value === "bigint") {
    return value.toString();
  }
  return undefined;
}

function jsonErrorBody(value: unknown): Json | undefined {
  const scalar = jsonScalar(value);
  if (scalar !== undefined) {
    return scalar;
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return undefined;
  }

  const result: JsonObject = {};
  for (const key of ["code", "message", "details"]) {
    const scalarField = jsonScalar(readField(value, key));
    if (scalarField !== undefined) {
      result[key] = scalarField;
    }
  }
  return Object.keys(result).length > 0 ? result : undefined;
}

function headerValue(headers: unknown, key: string): string | undefined {
  if (!headers || typeof headers !== "object") {
    return undefined;
  }
  const getter = readField(headers, "get");
  if (typeof getter === "function") {
    try {
      const value = getter.call(headers, key);
      return typeof value === "string" && value ? value : undefined;
    } catch {
      return undefined;
    }
  }
  const value = readField(headers, key) ?? readField(headers, key.toLowerCase());
  return typeof value === "string" && value ? value : undefined;
}

function appendCapped(current: string, chunk: string, maxBytes: number): string {
  const combined = current + chunk;
  if (Buffer.byteLength(combined, "utf8") <= maxBytes) {
    return combined;
  }
  return Buffer.from(combined, "utf8").subarray(0, maxBytes).toString("utf8");
}
