/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { loadAllYaml } from "@kubernetes/client-node";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import {
  buildExecutionPod,
  unsafeAdmissionVariants
} from "../src/isolation/kubernetes-pod.ts";
import { runtimePolicyFor } from "../src/isolation/kubernetes-runtime-policy.ts";
import {
  conformingPodAdmission,
  reviewedResourceSettings,
  validInClusterEnvironment
} from "./kata-fixtures.ts";

type Manifest = {
  kind: string;
  metadata: { name: string; namespace?: string; labels?: Record<string, string> };
  rules?: Array<{
    apiGroups: string[];
    resources: string[];
    resourceNames?: string[];
    verbs: string[];
  }>;
  subjects?: Array<{ kind: string; name: string; namespace?: string }>;
  spec?: Record<string, any>;
  automountServiceAccountToken?: boolean;
};

const standardSource = readFileSync(join(
  process.cwd(),
  "examples",
  "kubernetes",
  "v1",
  "standard-in-cluster.yaml"
), "utf8");
const standard = loadAllYaml(standardSource) as Manifest[];
const localSource = readFileSync(join(
  process.cwd(),
  "examples",
  "kubernetes",
  "v1",
  "local-in-cluster.yaml"
), "utf8");
const local = loadAllYaml(localSource) as Manifest[];
const kataSource = readFileSync(join(
  process.cwd(),
  "examples",
  "kata-kubernetes",
  "v1",
  "06-admission-policy.yaml"
), "utf8");

test("standard in-cluster assets provide separate topology and least privilege", () => {
  const namespaces = standard.filter(value => value.kind === "Namespace");
  assert.deepEqual(namespaces.map(value => value.metadata.name), [
    "oci-js-standard-host",
    "oci-js-standard-execution"
  ]);
  assert.equal(namespaces[0]?.metadata.labels?.["pod-security.kubernetes.io/enforce"], "restricted");
  assert.equal(namespaces[1]?.metadata.labels?.["pod-security.kubernetes.io/enforce"], "restricted");
  const runner = standard.find(value => (
    value.kind === "ServiceAccount" && value.metadata.name === "oci-js-runner"
  ));
  assert.equal(runner?.automountServiceAccountToken, false);
  const binding = standard.find(value => (
    value.kind === "RoleBinding" && value.metadata.name === "oci-js-standard-executor"
  ));
  assert.deepEqual(plain(binding?.subjects), [{
    kind: "ServiceAccount",
    name: "oci-js-standard-host",
    namespace: "oci-js-standard-host"
  }]);
  assert.equal(binding?.metadata.namespace, "oci-js-standard-execution");
});

test("standard RBAC and admission omit RuntimeClass while Kata remains additive", () => {
  const clusterRoles = standard.filter(value => value.kind === "ClusterRole");
  assert.equal(JSON.stringify(clusterRoles).includes("runtimeclasses"), false);
  assert.deepEqual(plain(clusterRoles[0]?.rules), [{
    apiGroups: [""],
    resources: ["namespaces"],
    resourceNames: ["oci-js-standard-execution"],
    verbs: ["get"]
  }]);
  const executor = standard.find(value => (
    value.kind === "Role" && value.metadata.name === "oci-js-standard-executor"
  ))!;
  assert.equal(executor.rules?.every(rule => rule.resourceNames === undefined), true);
  const standardPolicy = standard.find(value => value.kind === "ValidatingAdmissionPolicy")!;
  const standardExpressions = JSON.stringify(standardPolicy.spec?.validations);
  assert.equal(standardExpressions.includes("!has(object.spec.runtimeClassName)"), true);
  assert.equal(standardExpressions.includes("kubernetes-profile'] == 'in-cluster"), true);
  assert.equal(
    standardExpressions.includes("!has(object.spec.hostNetwork) || object.spec.hostNetwork == false"),
    true
  );
  assert.equal(
    standardExpressions.includes(
      "!has(object.spec.containers[0].volumeMounts[0].readOnly) || object.spec.containers[0].volumeMounts[0].readOnly == false"
    ),
    true
  );
  assert.equal(kataSource.includes("runtimeClassName == 'kata-qemu-runtime-rs'"), true);
  assert.equal(kataSource.includes("kubernetes-profile'] == 'kata-in-cluster"), true);
  for (const constraint of [
    "quantity(object.spec.containers[0].resources.requests.cpu).compareTo(quantity('100m')) >= 0",
    "quantity(object.spec.containers[0].resources.requests.cpu).compareTo(quantity('4')) <= 0",
    "quantity(object.spec.containers[0].resources.requests.memory).compareTo(quantity('128Mi')) >= 0",
    "quantity(object.spec.containers[0].resources.requests.memory).compareTo(quantity('2Gi')) <= 0",
    "quantity(object.spec.containers[0].resources.requests['ephemeral-storage']).compareTo(quantity('16Mi')) >= 0",
    "quantity(object.spec.containers[0].resources.requests['ephemeral-storage']).compareTo(quantity('1Gi')) <= 0",
    "quantity(object.spec.volumes[0].emptyDir.sizeLimit).compareTo(quantity('1Mi')) >= 0",
    "quantity(object.spec.volumes[0].emptyDir.sizeLimit).compareTo(quantity('64Mi')) <= 0",
    "resources.requests.cpu == object.spec.containers[0].resources.limits.cpu"
  ]) {
    assert.equal(standardExpressions.includes(constraint), true, constraint);
  }
  assert.doesNotMatch(
    standardExpressions,
    /quantity\([^)]*\)\s*(?:<=|>=|<|>)\s*quantity\(/
  );
});

test("standard admission fixture accepts the conforming pod and rejects every named variant", () => {
  for (const settings of reviewedResourceSettings) {
    const config = parseKubernetesConfig({ ...validInClusterEnvironment(), ...settings });
    const conforming = buildExecutionPod(
      config,
      runtimePolicyFor(config),
      "oci-javascript-k8s-policy-range",
      "correlation",
      Date.now() + 30_000
    );
    assert.equal(conformingPodAdmission(conforming, "in-cluster"), true, JSON.stringify(settings));
  }
  const config = parseKubernetesConfig(validInClusterEnvironment());
  const pod = buildExecutionPod(
    config,
    runtimePolicyFor(config),
    "oci-javascript-k8s-policy-test",
    "correlation",
    Date.now() + 30_000
  );
  assert.equal(conformingPodAdmission(pod, "in-cluster"), true);
  for (const variant of unsafeAdmissionVariants(pod)) {
    assert.equal(conformingPodAdmission(variant.pod, "in-cluster"), false, variant.id);
  }
});

test("standard cleanup reconciler has no create or exec authority", () => {
  const cleanup = standard.find(value => (
    value.kind === "Role" && value.metadata.name === "oci-js-standard-cleanup"
  ))!;
  assert.deepEqual(plain(cleanup.rules), [{
    apiGroups: [""],
    resources: ["pods"],
    verbs: ["get", "list", "watch", "delete"]
  }]);
  assert.equal(JSON.stringify(cleanup).includes("pods/exec"), false);
  assert.equal(cleanup.rules?.some(rule => rule.verbs.includes("create")), false);
  const deployment = standard.find(value => (
    value.kind === "Deployment" && value.metadata.name === "oci-js-standard-reconciler"
  ))!;
  assert.equal(deployment.metadata.namespace, "oci-js-standard-host");
  assert.equal(
    deployment.spec?.template.spec.containers[0].command.at(-1),
    "/app/src/kubernetes-reconciler.ts"
  );
});

test("standard in-cluster assets include the hardened trusted host", () => {
  const host = standard.find(value => (
    value.kind === "Deployment" && value.metadata.name === "oci-js-standard-host"
  ))!;
  const hostPod = host.spec!.template.spec;
  const hostContainer = hostPod.containers[0];
  const hostEnv = Object.fromEntries(hostContainer.env.map((value: any) => [value.name, value]));

  assert.equal(host.metadata.namespace, "oci-js-standard-host");
  assert.equal(host.spec!.replicas, 1);
  assert.equal(host.spec!.strategy.type, "Recreate");
  assert.equal(hostPod.serviceAccountName, "oci-js-standard-host");
  assert.equal(hostPod.automountServiceAccountToken, true);
  assert.equal(hostContainer.stdin, true);
  assert.match(hostContainer.image, /oci-javascript-mcp-host@sha256:[a-f0-9]{64}$/);
  assert.equal(hostEnv.OCI_JAVASCRIPT_ISOLATION_PROVIDER.value, "kubernetes");
  assert.equal(hostEnv.OCI_JAVASCRIPT_KUBERNETES_PROFILE.value, "in-cluster");
  assert.match(hostEnv.OCI_JAVASCRIPT_KUBERNETES_IMAGE.value, /@sha256:[a-f0-9]{64}$/);
  assert.equal(
    hostEnv.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE.valueFrom.fieldRef.fieldPath,
    "metadata.namespace"
  );
  assert.equal(
    hostEnv.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME.valueFrom.fieldRef.fieldPath,
    "metadata.name"
  );
  assert.equal(
    hostEnv.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID.valueFrom.fieldRef.fieldPath,
    "metadata.uid"
  );
  assert.equal(hostEnv.OCI_CONFIG_FILE.value, "/var/run/oci/config");
  assert.equal(hostPod.volumes[0].secret.secretName, "oci-js-host-oci-config");
  assert.equal(hostPod.volumes[0].secret.defaultMode, 292);

  const policy = standard.find(value => value.kind === "ValidatingAdmissionPolicy")!;
  assert.equal(
    JSON.stringify(policy.spec?.validations).includes(hostEnv.OCI_JAVASCRIPT_KUBERNETES_IMAGE.value),
    true
  );
});

test("local in-cluster assets deploy one hardened stdio host and a minimal reconciler", () => {
  const host = local.find(value => (
    value.kind === "Deployment" && value.metadata.name === "oci-js-standard-host"
  ))!;
  const hostSpec = host.spec!;
  const hostPod = hostSpec.template.spec;
  const hostContainer = hostPod.containers[0];
  const hostEnv = Object.fromEntries(hostContainer.env.map((value: any) => [value.name, value]));

  assert.equal(host.metadata.namespace, "oci-js-standard-host");
  assert.equal(hostSpec.replicas, 1);
  assert.equal(hostSpec.strategy.type, "Recreate");
  assert.equal(hostPod.serviceAccountName, "oci-js-standard-host");
  assert.equal(hostPod.automountServiceAccountToken, true);
  assert.equal(hostContainer.stdin, true);
  assert.match(hostContainer.image, /oci-javascript-mcp-host@sha256:[a-f0-9]{64}$/);
  assert.equal(hostEnv.OCI_JAVASCRIPT_ISOLATION_PROVIDER.value, "kubernetes");
  assert.equal(hostEnv.OCI_JAVASCRIPT_KUBERNETES_PROFILE.value, "in-cluster");
  assert.match(hostEnv.OCI_JAVASCRIPT_KUBERNETES_IMAGE.value, /@sha256:[a-f0-9]{64}$/);
  assert.equal(
    hostEnv.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE.valueFrom.fieldRef.fieldPath,
    "metadata.namespace"
  );
  assert.equal(
    hostEnv.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME.valueFrom.fieldRef.fieldPath,
    "metadata.name"
  );
  assert.equal(
    hostEnv.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID.valueFrom.fieldRef.fieldPath,
    "metadata.uid"
  );
  assert.equal(hostEnv.OCI_CONFIG_FILE.value, "/var/run/oci/config");
  assert.equal(hostPod.volumes[0].secret.secretName, "oci-js-host-oci-config");
  assert.equal(hostPod.volumes[0].secret.defaultMode, 292);

  const policy = local.find(value => value.kind === "ValidatingAdmissionPolicy")!;
  assert.equal(
    JSON.stringify(policy.spec?.validations).includes(hostEnv.OCI_JAVASCRIPT_KUBERNETES_IMAGE.value),
    true
  );

  const reconciler = local.find(value => (
    value.kind === "Deployment" && value.metadata.name === "oci-js-standard-reconciler"
  ))!;
  const reconcilerPod = reconciler.spec!.template.spec;
  assert.equal(reconcilerPod.serviceAccountName, "oci-js-standard-reconciler");
  assert.match(
    reconcilerPod.containers[0].image,
    /oci-javascript-mcp-host@sha256:[a-f0-9]{64}$/
  );
  assert.deepEqual(
    reconcilerPod.containers[0].env.map((value: any) => value.name),
    [
      "OCI_JAVASCRIPT_KUBERNETES_PROFILE",
      "OCI_JAVASCRIPT_KUBERNETES_NAMESPACE",
      "OCI_JAVASCRIPT_KUBERNETES_RECONCILE_INTERVAL_SECONDS"
    ]
  );
  assert.equal(JSON.stringify(reconcilerPod).includes("OCI_CONFIG_FILE"), false);
});

function plain<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

test("standard manifests include bounded resource and default-deny network controls", () => {
  for (const kind of ["ResourceQuota", "LimitRange", "NetworkPolicy"]) {
    const values = standard.filter(value => value.kind === kind);
    assert.equal(values.length > 0, true);
    assert.equal(values.every(
      value => value.metadata.namespace === "oci-js-standard-execution"
    ), true);
  }
  assert.equal(standardSource.includes("ingress: []"), true);
  assert.equal(standardSource.includes("egress: []"), true);
  assert.equal(standardSource.includes("/Users/"), false);
  assert.equal(/password|private[_-]?key|bearer[_-]?token/i.test(standardSource), false);
});
