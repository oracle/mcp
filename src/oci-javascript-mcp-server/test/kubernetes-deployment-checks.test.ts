/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import type {
  V1LabelSelector, V1MatchResources, V1Node, V1RuntimeClass,
  V1ValidatingAdmissionPolicy, V1ValidatingAdmissionPolicyBinding
} from "@kubernetes/client-node";
import {
  inspectAdmission, inspectKataNodes, inspectKataRuntime,
  type AdmissionExpectation, type KataExpectation
} from "../src/kubernetes-deployment-checks.ts";

const admission: AdmissionExpectation = {
  policyName: "runner-guard", namespace: "runners",
  namespaceLabels: { "kubernetes.io/metadata.name": "runners", purpose: "execution", environment: "test" },
  operations: ["CREATE", "UPDATE"], resources: ["pods", "pods/ephemeralcontainers"]
};
const kata: KataExpectation = {
  handler: "kata-qemu", profile: "qemu-2026-11", executionPool: "execution", trustedHostPool: "trusted"
};
const poolKey = "oci.oracle.com.node-restriction.kubernetes.io/workload-pool";
const profileKey = "oci.oracle.com.node-restriction.kubernetes.io/kata-profile";
const taintKey = "oci.oracle.com/workload-pool";

function rules(): V1MatchResources {
  return { resourceRules: [{
    apiGroups: [""], apiVersions: ["v1"], operations: ["CREATE", "UPDATE"],
    resources: ["pods", "pods/ephemeralcontainers"], scope: "Namespaced"
  }] };
}

function policy(): V1ValidatingAdmissionPolicy {
  return {
    metadata: { name: "runner-guard" },
    spec: { failurePolicy: "Fail", matchConstraints: rules(), validations: [{ expression: "object.spec.hostNetwork == false" }] }
  };
}

function binding(): V1ValidatingAdmissionPolicyBinding {
  return {
    spec: {
      policyName: "runner-guard", validationActions: ["Deny"],
      matchResources: { namespaceSelector: { matchLabels: { "kubernetes.io/metadata.name": "runners" } } }
    }
  };
}

function runtime(): V1RuntimeClass {
  return {
    handler: "kata-qemu",
    scheduling: {
      nodeSelector: {
        "kubernetes.io/os": "linux", "kubernetes.io/arch": "amd64",
        "oci.oracle.com.node-restriction.kubernetes.io/workload-pool": "execution",
        "oci.oracle.com.node-restriction.kubernetes.io/kata-profile": "qemu-2026-11"
      },
      tolerations: [{ key: "oci.oracle.com/workload-pool", operator: "Equal", value: "execution", effect: "NoSchedule" }]
    }
  };
}

function nodes(): V1Node[] {
  return [
    {
      metadata: { name: "worker", labels: {
        "kubernetes.io/os": "linux", "kubernetes.io/arch": "amd64",
        "oci.oracle.com.node-restriction.kubernetes.io/workload-pool": "execution",
        "oci.oracle.com.node-restriction.kubernetes.io/kata-profile": "qemu-2026-11"
      } },
      spec: { taints: [{ key: "oci.oracle.com/workload-pool", value: "execution", effect: "NoSchedule" }] },
      status: {
        conditions: [{ type: "Ready", status: "True" }],
        nodeInfo: {
          architecture: "amd64", operatingSystem: "linux", bootID: "boot", containerRuntimeVersion: "containerd://2",
          kernelVersion: "6", kubeProxyVersion: "v1", kubeletVersion: "v1", machineID: "machine", osImage: "Linux", systemUUID: "uuid"
        }
      }
    },
    {
      metadata: { name: "host", labels: { "oci.oracle.com.node-restriction.kubernetes.io/workload-pool": "trusted" } },
      status: { conditions: [{ type: "Ready", status: "True" }] }
    }
  ];
}

test("admission accepts explicit fail-closed policy coverage and a denying binding", () => {
  assert.deepEqual(inspectAdmission(policy(), binding(), admission), []);
  const all = binding();
  delete all.spec!.matchResources;
  all.spec!.validationActions = ["Deny", "Audit"];
  assert.deepEqual(inspectAdmission(policy(), all, admission), []);
  const split = policy();
  split.spec!.matchConstraints!.resourceRules = [
    { apiGroups: [""], apiVersions: ["v1"], operations: ["CREATE"], resources: ["pods", "pods/ephemeralcontainers"], scope: "Namespaced" },
    { apiGroups: [""], apiVersions: ["v1"], operations: ["UPDATE"], resources: ["pods", "pods/ephemeralcontainers"], scope: "Namespaced" }
  ];
  assert.deepEqual(inspectAdmission(split, binding(), admission), []);
});

test("admission evaluates every supported namespace selector operator on policy and binding", () => {
  const selectors: V1LabelSelector[] = [
    {}, { matchLabels: { purpose: "execution" } },
    { matchExpressions: [{ key: "purpose", operator: "In", values: ["execution", "other"] }] },
    { matchExpressions: [{ key: "purpose", operator: "NotIn", values: ["other"] }] },
    { matchExpressions: [{ key: "absent", operator: "NotIn", values: ["other"] }] },
    { matchExpressions: [{ key: "purpose", operator: "Exists" }] },
    { matchExpressions: [{ key: "absent", operator: "DoesNotExist" }] }
  ];
  for (const selector of selectors) {
    const p = policy();
    const b = binding();
    p.spec!.matchConstraints!.namespaceSelector = selector;
    b.spec!.matchResources!.namespaceSelector = selector;
    assert.deepEqual(inspectAdmission(p, b, admission), [], JSON.stringify(selector));
  }
});

const invalidSelectors: Array<[string, V1LabelSelector]> = [
  ["different label", { matchLabels: { purpose: "trusted" } }],
  ["missing label", { matchLabels: { absent: "" } }],
  ["In mismatch", { matchExpressions: [{ key: "purpose", operator: "In", values: ["trusted"] }] }],
  ["In absent", { matchExpressions: [{ key: "absent", operator: "In", values: [""] }] }],
  ["NotIn mismatch", { matchExpressions: [{ key: "purpose", operator: "NotIn", values: ["execution"] }] }],
  ["Exists absent", { matchExpressions: [{ key: "absent", operator: "Exists" }] }],
  ["DoesNotExist present", { matchExpressions: [{ key: "purpose", operator: "DoesNotExist" }] }],
  ["unknown operator", { matchExpressions: [{ key: "purpose", operator: "GreaterThan", values: ["0"] }] }],
  ["In empty values", { matchExpressions: [{ key: "purpose", operator: "In", values: [] }] }],
  ["Exists with values", { matchExpressions: [{ key: "purpose", operator: "Exists", values: ["execution"] }] }],
  ["unknown selector", { unknown: "value" } as V1LabelSelector]
];
for (const [name, selector] of invalidSelectors) {
  test(`admission rejects ${name} namespace selectors on policy and binding`, () => {
    const p = policy();
    p.spec!.matchConstraints!.namespaceSelector = selector;
    assert(inspectAdmission(p, binding(), admission).length > 0);
    const b = binding();
    b.spec!.matchResources!.namespaceSelector = selector;
    assert(inspectAdmission(policy(), b, admission).length > 0);
  });
}

const weakenedPolicies: Array<[string, (p: V1ValidatingAdmissionPolicy) => void]> = [
  ["missing metadata", p => { delete p.metadata; }],
  ["wrong name", p => { p.metadata!.name = "different"; }],
  ["missing spec", p => { delete p.spec; }],
  ["ignored failures", p => { p.spec!.failurePolicy = "Ignore"; }],
  ["default failure policy", p => { delete p.spec!.failurePolicy; }],
  ["no validations", p => { p.spec!.validations = []; }],
  ["empty expression", p => { p.spec!.validations = [{ expression: "  " }]; }],
  ["parameterized policy", p => { p.spec!.paramKind = { apiVersion: "v1", kind: "ConfigMap" }; }],
  ["match condition bypass", p => { p.spec!.matchConditions = [{ name: "skip", expression: "false" }]; }],
  ["missing constraints", p => { delete p.spec!.matchConstraints; }],
  ["missing rules", p => { delete p.spec!.matchConstraints!.resourceRules; }],
  ["excluded rules", p => { p.spec!.matchConstraints!.excludeResourceRules = rules().resourceRules; }],
  ["object selector bypass", p => { p.spec!.matchConstraints!.objectSelector = { matchLabels: { enforce: "yes" } }; }],
  ["named resource bypass", p => { p.spec!.matchConstraints!.resourceRules![0].resourceNames = ["one-runner"]; }],
  ["missing operation", p => { p.spec!.matchConstraints!.resourceRules![0].operations = ["CREATE"]; }],
  ["missing resource", p => { p.spec!.matchConstraints!.resourceRules![0].resources = ["pods"]; }],
  ["wrong API group", p => { p.spec!.matchConstraints!.resourceRules![0].apiGroups = ["apps"]; }],
  ["wrong API version", p => { p.spec!.matchConstraints!.resourceRules![0].apiVersions = ["v2"]; }],
  ["cluster scope", p => { p.spec!.matchConstraints!.resourceRules![0].scope = "Cluster"; }],
  ["wildcard operation", p => { p.spec!.matchConstraints!.resourceRules![0].operations = ["*"]; }],
  ["typechecking warnings", p => { p.status = { typeChecking: { expressionWarnings: [{ fieldRef: "spec.validations[0]", warning: "private detail" }] } }; }]
];
for (const [name, weaken] of weakenedPolicies) {
  test(`admission rejects policy with ${name}`, () => {
    const p = policy();
    weaken(p);
    assert(inspectAdmission(p, binding(), admission).length > 0);
  });
}

const weakenedBindings: Array<[string, (b: V1ValidatingAdmissionPolicyBinding) => void]> = [
  ["missing spec", b => { Reflect.deleteProperty(b, "spec"); }],
  ["wrong policy", b => { b.spec!.policyName = "other"; }],
  ["only Audit", b => { b.spec!.validationActions = ["Audit"]; }],
  ["Warn", b => { b.spec!.validationActions = ["Deny", "Warn"]; }],
  ["unknown action", b => { b.spec!.validationActions = ["Deny", "Ignore"]; }],
  ["duplicate action", b => { b.spec!.validationActions = ["Deny", "Deny"]; }],
  ["parameter reference", b => { b.spec!.paramRef = { name: "params", parameterNotFoundAction: "Allow" }; }],
  ["resource exclusion", b => { b.spec!.matchResources!.excludeResourceRules = rules().resourceRules; }],
  ["object selector", b => { b.spec!.matchResources!.objectSelector = { matchExpressions: [{ key: "skip", operator: "DoesNotExist" }] }; }],
  ["partial resource coverage", b => { b.spec!.matchResources!.resourceRules = [{ ...rules().resourceRules![0], resources: ["pods"] }]; }],
  ["resource name filter", b => { b.spec!.matchResources!.resourceRules = [{ ...rules().resourceRules![0], resourceNames: ["one"] }]; }]
];
for (const [name, weaken] of weakenedBindings) {
  test(`admission rejects binding with ${name}`, () => {
    const b = binding();
    weaken(b);
    assert(inspectAdmission(policy(), b, admission).length > 0);
  });
}

test("admission permits explicit empty filters and complete binding rules", () => {
  const p = policy();
  p.spec!.matchConditions = [];
  p.spec!.matchConstraints!.excludeResourceRules = [];
  p.spec!.matchConstraints!.objectSelector = { matchLabels: {}, matchExpressions: [] };
  p.spec!.matchConstraints!.resourceRules![0].resourceNames = [];
  const b = binding();
  b.spec!.matchResources = rules();
  assert.deepEqual(inspectAdmission(p, b, admission), []);
});

test("deployment diagnostics do not expose names, labels, expressions or typechecking details", () => {
  const p = policy();
  p.metadata!.name = "SECRET_NAME";
  p.spec!.matchConstraints!.namespaceSelector = { matchLabels: { SECRET_LABEL: "SECRET_VALUE" } };
  p.status = { typeChecking: { expressionWarnings: [{ fieldRef: "SECRET_FIELD", warning: "SECRET_WARNING" }] } };
  const n = nodes();
  n[0].metadata!.name = "SECRET_NODE";
  n[0].metadata!.labels![profileKey] = "SECRET_PROFILE";
  assert(!JSON.stringify([...inspectAdmission(p, binding(), admission), ...inspectKataNodes(n, kata)]).includes("SECRET"));
});

test("Kata runtime accepts the exact handler, selector and execution toleration", () => {
  assert.deepEqual(inspectKataRuntime(runtime(), kata), []);
});

const weakenedRuntimes: Array<[string, (r: V1RuntimeClass) => void]> = [
  ["wrong handler", r => { r.handler = "runc"; }],
  ["missing scheduling", r => { delete r.scheduling; }],
  ["missing selector", r => { delete r.scheduling!.nodeSelector; }],
  ["missing protected profile", r => { delete r.scheduling!.nodeSelector![profileKey]; }],
  ["different profile", r => { r.scheduling!.nodeSelector![profileKey] = "other"; }],
  ["different pool", r => { r.scheduling!.nodeSelector![poolKey] = "trusted"; }],
  ["wrong OS", r => { r.scheduling!.nodeSelector!["kubernetes.io/os"] = "windows"; }],
  ["wrong architecture", r => { r.scheduling!.nodeSelector!["kubernetes.io/arch"] = "arm64"; }],
  ["extra selector", r => { r.scheduling!.nodeSelector!.extra = "value"; }],
  ["missing toleration", r => { delete r.scheduling!.tolerations; }],
  ["extra toleration", r => { r.scheduling!.tolerations!.push({ operator: "Exists" }); }],
  ["broad toleration", r => { r.scheduling!.tolerations![0].operator = "Exists"; }],
  ["wrong taint key", r => { r.scheduling!.tolerations![0].key = "other"; }],
  ["wrong taint value", r => { r.scheduling!.tolerations![0].value = "trusted"; }],
  ["wrong taint effect", r => { r.scheduling!.tolerations![0].effect = "NoExecute"; }],
  ["timed toleration", r => { r.scheduling!.tolerations![0].tolerationSeconds = 0; }]
];
for (const [name, weaken] of weakenedRuntimes) {
  test(`Kata runtime rejects ${name}`, () => {
    const r = runtime();
    weaken(r);
    assert(inspectKataRuntime(r, kata).length > 0);
  });
}

test("Kata nodes require one ready execution worker and separate trusted pool", () => {
  assert.deepEqual(inspectKataNodes(nodes(), kata), []);
  const mixed = nodes();
  const offline = structuredClone(mixed[0]);
  offline.spec!.unschedulable = true;
  offline.status!.conditions = [{ type: "Ready", status: "False" }];
  mixed.push(offline);
  assert.deepEqual(inspectKataNodes(mixed, kata), []);
  assert(inspectKataNodes(nodes(), { ...kata, trustedHostPool: "execution" }).length > 0);
});

const weakenedNodes: Array<[string, (n: V1Node[]) => void]> = [
  ["empty inventory", n => { n.length = 0; }],
  ["no execution pool", n => { n.shift(); }],
  ["no trusted pool", n => { n.pop(); }],
  ["missing metadata", n => { delete n[0].metadata; }],
  ["missing profile", n => { delete n[0].metadata!.labels![profileKey]; }],
  ["incorrect profile", n => { n[0].metadata!.labels![profileKey] = "qemu-other"; }],
  ["wrong OS label", n => { n[0].metadata!.labels!["kubernetes.io/os"] = "windows"; }],
  ["wrong architecture label", n => { n[0].metadata!.labels!["kubernetes.io/arch"] = "arm64"; }],
  ["wrong reported OS", n => { n[0].status!.nodeInfo!.operatingSystem = "windows"; }],
  ["wrong reported architecture", n => { n[0].status!.nodeInfo!.architecture = "arm64"; }],
  ["missing node info", n => { delete n[0].status!.nodeInfo; }],
  ["missing taint", n => { delete n[0].spec!.taints; }],
  ["wrong taint value", n => { n[0].spec!.taints![0].value = "trusted"; }],
  ["wrong taint effect", n => { n[0].spec!.taints![0].effect = "PreferNoSchedule"; }],
  ["unready execution pool", n => { n[0].status!.conditions = [{ type: "Ready", status: "False" }]; }],
  ["unknown readiness", n => { delete n[0].status!.conditions; }],
  ["unschedulable execution pool", n => { n[0].spec!.unschedulable = true; }],
  ["execution taint on trusted pool", n => { n[1].spec = { taints: [{ key: "oci.oracle.com/workload-pool", value: "execution", effect: "NoSchedule" }] }; }]
];
for (const [name, weaken] of weakenedNodes) {
  test(`Kata nodes reject ${name}`, () => {
    const n = nodes();
    weaken(n);
    assert(inspectKataNodes(n, kata).length > 0);
  });
}


test("admission rejects incomplete expectations and inconsistent namespace identity", () => {
  for (const change of [
    { policyName: "" }, { namespace: "" }, { operations: [] }, { resources: [] },
    { namespaceLabels: { "kubernetes.io/metadata.name": "different" } }
  ]) {
    const b = binding();
    delete b.spec.matchResources;
    assert(inspectAdmission(policy(), b, { ...admission, ...change }).length > 0);
  }
});

test("admission rejects unsupported resource match policies", () => {
  const p = policy();
  p.spec!.matchConstraints!.matchPolicy = "Unknown";
  assert(inspectAdmission(p, binding(), admission).length > 0);
  const b = binding();
  b.spec.matchResources!.matchPolicy = "Unknown";
  assert(inspectAdmission(policy(), b, admission).length > 0);
});

test("Kata checks every execution node even when a healthy worker exists", () => {
  const n = nodes();
  const weakened = structuredClone(n[0]);
  weakened.metadata!.labels![profileKey] = "different";
  n.push(weakened);
  assert(inspectKataNodes(n, kata).length > 0);
});


test("admission rejects malformed empty-looking object selectors", () => {
  for (const matchLabels of [null, "", 0, [], false]) {
    const selector = { matchLabels } as unknown as V1LabelSelector;
    const p = policy();
    p.spec!.matchConstraints!.objectSelector = selector;
    assert(inspectAdmission(p, binding(), admission).length > 0);
    const b = binding();
    b.spec.matchResources!.objectSelector = selector;
    assert(inspectAdmission(policy(), b, admission).length > 0);
  }
});

for (const [name, weaken] of [
  ["unready trusted pool", (node: V1Node) => { node.status!.conditions = [{ type: "Ready", status: "False" }]; }],
  ["unknown trusted readiness", (node: V1Node) => { delete node.status; }],
  ["cordoned trusted pool", (node: V1Node) => { node.spec = { unschedulable: true }; }]
] as const) {
  test(`Kata nodes reject ${name} but accept another Ready schedulable trusted host`, () => {
    const n = nodes();
    const healthy = structuredClone(n[1]);
    weaken(n[1]);
    assert(inspectKataNodes(n, kata).length > 0);
    n.push(healthy);
    assert.deepEqual(inspectKataNodes(n, kata), []);
  });
}

test("execution availability rejects an additional hard taint unless another eligible worker exists", () => {
  const n = nodes();
  const healthy = structuredClone(n[0]);
  n[0].spec!.taints!.push({ key: "maintenance", effect: "NoSchedule" });
  assert(inspectKataNodes(n, kata).length > 0);
  n.push(healthy);
  assert.deepEqual(inspectKataNodes(n, kata), []);
});

test("trusted-host availability rejects a hard taint unless another eligible host exists", () => {
  const n = nodes();
  const healthy = structuredClone(n[1]);
  n[1].spec = { taints: [{ key: "maintenance", effect: "NoExecute" }] };
  assert(inspectKataNodes(n, kata).length > 0);
  n.push(healthy);
  assert.deepEqual(inspectKataNodes(n, kata), []);
});

test("availability permits soft taints and the fixed default health NoExecute tolerations", () => {
  for (const taint of [
    { key: "maintenance", effect: "PreferNoSchedule" },
    { key: "node.kubernetes.io/not-ready", effect: "NoExecute" },
    { key: "node.kubernetes.io/unreachable", value: "any", effect: "NoExecute" }
  ]) {
    const n = nodes();
    n[0].spec!.taints!.push(taint);
    n[1].spec = { taints: [taint] };
    assert.deepEqual(inspectKataNodes(n, kata), []);
  }
});

test("pool and health tolerations do not tolerate different hard-taint effects", () => {
  for (const taint of [
    { key: "oci.oracle.com/workload-pool", value: "execution", effect: "NoExecute" },
    { key: "node.kubernetes.io/not-ready", effect: "NoSchedule" },
    { key: "node.kubernetes.io/unreachable", effect: "NoSchedule" }
  ]) {
    const n = nodes();
    n[0].spec!.taints!.push(taint);
    assert(inspectKataNodes(n, kata).length > 0);
  }
});
