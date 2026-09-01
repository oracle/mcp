/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const packageJson = JSON.parse(readFileSync("package.json", "utf8")) as {
  scripts: Record<string, string>;
};
const guides = [
  "README.md",
  "docs/kubernetes-isolation-profiles.md",
  "docs/kata-kubernetes-poc.md",
  "docs/architecture-and-isolation-design.md"
];

test("Kubernetes guide npm validation commands resolve to package scripts", () => {
  for (const guide of guides) {
    const source = readFileSync(guide, "utf8");
    const commands = [...source.matchAll(/\bnpm run ([a-z0-9:-]+)/g)].map(match => match[1]!);
    for (const command of commands) {
      assert.equal(
        Object.hasOwn(packageJson.scripts, command),
        true,
        `${guide}: npm run ${command}`
      );
    }
  }
});
