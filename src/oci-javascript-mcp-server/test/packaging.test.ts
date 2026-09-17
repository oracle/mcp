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
  // pretest built the package. Do not regenerate while other tests import it.
  const output = execFileSync("npm", [
    "pack", "--ignore-scripts", "--json", "--pack-destination", directory,
    "--cache", join(tmpdir(), "oci-javascript-mcp-server-npm-cache")
  ], { cwd: new URL("../", import.meta.url), encoding: "utf8", timeout: 30_000 });
  const [pack] = JSON.parse(output) as { filename: string; files: { path: string }[] }[];
  const files = new Set(pack.files.map(file => file.path));
  for (const path of [
    "dist/server.js", "dist/generated/runner.js", "dist/isolation/grpc-execution.js",
    "src/generated/runner.ts", "src/grpc.ts", "proto/runner.proto",
    "buf.gen.yaml", "Containerfile", ".dockerignore"
  ]) {
    assert.ok(files.has(path), `package is missing ${path}`);
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
    env: {
      PATH: process.env.PATH ?? "",
      OCI_JAVASCRIPT_PODMAN_CLI: fileURLToPath(new URL("./fake-podman.ts", import.meta.url)),
      OCI_JAVASCRIPT_PODMAN_IMAGE: "test-runner:dev"
    }
  });
  const client = new Client({ name: "oci-javascript-package-test", version: "1.0.0" });
  try {
    await client.connect(transport);
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
