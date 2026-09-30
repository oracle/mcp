/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

test("npm package runs from node_modules with compiled bindings", { timeout: 30_000 }, async t => {
  const directory = mkdtempSync(join(tmpdir(), "oci-javascript-package-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  // Moon compiled the package. Do not regenerate while other tests import it.
  const output = execFileSync("npm", [
    "pack", "--ignore-scripts", "--json", "--pack-destination", directory,
    "--cache", join(tmpdir(), "oci-javascript-mcp-server-npm-cache")
  ], { cwd: new URL("../", import.meta.url), encoding: "utf8", timeout: 30_000 });
  const [pack] = JSON.parse(output) as { filename: string; files: { path: string }[] }[];
  const files = new Set(pack.files.map(file => file.path));
  assert.ok(![...files].some(path => path.endsWith(".tgz")), "package includes a prior tarball");
  for (const path of [
    "dist/server.js", "dist/generated/runner.js", "dist/isolation/grpc-execution.js",
    "dist/isolation/kubernetes.js", "dist/isolation/kubernetes-grpc.js",
    "src/generated/runner.ts", "src/grpc.ts", "src/grpc-tls.ts", "proto/runner.proto",
    "buf.gen.yaml", "Containerfile", "Containerfile.host", ".dockerignore",
    "examples/kubernetes/v1/standard-in-cluster.yaml",
    "examples/kata-kubernetes/v1/02-rbac.yaml",
    "scripts/kubectl-dry-run-kubernetes.ts"
  ]) {
    assert.ok(files.has(path), `package is missing ${path}`);
  }
  for (const path of [
    "src/isolation/pipe-execution.ts",
    "src/isolation/worker-channel.ts",
    "dist/isolation/pipe-execution.js",
    "dist/isolation/worker-channel.js"
  ]) {
    assert.equal(files.has(path), false, `package includes removed transport ${path}`);
  }

  const installed = join(directory, "node_modules", "oci-javascript-mcp-server");
  mkdirSync(installed, { recursive: true });
  execFileSync("tar", ["-xzf", join(directory, pack.filename), "--strip-components=1", "-C", installed]);
  // Reuse installed dependencies; server code and metadata come only from the tarball.
  symlinkSync(fileURLToPath(new URL("../node_modules", import.meta.url)), join(installed, "node_modules"), "dir");
  const { bin } = JSON.parse(readFileSync(join(installed, "package.json"), "utf8"));
  const transport = new StdioClientTransport({
    command: process.execPath,
    args: ["--no-node-snapshot", join(installed, bin["oci-javascript-mcp-server"])],
    cwd: directory,
    stderr: "pipe",
    env: {
      PATH: process.env.PATH ?? "",
      OCI_JAVASCRIPT_PODMAN_CLI: fileURLToPath(new URL("./fake-podman.ts", import.meta.url)),
      OCI_JAVASCRIPT_PODMAN_IMAGE: "test-runner:dev"
    }
  });
  let serverStderr = "";
  transport.stderr?.on("data", chunk => { serverStderr += String(chunk); });
  const client = new Client({ name: "oci-javascript-package-test", version: "1.0.0" });
  try {
    try {
      await client.connect(transport);
    } catch (error) {
      throw new Error(`packaged server failed to start: ${serverStderr}`, { cause: error });
    }
    const tools = await client.listTools();
    assert.deepEqual(tools.tools.map(tool => tool.name), ["run_javascript", "discover_oci"]);
    const result = await client.callTool({
      name: "run_javascript",
      arguments: { code: "40 + 2", timeout: 10 }
    });
    assert.deepEqual(result.structuredContent, {
      result: 42, error: null, stdout: "", stderr: "", exit_code: 0, timed_out: false
    });
  } finally {
    await client.close();
  }
});
