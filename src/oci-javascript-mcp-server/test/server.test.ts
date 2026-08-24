/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { createMcpServer, dependenciesFromEnvironment } from "../src/server.ts";
import { OciSdkRuntime } from "../src/oci.ts";
import type { IsolationProvider, ReflectionManifest } from "../src/types.ts";

test("stdio server advertises and executes both MCP tools", async () => {
  const environment = Object.fromEntries(
    Object.entries(process.env).filter((entry): entry is [string, string] => entry[1] !== undefined)
  );
  environment.OCI_JAVASCRIPT_MODE = "development";
  environment.OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS = "1";
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: ["--experimental-strip-types", "src/server.ts"],
    env: environment
  });
  const client = new Client({ name: "oci-javascript-test", version: "1.0.0" });
  await client.connect(transport);
  try {
    const tools = await client.listTools();
    assert.deepEqual(tools.tools.map(tool => tool.name), ["run_javascript", "discover_oci"]);
    const run = await client.callTool({
      name: "run_javascript",
      arguments: { code: "40 + 2", timeout: 5 }
    });
    assert.deepEqual(run.structuredContent, {
      result: 42,
      error: null,
      stdout: "",
      stderr: "",
      exit_code: 0,
      timed_out: false
    });
    const discovery = await client.callTool({ name: "discover_oci", arguments: {} });
    assert.equal((discovery.structuredContent as { type?: unknown }).type, "index");
  } finally {
    await client.close();
  }
});

test("in-memory MCP handlers return structured results and safe failures", async () => {
  const manifest: ReflectionManifest = { services: {} };
  const runtime = new OciSdkRuntime(() => ({ sdk: {}, common: {} }), () => ({}));
  Object.defineProperties(runtime, {
    manifest: { value: () => manifest },
    discover: {
      value: (filter: Record<string, unknown>) => ({ type: "test", ...filter }),
      writable: true
    }
  });
  const provider: IsolationProvider = {
    capabilities: {
      provider: "test", boundary: "process", developmentOnly: true,
      separateGuestKernel: false, hardwareVirtualization: false, networkCreationBlocked: false
    },
    async start() {
      return {
        result: Promise.resolve({
          result: 9, error: null, stdout: "out", stderr: "", exitCode: 0, timedOut: false
        }),
        async destroy() {}
      };
    }
  };
  const server = createMcpServer({ provider, runtime, mode: "development" });
  const client = new Client({ name: "in-memory-test", version: "1" });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await Promise.all([server.connect(serverTransport), client.connect(clientTransport)]);
  try {
    const run = await client.callTool({ name: "run_javascript", arguments: { code: "3 * 3" } });
    assert.equal((run.structuredContent as any).result, 9);
    const discover = await client.callTool({
      name: "discover_oci", arguments: { service: "core" }
    });
    assert.deepEqual(discover.structuredContent, { type: "test", service: "core" });

    provider.start = async () => { throw new Error("private provider detail"); };
    const failedRun = await client.callTool({
      name: "run_javascript", arguments: { code: "1" }
    });
    assert.equal(
      (failedRun.structuredContent as any).error.message,
      "JavaScript execution could not be started"
    );
    (runtime as any).discover = () => { throw new Error("private discovery detail"); };
    const failedDiscovery = await client.callTool({
      name: "discover_oci", arguments: { service: "core" }
    });
    assert.equal((failedDiscovery.structuredContent as any).error.message, "OCI discovery failed");
  } finally {
    await client.close();
    await server.close();
  }
});

test("environment dependency selection requires known provider and explicit development opt-in", () => {
  const saved = {
    mode: process.env.OCI_JAVASCRIPT_MODE,
    provider: process.env.OCI_JAVASCRIPT_ISOLATION_PROVIDER,
    allow: process.env.OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS,
    image: process.env.OCI_JAVASCRIPT_APPLE_CONTAINER_IMAGE,
    network: process.env.OCI_JAVASCRIPT_APPLE_CONTAINER_NETWORK
  };
  try {
    process.env.OCI_JAVASCRIPT_ISOLATION_PROVIDER = "unknown";
    assert.throws(() => dependenciesFromEnvironment(), /not implemented/);
    process.env.OCI_JAVASCRIPT_ISOLATION_PROVIDER = "process";
    process.env.OCI_JAVASCRIPT_MODE = "development";
    process.env.OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS = "1";
    const dependencies = dependenciesFromEnvironment();
    assert.equal(dependencies.mode, "development");
    assert.equal(dependencies.provider.capabilities.provider, "process");

    process.env.OCI_JAVASCRIPT_ISOLATION_PROVIDER = "apple-container";
    process.env.OCI_JAVASCRIPT_APPLE_CONTAINER_IMAGE = "custom-runner:dev";
    process.env.OCI_JAVASCRIPT_APPLE_CONTAINER_NETWORK = "custom-internal";
    const appleDependencies = dependenciesFromEnvironment();
    assert.equal(appleDependencies.provider.capabilities.provider, "apple-container");
    assert.equal(appleDependencies.provider.capabilities.boundary, "virtual-machine");
  } finally {
    restoreEnvironment("OCI_JAVASCRIPT_MODE", saved.mode);
    restoreEnvironment("OCI_JAVASCRIPT_ISOLATION_PROVIDER", saved.provider);
    restoreEnvironment("OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS", saved.allow);
    restoreEnvironment("OCI_JAVASCRIPT_APPLE_CONTAINER_IMAGE", saved.image);
    restoreEnvironment("OCI_JAVASCRIPT_APPLE_CONTAINER_NETWORK", saved.network);
  }
});

function restoreEnvironment(name: string, value: string | undefined): void {
  if (value === undefined) delete process.env[name];
  else process.env[name] = value;
}

test("server startup fails closed without development process opt-in", async () => {
  const { spawn } = await import("node:child_process");
  const child = spawn(process.execPath, ["--experimental-strip-types", "src/server.ts"], {
    env: { PATH: process.env.PATH ?? "" },
    stdio: ["ignore", "ignore", "pipe"]
  });
  let stderr = "";
  child.stderr.on("data", chunk => { stderr += String(chunk); });
  const code = await new Promise<number | null>(resolve => child.once("exit", resolve));
  assert.notEqual(code, 0);
  assert.match(stderr, /local process isolation is insecure/);
});

test("production rejects the process provider even when process opt-in is present", async () => {
  const { spawn } = await import("node:child_process");
  const child = spawn(process.execPath, ["--experimental-strip-types", "src/server.ts"], {
    env: {
      PATH: process.env.PATH ?? "",
      OCI_JAVASCRIPT_MODE: "production",
      OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS: "1"
    },
    stdio: ["ignore", "ignore", "pipe"]
  });
  let stderr = "";
  child.stderr.on("data", chunk => { stderr += String(chunk); });
  const code = await new Promise<number | null>(resolve => child.once("exit", resolve));
  assert.notEqual(code, 0);
  assert.match(stderr, /not admitted in production/);
});
