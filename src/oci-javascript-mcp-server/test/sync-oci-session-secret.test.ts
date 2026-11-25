/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { access, chmod, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const script = join(process.cwd(), "scripts", "sync-oci-session-secret.py");

test("OCI session Secret helper validates session and API-key profiles without exposing values", async () => {
  const directory = await mkdtemp(join(tmpdir(), "oci-js-secret-sync-"));
  try {
    const key = join(directory, "private-key.pem");
    const token = join(directory, "token");
    const config = join(directory, "config");
    await writeFile(key, "private-key-content", { mode: 0o600 });
    await writeFile(token, "session-token-content", { mode: 0o600 });
    await writeFile(config, `[DEFAULT]
fingerprint=fingerprint
tenancy=tenancy
region=us-ashburn-1
key_file=${key}
security_token_file=${token}

[api-key]
user=user
fingerprint=fingerprint
tenancy=tenancy
region=us-ashburn-1
key_file=${key}
`, { mode: 0o600 });

    const session = run(config, "DEFAULT");
    assert.equal(session.status, 0, session.stderr);
    assert.match(session.stdout, /Validated session profile 'DEFAULT'/);
    assert.doesNotMatch(session.stdout, /private-key-content|session-token-content/);

    const apiKey = run(config, "api-key");
    assert.equal(apiKey.status, 0, apiKey.stderr);
    assert.match(apiKey.stdout, /Validated API-key profile 'api-key'/);
    assert.doesNotMatch(apiKey.stdout, /private-key-content|session-token-content/);

    const kubectl = join(directory, "kubectl");
    await writeFile(kubectl, `#!/bin/sh
if [ "$1" = "create" ]; then
  printf '%s\\n' 'apiVersion: v1' 'kind: Secret' 'metadata:' '  name: oci-js-host-oci-config'
  exit 0
fi
if [ "$1" = "apply" ]; then
  cat >/dev/null
  exit 0
fi
if [ "$1" = "rollout" ]; then
  exit 0
fi
exit 1
`, { mode: 0o700 });
    await chmod(kubectl, 0o700);
    const synchronized = run(config, "DEFAULT", false, { PATH: `${directory}:${process.env.PATH}` }, [
      "--restart-host"
    ]);
    assert.equal(synchronized.status, 0, synchronized.stderr);
    assert.match(synchronized.stdout, /restarted the trusted host Deployment/);
    assert.doesNotMatch(synchronized.stdout, /private-key-content|session-token-content/);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

for (const scenario of [
  {
    stage: "refresh",
    summary: "OCI session refresh failed; the Kubernetes Secret was not changed",
    stages: ["refresh"]
  },
  {
    stage: "create",
    summary: "Kubernetes Secret rendering failed; the Kubernetes Secret was not changed",
    stages: ["create"]
  },
  {
    stage: "apply",
    summary: "Kubernetes Secret update failed; the trusted host Deployment was not restarted",
    stages: ["create", "apply"]
  },
  {
    stage: "restart",
    summary: "Trusted host Deployment restart failed; the Kubernetes Secret was already updated",
    stages: ["create", "apply", "restart"]
  },
  {
    stage: "success",
    summary: "Updated Secret 'oci-js-host-oci-config' in namespace 'oci-js-standard-host' and restarted the trusted host Deployment.",
    stages: ["refresh", "create", "apply", "restart"]
  }
]) {
  test(`OCI session Secret helper suppresses child output on ${scenario.stage}`, async () => {
    const directory = await mkdtemp(join(tmpdir(), "oci-js-secret-output-"));
    try {
      const key = "synthetic-private-key-marker";
      const token = "synthetic-session-token-marker";
      const markers = [key, token, Buffer.from(key).toString("base64"), Buffer.from(token).toString("base64")];
      const config = join(directory, "config");
      const calls = join(directory, "calls.jsonl");
      await writeFile(join(directory, "private-key.pem"), key, { mode: 0o600 });
      await writeFile(join(directory, "token"), token, { mode: 0o600 });
      await writeFile(config, `[DEFAULT]
fingerprint=fingerprint
tenancy=tenancy
region=us-ashburn-1
key_file=private-key.pem
security_token_file=token
`, { mode: 0o600 });
      // Replace only the external CLI boundary; config rendering, piping, and cleanup stay real.
      const fakeCommand = `#!/usr/bin/env python3
import base64
import json
import os
from pathlib import Path
import sys

stage = "refresh" if Path(sys.argv[0]).name == "oci" else {"create": "create", "apply": "apply", "rollout": "restart"}[sys.argv[1]]
event = {"stage": stage}
if stage == "create":
    files = dict(argument.removeprefix("--from-file=").split("=", 1) for argument in sys.argv[1:] if argument.startswith("--from-file="))
    event["config_path"] = files["config"]
    manifest = json.dumps({"apiVersion": "v1", "kind": "Secret", "data": {name: base64.b64encode(Path(path).read_bytes()).decode() for name, path in files.items()}})
    Path(os.environ["MANIFEST_FILE"]).write_text(manifest)
elif stage == "apply":
    incoming = sys.stdin.read()
    event["received_secret"] = incoming == Path(os.environ["MANIFEST_FILE"]).read_text() + "\\n"
with open(os.environ["CALLS_FILE"], "a") as output:
    output.write(json.dumps(event) + "\\n")
noise = " ".join(json.loads(os.environ["OUTPUT_MARKERS"]))
if stage == "create" and os.environ["FAIL_STAGE"] != stage:
    print(manifest)
elif os.environ["FAIL_STAGE"] in (stage, "success"):
    print(noise)
    if stage == "apply":
        print(incoming)
if os.environ["FAIL_STAGE"] in (stage, "success"):
    print(noise, file=sys.stderr)
    if stage == "apply":
        print(incoming, file=sys.stderr)
sys.exit(7 if os.environ["FAIL_STAGE"] == stage else 0)
`;
      await writeFile(join(directory, "oci"), fakeCommand, { mode: 0o700 });
      await writeFile(join(directory, "kubectl"), fakeCommand, { mode: 0o700 });
      const result = run(config, "DEFAULT", false, {
        PATH: `${directory}:${process.env.PATH}`,
        CALLS_FILE: calls,
        MANIFEST_FILE: join(directory, "manifest"),
        OUTPUT_MARKERS: JSON.stringify(markers),
        FAIL_STAGE: scenario.stage
      }, [
        ...(scenario.stage === "refresh" || scenario.stage === "success" ? ["--refresh-session"] : []),
        "--restart-host"
      ]);

      assert.equal(result.status, scenario.stage === "success" ? 0 : 1);
      const events = (await readFile(calls, "utf8")).trim().split("\n").map(line => JSON.parse(line));
      assert.deepEqual(events.map(event => event.stage), scenario.stages);
      const created = events.find(event => event.stage === "create");
      if (created) {
        await assert.rejects(access(created.config_path), { code: "ENOENT" });
      }
      const applied = events.find(event => event.stage === "apply");
      if (applied) {
        assert.equal(applied.received_secret, true, "apply must receive the complete rendered Secret");
      }
      for (const [stream, output] of [["stdout", result.stdout], ["stderr", result.stderr]]) {
        for (const [index, marker] of markers.entries()) {
          assert.equal(output.includes(marker), false, `${stream} leaked synthetic credential marker ${index}`);
        }
      }
      assert.equal(result.stdout, scenario.stage === "success" ? `${scenario.summary}\n` : "");
      assert.equal(result.stderr, scenario.stage === "success" ? "" : `error: ${scenario.summary}\n`);
    } finally {
      await rm(directory, { recursive: true, force: true });
    }
  });
}

function run(
  config: string,
  profile: string,
  dryRun = true,
  environment: NodeJS.ProcessEnv = {},
  argumentsAfterProfile: string[] = []
) {
  return spawnSync(
    "python3",
    [
      script,
      "--config-file",
      config,
      "--profile",
      profile,
      ...(dryRun ? ["--dry-run"] : []),
      ...argumentsAfterProfile
    ],
    { encoding: "utf8", env: { ...process.env, ...environment } }
  );
}
