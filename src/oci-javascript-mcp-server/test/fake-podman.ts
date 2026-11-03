#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";

const [command, ...args] = process.argv.slice(2);
if (command === "network" && args[0] === "create") {
  assert.equal(args.length, 4);
  assert.deepEqual(args.slice(0, 3), ["create", "--internal", "--disable-dns"]);
  assert.match(args[3] ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
} else if (command === "network" && args[0] === "rm") {
  assert.equal(args.length, 3);
  assert.equal(args[1], "--ignore");
  assert.match(args[2] ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
} else if (command === "run") {
  const nameIndex = args.indexOf("--name");
  const name = args[nameIndex + 1];
  const network = args[args.indexOf("--network") + 1];
  const publish = args[args.indexOf("--publish") + 1];
  assert.match(name ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
  assert.match(network ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
  assert.equal(network, name);
  assert.match(publish ?? "", /^127\.0\.0\.1:\d+:50051$/);
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
    "--network", network,
    "--publish", publish,
    "--user", "65532:65532",
    "--ulimit", "nofile=64:64",
    "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
    "test-runner:dev"
  ]);
  process.env.OCI_JAVASCRIPT_RUNNER_PORT = publish?.split(":")[1];
  process.stderr.write("runner-internal-secret\n");
  await import("../src/sandbox-worker.ts");
} else if (command === "rm") {
  assert.equal(args.length, 3);
  assert.deepEqual(args, ["--force", "--ignore", args[2]]);
  assert.match(args[2] ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
} else {
  throw new Error(`unexpected fake Podman command: ${String(command)}`);
}
