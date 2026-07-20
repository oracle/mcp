/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

test("stdio server advertises and executes its MCP tools", async () => {
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [
      "--no-node-snapshot",
      "--experimental-strip-types",
      "src/server.ts"
    ]
  });
  const client = new Client({ name: "oci-javascript-test", version: "1.0.0" });

  await client.connect(transport);
  try {
    const tools = await client.listTools();
    assert.deepEqual(tools.tools.map(tool => tool.name), ["run_javascript", "discover_oci"]);

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
  } finally {
    await client.close();
  }
});
