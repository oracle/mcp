/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { loadAllYaml } from "@kubernetes/client-node";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import {
  buildExecutionPod,
  runtimeAdmissionVariants,
  unsafeAdmissionVariants
} from "../src/isolation/kubernetes-pod.ts";
import { runtimePolicyFor } from "../src/isolation/kubernetes-runtime-policy.ts";
import {
  conformingPodAdmission,
  reviewedResourceSettings,
  validKataEnvironment
} from "./kata-fixtures.ts";

type Manifest = {
  apiVersion: string;
  kind: string;
  metadata: { name: string; namespace?: string; labels?: Record<string, string> };
  rules?: Array<{
    apiGroups: string[];
    resources: string[];
    resourceNames?: string[];
    verbs: string[];
  }>;
  subjects?: Array<{ kind: string; name: string; namespace?: string }>;
  roleRef?: { name: string };
  spec?: Record<string, any>;
  automountServiceAccountToken?: boolean;
};

const directory = join(process.cwd(), "examples", "kata-kubernetes", "v1");
const files = readdirSync(directory).filter(name => name.endsWith(".yaml")).sort();
const source = files.map(name => readFileSync(join(directory, name), "utf8")).join("\n---\n");
const manifests = loadAllYaml(source) as Manifest[];

test("versioned Kata assets are syntactically valid Kubernetes objects", () => {
  assert.equal(files.length, 9);
  assert.equal(manifests.length > files.length, true);
  for (const manifest of manifests) {
    assert.match(manifest.apiVersion, /^[a-z0-9./-]+$/i);
    assert.match(manifest.kind, /^[A-Z][A-Za-z]+$/);
    assert.match(manifest.metadata.name, /^[a-z0-9](?:[-a-z0-9]*[a-z0-9])?$/);
  }
  assert.equal(manifests.some(item => item.kind === "Service"), false);
  assert.equal(source.includes("/Users/"), false);
  assert.equal(/password|private[_-]?key|bearer[_-]?token/i.test(source), false);
});

test("trusted host and execution namespaces remain separate with restricted execution policy", () => {
  const namespaces = manifests.filter(item => item.kind === "Namespace");
  assert.deepEqual(namespaces.map(item => item.metadata.name), ["oci-js-host", "oci-js-execution"]);
  const execution = namespaces.find(item => item.metadata.name === "oci-js-execution")!;
  const host = namespaces.find(item => item.metadata.name === "oci-js-host")!;
  assert.equal(host.metadata.labels?.["pod-security.kubernetes.io/enforce"], "restricted");
  assert.equal(execution.metadata.labels?.["pod-security.kubernetes.io/enforce"], "restricted");
  assert.equal(execution.metadata.labels?.["oci.oracle.com/kubernetes-profile"], "kata-in-cluster");
  const runner = manifests.find(
    item => item.kind === "ServiceAccount" && item.metadata.name === "oci-js-runner"
  )!;
  assert.equal(runner.automountServiceAccountToken, false);
});

test("execution grants name only the cross-namespace host and cleanup identity stays delete-only", () => {
  const hostBinding = manifests.find(
    item => item.kind === "RoleBinding" && item.metadata.name === "oci-js-kata-executor"
  )!;
  assert.deepEqual(plain(hostBinding.subjects), [{
    kind: "ServiceAccount",
    name: "oci-js-host",
    namespace: "oci-js-host"
  }]);
  assert.equal(hostBinding.metadata.namespace, "oci-js-execution");

  const hostRole = manifests.find(
    item => item.kind === "Role" && item.metadata.name === "oci-js-kata-executor"
  )!;
  assert.equal(hostRole.rules?.some(rule => rule.resources.includes("pods/exec")), true);
  assert.equal(hostRole.rules?.some(rule => rule.verbs.includes("create")), true);

  const cleanupRole = manifests.find(
    item => item.kind === "Role" && item.metadata.name === "oci-js-kata-cleanup"
  )!;
  assert.deepEqual(plain(cleanupRole.rules), [{
    apiGroups: [""],
    resources: ["pods"],
    verbs: ["get", "list", "watch", "delete"]
  }]);
  assert.equal(JSON.stringify(cleanupRole).includes("pods/exec"), false);
  assert.equal(cleanupRole.rules?.some(rule => rule.verbs.includes("create")), false);

  const preflight = manifests.find(
    item => item.kind === "ClusterRole" && item.metadata.name === "oci-js-kata-preflight"
  )!;
  assert.deepEqual(plain(preflight.rules), [{
    apiGroups: [""],
    resources: ["namespaces"],
    resourceNames: ["oci-js-execution"],
    verbs: ["get"]
  }, {
    apiGroups: ["node.k8s.io"],
    resources: ["runtimeclasses"],
    resourceNames: ["kata-qemu-runtime-rs"],
    verbs: ["get"]
  }]);
  assert.equal(hostRole.rules?.every(rule => rule.resourceNames === undefined), true);
});

function plain<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

test("resource and default-deny network controls apply only to execution pods", () => {
  for (const kind of ["ResourceQuota", "LimitRange", "NetworkPolicy"]) {
    const values = manifests.filter(item => item.kind === kind);
    assert.equal(values.length > 0, true);
    assert.equal(values.every(item => item.metadata.namespace === "oci-js-execution"), true);
  }
  const policies = manifests.filter(item => item.kind === "NetworkPolicy");
  assert.deepEqual(policies.map(item => item.metadata.name).sort(), [
    "default-deny-egress", "default-deny-ingress"
  ]);
  assert.equal(source.includes("ingress: []"), true);
  assert.equal(source.includes("egress: []"), true);
});

test("fail-closed admission assets identify the conforming shape and every reviewed unsafe variant", () => {
  const policy = manifests.find(item => item.kind === "ValidatingAdmissionPolicy")!;
  const binding = manifests.find(item => item.kind === "ValidatingAdmissionPolicyBinding")!;
  assert.equal(policy.spec?.failurePolicy, "Fail");
  assert.deepEqual(binding.spec?.validationActions, ["Deny"]);
  const expressions = JSON.stringify(policy.spec?.validations);
  for (const requiredConstraint of [
    "request.userInfo.username",
    "ownerReferences",
    "runtimeClassName",
    "kubernetes-profile",
    "serviceAccountName",
    "automountServiceAccountToken",
    "command",
    "env",
    "hostNetwork",
    "volumes",
    "imagePullPolicy",
    "runAsGroup",
    "fsGroup",
    "capabilities.add",
    "sizeLimit",
    "readOnly",
    "allowPrivilegeEscalation",
    "@sha256"
  ]) {
    assert.equal(expressions.includes(requiredConstraint), true, requiredConstraint);
  }
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
    assert.equal(expressions.includes(constraint), true, constraint);
  }
  assert.doesNotMatch(expressions, /quantity\([^)]*\)\s*(?:<=|>=|<|>)\s*quantity\(/);

  for (const settings of reviewedResourceSettings) {
    const config = parseKubernetesConfig({ ...validKataEnvironment(), ...settings });
    const runtimePolicy = runtimePolicyFor(config);
    const conforming = buildExecutionPod(
      config,
      runtimePolicy,
      "oci-javascript-k8s-policy-range",
      "correlation",
      Date.now() + 30_000
    );
    assert.equal(
      conformingPodAdmission(conforming, "kata-in-cluster"),
      true,
      JSON.stringify(settings)
    );
  }
  const config = parseKubernetesConfig(validKataEnvironment());
  const runtimePolicy = runtimePolicyFor(config);
  const pod = buildExecutionPod(
    config,
    runtimePolicy,
    "oci-javascript-k8s-policy-test",
    "correlation",
    Date.now() + 30_000
  );
  assert.equal(conformingPodAdmission(pod, "kata-in-cluster"), true);
  for (const variant of [
    ...unsafeAdmissionVariants(pod),
    ...runtimeAdmissionVariants(pod, runtimePolicy)
  ]) {
    assert.equal(conformingPodAdmission(variant.pod, "kata-in-cluster"), false, variant.id);
  }
});

test("cleanup reconciler is outside the execution namespace and uses its distinct identity", () => {
  const deployment = manifests.find(
    item => item.kind === "Deployment" && item.metadata.name === "oci-js-kata-reconciler"
  )!;
  assert.equal(deployment.metadata.namespace, "oci-js-host");
  assert.equal(deployment.spec?.template.spec.serviceAccountName, "oci-js-kata-reconciler");
  assert.equal(
    deployment.spec?.template.spec.containers[0].command.at(-1),
    "/app/src/kubernetes-reconciler.ts"
  );
});

test("Kata assets deploy a hardened trusted host with an admission-aligned runner", () => {
  const host = manifests.find(
    item => item.kind === "Deployment" && item.metadata.name === "oci-js-kata-host"
  )!;
  const hostPod = host.spec!.template.spec;
  const hostContainer = hostPod.containers[0];
  const hostEnv = Object.fromEntries(hostContainer.env.map((value: any) => [value.name, value]));

  assert.equal(host.metadata.namespace, "oci-js-host");
  assert.equal(host.spec!.replicas, 1);
  assert.equal(host.spec!.strategy.type, "Recreate");
  assert.equal(hostPod.serviceAccountName, "oci-js-host");
  assert.equal(hostPod.automountServiceAccountToken, true);
  assert.equal(hostContainer.stdin, true);
  assert.match(hostContainer.image, /oci-javascript-mcp-host@sha256:[a-f0-9]{64}$/);
  assert.equal(hostEnv.OCI_JAVASCRIPT_ISOLATION_PROVIDER.value, "kubernetes");
  assert.equal(hostEnv.OCI_JAVASCRIPT_KUBERNETES_PROFILE.value, "kata-in-cluster");
  assert.equal(hostEnv.OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS.value, "kata-qemu-runtime-rs");
  assert.equal(hostEnv.OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER.value, "kata-qemu-runtime-rs");
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
  assert.equal(hostPod.volumes[0].secret.secretName, "oci-js-kata-oci-config");
  assert.equal(hostPod.volumes[0].secret.defaultMode, 292);

  const policy = manifests.find(item => item.kind === "ValidatingAdmissionPolicy")!;
  assert.equal(
    JSON.stringify(policy.spec?.validations).includes(hostEnv.OCI_JAVASCRIPT_KUBERNETES_IMAGE.value),
    true
  );

  const reconciler = manifests.find(
    item => item.kind === "Deployment" && item.metadata.name === "oci-js-kata-reconciler"
  )!;
  assert.equal(JSON.stringify(reconciler.spec!.template.spec).includes("OCI_CONFIG_FILE"), false);
  assert.equal(JSON.stringify(reconciler.spec!.template.spec).includes("oci-js-kata-oci-config"), false);
});
