/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { z } from "zod";
import { schemaValidator } from "./schema-validator.ts";
import { discoverOci, DISCOVER_OCI_TOOL, executionToolResult, RUN_JAVASCRIPT_TOOL } from "../src/tool-contracts.ts";
import type { Json, JsonObject, OciDiscoverPayload, SandboxResult } from "../src/types.ts";

const success: SandboxResult = {
  result: null, error: null, stdout: "log", stderr: "warning", exitCode: 0, timedOut: false
};

const validateExecution = schemaValidator(
  z.toJSONSchema(RUN_JAVASCRIPT_TOOL.outputSchema)
);

test("execution envelopes preserve JSON values and text/structured equivalence", () => {
  for (const result of [null, 42, true, "value", [1, null], { __oci_wire_type: "bigint", value: "42" }]) {
    const response = executionToolResult({ ...success, result });
    assert.deepEqual(response.structuredContent, {
      result, error: null, stdout: "log", stderr: "warning", exit_code: 0, timed_out: false
    });
    assert.deepEqual(JSON.parse((response.content[0] as { text: string }).text), response.structuredContent);
    assert.equal(response.isError ?? false, false);
    assert.equal(validateExecution(response.structuredContent).valid, true);
  }
});

test("each execution failure signal marks the MCP result without losing its envelope", () => {
  for (const override of [
    { error: { message: "OCI call failed", statusCode: 503, serviceCode: "ServiceUnavailable",
      opcRequestId: "example-request", operationName: "listCompartments" } },
    { timedOut: true },
    { exitCode: 1 },
    { exitCode: -1 }
  ]) {
    const response = executionToolResult({ ...success, ...override });
    assert.equal(response.isError, true);
    assert.equal(validateExecution(response.structuredContent).valid, true);
    assert.deepEqual(JSON.parse((response.content[0] as { text: string }).text), response.structuredContent);
    assert.deepEqual(response.structuredContent?.error, override.error ?? null);
  }
});

test("execution output schema rejects missing fields and malformed envelope values", () => {
  const envelope = executionToolResult(success).structuredContent!;
  for (const field of ["result", "error", "stdout", "stderr", "exit_code", "timed_out"]) {
    const incomplete = { ...envelope };
    delete incomplete[field];
    assert.equal(validateExecution(incomplete).valid, false, field);
  }
  for (const override of [
    { error: {} }, { error: { message: "" } }, { error: { message: 1 } },
    { stdout: null }, { stderr: 1 }, { exit_code: 0.5 }, { timed_out: "false" }
  ]) {
    assert.equal(validateExecution({ ...envelope, ...override }).valid, false);
  }
});

test("empty execution error messages receive a nonempty fallback without changing runtime details", () => {
  const error = { message: "", statusCode: 503, opcRequestId: "example-request" };
  const response = executionToolResult({ ...success, error, exitCode: 1 });
  assert.equal(validateExecution(response.structuredContent).valid, true);
  assert.equal(response.isError, true);
  assert.deepEqual(response.structuredContent?.error, {
    message: "Execution failed without an error message", statusCode: 503, opcRequestId: "example-request"
  });
  assert.deepEqual(JSON.parse((response.content[0] as { text: string }).text), response.structuredContent);
  assert.equal(error.message, "");
});

test("discovery rejects malformed identifiers and missing parents before host RPC", async () => {
  let calls = 0;
  const hostRpc = async () => { calls += 1; return null; };
  for (const [args, missing] of [
    [{ client: "IdentityClient" }, /service/],
    [{ operation: "listCompartments" }, /service.*client/],
    [{ service: "identity", operation: "listCompartments" }, /client/],
    [{ client: "IdentityClient", operation: "listCompartments" }, /service/]
  ] as const) {
    await assert.rejects(discoverOci(args, hostRpc), missing);
  }
  for (const field of ["service", "client", "operation"]) {
    for (const value of ["", " ", " identity", "identity ", "a.b", "a-b", "1name", null, 3, true, [], {}]) {
      const args = { service: "identity", client: "IdentityClient", operation: "listCompartments", [field]: value };
      await assert.rejects(discoverOci(args as OciDiscoverPayload, hostRpc), /Invalid discovery input/);
    }
  }
  assert.equal(calls, 0);
});

const discoveryFixtures: Array<{ args: OciDiscoverPayload; result: JsonObject }> = [
  { args: {}, result: { type: "index", services: ["identity"] } },
  { args: { service: "identity" }, result: { type: "service", service: "identity", clients: ["IdentityClient"] } },
  { args: { service: "identity", client: "IdentityClient" }, result: {
    type: "client", service: "identity", client: "IdentityClient", operations: ["listCompartments"]
  } },
  { args: { service: "identity", client: "IdentityClient", operation: "listCompartments" }, result: {
    type: "operation", service: "identity", client: "IdentityClient", operation: "listCompartments", requestShape: "Plain object"
  } }
];

test("discovery preserves all valid result variants and additional extraction data", async () => {
  const validate = schemaValidator(z.toJSONSchema(DISCOVER_OCI_TOOL.outputSchema));
  for (const { args, result } of discoveryFixtures) {
    const data = { ...result, extra: { futureField: [true, null] } } as Json;
    const actual = await discoverOci(args, async request => {
      assert.deepEqual(request, { binding: "oracle", namespace: "oci", operation: "discover", payload: args });
      return data;
    });
    assert.equal(actual, data);
    assert.equal(validate(actual).valid, true);
  }
  const details: JsonObject = {
    ...discoveryFixtures[3].result,
    requestType: "ListCompartmentsRequest",
    requestFields: [{ name: "compartmentId", required: true, type: "string", modelRefs: ["Compartment"], extra: null }],
    models: { Compartment: { fields: [{ name: "id", required: false, type: "string" }], extra: [] } },
    exampleRequest: { compartmentId: "<compartmentId>", nested: { optional: null } },
    responseShape: { bodyKey: "items", bodyModel: "Compartment", requestIdField: "opcRequestId",
      pagination: { nextPageField: "opcNextPage", requestPageField: "page", extra: true }, extra: 42 }
  };
  const actual = await discoverOci(discoveryFixtures[3].args, async () => details as Json);
  assert.equal(actual, details);
  assert.equal(validate(actual).valid, true);
});

test("discovery rejects malformed results instead of presenting successful defaults", async () => {
  const invalid: Json[] = [null, [], "index", {}, { type: "unknown" }];
  for (const { result } of discoveryFixtures) {
    for (const field of Object.keys(result)) {
      const incomplete = { ...result } as Record<string, Json>;
      delete incomplete[field];
      invalid.push(incomplete, { ...result, [field]: 42 } as Json);
    }
  }
  const operation = discoveryFixtures[3].result;
  const invalidDetails: JsonObject[] = [
    { requestType: 42 }, { requestFields: [{}] }, { requestFields: [{ name: "id", required: "true", type: "string" }] },
    { requestFields: [{ name: "id", required: true, type: "string", modelRefs: [1] }] },
    { models: { Compartment: {} } }, { models: [] }, { exampleRequest: [] },
    { responseShape: { bodyKey: 42 } }, { responseShape: { pagination: {} } },
    { responseShape: { pagination: { nextPageField: 42, requestPageField: "page" } } },
    { services: [42] }, { clients: null }, { operations: "list" }
  ];
  for (const override of invalidDetails) invalid.push({ ...operation, ...override });
  for (const result of invalid) {
    await assert.rejects(discoverOci({}, async () => result), /Invalid discovery result/);
  }
});

test("discovery preserves unknown-identifier host errors", async () => {
  const failure = new Error("Unknown OCI SDK service 'Identity'");
  await assert.rejects(discoverOci({ service: "Identity" }, async () => { throw failure; }), error => error === failure);
});
