#!/usr/bin/env -S node --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";

const [command, ...args] = process.argv.slice(2);
if (command === "run") {
  const nameIndex = args.indexOf("--name");
  assert.match(args[nameIndex + 1] ?? "", /^oci-javascript-[0-9a-f-]{36}$/);
  for (const expected of [
    "--rm", "--interactive", "--name", "--cpus", "1", "--memory", "512M",
    "--read-only", "--cap-drop", "ALL", "--no-dns",
    "--network", "test-internal", "--user", "65532:65532", "--ulimit", "nofile=64:64",
    "test-runner:dev"
  ]) {
    assert.ok(args.includes(expected), `missing hardened run argument: ${expected}`);
  }
  await import("../src/runner.ts");
} else if (command !== "delete") {
  throw new Error(`unexpected fake container command: ${String(command)}`);
}
