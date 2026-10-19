/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { schemaValidator } from "./schema-validator.ts";

test("stdio server advertises and executes its MCP tools", async t => {
  const directory = mkdtempSync(join(tmpdir(), "oci-javascript-server-test-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const { privateKey } = generateKeyPairSync("rsa", {
    modulusLength: 2048, privateKeyEncoding: { type: "pkcs8", format: "pem" },
    publicKeyEncoding: { type: "spki", format: "pem" }
  });
  writeFileSync(join(directory, "key.pem"), privateKey);
  writeFileSync(join(directory, "config"), `[DEFAULT]
user=ocid1.user.oc1..example
tenancy=ocid1.tenancy.oc1..example
fingerprint=example
region=us-ashburn-1
key_file=${join(directory, "key.pem")}
`);
  const environment = Object.fromEntries(
    Object.entries(process.env).filter((entry): entry is [string, string] => (
      entry[1] !== undefined
    ))
  );
  environment.OCI_JAVASCRIPT_PODMAN_CLI = fileURLToPath(
    new URL("./fake-podman.ts", import.meta.url)
  );
  environment.OCI_JAVASCRIPT_PODMAN_IMAGE = "test-runner:dev";
  environment.OCI_JAVASCRIPT_MAX_RESULT_BYTES = "1500000";
  environment.OCI_JAVASCRIPT_MAX_CONCURRENT_TOOL_CALLS = "1";
  environment.OCI_CONFIG_FILE = join(directory, "config");
  environment.OCI_CONFIG_PROFILE = "DEFAULT";
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [
      "--no-node-snapshot",
      "--experimental-strip-types",
      "--import", "data:text/javascript," + encodeURIComponent(`
        globalThis.fetch = async request => {
          const url = typeof request === "string" ? request : request.url;
          if (url.includes("/regionSubscriptions")) return new Response(JSON.stringify([
            { regionName: "us-ashburn-1", regionKey: "IAD", status: "READY", isHomeRegion: true },
            { regionName: "us-phoenix-1", regionKey: "PHX", status: "READY", isHomeRegion: false }
          ]), { status: 200, headers: { "content-type": "application/json" } });
          return new Response(JSON.stringify({
          code: "ServiceUnavailable", message: "private service details"
        }), { status: 503, headers: {
          "content-type": "application/json", "opc-request-id": "example-request"
        } }); };
      `),
      "src/server.ts"
    ],
    env: environment
  });
  const client = new Client({ name: "oci-javascript-test", version: "1.0.0" });

  await client.connect(transport);
  try {
    const tools = await client.listTools();
    assert.deepEqual(tools.tools.map(tool => tool.name), ["run_javascript", "discover_oci"]);
    const runTool = tools.tools[0];
    assert.equal(runTool.title, "Run OCI JavaScript");
    assert.deepEqual(runTool.annotations, {
      readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true
    });
    assert.equal(runTool.outputSchema?.type, "object");
    assert.deepEqual(runTool.outputSchema?.required, [
      "result", "error", "stdout", "stderr", "exit_code", "timed_out"
    ]);
    const validateRun = schemaValidator(runTool.outputSchema!);
    const codeSchema = runTool.inputSchema.properties?.code as { description: string };
    assert.match(codeSchema.description, /return response.items.map/);
    assert.match(codeSchema.description, /1 MiB/);
    assert.deepEqual(runTool.inputSchema.properties?.timeout, {
      type: "number", minimum: 1, maximum: 120, default: 30,
      description: (runTool.inputSchema.properties?.timeout as { description: string }).description
    });
    assert.match(client.getInstructions() ?? "", /camelCase/);
    const discoverTool = tools.tools[1];
    assert.equal(discoverTool.title, "Discover OCI SDK");
    assert.deepEqual(discoverTool.annotations, { readOnlyHint: true, openWorldHint: false });
    assert.equal(discoverTool.outputSchema?.type, "object");
    assert.deepEqual(discoverTool.outputSchema?.required, ["type"]);
    for (const field of ["service", "client", "operation"]) {
      const input = discoverTool.inputSchema.properties?.[field] as { pattern: string; description: string };
      assert.equal(input.pattern, "^[A-Za-z][A-Za-z0-9_]*$");
      assert.match(input.description, /case-sensitive/i);
    }
    const validateDiscovery = schemaValidator(discoverTool.outputSchema!);

    const oversizedResult = await client.callTool({
      name: "run_javascript",
      arguments: { code: "x".repeat(1024 * 1024 + 1), timeout: 10 }
    });
    assert.equal(oversizedResult.isError, true);
    const oversizedContent = oversizedResult.content as Array<{ text: string }>;
    assert.match(
      oversizedContent[0].text,
      /JavaScript code exceeds 1048576 bytes/
    );

    const runResult = await client.callTool({
      name: "run_javascript",
      arguments: { code: "40 + 2;", timeout: 10 }
    });
    assert.deepEqual(runResult.structuredContent, {
      result: 42,
      error: null,
      stdout: "",
      stderr: "",
      exit_code: 0,
      timed_out: false
    });
    assert.equal(JSON.stringify(runResult).includes("runner-internal-secret"), false);
    assert.equal(runResult.isError ?? false, false);
    assert.equal(validateRun(runResult.structuredContent).valid, true);
    const advertisedExample = /```js\n([\s\S]*?)\n```/.exec(codeSchema.description)?.[1];
    assert.ok(advertisedExample);
    const exampleResult = await client.callTool({ name: "run_javascript", arguments: { code: advertisedExample } });
    assert.equal(exampleResult.isError ?? false, false);
    assert.deepEqual((exampleResult.structuredContent as Record<string, unknown>).result, ["us-ashburn-1", "us-phoenix-1"]);
    assert.equal(validateRun(exampleResult.structuredContent).valid, true);
    for (const [code, expected] of [
      ["return null;", null], ["return true;", true], ["return [1, null];", [1, null]],
      ["return 42n;", { __oci_wire_type: "bigint", value: "42" }]
    ]) {
      const response = await client.callTool({ name: "run_javascript", arguments: { code, timeout: 10 } });
      assert.equal(response.isError ?? false, false);
      assert.deepEqual((response.structuredContent as Record<string, unknown>).result, expected);
      assert.equal(validateRun(response.structuredContent).valid, true);
      assert.deepEqual(JSON.parse((response.content as Array<{ text: string }>)[0].text), response.structuredContent);
    }
    for (const [code, timeout] of [["throw new Error('script failed');", 10], ['throw "";', 10], ["while (true) {}", 1]] as const) {
      const response = await client.callTool({ name: "run_javascript", arguments: { code, timeout } });
      assert.equal(response.isError, true);
      assert.equal(validateRun(response.structuredContent).valid, true);
      assert.equal((response.structuredContent as Record<string, unknown>).timed_out, timeout === 1);
      assert.deepEqual(JSON.parse((response.content as Array<{ text: string }>)[0].text), response.structuredContent);
    }
    for (const args of [{}, { code: 42 }, { code: "return 1;", timeout: 0 }, { code: "return 1;", timeout: 121 }]) {
      const response = await client.callTool({ name: "run_javascript", arguments: args });
      assert.equal(response.isError, true);
      assert.equal(response.structuredContent, undefined);
    }

    const failedOciCall = await client.callTool({
      name: "run_javascript",
      arguments: {
        code: 'await oci.identity.IdentityClient.listCompartments({ compartmentId: "ocid1.compartment.oc1..example" })',
        timeout: 10
      }
    });
    assert.deepEqual(failedOciCall.structuredContent, {
      result: null,
      error: {
        message: "OCI call failed", name: "Error", statusCode: 503,
        serviceCode: "ServiceUnavailable", opcRequestId: "example-request",
        targetService: "Identity", operationName: "listCompartments"
      },
      stdout: "", stderr: "", exit_code: 1, timed_out: false
    });
    const errorContent = failedOciCall.content as Array<{ text: string }>;
    assert.equal(failedOciCall.isError, true);
    assert.equal(validateRun(failedOciCall.structuredContent).valid, true);
    assert.deepEqual(JSON.parse(errorContent[0].text), failedOciCall.structuredContent);
    assert.equal(JSON.stringify(failedOciCall).includes("private service details"), false);

    const discoveryResult = await client.callTool({
      name: "discover_oci",
      arguments: {}
    });
    const discovery = discoveryResult.structuredContent as {
      type?: unknown;
      services?: unknown;
    };
    assert.equal(discovery.type, "index");
    assert.equal(Array.isArray(discovery.services), true);
    for (const args of [
      { service: "identity" },
      { service: "identity", client: "IdentityClient" },
      { service: "identity", client: "IdentityClient", operation: "listCompartments" }
    ]) {
      const response = await client.callTool({ name: "discover_oci", arguments: args });
      assert.equal(response.isError ?? false, false);
      assert.equal(validateDiscovery(response.structuredContent).valid, true);
      assert.deepEqual(JSON.parse((response.content as Array<{ text: string }>)[0].text), response.structuredContent);
    }
    assert.equal(validateDiscovery(discovery).valid, true);
    for (const args of [
      { client: "IdentityClient" }, { operation: "listCompartments" },
      { service: "identity", operation: "listCompartments" },
      { client: "IdentityClient", operation: "listCompartments" },
      { service: "" }, { service: " identity" }, { service: "a.b" },
      { service: 42 }, { service: "Identity" }, { service: "unknownService" },
      { service: "identity", client: "identityClient" },
      { service: "identity", client: "IdentityClient", operation: "ListCompartments" }
    ]) {
      const response = await client.callTool({ name: "discover_oci", arguments: args });
      assert.equal(response.isError, true, JSON.stringify(args));
      assert.equal(response.structuredContent, undefined);
      assert.ok((response.content as Array<{ text: string }>)[0].text.length > 0);
    }

    for (const length of [1_500_000 - 2, 1_500_000]) {
      const response = await client.callTool({
        name: "run_javascript", arguments: { code: `"x".repeat(${length})`, timeout: 10 }
      });
      const value = response.structuredContent as Record<string, unknown>;
      if (length < 1_500_000) {
        assert.equal(value.exit_code, 0);
        assert.equal((value.result as string).length, length);
      } else {
        assert.equal(value.exit_code, 1);
        assert.equal(response.isError, true);
        assert.match((value.error as { message: string }).message, /exceeding result limit 1500000 bytes/);
      }
      assert.equal(validateRun(value).valid, true);
    }

    const controller = new AbortController();
    const cancelled = assert.rejects(client.callTool({
      name: "run_javascript", arguments: { code: "while (true) {}", timeout: 30 }
    }, undefined, { signal: controller.signal }), /abort/i);
    const busy = await client.callTool({ name: "discover_oci", arguments: {} });
    assert.equal(busy.isError, true);
    controller.abort();
    await cancelled;
    const cleanupDeadline = Date.now() + 5000;
    while (true) {
      const next = await client.callTool({ name: "discover_oci", arguments: {} });
      if (!next.isError) break;
      assert(Date.now() < cleanupDeadline, "cancelled execution must release its slot before its deadline");
      await new Promise(resolve => setTimeout(resolve, 50));
    }
  } finally {
    await client.close();
  }
});
