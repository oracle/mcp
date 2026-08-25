/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import type {
  KubernetesApi,
  KubernetesPod,
  ResourceAttributes
} from "../src/isolation/kubernetes-api.ts";
import { parseKubernetesConfig, type KubernetesProfile } from "../src/isolation/kubernetes-config.ts";
import type { KubernetesDiagnosticEvent } from "../src/isolation/kubernetes-diagnostics.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import {
  EXPIRY_ANNOTATION,
  MANAGED_BY_LABEL,
  PROFILE_LABEL,
  PROVIDER_LABEL
} from "../src/isolation/kubernetes-pod.ts";
import { reconcileExpiredPods } from "../src/isolation/kubernetes-reconciler.ts";
import {
  validInClusterEnvironment,
  validLocalEnvironment
} from "./kata-fixtures.ts";

test("local development reports optional admission gaps without claiming Kata evidence", async () => {
  const api = new ProfileApi(() => true);
  const events: KubernetesDiagnosticEvent[] = [];
  const provider = new KubernetesIsolationProvider(
    parseKubernetesConfig(validLocalEnvironment()),
    api,
    event => events.push(event)
  );
  await provider.preflight({ startReconciliation: false });
  assert.equal(provider.descriptor?.profile, "local-development");
  assert.equal(provider.descriptor?.credentialMode, "explicit-kubeconfig");
  assert.equal(provider.descriptor?.assurance, "development-only-container");
  assert.equal(provider.descriptor?.admissionPreflight, "unverified");
  assert.equal(provider.descriptor?.runtimePolicy, "standard");
  assert.equal(provider.descriptor?.externalEvidence.kataGuestKernelRequested, false);
  assert.equal(provider.descriptor?.externalEvidence.kataGuestKernelVerified, false);
  assert.equal(api.runtimeClassReads, 0);
  assert.equal(api.permissions.length, 8);
  assert.equal(JSON.stringify(events).includes("kubeconfig"), false);
});

test("standard in-cluster requires base admission and omits RuntimeClass", async () => {
  const api = new ProfileApi(safeStandardPod);
  const provider = new KubernetesIsolationProvider(
    parseKubernetesConfig(validInClusterEnvironment()),
    api,
    () => undefined
  );
  await provider.preflight({ startReconciliation: false });
  assert.equal(provider.descriptor?.profile, "in-cluster");
  assert.equal(provider.descriptor?.credentialMode, "in-cluster");
  assert.equal(provider.descriptor?.assurance, "in-cluster-container");
  assert.equal(provider.descriptor?.admissionPreflight, "enforced");
  assert.equal(provider.descriptor?.runtimeClass, undefined);
  assert.equal(api.runtimeClassReads, 0);
  assert.equal(api.dryRunPods.every(pod => pod.spec?.runtimeClassName === undefined), true);

  const unsafeAccepted = new ProfileApi(() => true);
  await assert.rejects(new KubernetesIsolationProvider(
    parseKubernetesConfig(validInClusterEnvironment()),
    unsafeAccepted,
    () => undefined
  ).preflight({ startReconciliation: false }), /admission/);
});

test("every shared lifecycle permission is fail-closed for in-cluster profiles", async () => {
  const probe = new ProfileApi(safeStandardPod);
  const successful = new KubernetesIsolationProvider(
    parseKubernetesConfig(validInClusterEnvironment()),
    probe,
    () => undefined
  );
  await successful.preflight({ startReconciliation: false });
  for (const missing of probe.permissions) {
    const api = new ProfileApi(safeStandardPod);
    api.permission = value => !samePermission(value, missing);
    await assert.rejects(new KubernetesIsolationProvider(
      parseKubernetesConfig(validInClusterEnvironment()),
      api,
      () => undefined
    ).preflight({ startReconciliation: false }), /authorization/);
  }
});

test("reconciliation adopts only the exact Kubernetes profile and namespace", async () => {
  const now = Date.now();
  const api = new ProfileApi(safeStandardPod);
  api.pods = [
    managedPod("local-expired", "local-development", "execution", now - 1),
    managedPod("standard-expired", "in-cluster", "execution", now - 1),
    managedPod("kata-expired", "kata-in-cluster", "execution", now - 1),
    managedPod("wrong-namespace", "in-cluster", "other", now - 1),
    managedPod("standard-fresh", "in-cluster", "execution", now + 60_000)
  ];
  assert.deepEqual(
    await reconcileExpiredPods(api, "execution", "in-cluster", now),
    ["standard-expired"]
  );
  assert.deepEqual(api.listRequests, [{ namespace: "execution", profile: "in-cluster" }]);
  assert.deepEqual(api.deleted, ["standard-expired"]);
});

class ProfileApi implements KubernetesApi {
  readonly admission: (pod: KubernetesPod) => boolean;
  runtimeClassReads = 0;
  permissions: ResourceAttributes[] = [];
  permission: (attributes: ResourceAttributes) => boolean = () => true;
  dryRunPods: KubernetesPod[] = [];
  pods: KubernetesPod[] = [];
  deleted: string[] = [];
  listRequests: Array<{ namespace: string; profile: KubernetesProfile }> = [];

  constructor(admission: (pod: KubernetesPod) => boolean) {
    this.admission = admission;
  }

  async readNamespace() {}
  async readRuntimeClass() {
    this.runtimeClassReads += 1;
    return { handler: "kata-qemu-runtime-rs" };
  }
  async selfCan(attributes: ResourceAttributes) {
    this.permissions.push(attributes);
    return this.permission(attributes);
  }
  async dryRunCreatePod(_namespace: string, pod: KubernetesPod) {
    this.dryRunPods.push(structuredClone(pod));
    return this.admission(pod);
  }
  async createPod() {}
  async waitForPodRunning() {}
  async openExecChannel(): Promise<never> { throw new Error("unused"); }
  async deletePod(_namespace: string, name: string) { this.deleted.push(name); }
  async podExists() { return false; }
  async waitForPodDeleted() { return true; }
  async listManagedPods(namespace: string, profile: KubernetesProfile) {
    this.listRequests.push({ namespace, profile });
    return this.pods.map(pod => structuredClone(pod));
  }
}

function safeStandardPod(pod: KubernetesPod): boolean {
  const container = pod.spec?.containers[0];
  return container?.image?.includes("@sha256:") === true
    && pod.spec?.runtimeClassName === undefined
    && pod.spec?.serviceAccountName === "oci-js-runner"
    && pod.spec?.automountServiceAccountToken === false
    && pod.spec?.hostNetwork === false
    && pod.spec?.volumes?.length === 1
    && container.env === undefined
    && container.command?.[0] === "node"
    && container.securityContext?.allowPrivilegeEscalation === false;
}

function samePermission(left: ResourceAttributes, right: ResourceAttributes): boolean {
  return left.group === right.group
    && left.namespace === right.namespace
    && left.resource === right.resource
    && left.subresource === right.subresource
    && left.verb === right.verb;
}

function managedPod(
  name: string,
  profile: KubernetesProfile,
  namespace: string,
  expiryMs: number
): KubernetesPod {
  return {
    metadata: {
      name,
      namespace,
      labels: {
        [MANAGED_BY_LABEL]: "oci-javascript-mcp",
        [PROVIDER_LABEL]: "kubernetes",
        [PROFILE_LABEL]: profile
      },
      annotations: { [EXPIRY_ANNOTATION]: new Date(expiryMs).toISOString() }
    }
  };
}
