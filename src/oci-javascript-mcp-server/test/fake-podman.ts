#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";

const [command, ...args] = process.argv.slice(2);
if (command === "run") {
  const nameIndex = args.indexOf("--name");
  const name = args[nameIndex + 1];
  assert.match(name ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
  assert.deepEqual(args, [
    "--rm",
    "--interactive",
    "--pull", "never",
    "--log-driver", "none",
    "--name", name,
    "--cpus", "1",
    "--memory", "512m",
    "--pids-limit", "64",
    "--read-only",
    "--cap-drop", "ALL",
    "--security-opt", "no-new-privileges",
    "--network", "none",
    "--user", "65532:65532",
    "--ulimit", "nofile=64:64",
    "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
    "test-runner:dev"
  ]);
  process.stderr.write("runner-internal-secret\n");
  await import("../src/sandbox-worker.ts");
} else if (command === "rm") {
  assert.equal(args.length, 3);
  assert.deepEqual(args, ["--force", "--ignore", args[2]]);
  assert.match(args[2] ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
} else {
  throw new Error(`unexpected fake Podman command: ${String(command)}`);
}
