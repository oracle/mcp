/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import test from "node:test";
import {
  childProcessChannel,
  runCleanupCommand,
  runnerEnvironment
} from "../src/isolation/pipe-execution.ts";

test("runner environment copies only the process allowlist", () => {
  const previousTemp = process.env.TEMP;
  const previousSecret = process.env.OCI_JAVASCRIPT_TEST_SECRET;
  try {
    process.env.TEMP = "/tmp/oci-javascript-runner-test";
    process.env.OCI_JAVASCRIPT_TEST_SECRET = "must-not-cross-boundary";
    const environment = runnerEnvironment();

    assert.equal(environment.TEMP, "/tmp/oci-javascript-runner-test");
    assert.equal(environment.OCI_JAVASCRIPT_TEST_SECRET, undefined);
    assert.deepEqual(
      Object.keys(environment).filter(name => (
        !["PATH", "TMPDIR", "TMP", "TEMP", "NODE_V8_COVERAGE"].includes(name)
      )),
      []
    );
  } finally {
    restoreEnvironment("TEMP", previousTemp);
    restoreEnvironment("OCI_JAVASCRIPT_TEST_SECRET", previousSecret);
  }
});

test("cleanup commands report spawn and exit failures without raw process output", async () => {
  await runCleanupCommand(process.execPath, ["-e", "process.exit(0)"]);
  await assert.rejects(
    runCleanupCommand(process.execPath, [
      "-e",
      "process.stderr.write('secret cleanup detail'); process.exit(9)"
    ]),
    error => {
      assert.equal(String(error), "Error: Podman cleanup command exited unsuccessfully");
      assert.equal(String(error).includes("secret cleanup detail"), false);
      return true;
    }
  );
  await assert.rejects(
    runCleanupCommand("oci-javascript-command-that-does-not-exist", []),
    /Podman cleanup command failed/
  );
});

test("child process channel stops a process tree and runs cleanup once", async () => {
  const child = spawn(process.execPath, ["-e", "setInterval(() => {}, 1000)"], {
    detached: process.platform !== "win32",
    stdio: ["pipe", "pipe", "pipe"]
  });
  let cleanupCalls = 0;
  const channel = childProcessChannel(child, async () => {
    cleanupCalls += 1;
  });

  await Promise.all([
    channel.stop(Date.now() + 1000),
    channel.stop(Date.now() + 1000)
  ]);

  assert.equal(cleanupCalls, 1);
  const status = await channel.closed;
  assert.equal(status.exitCode, null);
  assert.equal(status.signal, "SIGKILL");
});

function restoreEnvironment(name: string, value: string | undefined): void {
  if (value === undefined) {
    delete process.env[name];
  } else {
    process.env[name] = value;
  }
}
