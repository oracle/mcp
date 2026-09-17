/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

test("stdio server advertises and executes its MCP tools", async () => {
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
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [
      "--no-node-snapshot",
      "--experimental-strip-types",
      "src/server.ts"
    ],
    env: environment
  });
  const client = new Client({ name: "oci-javascript-test", version: "1.0.0" });

  await client.connect(transport);
  try {
    const tools = await client.listTools();
    assert.deepEqual(tools.tools.map(tool => tool.name), ["run_javascript", "discover_oci"]);

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
        assert.match((value.error as { message: string }).message, /exceeding result limit 1500000 bytes/);
      }
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
