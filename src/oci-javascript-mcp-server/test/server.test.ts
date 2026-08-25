/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { once } from "node:events";
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
  } finally {
    await client.close();
  }
});

test("stdio server preserves result fields through a fake Kata provider", async () => {
  const environment = cleanEnvironment();
  environment.OCI_JAVASCRIPT_MAX_CONCURRENT_TOOL_CALLS = "1";
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: [
      "--no-node-snapshot",
      "--experimental-strip-types",
      fileURLToPath(new URL("./fake-kata-server.ts", import.meta.url))
    ],
    env: environment
  });
  const client = new Client({ name: "oci-javascript-kata-test", version: "1.0.0" });
  await client.connect(transport);
  try {
    for (const [code, expected] of [
      ["success", { result: 42, error: null, stdout: "", stderr: "", exit_code: 0, timed_out: false }],
      ["log", { result: 42, error: null, stdout: "stdout-log", stderr: "stderr-log", exit_code: 0, timed_out: false }],
      ["script-error", {
        result: null,
        error: { message: "script failed" },
        stdout: "",
        stderr: "",
        exit_code: 1,
        timed_out: false
      }],
      ["timeout", {
        result: null,
        error: { message: "sandbox run deadline exceeded" },
        stdout: "",
        stderr: "",
        exit_code: -1,
        timed_out: true
      }],
      ["rpc", { result: 42, error: null, stdout: "", stderr: "", exit_code: 0, timed_out: false }]
    ] as const) {
      const response = await client.callTool({
        name: "run_javascript",
        arguments: { code, timeout: 10 }
      });
      assert.deepEqual(response.structuredContent, expected);
      assert.equal(JSON.stringify(response).includes("internalControlPlane"), false);
    }
    const concurrent = await Promise.all([
      client.callTool({ name: "run_javascript", arguments: { code: "delay-one", timeout: 10 } }),
      client.callTool({ name: "run_javascript", arguments: { code: "delay-two", timeout: 10 } })
    ]);
    assert.deepEqual(concurrent.map(
      response => (response.structuredContent as { result?: unknown } | undefined)?.result
    ), [42, 42]);
  } finally {
    await client.close();
  }
});

test("stdio server preserves the contract through every Kubernetes profile", async () => {
  for (const profile of ["local-development", "in-cluster", "kata-in-cluster"] as const) {
    const environment = cleanEnvironment();
    environment.OCI_JAVASCRIPT_TEST_FAKE_PROFILE = profile;
    const transport = new StdioClientTransport({
      command: process.execPath,
      args: [
        "--no-node-snapshot",
        "--experimental-strip-types",
        fileURLToPath(new URL("./fake-kubernetes-server.ts", import.meta.url))
      ],
      env: environment
    });
    const client = new Client({ name: `oci-javascript-${profile}-test`, version: "1.0.0" });
    await client.connect(transport);
    try {
      for (const [code, expected] of [
        ["success", { result: 42, error: null, stdout: "", stderr: "", exit_code: 0, timed_out: false }],
        ["log", { result: 42, error: null, stdout: "stdout-log", stderr: "stderr-log", exit_code: 0, timed_out: false }],
        ["script-error", {
          result: null,
          error: { message: "script failed" },
          stdout: "",
          stderr: "",
          exit_code: 1,
          timed_out: false
        }],
        ["timeout", {
          result: null,
          error: { message: "sandbox run deadline exceeded" },
          stdout: "",
          stderr: "",
          exit_code: -1,
          timed_out: true
        }],
        ["rpc", { result: 42, error: null, stdout: "", stderr: "", exit_code: 0, timed_out: false }],
        ["provider-failure", {
          result: null,
          error: { message: "isolation provider failed" },
          stdout: "",
          stderr: "",
          exit_code: 1,
          timed_out: false
        }]
      ] as const) {
        const response = await client.callTool({
          name: "run_javascript",
          arguments: { code, timeout: 10 }
        });
        assert.deepEqual(response.structuredContent, expected, `${profile}: ${code}`);
        const serialized = JSON.stringify(response);
        assert.equal(serialized.includes("internalControlPlane"), false);
        assert.equal(serialized.includes("runtimeClass"), false);
        assert.equal(serialized.includes("kubeconfig"), false);
      }
    } finally {
      await client.close();
    }
  }
});

test("invalid provider startup exits before MCP stdio accepts a request", async () => {
  const environment = cleanEnvironment();
  environment.OCI_JAVASCRIPT_ISOLATION_PROVIDER = "unknown-provider";
  environment.OCI_JAVASCRIPT_PODMAN_CLI = fileURLToPath(
    new URL("./fake-podman.ts", import.meta.url)
  );
  const child = spawn(process.execPath, [
    "--no-node-snapshot",
    "--experimental-strip-types",
    "src/server.ts"
  ], {
    cwd: process.cwd(),
    env: environment,
    stdio: ["pipe", "pipe", "pipe"]
  });
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", chunk => { stdout += chunk.toString("utf8"); });
  child.stderr.on("data", chunk => { stderr += chunk.toString("utf8"); });
  child.stdin.write('{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n');
  child.stdin.end();
  const [code] = await once(child, "close");
  assert.notEqual(code, 0);
  assert.equal(stdout, "");
  assert.match(stderr, /OCI_JAVASCRIPT_ISOLATION_PROVIDER must be/);
  assert.equal(stderr.includes("unexpected fake Podman command"), false);
});

function cleanEnvironment(): Record<string, string> {
  return Object.fromEntries(
    Object.entries(process.env).filter((entry): entry is [string, string] => entry[1] !== undefined)
  );
}
