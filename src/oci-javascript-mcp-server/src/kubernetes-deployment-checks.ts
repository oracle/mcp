/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type {
  V1LabelSelector, V1MatchResources, V1NamedRuleWithOperations, V1Node,
  V1RuntimeClass, V1ValidatingAdmissionPolicy, V1ValidatingAdmissionPolicyBinding
} from "@kubernetes/client-node";

export type AdmissionExpectation = {
  policyName: string;
  namespace: string;
  namespaceLabels: Record<string, string>;
  operations: string[];
  resources: string[];
};

export type KataExpectation = {
  handler: string;
  profile: string;
  executionPool: string;
  trustedHostPool: string;
};

const POOL_LABEL = "oci.oracle.com.node-restriction.kubernetes.io/workload-pool";
const PROFILE_LABEL = "oci.oracle.com.node-restriction.kubernetes.io/kata-profile";
const POOL_TAINT = "oci.oracle.com/workload-pool";

// These inspect explicit configuration properties, not CEL semantics or policy revisions.
export function inspectAdmission(
  policy: V1ValidatingAdmissionPolicy,
  binding: V1ValidatingAdmissionPolicyBinding,
  expected: AdmissionExpectation
): string[] {
  const problems: string[] = [];
  if (!expected.policyName || !expected.namespace || !expected.operations.length || !expected.resources.length) {
    problems.push("Admission expectations must identify the policy, namespace, operations and resources");
  }
  const namespaceName = expected.namespaceLabels["kubernetes.io/metadata.name"];
  if (namespaceName !== undefined && namespaceName !== expected.namespace) {
    problems.push("Execution namespace labels disagree with the expected namespace name");
  }
  if (policy.metadata?.name !== expected.policyName) problems.push("Admission policy name differs from the expected policy");
  const spec = policy.spec;
  if (spec?.failurePolicy !== "Fail") problems.push("Admission policy must explicitly fail closed");
  if (!spec?.validations?.length || spec.validations.some(validation => !validation.expression?.trim())) {
    problems.push("Admission policy must have nonempty validation expressions");
  }
  if (spec?.paramKind !== undefined) problems.push("Admission policy parameters are unsupported");
  if (spec?.matchConditions?.length) problems.push("Admission policy match conditions can bypass validation");
  if (policy.status?.typeChecking?.expressionWarnings?.length) problems.push("Admission policy reports typechecking warnings");
  if (!spec?.matchConstraints) problems.push("Admission policy match constraints are required");
  else inspectMatchResources(spec.matchConstraints, expected, true, "Policy", problems);

  const bindingSpec = binding.spec;
  if (bindingSpec?.policyName !== expected.policyName) problems.push("Admission binding must reference the expected policy");
  const actions = bindingSpec?.validationActions ?? [];
  if (!actions.includes("Deny") || actions.some(action => action !== "Deny" && action !== "Audit")
    || new Set(actions).size !== actions.length) {
    problems.push("Admission binding must use Deny with only optional Audit");
  }
  if (bindingSpec?.paramRef !== undefined) problems.push("Admission binding parameter references are unsupported");
  if (bindingSpec?.matchResources) inspectMatchResources(bindingSpec.matchResources, expected, false, "Binding", problems);
  return problems;
}

function inspectMatchResources(
  match: V1MatchResources, expected: AdmissionExpectation, requireRules: boolean,
  owner: "Policy" | "Binding", problems: string[]
): void {
  if (!matchesNamespace(match.namespaceSelector, expected.namespaceLabels)) {
    problems.push(`${owner} namespace selector must match the execution namespace`);
  }
  if (match.objectSelector !== undefined && !emptySelector(match.objectSelector)) {
    problems.push(`${owner} object selectors can bypass validation`);
  }
  if (match.excludeResourceRules?.length) problems.push(`${owner} resource exclusions can bypass validation`);
  if (match.matchPolicy !== undefined && match.matchPolicy !== "Exact" && match.matchPolicy !== "Equivalent") {
    problems.push(`${owner} resource match policy is unsupported`);
  }
  const rules = match.resourceRules;
  if (!requireRules && !rules?.length) return;
  if (!rules?.length || rules.some(rule => !explicitRule(rule))) {
    problems.push(`${owner} requires explicit core v1 namespaced resource rules without name filters or wildcards`);
    return;
  }
  if (expected.operations.some(operation => expected.resources.some(resource => !rules.some(rule =>
    rule.operations!.includes(operation) && rule.resources!.includes(resource)
  )))) {
    problems.push(`${owner} resource rules do not cover all required operations and resources`);
  }
}

function explicitRule(rule: V1NamedRuleWithOperations): boolean {
  return rule.scope === "Namespaced"
    && !!rule.apiGroups?.includes("") && !!rule.apiVersions?.includes("v1")
    && !!rule.operations?.length && !!rule.resources?.length
    && !rule.resourceNames?.length
    && [rule.apiGroups, rule.apiVersions, rule.operations, rule.resources]
      .every(values => values.every(value => typeof value === "string" && !value.includes("*")));
}

function knownSelector(selector: V1LabelSelector): boolean {
  return selector !== null && typeof selector === "object" && !Array.isArray(selector)
    && Object.keys(selector).every(key => key === "matchLabels" || key === "matchExpressions");
}

function emptySelector(selector: V1LabelSelector): boolean {
  return knownSelector(selector)
    && (selector.matchLabels === undefined || selector.matchLabels !== null
      && typeof selector.matchLabels === "object" && !Array.isArray(selector.matchLabels)
      && Object.keys(selector.matchLabels).length === 0)
    && (selector.matchExpressions === undefined || Array.isArray(selector.matchExpressions) && selector.matchExpressions.length === 0);
}

function matchesNamespace(selector: V1LabelSelector | undefined, labels: Record<string, string>): boolean {
  if (selector === undefined) return true;
  if (!knownSelector(selector)) return false;
  if (selector.matchLabels !== undefined && (selector.matchLabels === null
    || typeof selector.matchLabels !== "object" || Array.isArray(selector.matchLabels))) return false;
  if (!Object.entries(selector.matchLabels ?? {}).every(([key, value]) =>
    typeof value === "string" && Object.hasOwn(labels, key) && labels[key] === value)) return false;
  if (selector.matchExpressions !== undefined && !Array.isArray(selector.matchExpressions)) return false;
  return (selector.matchExpressions ?? []).every(expression => {
    if (!expression || typeof expression.key !== "string" || !expression.key
      || Object.keys(expression).some(key => key !== "key" && key !== "operator" && key !== "values")) return false;
    const values = expression.values ?? [];
    if (!Array.isArray(values) || values.some(value => typeof value !== "string")) return false;
    const present = Object.hasOwn(labels, expression.key);
    switch (expression.operator) {
      case "In": return values.length > 0 && present && values.includes(labels[expression.key]);
      case "NotIn": return values.length > 0 && (!present || !values.includes(labels[expression.key]));
      case "Exists": return values.length === 0 && present;
      case "DoesNotExist": return values.length === 0 && !present;
      default: return false;
    }
  });
}

// Runtime overhead and hypervisor behavior require separate measured evidence.
export function inspectKataRuntime(runtime: V1RuntimeClass, expected: KataExpectation): string[] {
  const problems: string[] = [];
  if (runtime.handler !== expected.handler) problems.push("Kata RuntimeClass handler differs from the expected handler");
  const selector = runtime.scheduling?.nodeSelector;
  const required = {
    "kubernetes.io/os": "linux", "kubernetes.io/arch": "amd64",
    [POOL_LABEL]: expected.executionPool, [PROFILE_LABEL]: expected.profile
  };
  if (!selector || Object.keys(selector).length !== 4
    || !Object.entries(required).every(([key, value]) => Object.hasOwn(selector, key) && selector[key] === value)) {
    problems.push("Kata RuntimeClass must select exactly the protected execution pool and profile on linux amd64");
  }
  const tolerations = runtime.scheduling?.tolerations;
  const toleration = tolerations?.[0];
  if (tolerations?.length !== 1 || !toleration || toleration.key !== POOL_TAINT
    || toleration.operator !== "Equal" || toleration.value !== expected.executionPool
    || toleration.effect !== "NoSchedule" || toleration.tolerationSeconds !== undefined) {
    problems.push("Kata RuntimeClass must tolerate exactly the execution pool NoSchedule taint");
  }
  return problems;
}

// The caller supplies a complete bounded inventory. Labels assert configuration,
// not physical cloud-pool provenance or VM/QEMU attestation.
export function inspectKataNodes(nodes: V1Node[], expected: KataExpectation): string[] {
  const problems: string[] = [];
  if (!expected.executionPool || !expected.trustedHostPool || expected.executionPool === expected.trustedHostPool) {
    problems.push("Execution and trusted host pools must be nonempty and distinct");
  }
  const execution = nodes.filter(node => node.metadata?.labels?.[POOL_LABEL] === expected.executionPool);
  const trusted = nodes.filter(node => node.metadata?.labels?.[POOL_LABEL] === expected.trustedHostPool);
  if (!execution.length) problems.push("Execution node pool is empty");
  if (!trusted.length) problems.push("Trusted host node pool is empty");
  if (execution.some(node => node.metadata?.labels?.[PROFILE_LABEL] !== expected.profile)) {
    problems.push("Every execution node must declare the expected protected Kata profile");
  }
  if (execution.some(node => node.metadata?.labels?.["kubernetes.io/os"] !== "linux"
    || node.metadata?.labels?.["kubernetes.io/arch"] !== "amd64"
    || node.status?.nodeInfo?.operatingSystem !== "linux" || node.status?.nodeInfo?.architecture !== "amd64")) {
    problems.push("Every execution node must label and report linux amd64");
  }
  if (execution.some(node => !node.spec?.taints?.some(taint =>
    taint.key === POOL_TAINT && taint.value === expected.executionPool && taint.effect === "NoSchedule"))) {
    problems.push("Every execution node must carry the execution pool NoSchedule taint");
  }
  if (!execution.some(node => availableNode(node, expected.executionPool))) {
    problems.push("Execution node pool needs a Ready uncordoned node with compatible taints");
  }
  if (!trusted.some(node => availableNode(node))) {
    problems.push("Trusted host node pool needs a Ready uncordoned node with compatible taints");
  }
  if (trusted.some(node => node.spec?.taints?.some(taint => taint.key === POOL_TAINT && taint.value === expected.executionPool))) {
    problems.push("Trusted host nodes must not carry the execution pool taint");
  }
  return problems;
}


// Match the fixed admitted pod tolerations. Readiness, cordon and taint checks
// do not establish scheduler capacity or placement. Health tolerations expire.
function availableNode(node: V1Node, executionPool?: string): boolean {
  return node.spec?.unschedulable !== true
    && !!node.status?.conditions?.some(condition => condition.type === "Ready" && condition.status === "True")
    && (node.spec?.taints ?? []).every(taint =>
      taint.effect === "PreferNoSchedule"
      || taint.effect === "NoSchedule" && executionPool !== undefined
        && taint.key === POOL_TAINT && taint.value === executionPool
      || taint.effect === "NoExecute"
        && (taint.key === "node.kubernetes.io/not-ready" || taint.key === "node.kubernetes.io/unreachable"));
}
