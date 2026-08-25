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

type Manifest = {
  kind: string;
  metadata: { name: string; namespace?: string; labels?: Record<string, string> };
  rules?: Array<{ resources: string[]; verbs: string[] }>;
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
  const standardPolicy = standard.find(value => value.kind === "ValidatingAdmissionPolicy")!;
  const standardExpressions = JSON.stringify(standardPolicy.spec?.validations);
  assert.equal(standardExpressions.includes("!has(object.spec.runtimeClassName)"), true);
  assert.equal(standardExpressions.includes("kubernetes-profile'] == 'in-cluster"), true);
  assert.equal(kataSource.includes("runtimeClassName == 'kata-qemu-runtime-rs'"), true);
  assert.equal(kataSource.includes("kubernetes-profile'] == 'kata-in-cluster"), true);
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
  const deployment = standard.find(value => value.kind === "Deployment")!;
  assert.equal(deployment.metadata.namespace, "oci-js-standard-host");
  assert.equal(
    deployment.spec?.template.spec.containers[0].command.at(-1),
    "/app/src/kubernetes-reconciler.ts"
  );
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
