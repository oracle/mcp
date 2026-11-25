/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */
import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile, symlink } from "node:fs/promises";
import { networkInterfaces, tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { execFile, spawn } from "node:child_process";
import { createServer } from "node:net";
import { once } from "node:events";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { createGrpcTlsBootstrap } from "../src/grpc-tls-host.ts";
import { readRunnerTlsFiles, runnerTlsMode, RUNNER_TLS_DIRECTORY } from "../src/grpc-tls.ts";
import { startGrpcExecution } from "../src/isolation/grpc-execution.ts";

test("TLS files preserve exact bootstrap fields and projected symlinks", async () => {
  const directory = await mkdtemp(join(tmpdir(), "runner-tls-"));
  try {
    const tls = createGrpcTlsBootstrap().runner;
    for (const [key, value] of Object.entries(tls)) {
      await writeFile(join(directory, `${key}.pem`), value);
      await symlink(`${key}.pem`, join(directory, key));
    }
    assert.deepEqual(await readRunnerTlsFiles(directory), tls);
    assert.equal(RUNNER_TLS_DIRECTORY, "/run/oci-javascript/tls");
  } finally { await rm(directory, { recursive: true, force: true }); }
});

test("TLS files reject missing empty oversized and combined oversized content", async () => {
  const directory = await mkdtemp(join(tmpdir(), "runner-tls-"));
  try {
    await assert.rejects(readRunnerTlsFiles(directory), /^Error: invalid sandbox TLS bootstrap$/);
    for (const key of ["serverKey", "serverCert", "clientCert"]) await writeFile(join(directory, key), "key");
    await writeFile(join(directory, "serverKey"), "");
    await assert.rejects(readRunnerTlsFiles(directory), /invalid sandbox TLS bootstrap/);
    await writeFile(join(directory, "serverKey"), "x".repeat(32 * 1024 + 1));
    await assert.rejects(readRunnerTlsFiles(directory), /invalid sandbox TLS bootstrap/);
    for (const key of ["serverKey", "serverCert", "clientCert"]) await writeFile(join(directory, key), "x".repeat(12 * 1024));
    await assert.rejects(readRunnerTlsFiles(directory), /invalid sandbox TLS bootstrap/);
  } finally { await rm(directory, { recursive: true, force: true }); }
});

test("runner TLS mode accepts only exact host-owned arguments", () => {
  assert.equal(runnerTlsMode([]), "stdin");
  assert.equal(runnerTlsMode(["--tls-files"]), "files");
  for (const args of [["--tls-files", "/other"], ["--unknown"], ["--tls-files", "--tls-files"]]) {
    assert.throws(() => runnerTlsMode(args), /invalid sandbox TLS bootstrap/);
  }
});

test("worker file mode and invalid arguments fail promptly without waiting for stdin", async () => {
  for (const args of [["--tls-files"], ["--unknown"]]) {
    await assert.rejects(promisify(execFile)(process.execPath, [
      "--no-node-snapshot", "--experimental-strip-types",
      fileURLToPath(new URL("../src/sandbox-worker.ts", import.meta.url)), ...args
    ], { timeout: 3000 }), error => {
      const value = error as Error & { code: number; stderr: string; stdout: string };
      assert.equal(value.code, 70);
      assert.equal(value.stderr, "");
      assert.equal(value.stdout, "");
      return true;
    });
  }
});

for (const host of ["127.0.0.1", "::1"]) {
  test(`actual worker accepts authenticated execution over ${host}`, {
    skip: host === "::1" && !Object.values(networkInterfaces()).flat().some(value => value?.family === "IPv6")
  }, async () => {
    const reservation = createServer();
    reservation.listen(0, host);
    await once(reservation, "listening");
    const port = (reservation.address() as import("node:net").AddressInfo).port;
    await new Promise<void>(resolve => reservation.close(() => resolve()));
    const tls = createGrpcTlsBootstrap();
    const child = spawn(process.execPath, ["--no-node-snapshot", "--experimental-strip-types",
      fileURLToPath(new URL("../src/sandbox-worker.ts", import.meta.url))], {
      env: { ...process.env, OCI_JAVASCRIPT_RUNNER_PORT: String(port) }, stdio: ["pipe", "pipe", "pipe"]
    });
    const closed = once(child, "close");
    let output = "";
    const ready = new Promise<void>((resolve, reject) => {
      child.stdout.on("data", chunk => { output += String(chunk); if (output === "READY\n") resolve(); });
      child.once("error", reject);
      child.once("exit", () => reject(new Error("worker exited before readiness")));
    });
    const timer = setTimeout(() => child.kill(), 10_000);
    try {
      child.stdin.write(`${JSON.stringify(tls.runner)}\n`);
      await ready;
      const execution = startGrpcExecution(host === "::1" ? `[::1]:${port}` : `${host}:${port}`,
        tls.credentials, "40 + 2", { deadlineMs: Date.now() + 2000,
          signal: new AbortController().signal, hostRpc: async () => null,
          memoryLimitMb: 128, maxResultBytes: 1024 * 1024 });
      const result = await execution.result;
      assert.equal(result.result, 42);
      assert.equal(result.error, null);
      assert.equal((await closed)[0], 0);
    } finally { clearTimeout(timer); child.kill(); await closed; }
  });
}
