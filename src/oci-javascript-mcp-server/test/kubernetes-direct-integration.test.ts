/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import { createGrpcTlsBootstrap } from "../src/grpc-tls-host.ts";
import { createInClusterKubernetesApi } from "../src/isolation/kubernetes-api.ts";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import { buildExecutionPod, EXPIRY_ANNOTATION } from "../src/isolation/kubernetes-pod.ts";
import { buildExecutionSecret } from "../src/isolation/kubernetes-secret.ts";
import { reconcileExpiredExecutions } from "../src/isolation/kubernetes-reconciler.ts";
import { runtimePolicyFor } from "../src/isolation/kubernetes-runtime-policy.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import { runJavaScript } from "../src/sandbox.ts";

const enabled = process.env.OCI_JAVASCRIPT_RUN_DIRECT_KUBERNETES_TESTS === "true";
const gate = { skip: enabled ? false : "run inside a configured trusted host with OCI_JAVASCRIPT_RUN_DIRECT_KUBERNETES_TESTS=true" };

async function harness() {
  const config = parseKubernetesConfig(process.env);
  assert.notEqual(config.profile, "local-development");
  const api = createInClusterKubernetesApi();
  const names: string[] = [];
  const secrets: string[] = [];
  const createPod = api.createPod.bind(api);
  const createSecret = api.createSecret.bind(api);
  api.createPod = async (...args) => { names.push(args[1].metadata!.name!); return createPod(...args); };
  api.createSecret = async (...args) => { secrets.push(args[1].metadata!.name!); return createSecret(...args); };
  api.startRunner = async () => assert.fail("direct execution attempted exec");
  api.openTunnel = async () => assert.fail("direct execution attempted port-forward");
  const provider = new KubernetesIsolationProvider(config, api, () => undefined);
  await provider.preflight({ startReconciliation: false });
  return { config, api, names, secrets, provider };
}

test("opt-in direct in-cluster execution cleans up its pod and TLS Secret", gate, async () => {
  const { config, api, names, secrets, provider } = await harness();
  const result = await runJavaScript("40 + 2", { isolationProvider: provider, timeoutSeconds: 120, hostRpc: async () => null });
  assert.equal(result.result, 42);
  assert.equal(result.error, null);
  assert.equal(names.length, 1);
  assert.equal(secrets.length, 1);
  for (const name of names) assert.equal(await api.podExists(config.namespace, name), false);
  for (const name of secrets) assert.equal(await api.waitForSecretDeleted(config.namespace, name, Date.now() + 1000), true);
});

test("opt-in direct cancellation cleans up both attempted execution resources", gate, async () => {
  const { config, api, names, secrets, provider } = await harness();
  const controller = new AbortController();
  const execution = provider.run("while (true) {}", {
    deadlineMs: Date.now() + 120_000, signal: controller.signal, hostRpc: async () => null
  });
  try {
    controller.abort();
    assert.equal((await execution.result).timedOut, true);
  } finally { await execution.terminate(); }
  for (const name of names) assert.equal(await api.podExists(config.namespace, name), false);
  for (const name of secrets) assert.equal(await api.waitForSecretDeleted(config.namespace, name, Date.now() + 1000), true);
});

test("opt-in expired orphan TLS Secret is reconciled without a pod", gate, async () => {
  const { config, api } = await harness();
  const pod = buildExecutionPod(config, runtimePolicyFor(config), `oci-javascript-k8s-${randomUUID()}`,
    randomUUID(), Date.now() + 30_000);
  const secret = buildExecutionSecret(pod, createGrpcTlsBootstrap().runner);
  secret.metadata!.annotations![EXPIRY_ANNOTATION] = new Date(Date.now() - 1000).toISOString();
  const name = secret.metadata!.name!;
  try {
    await api.createSecret(config.namespace, secret, Date.now() + 10_000, new AbortController().signal);
    const summary = await reconcileExpiredExecutions(api, config.namespace, config.profile);
    assert.equal(summary.failureCount, 0);
    assert(summary.deletedSecretNames.includes(name));
    assert.equal(await api.waitForSecretDeleted(config.namespace, name, Date.now() + 1000), true);
  } finally { await api.deleteSecret(config.namespace, name); }
});
