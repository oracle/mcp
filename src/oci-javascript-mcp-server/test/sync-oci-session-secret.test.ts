/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { chmod, mkdtemp, rm, writeFile } from "node:fs/promises";
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
