/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { Json, JsonObject, SandboxError } from "./types.ts";

export const MAX_CODE_BYTES = 1024 * 1024;
export const DEFAULT_TIMEOUT_SECONDS = 30;
export const MIN_TIMEOUT_SECONDS = 1;
export const MAX_TIMEOUT_SECONDS = 120;

export function withDeadline<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
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

export function positiveIntegerEnv(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined) {
    return fallback;
  }
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

export function normalizeTimeoutMs(timeoutSeconds: number | undefined): number {
  const raw = timeoutSeconds ?? DEFAULT_TIMEOUT_SECONDS;
  if (!Number.isFinite(raw)) {
    throw new Error("timeout must be a finite number");
  }
  const clamped = Math.min(MAX_TIMEOUT_SECONDS, Math.max(MIN_TIMEOUT_SECONDS, raw));
  return Math.ceil(clamped * 1000);
}

export function isTimeoutError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error);
  return /timed out|deadline exceeded|Script execution timed out/i.test(message);
}

export function formatError(error: unknown): SandboxError {
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

export function appendCapped(current: string, chunk: string, maxBytes: number): string {
  const combined = current + chunk;
  if (Buffer.byteLength(combined, "utf8") <= maxBytes) {
    return combined;
  }
  return Buffer.from(combined, "utf8").subarray(0, maxBytes).toString("utf8");
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
