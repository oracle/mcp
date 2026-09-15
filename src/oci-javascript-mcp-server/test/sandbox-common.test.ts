/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import {
  appendCapped,
  formatError,
  formatPublicOciError,
  isTimeoutError,
  normalizeTimeoutMs,
  positiveIntegerEnv,
  PublicError,
  withDeadline
} from "../src/sandbox-common.ts";

test("sandbox common helpers enforce deadlines and numeric limits", async () => {
  await assert.rejects(withDeadline(Promise.resolve("late"), 0), /deadline exceeded/);
  assert.equal(await withDeadline(Promise.resolve("ok"), 100), "ok");

  const environmentName = "OCI_JAVASCRIPT_TEST_POSITIVE_INTEGER";
  delete process.env[environmentName];
  assert.equal(positiveIntegerEnv(environmentName, 7), 7);
  process.env[environmentName] = "invalid";
  assert.equal(positiveIntegerEnv(environmentName, 7), 7);
  process.env[environmentName] = "12";
  assert.equal(positiveIntegerEnv(environmentName, 7), 12);
  delete process.env[environmentName];

  assert.equal(normalizeTimeoutMs(undefined), 30_000);
  assert.equal(normalizeTimeoutMs(0), 1_000);
  assert.equal(normalizeTimeoutMs(999), 120_000);
  assert.throws(() => normalizeTimeoutMs(Number.POSITIVE_INFINITY), /finite number/);
  assert.equal(isTimeoutError(new Error("Script execution timed out")), true);
  assert.equal(isTimeoutError("ordinary failure"), false);
});

test("sandbox common helpers cap UTF-8 output", () => {
  assert.equal(appendCapped("ab", "cd", 4), "abcd");
  assert.equal(Buffer.byteLength(appendCapped("ab", "cdef", 4), "utf8"), 4);
});

test("sandbox common helpers keep only allowlisted public OCI error details", () => {
  const cause = new Error("socket closed");
  Object.defineProperty(cause, "code", { value: "ECONNRESET" });
  const error = new Error("request failed", { cause });
  Object.assign(error, {
    statusCode: 400,
    serviceCode: "InvalidParameter",
    requestEndpoint: "https://internal.example/signed?token=secret",
    response: {
      status: 400,
      headers: new Map([
        ["opc-request-id", "request-1"],
        ["authorization", "secret"]
      ]),
      body: { code: "InvalidParameter", message: "secret response body" }
    }
  });

  assert.deepEqual(formatError(error), {
    message: "request failed",
    name: "Error",
    statusCode: 400,
    serviceCode: "InvalidParameter"
  });
  assert.deepEqual(formatPublicOciError(error), {
    message: "OCI call failed",
    statusCode: 400,
    serviceCode: "InvalidParameter",
    opcRequestId: "request-1",
  });
  assert.deepEqual(formatPublicOciError(new PublicError("safe broker guidance")), {
    message: "safe broker guidance"
  });
  const publicText = JSON.stringify(formatPublicOciError(error));
  for (const secret of [
    "request failed",
    "socket closed",
    "internal.example",
    "secret response body",
    "authorization"
  ]) {
    assert.equal(publicText.includes(secret), false);
  }
  assert.deepEqual(formatError({ name: "NamedFailure" }), { message: "NamedFailure", name: "NamedFailure" });
  assert.deepEqual(formatError({}), { message: "OCI call failed" });
  assert.deepEqual(formatError("plain failure"), { message: "plain failure" });
});
