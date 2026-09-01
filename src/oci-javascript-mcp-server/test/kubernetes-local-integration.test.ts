/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { AdmissionregistrationV1Api, KubeConfig } from "@kubernetes/client-node";
import { createKubeconfigKubernetesApi } from "../src/isolation/kubernetes-api.ts";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import { reconcileExpiredPods } from "../src/isolation/kubernetes-reconciler.ts";
import { runJavaScript } from "../src/sandbox.ts";

const enabled = process.env.OCI_JAVASCRIPT_RUN_LOCAL_KUBERNETES_TESTS === "true";
const admissionEvidenceEnabled = (
  process.env.OCI_JAVASCRIPT_RUN_REAL_KUBERNETES_ADMISSION_TESTS === "true"
);

test("opt-in local cluster exercises create/watch/exec/cancel/delete/reconcile", {
  skip: enabled ? false : (
    "set OCI_JAVASCRIPT_RUN_LOCAL_KUBERNETES_TESTS=true and the documented test variables"
  )
}, async () => {
  const image = requiredTestEnv("OCI_JAVASCRIPT_TEST_KUBERNETES_IMAGE");
  const environment: NodeJS.ProcessEnv = {
    OCI_JAVASCRIPT_ISOLATION_PROVIDER: "kubernetes",
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "local-development",
    OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG: requiredTestEnv(
      "OCI_JAVASCRIPT_TEST_KUBERNETES_KUBECONFIG"
    ),
    OCI_JAVASCRIPT_KUBERNETES_CONTEXT: requiredTestEnv(
      "OCI_JAVASCRIPT_TEST_KUBERNETES_CONTEXT"
    ),
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: requiredTestEnv(
      "OCI_JAVASCRIPT_TEST_KUBERNETES_NAMESPACE"
    ),
    OCI_JAVASCRIPT_KUBERNETES_IMAGE: image,
    OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT: (
      process.env.OCI_JAVASCRIPT_TEST_KUBERNETES_RUNNER_SERVICE_ACCOUNT ?? "default"
    ),
    ...(image.includes("@sha256:") ? {} : {
      OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE: "true"
    })
  };
  const config = parseKubernetesConfig(environment);
  assert.equal(config.profile, "local-development");
  const api = createKubeconfigKubernetesApi(config.kubeconfigPath, config.kubeconfigContext);
  const provider = new KubernetesIsolationProvider(config, api, () => undefined);
  await provider.preflight();
  try {
    assert.equal(provider.descriptor?.runtimePolicy, "standard");
    assert.equal(provider.descriptor?.externalEvidence.kataGuestKernelRequested, false);
    const success = await runJavaScript("40 + 2", {
      isolationProvider: provider,
      async hostRpc() { return null; }
    });
    assert.deepEqual({ result: success.result, error: success.error, exitCode: success.exitCode }, {
      result: 42,
      error: null,
      exitCode: 0
    });

    const controller = new AbortController();
    const cancelled = provider.run("while (true) {}", {
      deadlineMs: Date.now() + 10_000,
      signal: controller.signal,
      async hostRpc() { return null; },
      channelLimits: Object.freeze({
        maxFrameBytes: 2 * 1024 * 1024,
        maxIngressBytes: 32 * 1024 * 1024,
        maxAcceptedMessages: 128,
        maxLogBytes: 2 * 1024 * 1024,
        maxEgressBytes: 32 * 1024 * 1024,
        maxResultBytes: 1024 * 1024
      })
    });
    controller.abort();
    assert.equal((await cancelled.result as { timedOut: boolean }).timedOut, true);
    await cancelled.terminate();

    assert.deepEqual(
      await reconcileExpiredPods(api, config.namespace, config.profile),
      { deletedNames: [], failureCount: 0 }
    );
  } finally {
    provider.stopReconciliation();
  }
});

test("opt-in applied admission policies have no server-side CEL type warnings", {
  skip: admissionEvidenceEnabled ? false : (
    "set OCI_JAVASCRIPT_RUN_REAL_KUBERNETES_ADMISSION_TESTS=true with the documented kubeconfig inputs"
  )
}, async () => {
  const config = new KubeConfig();
  config.loadFromFile(requiredTestEnv("OCI_JAVASCRIPT_TEST_KUBERNETES_KUBECONFIG"));
  const context = requiredTestEnv("OCI_JAVASCRIPT_TEST_KUBERNETES_CONTEXT");
  if (config.getContextObject(context) === null) {
    throw new Error("configured Kubernetes context does not exist");
  }
  config.setCurrentContext(context);
  const admission = config.makeApiClient(AdmissionregistrationV1Api);
  for (const name of [
    "oci-js-standard-execution-pods-v1",
    "oci-js-kata-execution-pods-v1"
  ]) {
    const policy = await admission.readValidatingAdmissionPolicy({ name });
    assert.equal(policy.status?.observedGeneration, policy.metadata?.generation, name);
    assert.deepEqual(policy.status?.typeChecking?.expressionWarnings ?? [], [], name);
  }
});

function requiredTestEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required when local Kubernetes integration is enabled`);
  }
  return value;
}
