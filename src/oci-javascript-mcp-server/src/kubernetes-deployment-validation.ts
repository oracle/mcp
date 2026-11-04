/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { randomUUID } from "node:crypto";
import { resolve } from "node:path";
import { parseArgs } from "node:util";
import {
  AuthenticationV1Api,
  AdmissionregistrationV1Api,
  AuthorizationV1Api,
  CoreV1Api,
  KubeConfig,
  NodeV1Api,
  Observable,
  type ConfigurationOptions,
  type RequestContext,
  type ResponseContext,
  type V1Namespace, type V1RuntimeClass, type V1Node,
  type V1ValidatingAdmissionPolicy, type V1ValidatingAdmissionPolicyBinding
} from "@kubernetes/client-node";
import { requiredExecutionPermissions, type KubernetesPod, type ResourceAttributes } from "./isolation/kubernetes-api.ts";
import { parseKubernetesConfig, type KubernetesConfig } from "./isolation/kubernetes-config.ts";
import { buildExecutionPod, runtimeAdmissionVariants, unsafeAdmissionVariants } from "./isolation/kubernetes-pod.ts";
import { runtimePolicyFor } from "./isolation/kubernetes-runtime-policy.ts";
import { inspectAdmission, inspectKataRuntime, inspectKataNodes } from "./kubernetes-deployment-checks.ts";

export type ValidationOptions = {
  config: KubernetesConfig;
  kubeconfigPath: string;
  context: string;
  inspectionContext?: string;
  admissionPolicy: string;
  admissionBinding: string;
  hostPlacementPolicy: string;
  hostPlacementBinding: string;
  kataProfile: string;
  executionPool: string;
  trustedHostPool: string;
  expectedIdentity?: string;
  impersonate: boolean;
  timeoutMs: number;
  json: boolean;
  probeMetadata: "synthetic-host-identity" | "configured-host-identity" | "local-development";
};

export type ValidationIdentity = { username: string; groups: string[] };
export type AdmissionProbeResult =
  | { outcome: "accepted" }
  | { outcome: "rejected"; statusCode: 400 | 403 | 422; reason: "BadRequest" | "Forbidden" | "Invalid" };

export interface DeploymentValidationApi {
  identity(signal: AbortSignal): Promise<ValidationIdentity>;
  readNamespace(name: string, signal: AbortSignal): Promise<V1Namespace>;
  readRuntimeClass(name: string, signal: AbortSignal): Promise<V1RuntimeClass>;
  inspection?: DeploymentInspectionApi;
  selfCan(permission: ResourceAttributes, signal: AbortSignal): Promise<boolean>;
  dryRunCreatePod(namespace: string, pod: KubernetesPod, signal: AbortSignal): Promise<AdmissionProbeResult>;
}

export interface DeploymentInspectionApi {
  identity(signal: AbortSignal): Promise<ValidationIdentity>;
  readNamespace(name: string, signal: AbortSignal): Promise<V1Namespace>;
  readPolicy(name: string, signal: AbortSignal): Promise<V1ValidatingAdmissionPolicy>;
  readBinding(name: string, signal: AbortSignal): Promise<V1ValidatingAdmissionPolicyBinding>;
  listNodes(signal: AbortSignal): Promise<V1Node[]>;
  dryRunCreatePod(namespace: string, pod: KubernetesPod, signal: AbortSignal): Promise<AdmissionProbeResult>;
}

export type ValidationCheck = {
  id: string;
  outcome: "passed" | "failed";
  detail: string;
  statusCode?: number;
  reason?: "BadRequest" | "Forbidden" | "Invalid";
};

export type ValidationReport = {
  startedAt: string;
  profile: KubernetesConfig["profile"];
  context: string;
  identity: ValidationIdentity | null;
  inspectionIdentity?: ValidationIdentity;
  inspectedResources?: Array<{ kind: string; name: string; uid?: string; resourceVersion?: string; generation?: number }>;
  probeMetadata: ValidationOptions["probeMetadata"];
  dryRunOnly: true;
  passed: boolean;
  checks: ValidationCheck[];
};

const HELP = `Validate Kubernetes deployment identity, permissions, RuntimeClass and admission.

node --experimental-strip-types src/kubernetes-deployment-validation.ts \\
  --kubeconfig PATH --context NAME [--host-service-account NAME] [--impersonate]

Set the existing OCI_JAVASCRIPT_KUBERNETES_* variables for the target profile,
execution namespace, runner image, runner service account and resource settings.
In-cluster profiles also require the trusted-host namespace and host service
account; Kata additionally requires its RuntimeClass and expected handler.

--kubeconfig PATH             Explicit kubeconfig; no default discovery
--context NAME                Exact context in that file
--inspection-context NAME     Deployment inspection context (required in-cluster)
--admission-policy NAME       Execution policy name (default: profile example name)
--admission-binding NAME      Execution binding name (default: policy name)
--host-placement-policy NAME  Kata trusted-host placement policy name
--host-placement-binding NAME Kata trusted-host placement binding name
--kata-profile NAME           Expected protected Kata node-profile label (default kata-qemu-runtime-rs-v1)
--execution-pool NAME         Expected Kata execution pool (default kata-execution)
--trusted-host-pool NAME      Expected Kata trusted pool (default trusted-host)
--host-service-account NAME   Expected host identity for in-cluster profiles
--impersonate                 Act as that service account (requires permission)
--timeout-seconds N           Whole validation deadline, 1–300 (default 60)
--json                        Emit a JSON report
--help                        Show this help

Exit 0: all checks passed. Exit 1: a check, configuration or API request failed.
No execution pods are persisted, executed or deleted. Rejections describe only
the observed API outcome; this command does not certify runtime isolation.
Use token or client-certificate credentials. Kubeconfig exec and auth-provider
helpers are unsupported because the SDK cannot cancel their authentication.
`;

class ValidationInputError extends Error {}

export function parseValidationOptions(
  argv: string[],
  environment: NodeJS.ProcessEnv
): ValidationOptions {
  let values;
  try {
    ({ values } = parseArgs({ args: argv, options: {
      kubeconfig: { type: "string" }, context: { type: "string" },
      "host-service-account": { type: "string" }, impersonate: { type: "boolean" },
      "inspection-context": { type: "string" },
      "admission-policy": { type: "string" }, "admission-binding": { type: "string" },
      "host-placement-policy": { type: "string" }, "host-placement-binding": { type: "string" },
      "kata-profile": { type: "string" }, "execution-pool": { type: "string" }, "trusted-host-pool": { type: "string" },
      "timeout-seconds": { type: "string", default: "60" }, json: { type: "boolean" },
      help: { type: "boolean" }
    }, allowPositionals: false }));
  } catch {
    throw new ValidationInputError("Invalid command-line arguments; use --help");
  }
  if (!values.kubeconfig || !values.context) {
    throw new ValidationInputError("--kubeconfig and --context are required");
  }
  if (environment.OCI_JAVASCRIPT_ISOLATION_PROVIDER !== undefined
    && environment.OCI_JAVASCRIPT_ISOLATION_PROVIDER !== "kubernetes") {
    throw new ValidationInputError("Deployment validation requires a kubernetes target");
  }
  const timeoutSeconds = Number(values["timeout-seconds"]);
  if (!/^\d+$/.test(values["timeout-seconds"]!) || timeoutSeconds < 1 || timeoutSeconds > 300) {
    throw new ValidationInputError("--timeout-seconds must be an integer from 1 to 300");
  }
  const kubeconfigPath = resolve(values.kubeconfig);
  const local = environment.OCI_JAVASCRIPT_KUBERNETES_PROFILE === "local-development";
  let config: KubernetesConfig;
  try {
    config = parseKubernetesConfig(local ? {
      ...environment,
      OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG: kubeconfigPath,
      OCI_JAVASCRIPT_KUBERNETES_CONTEXT: values.context
    } : {
      ...environment,
      // Dry-run metadata describes the probe, not an existing trusted host pod.
      OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME:
        environment.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME ?? "deployment-validation",
      OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID:
        environment.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID ?? randomUUID()
    });
  } catch (error) {
    throw new ValidationInputError((error as Error).message);
  }
  const hostAccount = values["host-service-account"];
  if (local && (hostAccount !== undefined || values.impersonate)) {
    throw new ValidationInputError("Host service-account options require an in-cluster target profile");
  }
  if (!local && (!hostAccount || !/^[a-z0-9](?:[-a-z0-9.]{0,251}[a-z0-9])?$/.test(hostAccount))) {
    throw new ValidationInputError("--host-service-account must name the in-cluster host service account");
  }
  if (!local && !values["inspection-context"]) {
    throw new ValidationInputError("--inspection-context is required for in-cluster deployment inspection");
  }
  const inspectionFlags = ["inspection-context", "admission-policy", "admission-binding", "host-placement-policy",
    "host-placement-binding", "kata-profile", "execution-pool", "trusted-host-pool"] as const;
  if (local && inspectionFlags.some(key => values[key] !== undefined)) {
    throw new ValidationInputError("Deployment inspection options require an in-cluster target profile");
  }
  if (config.profile !== "kata-in-cluster" && ["host-placement-policy", "host-placement-binding", "kata-profile",
    "execution-pool", "trusted-host-pool"].some(key => values[key as keyof typeof values] !== undefined)) {
    throw new ValidationInputError("Kata inspection options require the kata-in-cluster profile");
  }
  const admissionPolicy = values["admission-policy"] ?? (config.profile === "kata-in-cluster"
    ? "oci-js-kata-execution-pods-v1" : "oci-js-standard-execution-pods-v1");
  const hostPlacementPolicy = values["host-placement-policy"] ?? "oci-js-kata-trusted-host-placement-v1";
  const settings = {
    admissionPolicy, admissionBinding: values["admission-binding"] ?? admissionPolicy,
    hostPlacementPolicy, hostPlacementBinding: values["host-placement-binding"] ?? hostPlacementPolicy,
    kataProfile: values["kata-profile"] ?? "kata-qemu-runtime-rs-v1",
    executionPool: values["execution-pool"] ?? "kata-execution",
    trustedHostPool: values["trusted-host-pool"] ?? "trusted-host"
  };
  if (Object.values(settings).some(value => !/^[a-z0-9](?:[-a-z0-9.]{0,251}[a-z0-9])?$/.test(value))) {
    throw new ValidationInputError("Deployment inspection names must be DNS names");
  }
  if ([settings.kataProfile, settings.executionPool, settings.trustedHostPool].some(value => value.length > 63)) {
    throw new ValidationInputError("Node profile and pool label values must be at most 63 characters");
  }
  if (config.profile === "kata-in-cluster" && settings.executionPool === settings.trustedHostPool) {
    throw new ValidationInputError("Execution and trusted-host pools must differ");
  }
  return {
    config, kubeconfigPath, context: values.context,
    inspectionContext: values["inspection-context"], ...settings,
    expectedIdentity: config.credentialMode === "in-cluster"
      ? `system:serviceaccount:${config.trustedHostNamespace}:${hostAccount}` : undefined,
    impersonate: values.impersonate ?? false,
    timeoutMs: timeoutSeconds * 1000,
    json: values.json ?? false,
    probeMetadata: local ? "local-development"
      : environment.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME !== undefined
        && environment.OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID !== undefined
        ? "configured-host-identity" : "synthetic-host-identity"
  };
}

export function createKubeconfigValidationApi(options: ValidationOptions): DeploymentValidationApi {
  const kubeconfig = loadValidationKubeconfig(options.kubeconfigPath, options.context);
  if (options.impersonate) {
    const user = kubeconfig.getCurrentUser()!;
    kubeconfig.users = kubeconfig.users.map(value => value.name === user.name
      ? { ...value, impersonateUser: options.expectedIdentity } : value);
  }
  const core = kubeconfig.makeApiClient(CoreV1Api);
  const node = kubeconfig.makeApiClient(NodeV1Api);
  const authentication = kubeconfig.makeApiClient(AuthenticationV1Api);
  const authorization = kubeconfig.makeApiClient(AuthorizationV1Api);
  let inspection: DeploymentInspectionApi | undefined;
  if (options.inspectionContext) {
    const inspector = loadValidationKubeconfig(options.kubeconfigPath, options.inspectionContext);
    if (inspector.getCurrentCluster()?.name !== kubeconfig.getCurrentCluster()?.name) {
      throw new ValidationInputError("Inspection and workload contexts must use the same kubeconfig cluster");
    }
    const admission = inspector.makeApiClient(AdmissionregistrationV1Api);
    const inspectorCore = inspector.makeApiClient(CoreV1Api);
    const inspectorAuth = inspector.makeApiClient(AuthenticationV1Api);
    inspection = {
      identity: signal => readIdentity(inspectorAuth, signal),
      readNamespace: (name, signal) => inspectorCore.readNamespace({ name }, requestOptions(signal)),
      readPolicy: (name, signal) => admission.readValidatingAdmissionPolicy({ name }, requestOptions(signal)),
      readBinding: (name, signal) => admission.readValidatingAdmissionPolicyBinding({ name }, requestOptions(signal)),
      dryRunCreatePod: (namespace, pod, signal) => dryRunPod(inspectorCore, namespace, pod, signal),
      async listNodes(signal) {
        const nodes: V1Node[] = [];
        const seen = new Set<string>();
        let token: string | undefined;
        do {
          if (signal.aborted) throw new Error("aborted");
          const page = await inspectorCore.listNode({ limit: 250, _continue: token }, requestOptions(signal));
          nodes.push(...page.items);
          token = page.metadata?._continue;
          if (nodes.length > 1000 || (token && (seen.has(token) || seen.size >= 9))) {
            throw new Error("Node inventory exceeded its validation bound");
          }
          if (token) seen.add(token);
        } while (token);
        return nodes;
      }
    };
  }
  return {
    inspection,
    identity: signal => readIdentity(authentication, signal),
    async readNamespace(name, signal) {
      return await core.readNamespace({ name }, requestOptions(signal));
    },
    async readRuntimeClass(name, signal) {
      return await node.readRuntimeClass({ name }, requestOptions(signal));
    },
    async selfCan(permission, signal) {
      const review = await authorization.createSelfSubjectAccessReview({ body: {
        apiVersion: "authorization.k8s.io/v1", kind: "SelfSubjectAccessReview",
        spec: { resourceAttributes: { ...permission, group: permission.group ?? "" } }
      } }, requestOptions(signal));
      return review.status?.allowed === true;
    },
    async dryRunCreatePod(namespace, pod, signal) {
      return await dryRunPod(core, namespace, pod, signal);
    }
  };
}

async function dryRunPod(core: CoreV1Api, namespace: string, pod: KubernetesPod,
  signal: AbortSignal): Promise<AdmissionProbeResult> {
  try {
    await core.createNamespacedPod({ namespace, body: pod, dryRun: "All" }, requestOptions(signal));
    return { outcome: "accepted" };
  } catch (error) {
    const rejection = admissionRejection(error);
    if (rejection) return rejection;
    throw error;
  }
}

function loadValidationKubeconfig(path: string, contextName: string): KubeConfig {
  const kubeconfig = new KubeConfig();
  try {
    kubeconfig.loadFromFile(path);
    const context = kubeconfig.getContextObject(contextName);
    if (!context) throw new Error("missing context");
    kubeconfig.setCurrentContext(context.name);
    const user = kubeconfig.getCurrentUser();
    if (!user || !kubeconfig.getCurrentCluster()) throw new Error("incomplete context");
    // SDK credential acquisition precedes request-signal middleware and is not cancellable.
    if (user.exec != null || user.authProvider != null) {
      throw new ValidationInputError("Kubeconfig exec and auth-provider helpers are unsupported; use token or client-certificate credentials");
    }
  } catch (error) {
    if (error instanceof ValidationInputError) throw error;
    throw new ValidationInputError("Unable to load the explicit kubeconfig and context");
  }
  return kubeconfig;
}

async function readIdentity(api: AuthenticationV1Api, signal: AbortSignal): Promise<ValidationIdentity> {
  const review = await api.createSelfSubjectReview({
    body: { apiVersion: "authentication.k8s.io/v1", kind: "SelfSubjectReview" }
  }, requestOptions(signal));
  return { username: review.status?.userInfo?.username ?? "", groups: review.status?.userInfo?.groups ?? [] };
}

export async function validateDeployment(
  options: ValidationOptions,
  api: DeploymentValidationApi,
  parentSignal?: AbortSignal
): Promise<ValidationReport> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), options.timeoutMs);
  const signal = parentSignal ? AbortSignal.any([parentSignal, controller.signal]) : controller.signal;
  const report: ValidationReport = {
    startedAt: new Date().toISOString(),
    profile: options.config.profile, context: options.context, identity: null,
    probeMetadata: options.probeMetadata, dryRunOnly: true, passed: false, checks: []
  };
  type CheckResult = Omit<ValidationCheck, "id" | "outcome"> & { passed: boolean };
  const check = async <T>(id: string, request: () => Promise<T>, evaluate: (value: T) => CheckResult): Promise<boolean> => {
    try {
      if (signal.aborted) throw new Error("aborted");
      const value = await abortable(request(), signal);
      if (signal.aborted) throw new Error("aborted");
      const { passed, ...evidence } = evaluate(value);
      report.checks.push({ id, outcome: passed ? "passed" : "failed", ...evidence });
      return passed;
    } catch (error) {
      report.checks.push({ id, outcome: "failed", statusCode: statusCode(error), detail:
        signal.aborted ? "Validation cancelled or timed out" : "Kubernetes API request failed" });
      return false;
    }
  };
  try {
    if (!await check("identity", () => api.identity(signal), identity => {
      report.identity = identity;
      const groups = new Set(identity.groups);
      const expectedGroups = ["system:authenticated", "system:serviceaccounts",
        `system:serviceaccounts:${options.config.credentialMode === "in-cluster" ? options.config.trustedHostNamespace : ""}`];
      return {
        passed: !!identity.username && (!options.expectedIdentity || (identity.username === options.expectedIdentity
          && groups.size === expectedGroups.length && expectedGroups.every(value => groups.has(value)))),
        detail: options.expectedIdentity ? "Effective identity must match the host service account and its normal groups"
          : "Kubeconfig API identity is verified"
      };
    })) return report;
    let namespaceLabels: Record<string, string> = {};
    if (!await check("namespace", () => api.readNamespace(options.config.namespace, signal), value => {
      namespaceLabels = value.metadata?.labels ?? {};
      return { passed: value.metadata?.name === options.config.namespace && (options.config.profile === "local-development"
        || (namespaceLabels["oci.oracle.com/kubernetes-profile"] === options.config.profile
          && namespaceLabels["pod-security.kubernetes.io/enforce"] === "restricted"
          && namespaceLabels["kubernetes.io/metadata.name"] === options.config.namespace)),
      detail: "Execution namespace identity, profile and restricted Pod Security labels must match" };
    })) return report;
    for (const permission of requiredExecutionPermissions(options.config.profile)) {
      const { resource, subresource, verb, group, namespaced } = permission;
      if (!await check(`permission:${resource}${subresource ? `/${subresource}` : ""}:${verb}`,
        () => api.selfCan({ resource, subresource, verb, group, namespace: namespaced ? options.config.namespace : undefined,
          name: resource === "namespaces" ? options.config.namespace : undefined }, signal),
        passed => ({ passed, detail: "Required execution permission must be allowed" }))) return report;
    }
    const policy = runtimePolicyFor(options.config);
    const propertyResult = (problems: string[], success: string): CheckResult => ({
      passed: problems.length === 0, detail: problems.length ? problems.join("; ") : success
    });
    const remember = (kind: string, value: { metadata?: V1Namespace["metadata"] }) => {
      const metadata = value.metadata;
      (report.inspectedResources ??= []).push({ kind, name: metadata?.name ?? "", uid: metadata?.uid,
        resourceVersion: metadata?.resourceVersion, generation: metadata?.generation });
    };
    const kataExpected = { handler: policy.kind === "kata" ? policy.runtimeHandler : "",
      profile: options.kataProfile, executionPool: options.executionPool, trustedHostPool: options.trustedHostPool };
    if (policy.kind === "kata") {
      if (!await check("permission:runtimeclasses:get", () => api.selfCan({ group: "node.k8s.io",
        resource: "runtimeclasses", name: policy.runtimeClassName, verb: "get" }, signal),
      passed => ({ passed, detail: "Host identity must be allowed to read the exact RuntimeClass" }))) return report;
      if (!await check("deployment:runtime-class", () => api.readRuntimeClass(policy.runtimeClassName, signal), runtime => {
        remember("RuntimeClass", runtime);
        const problems = inspectKataRuntime(runtime, kataExpected);
        if (runtime.metadata?.name !== policy.runtimeClassName) problems.push("RuntimeClass identity does not match");
        return propertyResult(problems, "RuntimeClass handler, profile and scheduling match");
      })) return report;
    }
    if (options.config.profile !== "local-development") {
      const inspection = api.inspection;
      if (!await check("deployment:inspection-identity", async () => {
        if (!inspection) throw new Error("Deployment inspection is unavailable");
        return await inspection.identity(signal);
      }, identity => {
        report.inspectionIdentity = identity;
        return { passed: !!identity.username, detail: "Explicit inspection-context identity must be available" };
      })) return report;
      const inspectPolicy = async (id: string, name: string, bindingName: string,
        namespace: string, labels: Record<string, string>, operations: string[], resources: string[]) =>
        check(id, async () => {
          const deployedPolicy = await inspection!.readPolicy(name, signal);
          if (signal.aborted) throw new Error("aborted");
          const binding = await inspection!.readBinding(bindingName, signal);
          return { deployedPolicy, binding };
        }, ({ deployedPolicy, binding }) => {
          remember("ValidatingAdmissionPolicy", deployedPolicy);
          remember("ValidatingAdmissionPolicyBinding", binding);
          const problems = inspectAdmission(deployedPolicy, binding,
            { policyName: name, namespace, namespaceLabels: labels, operations, resources });
          if (binding.metadata?.name !== bindingName) problems.push("Admission binding identity does not match");
          return propertyResult(problems, "Admission policy and binding enforce the required namespace and request coverage");
        });
      if (!await inspectPolicy("deployment:admission", options.admissionPolicy, options.admissionBinding,
        options.config.namespace, namespaceLabels, policy.kind === "kata" ? ["CREATE", "UPDATE"] : ["CREATE"],
        policy.kind === "kata" ? ["pods", "pods/ephemeralcontainers", "pods/resize"] : ["pods"])) return report;
      if (policy.kind === "kata" && options.config.credentialMode === "in-cluster") {
        let hostLabels: Record<string, string> = {};
        const hostNamespace = options.config.trustedHostNamespace;
        if (!await check("deployment:trusted-host-namespace", () => inspection!.readNamespace(hostNamespace, signal), value => {
          hostLabels = value.metadata?.labels ?? {};
          return { passed: value.metadata?.name === hostNamespace && hostLabels["kubernetes.io/metadata.name"] === hostNamespace
            && hostLabels["pod-security.kubernetes.io/enforce"] === "restricted",
          detail: "Trusted-host namespace identity and restricted Pod Security labels must match" };
        })) return report;
        if (!await inspectPolicy("deployment:host-placement", options.hostPlacementPolicy, options.hostPlacementBinding,
          hostNamespace, hostLabels, ["CREATE", "UPDATE"], ["pods"])) return report;
        if (!await check("deployment:node-pools", () => inspection!.listNodes(signal), nodes =>
          propertyResult(inspectKataNodes(nodes, kataExpected), "Kata execution and trusted-host pool configuration match"))) return report;
      }
    }
    const probe = buildExecutionPod(options.config, policy, `oci-javascript-k8s-validation-${randomUUID()}`,
      randomUUID(), Date.now() + 30_000);
    const admission = (result: AdmissionProbeResult, expected: "accepted" | "rejected"): CheckResult => {
      if (result.outcome === "accepted") {
        return { passed: expected === "accepted", detail: "Accepted by server-side dry-run" };
      }
      if (result.outcome !== "rejected" || !(
        (result.statusCode === 400 && result.reason === "BadRequest")
        || (result.statusCode === 403 && result.reason === "Forbidden")
        || (result.statusCode === 422 && result.reason === "Invalid")
      )) return { passed: false, detail: "Inconclusive admission response" };
      return { passed: expected === "rejected", detail: "Rejected by the Kubernetes API",
        statusCode: result.statusCode, reason: result.reason };
    };
    if (!await check("admission:conforming", () => api.dryRunCreatePod(options.config.namespace, probe, signal),
      result => admission(result, "accepted"))) return report;
    for (const variant of [...unsafeAdmissionVariants(probe), ...runtimeAdmissionVariants(probe, policy),
      ...(policy.kind === "kata" ? kataDeploymentVariants(probe) : [])]) {
      await check(`admission:${variant.id}`, () => api.dryRunCreatePod(
        options.config.namespace, variant.pod, signal), result => admission(result, "rejected"));
      if (signal.aborted) return report;
    }
    if (policy.kind === "kata" && options.config.credentialMode === "in-cluster") {
      const host = structuredClone(probe);
      const namespace = options.config.trustedHostNamespace;
      host.metadata!.namespace = namespace;
      delete host.spec!.runtimeClassName;
      host.spec!.serviceAccountName = options.expectedIdentity!.split(":").at(-1)!;
      host.spec!.nodeSelector = { "oci.oracle.com.node-restriction.kubernetes.io/workload-pool": options.trustedHostPool };
      // Probe placement using a credential-free dummy pod. No host OCI Secret is referenced.
      host.spec!.volumes = host.spec!.volumes!.filter(volume => volume.name === "tmp");
      host.spec!.containers[0]!.volumeMounts = host.spec!.containers[0]!.volumeMounts!.filter(mount => mount.name === "tmp");
      if (!await check("admission:trusted-host:conforming", () => api.inspection!.dryRunCreatePod(namespace, host, signal),
        result => admission(result, "accepted"))) return report;
      const variants: Array<[string, (pod: KubernetesPod) => void]> = [
        ["pool", pod => { pod.spec!.nodeSelector!["oci.oracle.com.node-restriction.kubernetes.io/workload-pool"] = options.executionPool; }],
        ["node-name", pod => { pod.spec!.nodeName = "unsafe-execution-node"; }],
        ["runtime-class", pod => { pod.spec!.runtimeClassName = policy.runtimeClassName; }],
        ["toleration", pod => { pod.spec!.tolerations = [{ operator: "Exists" }]; }],
        ["scheduler", pod => { pod.spec!.schedulerName = "unsafe-scheduler"; }]
      ];
      for (const [id, mutate] of variants) {
        const unsafe = structuredClone(host);
        mutate(unsafe);
        await check(`admission:trusted-host:${id}`, () => api.inspection!.dryRunCreatePod(namespace, unsafe, signal),
          result => admission(result, "rejected"));
        if (signal.aborted) return report;
      }
    }
    report.passed = report.checks.every(value => value.outcome === "passed");
    return report;
  } finally {
    clearTimeout(timeout);
  }
}

function kataDeploymentVariants(pod: KubernetesPod): Array<{ id: string; pod: KubernetesPod }> {
  const mutations: Array<[string, (value: KubernetesPod) => void]> = [
    ["environment-source", value => { value.spec!.containers[0]!.envFrom = [{ configMapRef: { name: "unsafe-environment" } }]; }],
    ["arguments", value => { value.spec!.containers[0]!.args = ["--unsafe"]; }],
    ["working-directory", value => { value.spec!.containers[0]!.workingDir = "/tmp"; }],
    ["stdin", value => { value.spec!.containers[0]!.stdin = true; }],
    ["stdin-once", value => { value.spec!.containers[0]!.stdinOnce = true; }],
    ["tty", value => { value.spec!.containers[0]!.tty = true; }],
    ["extra-annotation", value => { value.metadata!.annotations!["io.katacontainers.config.hypervisor.path"] = "/unsafe"; }],
    ["extra-label", value => { value.metadata!.labels!["unsafe.example/label"] = "unsafe"; }],
    ["finalizer", value => { value.metadata!.finalizers = ["unsafe.example/finalizer"]; }],
    ["host-namespace", value => { value.metadata!.annotations!["oci.oracle.com/trusted-host-namespace"] = "unsafe-host"; }],
    ["missing-expiry", value => { delete value.metadata!.annotations!["oci.oracle.com/expires-at"]; }],
    ["node-selector", value => { value.spec!.nodeSelector = { "unsafe.example/node": "unsafe" }; }],
    ["affinity", value => { value.spec!.affinity = { nodeAffinity: { preferredDuringSchedulingIgnoredDuringExecution: [
      { weight: 1, preference: { matchExpressions: [{ key: "unsafe.example/node", operator: "Exists" }] } }
    ] } }; }],
    ["toleration", value => { value.spec!.tolerations = [{ operator: "Exists" }]; }],
    ["node-name", value => { value.spec!.nodeName = "unsafe-node"; }],
    ["scheduler", value => { value.spec!.schedulerName = "unsafe-scheduler"; }],
    ["scheduling-gate", value => { value.spec!.schedulingGates = [{ name: "unsafe.example/gate" }]; }],
    ["topology-spread", value => { value.spec!.topologySpreadConstraints = [
      { maxSkew: 1, topologyKey: "kubernetes.io/hostname", whenUnsatisfiable: "DoNotSchedule" }
    ]; }],
    ["priority-class", value => { value.spec!.priorityClassName = "system-node-critical"; }],
    ["preemption", value => { value.spec!.preemptionPolicy = "Never"; }]
  ];
  return mutations.map(([id, mutate]) => {
    const unsafe = structuredClone(pod);
    mutate(unsafe);
    return { id: `kata:${id}`, pod: unsafe };
  });
}

export async function main(
  argv: string[] = process.argv.slice(2),
  environment: NodeJS.ProcessEnv = process.env,
  dependencies: { api?: DeploymentValidationApi; write?: (text: string) => void; signal?: AbortSignal } = {}
): Promise<number> {
  const write = dependencies.write ?? (text => { process.stdout.write(`${text}\n`); });
  if (argv.includes("--help")) { write(HELP); return 0; }
  const controller = new AbortController();
  const abort = () => controller.abort();
  process.once("SIGINT", abort);
  process.once("SIGTERM", abort);
  try {
    const options = parseValidationOptions(argv, environment);
    const report = await validateDeployment(options, dependencies.api ?? createKubeconfigValidationApi(options),
      dependencies.signal ?? controller.signal);
    write(options.json ? JSON.stringify(report, null, 2) : [
      `${report.passed ? "PASS" : "FAIL"} Kubernetes deployment validation (${report.profile})`,
      `Context: ${report.context}; API identity: ${report.identity?.username ?? "unverified"}`,
      ...(report.inspectionIdentity ? [`Inspection context: ${options.inspectionContext}; identity: ${report.inspectionIdentity.username}`] : []),
      `Probe metadata: ${report.probeMetadata}`,
      ...report.checks.map(value => `${value.outcome === "passed" ? "PASS" : "FAIL"} ${value.id}: ${value.detail}${value.statusCode ? ` (HTTP ${value.statusCode}${value.reason ? ` ${value.reason}` : ""})` : ""}`),
      "Dry-run evidence only: runtime, CNI, image provenance and production approval are not certified."
    ].join("\n"));
    return report.passed ? 0 : 1;
  } catch (error) {
    const message = error instanceof ValidationInputError ? error.message : "Deployment validation could not be completed";
    write(argv.includes("--json") ? JSON.stringify({ passed: false, error: message }) : `FAIL ${message}`);
    return 1;
  } finally {
    process.removeListener("SIGINT", abort);
    process.removeListener("SIGTERM", abort);
  }
}

function requestOptions(signal: AbortSignal): ConfigurationOptions {
  return { middlewareMergeStrategy: "append", middleware: [{
    pre(context: RequestContext) { context.setSignal(signal); return new Observable(Promise.resolve(context)); },
    post(context: ResponseContext) { return new Observable(Promise.resolve(context)); }
  }] };
}

function statusCode(error: unknown): number | undefined {
  const value = error as { code?: unknown; statusCode?: unknown; response?: { statusCode?: unknown } } | null;
  const code = value?.statusCode ?? value?.code ?? value?.response?.statusCode;
  return typeof code === "number" && code >= 100 && code <= 599 ? code : undefined;
}

function admissionRejection(error: unknown): Extract<AdmissionProbeResult, { outcome: "rejected" }> | undefined {
  const code = statusCode(error);
  let raw = (error as { body?: unknown } | null)?.body;
  // The SDK leaves unlisted HTTP error responses as JSON text rather than V1Status objects.
  if (typeof raw === "string") {
    try { raw = JSON.parse(raw); } catch { return; }
  }
  if (!raw || typeof raw !== "object") return;
  const body = raw as Record<string, unknown>;
  if (body.apiVersion !== "v1" || body.kind !== "Status" || body.status !== "Failure" || body.code !== code) return;
  if ((code === 400 && body.reason === "BadRequest") || (code === 403 && body.reason === "Forbidden")
    || (code === 422 && body.reason === "Invalid")) {
    return { outcome: "rejected", statusCode: code, reason: body.reason };
  }
}

function abortable<T>(promise: Promise<T>, signal: AbortSignal): Promise<T> {
  return new Promise((resolve, reject) => {
    const abort = () => reject(new Error("aborted"));
    signal.addEventListener("abort", abort, { once: true });
    promise.then(resolve, reject).finally(() => signal.removeEventListener("abort", abort));
    if (signal.aborted) abort();
  });
}

if (import.meta.main) {
  process.exitCode = await main();
}
