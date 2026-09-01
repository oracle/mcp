/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import type { KubernetesApi } from "../src/isolation/kubernetes-api.ts";
import {
  parseIsolationProviderName,
  parseKubernetesConfig,
  parseKubernetesReconcilerConfig
} from "../src/isolation/kubernetes-config.ts";
import { createIsolationProvider } from "../src/isolation/provider-factory.ts";
import {
  conformingPodAdmission,
  validInClusterEnvironment,
  validKataEnvironment,
  validLocalEnvironment
} from "./kata-fixtures.ts";

test("provider and profile selection is exact with only the unset Podman default", () => {
  assert.equal(parseIsolationProviderName({}), "podman");
  assert.equal(parseIsolationProviderName({ OCI_JAVASCRIPT_ISOLATION_PROVIDER: "podman" }), "podman");
  assert.equal(
    parseIsolationProviderName({ OCI_JAVASCRIPT_ISOLATION_PROVIDER: "kubernetes" }),
    "kubernetes"
  );
  for (const value of ["", "kata-kubernetes", "kata", "PODMAN", " podman", "podman "]) {
    assert.throws(
      () => parseIsolationProviderName({ OCI_JAVASCRIPT_ISOLATION_PROVIDER: value }),
      /must be/
    );
  }
  assert.throws(() => parseIsolationProviderName({
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "local-development"
  }), /requires/);
  assert.throws(() => parseIsolationProviderName({
    OCI_JAVASCRIPT_ISOLATION_PROVIDER: "podman",
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "in-cluster"
  }), /incompatible/);
});

test("all three Kubernetes profiles parse as closed configuration bundles", () => {
  const local = parseKubernetesConfig(validLocalEnvironment());
  assert.deepEqual({
    profile: local.profile,
    credentialMode: local.credentialMode,
    imagePullPolicy: local.imagePullPolicy,
    imageDigestPinned: local.imageDigestPinned,
    kubeconfigPath: local.profile === "local-development" ? local.kubeconfigPath : undefined,
    kubeconfigContext: local.profile === "local-development" ? local.kubeconfigContext : undefined
  }, {
    profile: "local-development",
    credentialMode: "explicit-kubeconfig",
    imagePullPolicy: "Never",
    imageDigestPinned: false,
    kubeconfigPath: "/tmp/oci-javascript-test-kubeconfig",
    kubeconfigContext: "oci-js-local"
  });

  const standard = parseKubernetesConfig(validInClusterEnvironment());
  assert.equal(standard.profile, "in-cluster");
  assert.equal(standard.credentialMode, "in-cluster");
  assert.equal(standard.imagePullPolicy, "IfNotPresent");
  assert.equal("runtimeClass" in standard, false);

  const kata = parseKubernetesConfig(validKataEnvironment());
  assert.equal(kata.profile, "kata-in-cluster");
  assert.equal(kata.credentialMode, "in-cluster");
  assert.equal(kata.imageDigestPinned, true);
  assert.equal(kata.profile === "kata-in-cluster" ? kata.runtimeClass : undefined, "kata-qemu-runtime-rs");
});

test("Kubernetes config enforces profile credentials, topology, images, and numeric bounds", () => {
  const missingProfile = validKataEnvironment();
  delete missingProfile.OCI_JAVASCRIPT_KUBERNETES_PROFILE;
  assert.throws(() => parseKubernetesConfig(missingProfile), /PROFILE.*required/);

  const unknownProfile = validKataEnvironment();
  unknownProfile.OCI_JAVASCRIPT_KUBERNETES_PROFILE = "auto";
  assert.throws(() => parseKubernetesConfig(unknownProfile), /must be/);

  const missingLocalPath = validLocalEnvironment();
  delete missingLocalPath.OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG;
  assert.throws(() => parseKubernetesConfig(missingLocalPath), /KUBECONFIG.*required/);
  const relativeLocalPath = validLocalEnvironment();
  relativeLocalPath.OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG = "relative/config";
  assert.throws(() => parseKubernetesConfig(relativeLocalPath), /absolute path/);

  const localWithHostIdentity = validLocalEnvironment();
  localWithHostIdentity.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE = "host";
  assert.throws(() => parseKubernetesConfig(localWithHostIdentity), /incompatible/);

  const standardWithKubeconfig = validInClusterEnvironment();
  standardWithKubeconfig.OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG = "/tmp/config";
  assert.throws(() => parseKubernetesConfig(standardWithKubeconfig), /incompatible/);

  const standardWithKata = validInClusterEnvironment();
  standardWithKata.OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS = "kata";
  assert.throws(() => parseKubernetesConfig(standardWithKata), /incompatible/);

  const mutableInCluster = validInClusterEnvironment();
  mutableInCluster.OCI_JAVASCRIPT_KUBERNETES_IMAGE = "registry.example/runner:latest";
  assert.throws(() => parseKubernetesConfig(mutableInCluster), /immutable/);

  const localWithoutOptIn = validLocalEnvironment();
  delete localWithoutOptIn.OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE;
  assert.throws(() => parseKubernetesConfig(localWithoutOptIn), /explicitly allowed/);

  const unsafeLocalImage = validLocalEnvironment();
  unsafeLocalImage.OCI_JAVASCRIPT_KUBERNETES_IMAGE = "Runner Latest";
  assert.throws(() => parseKubernetesConfig(unsafeLocalImage), /explicitly allowed/);

  const sameNamespace = validInClusterEnvironment();
  sameNamespace.OCI_JAVASCRIPT_KUBERNETES_NAMESPACE = "oci-js-host";
  assert.throws(() => parseKubernetesConfig(sameNamespace), /must be different/);

  const invalidNumber = validKataEnvironment();
  invalidNumber.OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS = "61";
  assert.throws(() => parseKubernetesConfig(invalidNumber), /integer/);
});

test("cleanup-only config is exact-profile and in-cluster only", () => {
  assert.deepEqual(parseKubernetesReconcilerConfig({
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "in-cluster",
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: "oci-js-execution"
  }), {
    profile: "in-cluster",
    namespace: "oci-js-execution",
    reconcileIntervalMs: 30_000
  });
  assert.throws(() => parseKubernetesReconcilerConfig({
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "local-development",
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: "local"
  }), /only in-cluster/);
});

test("provider factory binds explicit kubeconfig or in-cluster credentials with no fallback", async () => {
  let podmanOptions: unknown;
  const podman = { run() { throw new Error("unused"); } };
  assert.equal(await createIsolationProvider({
    OCI_JAVASCRIPT_PODMAN_CLI: "podman-test",
    OCI_JAVASCRIPT_PODMAN_IMAGE: "runner:test"
  }, {
    createPodman(options) {
      podmanOptions = options;
      return podman;
    }
  }), podman);
  assert.deepEqual(podmanOptions, { cliPath: "podman-test", image: "runner:test" });

  const localApi = preflightApi("local");
  let localConnection: unknown;
  await createIsolationProvider(validLocalEnvironment(), {
    createKubeconfigApi(config) {
      localConnection = [config.kubeconfigPath, config.kubeconfigContext];
      return localApi;
    },
    createInClusterApi() { throw new Error("must not load in-cluster credentials"); },
    kubernetesDiagnostics: () => undefined,
    startReconciliation: false
  });
  assert.deepEqual(localConnection, [
    "/tmp/oci-javascript-test-kubeconfig",
    "oci-js-local"
  ]);

  let inClusterLoads = 0;
  const standardApi = preflightApi("standard");
  await createIsolationProvider(validInClusterEnvironment(), {
    createInClusterApi() {
      inClusterLoads += 1;
      return standardApi;
    },
    createKubeconfigApi() { throw new Error("must not load kubeconfig credentials"); },
    kubernetesDiagnostics: () => undefined,
    startReconciliation: false
  });
  assert.equal(inClusterLoads, 1);

  const failing = preflightApi("kata");
  failing.readNamespace = async () => { throw new Error("raw cluster endpoint"); };
  await assert.rejects(createIsolationProvider(validKataEnvironment(), {
    kubernetesApi: failing,
    kubernetesDiagnostics: () => undefined,
    startReconciliation: false,
    createPodman() { throw new Error("must not fall back"); }
  }), /preflight failed/);
});

function preflightApi(runtime: "local" | "standard" | "kata"): KubernetesApi {
  return {
    async readNamespace() {},
    async readRuntimeClass() { return { handler: "kata-qemu-runtime-rs" }; },
    async selfCan() { return true; },
    async dryRunCreatePod(_namespace, pod) {
      const profile = runtime === "local"
        ? "local-development"
        : runtime === "kata" ? "kata-in-cluster" : "in-cluster";
      return conformingPodAdmission(pod, profile);
    },
    async createPod() {},
    async waitForPodRunning() {},
    async openExecChannel() { throw new Error("unused"); },
    async deletePod() {},
    async podExists() { return false; },
    async waitForPodDeleted() { return true; },
    async listManagedPods() { return []; }
  };
}
