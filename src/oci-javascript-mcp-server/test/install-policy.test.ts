/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import test, { type TestContext } from "node:test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const installCommand = "node-gyp-build || node-gyp rebuild --release -j max";

function fixture(t: TestContext) {
  const directory = mkdtempSync(join(tmpdir(), "oci-javascript-install-"));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  writeFileSync(join(directory, "package.json"), JSON.stringify({ name: "install-policy-fixture", version: "1.0.0", private: true }));
  writeFileSync(join(directory, "user.npmrc"), "");
  writeFileSync(join(directory, "global.npmrc"), "");
  const env = Object.fromEntries(Object.entries(process.env).filter(([name]) => !/^npm_config_/i.test(name)));
  Object.assign(env, {
    npm_config_userconfig: join(directory, "user.npmrc"),
    npm_config_globalconfig: join(directory, "global.npmrc"),
    npm_config_cache: join(directory, "cache"),
    npm_config_offline: "true", npm_config_audit: "false", npm_config_fund: "false"
  });
  return { directory, env };
}

function policy(directory: string) {
  const source = join(root, ".npmrc");
  writeFileSync(join(directory, ".npmrc"), existsSync(source) ? readFileSync(source) : "");
}

function deniedDependency(directory: string) {
  const source = join(directory, "denied", "package");
  mkdirSync(source, { recursive: true });
  writeFileSync(join(source, "package.json"), JSON.stringify({
    name: "denied-lifecycle", version: "1.0.0",
    scripts: { install: "node -e \"require('node:fs').writeFileSync('denied-install', 'executed')\"" }
  }));
  execFileSync("tar", ["-czf", join(directory, "denied.tgz"), "-C", dirname(source), "package"]);
  const manifest = { name: "install-policy-fixture", version: "1.0.0", private: true,
    dependencies: { "denied-lifecycle": "file:denied.tgz" }, allowScripts: { "isolated-vm@7.0.0": true } };
  writeFileSync(join(directory, "package.json"), JSON.stringify(manifest));
  writeFileSync(join(directory, "package-lock.json"), JSON.stringify({
    name: manifest.name, version: manifest.version, lockfileVersion: 3, requires: true,
    packages: {
      "": { name: manifest.name, version: manifest.version, dependencies: manifest.dependencies },
      "node_modules/denied-lifecycle": { version: "1.0.0", resolved: "file:denied.tgz", hasInstallScript: true }
    }
  }));
  return join(directory, "node_modules", "denied-lifecycle", "denied-install");
}

test("allowScripts metadata does not gate an unapproved dependency install hook", t => {
  const { directory, env } = fixture(t);
  t.diagnostic(`Actual fixture npm version: ${execFileSync("npm", ["--version"], { env, encoding: "utf8" }).trim()}`);
  const sentinel = deniedDependency(directory);
  execFileSync("npm", ["ci", "--offline", "--no-audit"], { cwd: directory, env, stdio: "pipe", timeout: 30_000 });
  assert.equal(existsSync(sentinel), true, "baseline must demonstrate execution despite allowScripts");
});

test("server-local policy suppresses dependency lifecycle hooks during clean install and dedupe", t => {
  const { directory, env } = fixture(t);
  const sentinel = deniedDependency(directory);
  policy(directory);
  execFileSync("npm", ["ci", "--offline", "--no-audit"], { cwd: directory, env, stdio: "pipe", timeout: 30_000 });
  assert.equal(existsSync(sentinel), false, "automatic dependency install hook executed");
  execFileSync("npm", ["dedupe", "--offline", "--no-audit"], { cwd: directory, env, stdio: "pipe", timeout: 30_000 });
  assert.equal(existsSync(sentinel), false, "dedupe activated the denied hook");
});

function nativeFixture(t: TestContext, metadata: Record<string, unknown> = {}) {
  const { directory, env } = fixture(t);
  policy(directory);
  const addon = join(directory, "node_modules", "isolated-vm");
  mkdirSync(addon, { recursive: true });
  writeFileSync(join(addon, "package.json"), JSON.stringify({
    name: "isolated-vm", version: "7.0.0", main: "index.cjs",
    scripts: { preinstall: "node -e \"require('node:fs').writeFileSync('preinstall-sentinel', 'executed')\"",
      install: installCommand,
      postinstall: "node -e \"require('node:fs').writeFileSync('postinstall-sentinel', 'executed')\"" },
    ...metadata
  }));
  writeFileSync(join(addon, "index.cjs"), "require('node:fs').writeFileSync(__dirname + '/loaded-sentinel', 'loaded'); exports.Isolate = class {};\n");
  const unrelated = join(directory, "node_modules", "denied-lifecycle");
  mkdirSync(unrelated);
  writeFileSync(join(unrelated, "package.json"), JSON.stringify({ name: "denied-lifecycle", version: "1.0.0",
    scripts: { install: "node -e \"require('node:fs').writeFileSync('unrelated-sentinel', 'executed')\"" } }));
  const bin = join(directory, "node_modules", ".bin");
  mkdirSync(bin);
  writeFileSync(join(bin, "node-gyp-build"), "#!/usr/bin/env node\nrequire('node:fs').writeFileSync('native-sentinel', 'executed');\n", { mode: 0o755 });
  mkdirSync(join(directory, "scripts"));
  const script = join(directory, "scripts", "setup-native.mjs");
  if (existsSync(join(root, "scripts", "setup-native.mjs"))) cpSync(join(root, "scripts", "setup-native.mjs"), script);
  return { directory, env, addon, script };
}

test("reviewed native setup explicitly activates only the addon install command and loads it", t => {
  const { directory, env, addon, script } = nativeFixture(t);
  const result = spawnSync(process.execPath, ["--no-node-snapshot", script], { cwd: directory, env, encoding: "utf8", timeout: 30_000 });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(existsSync(join(addon, "native-sentinel")), true, "selected install command did not run");
  assert.equal(existsSync(join(addon, "loaded-sentinel")), true, "addon was not loaded after setup");
  assert.equal(existsSync(join(addon, "preinstall-sentinel")), false, "explicit setup activated a preinstall hook");
  assert.equal(existsSync(join(addon, "postinstall-sentinel")), false, "explicit setup activated a postinstall hook");
  assert.equal(existsSync(join(directory, "node_modules", "denied-lifecycle", "unrelated-sentinel")), false,
    "native setup activated an unrelated dependency hook");
});

for (const [label, metadata] of [
  ["name", { name: "unreviewed-addon" }],
  ["version", { version: "7.0.1" }],
  ["install command", { scripts: { install: "node -e \"require('node:fs').writeFileSync('unreviewed-sentinel', 'executed')\"" } }]
] as const) {
  test(`native setup rejects an unreviewed addon ${label} before activation`, t => {
    const { directory, env, addon, script } = nativeFixture(t, metadata);
    const result = spawnSync(process.execPath, ["--no-node-snapshot", script], { cwd: directory, env, encoding: "utf8", timeout: 30_000 });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /reviewed isolated-vm 7\.0\.0/);
    for (const sentinel of ["native-sentinel", "loaded-sentinel", "unreviewed-sentinel"]) {
      assert.equal(existsSync(join(addon, sentinel)), false, `rejected addon created ${sentinel}`);
    }
  });
}

test("Buf resolves its locked optional binary and fails without it without invoking postinstall fallback", t => {
  const require = createRequire(import.meta.url);
  const wrapper = require.resolve("@bufbuild/buf/bin/buf");
  assert.equal(execFileSync(process.execPath, [wrapper, "--version"], { encoding: "utf8" }).trim(), "1.73.0");
  const { directory, env } = fixture(t);
  const target = join(directory, "node_modules", "@bufbuild", "buf");
  mkdirSync(target, { recursive: true });
  cpSync(dirname(dirname(wrapper)), target, { recursive: true });
  const result = spawnSync(process.execPath, [join(target, "bin", "buf"), "--version"], { cwd: directory, env, encoding: "utf8" });
  assert.notEqual(result.status, 0, "Buf must fail when its platform optional package is absent");
  assert.match(result.stderr, /ENOENT/);
  assert.equal(existsSync(join(target, "npm-install")), false, "Buf activated its secondary install fallback");
});
