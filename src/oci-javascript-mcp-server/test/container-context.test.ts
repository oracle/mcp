/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { execFileSync, spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { once } from "node:events";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { createGrpcTlsBootstrap } from "../src/grpc-tls-host.ts";

const root = fileURLToPath(new URL("../", import.meta.url));
const builder = process.env.OCI_JAVASCRIPT_CONTAINER_BUILDER ?? "docker";
const contextEnabled = process.env.OCI_JAVASCRIPT_TEST_CONTAINER_CONTEXT === "true";
const imagesEnabled = process.env.OCI_JAVASCRIPT_TEST_CONTAINER_IMAGES === "true";
const hostImage = process.env.OCI_JAVASCRIPT_TEST_HOST_IMAGE ?? "localhost/oci-javascript-mcp-host:dev";
const runnerImage = process.env.OCI_JAVASCRIPT_TEST_RUNNER_IMAGE ?? "localhost/oci-javascript-mcp-runner:dev";

test("builder context contains the host source closure without local artifacts", {
  skip: !contextEnabled,
  timeout: 120_000
}, t => {
  const output = mkdtempSync(join(tmpdir(), "oci-javascript-context-"));
  const input = join(output, "input");
  mkdirSync(input);
  for (const path of [".dockerignore", ".npmrc", "package.json", "package-lock.json", "buf.gen.yaml", "proto", "src", "scripts"]) {
    cpSync(join(root, path), join(input, path), { recursive: true });
  }
  // Use the real sources and ignore rules with synthetic local artifacts only.
  for (const path of [
    "node_modules/local.ts", "dist/local.ts", "coverage/local.ts", ".git/local.ts",
    ".oci/config", "logs/local.ts", "proto/local.key", "proto/local.log",
    "scripts/local.key", "scripts/local.log", "scripts/node_modules/local.ts",
    "src/generated/stale.ts", "src/notes",
    "src/local.log", "src/.env", "src/isolation/notes", "src/isolation/local.key",
    "src/isolation/node_modules/local.ts", "src/isolation/logs/local.ts"
  ]) {
    mkdirSync(join(input, path, ".."), { recursive: true });
    writeFileSync(join(input, path), "synthetic local artifact\n");
  }
  const name = `oci-javascript-context-${randomUUID()}`;
  const image = `localhost/${name}:test`;
  t.after(() => rmSync(output, { recursive: true, force: true }));
  t.after(() => {
    execFileSync(builder, ["rm", "--force", name], { stdio: "ignore" });
    execFileSync(builder, ["image", "rm", image], { stdio: "ignore" });
  });
  // Let the real builder interpret .dockerignore, including directory traversal.
  execFileSync(builder, ["build", "--file", "-", "--tag", image, "."], {
    cwd: input,
    input: "FROM scratch\nCOPY . /context/\n",
    timeout: 110_000,
    stdio: ["pipe", "pipe", "pipe"]
  });
  // Export a stopped container so this also works with remote Podman builders.
  execFileSync(builder, ["create", "--name", name, image, "/unused"], { stdio: "pipe" });
  const archive = join(output, "context.tar");
  execFileSync(builder, ["export", "--output", archive, name], { stdio: "pipe" });
  execFileSync("tar", ["-xf", archive, "-C", output, "context"], { stdio: "pipe" });
  const context = join(output, "context");
  const sources = readdirSync(join(root, "src"), { recursive: true })
    .map(String).filter(path => path.endsWith(".ts") && !path.startsWith("generated/"));
  for (const path of sources) {
    assert.equal(readFileSync(join(context, "src", path), "utf8"),
      readFileSync(join(root, "src", path), "utf8"), `host context is missing src/${path}`);
  }
  const expected = new Set([
    "package.json", "package-lock.json", ".npmrc", "scripts/setup-native.mjs", "buf.gen.yaml", "proto/runner.proto",
    ...sources.map(path => `src/${path}`)
  ]);
  for (const path of [".npmrc", "scripts/setup-native.mjs"]) {
    assert.equal(readFileSync(join(context, path), "utf8"), readFileSync(join(root, path), "utf8"));
  }
  const files = readdirSync(context, { recursive: true, withFileTypes: true })
    .filter(entry => entry.isFile()).map(entry => join(entry.parentPath, entry.name).slice(context.length + 1));
  assert.deepEqual(new Set(files), expected, "context contains local or stale generated artifacts");
});

test("host image default CMD initializes MCP and lists tools without credentials or networking", {
  skip: !imagesEnabled,
  timeout: 30_000
}, async t => {
  const name = `oci-javascript-host-smoke-${randomUUID()}`;
  t.after(() => execFileSync(builder, ["rm", "--force", name], { stdio: "ignore" }));
  const transport = new StdioClientTransport({
    command: builder,
    args: ["run", "--interactive", "--network=none", "--name", name, hostImage],
    stderr: "pipe",
    env: { PATH: process.env.PATH ?? "" }
  });
  let stderr = "";
  transport.stderr?.on("data", chunk => { stderr += String(chunk); });
  const client = new Client({ name: "container-smoke", version: "1.0.0" });
  try {
    try {
      await client.connect(transport);
    } catch (cause) {
      throw new Error(`host image failed to initialize MCP: ${stderr}`, { cause });
    }
    assert.deepEqual((await client.listTools()).tools.map(tool => tool.name), ["run_javascript", "discover_oci"]);
  } finally {
    await client.close();
  }
  assert.equal(execFileSync(builder, ["wait", name], { encoding: "utf8", timeout: 10_000 }).trim(), "0");
});

test("host image reconciler main loads its dependencies and exits before calling an API when aborted", {
  skip: !imagesEnabled,
  timeout: 30_000
}, () => {
  const output = execFileSync(builder, ["run", "--rm", "--network=none", hostImage,
    "node", "--no-node-snapshot", "--experimental-strip-types", "--input-type=module", "-e", `
      import assert from 'node:assert/strict';
      import { main } from '/app/src/kubernetes-reconciler.ts';
      const controller = new AbortController();
      controller.abort();
      const api = new Proxy({}, { get() { assert.fail('reconciler must not access an API'); } });
      await main({ OCI_JAVASCRIPT_KUBERNETES_PROFILE: 'in-cluster',
        OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: 'smoke-test' }, {
        api, signal: controller.signal,
        diagnostics: () => assert.fail('reconciler must not emit diagnostics')
      });
      console.log('reconciler exited cleanly');
    `], { encoding: "utf8", timeout: 25_000 });
  assert.equal(output.trim(), "reconciler exited cleanly");
});

test("runner image retains its source boundary and accepts a synthetic TLS bootstrap", {
  skip: !imagesEnabled,
  timeout: 30_000
}, async t => {
  const output = execFileSync(builder, ["run", "--rm", "--network=none", runnerImage,
    "node", "-e", "console.log(JSON.stringify(require('node:fs').readdirSync('/app/src', { recursive: true }).filter(p => p.endsWith('.ts')).sort()))"],
  { encoding: "utf8", timeout: 10_000 });
  assert.deepEqual(JSON.parse(output), [
    "generated/runner.ts", "grpc-tls.ts", "grpc.ts", "protocol.ts", "sandbox-common.ts",
    "sandbox-isolate.ts", "sandbox-prelude.ts", "sandbox-worker.ts", "types.ts"
  ]);
  const name = `oci-javascript-runner-smoke-${randomUUID()}`;
  t.after(() => execFileSync(builder, ["rm", "--force", name], { stdio: "ignore" }));
  const child = spawn(builder, ["run", "--interactive", "--network=none", "--name", name, runnerImage], {
    stdio: ["pipe", "pipe", "pipe"], timeout: 20_000
  });
  t.after(() => child.kill());
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", chunk => { stdout += String(chunk); });
  child.stderr.on("data", chunk => { stderr += String(chunk); });
  const ready = new Promise<void>((resolve, reject) => {
    child.stdout.on("data", () => { if (stdout === "READY\n") resolve(); });
    child.once("error", reject);
    child.once("exit", () => reject(new Error(`runner exited before readiness: ${stderr}`)));
  });
  child.stdin.write(`${JSON.stringify(createGrpcTlsBootstrap().runner)}\n`);
  await ready;
  const closed = once(child, "close");
  execFileSync(builder, ["stop", "--time", "1", name], { stdio: "pipe", timeout: 5000 });
  await closed;
});
