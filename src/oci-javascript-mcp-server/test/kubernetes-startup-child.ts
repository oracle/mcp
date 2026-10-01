/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import { runJavaScript } from "../src/sandbox.ts";
import { validKataEnvironment } from "./kata-fixtures.ts";
import { StartupKubernetesApi } from "./kubernetes-startup-fixture.ts";

const api = new StartupKubernetesApi();
api.observeRunner = false;
const scenario = process.argv[2];
const controller = new AbortController();
if (scenario === "before-ready") api.beforeReady = "error";
if (scenario === "acquisition-cancel") {
  const startRunner = api.startRunner.bind(api);
  api.startRunner = (...args) => {
    controller.abort();
    return startRunner(...args);
  };
}
const provider = new KubernetesIsolationProvider(
  parseKubernetesConfig(validKataEnvironment()), api, () => undefined
);
await provider.preflight({ startReconciliation: false });
if (scenario === "acquisition-cancel") {
  const execution = provider.run("42", {
    deadlineMs: Date.now() + 2000,
    signal: controller.signal,
    hostRpc: async () => null
  });
  const result = await execution.result;
  assert.equal(result.error?.message, "sandbox run deadline exceeded");
  assert.equal(result.timedOut, true);
  await new Promise(resolve => setImmediate(resolve));
  await execution.terminate(Date.now() + 1000);
  assert.equal(api.deleted, true);
  console.log("sanitized outcome; finalization complete");
} else {
  const running = runJavaScript("42", {
    isolationProvider: provider,
    timeoutSeconds: 2,
    signal: controller.signal,
    hostRpc: async () => null
  });
  if (scenario === "pending-tunnel") {
    while (!api.resolveTunnel) await new Promise(resolve => setImmediate(resolve));
    api.failRunner("error");
    await new Promise(resolve => setImmediate(resolve));
    api.resolveTunnel();
  }
  const result = await running;
  assert.equal(result.error?.message, "isolation provider failed");
  assert.equal(result.timedOut, false);
  assert.equal(api.deleted, true);
  console.log("sanitized outcome; finalization complete");
}
