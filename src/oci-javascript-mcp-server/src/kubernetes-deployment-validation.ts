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
  AuthorizationV1Api,
  CoreV1Api,
  KubeConfig,
  NodeV1Api,
  Observable,
  type ConfigurationOptions,
  type RequestContext,
  type ResponseContext
} from "@kubernetes/client-node";
import type { KubernetesPod, ResourceAttributes } from "./isolation/kubernetes-api.ts";
import { parseKubernetesConfig, type KubernetesConfig } from "./isolation/kubernetes-config.ts";
import { buildExecutionPod, runtimeAdmissionVariants, unsafeAdmissionVariants } from "./isolation/kubernetes-pod.ts";
import { runtimePolicyFor } from "./isolation/kubernetes-runtime-policy.ts";

export type ValidationOptions = {
  config: KubernetesConfig;
  kubeconfigPath: string;
  context: string;
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
  readNamespace(name: string, signal: AbortSignal): Promise<void>;
  readRuntimeClass(name: string, signal: AbortSignal): Promise<{ handler: string }>;
  selfCan(permission: ResourceAttributes, signal: AbortSignal): Promise<boolean>;
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
  profile: KubernetesConfig["profile"];
  context: string;
  identity: ValidationIdentity | null;
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
  return {
    config, kubeconfigPath, context: values.context,
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
  const kubeconfig = new KubeConfig();
  try {
    kubeconfig.loadFromFile(options.kubeconfigPath);
    const context = kubeconfig.getContextObject(options.context);
    if (!context) throw new Error("missing context");
    kubeconfig.setCurrentContext(context.name);
    const user = kubeconfig.getCurrentUser();
    if (!user || !kubeconfig.getCurrentCluster()) throw new Error("incomplete context");
    // SDK credential acquisition precedes request-signal middleware and is not cancellable.
    if (user.exec != null || user.authProvider != null) {
      throw new ValidationInputError("Kubeconfig exec and auth-provider helpers are unsupported; use token or client-certificate credentials");
    }
    if (options.impersonate) {
      kubeconfig.users = kubeconfig.users.map(value => value.name === user.name
        ? { ...value, impersonateUser: options.expectedIdentity } : value);
    }
  } catch (error) {
    if (error instanceof ValidationInputError) throw error;
    throw new ValidationInputError("Unable to load the explicit kubeconfig and context");
  }
  const core = kubeconfig.makeApiClient(CoreV1Api);
  const node = kubeconfig.makeApiClient(NodeV1Api);
  const authentication = kubeconfig.makeApiClient(AuthenticationV1Api);
  const authorization = kubeconfig.makeApiClient(AuthorizationV1Api);
  return {
    async identity(signal) {
      const review = await authentication.createSelfSubjectReview({
        body: { apiVersion: "authentication.k8s.io/v1", kind: "SelfSubjectReview" }
      }, requestOptions(signal));
      return { username: review.status?.userInfo?.username ?? "", groups: review.status?.userInfo?.groups ?? [] };
    },
    async readNamespace(name, signal) {
      await core.readNamespace({ name }, requestOptions(signal));
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
      try {
        await core.createNamespacedPod({ namespace, body: pod, dryRun: "All" }, requestOptions(signal));
        return { outcome: "accepted" };
      } catch (error) {
        const rejection = admissionRejection(error);
        if (rejection) return rejection;
        throw error;
      }
    }
  };
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
    if (!await check("namespace", () => api.readNamespace(options.config.namespace, signal),
      () => ({ passed: true, detail: "Execution namespace is readable" }))) return report;
    for (const [resource, subresource, verbs] of [
      ["pods", undefined, ["create", "get", "list", "watch", "delete"]],
      ["pods", "exec", ["create", "get"]],
      ["pods", "portforward", ["create", "get"]]
    ] as const) {
      for (const verb of verbs) {
        if (!await check(`permission:${resource}${subresource ? `/${subresource}` : ""}:${verb}`,
          () => api.selfCan({ resource, subresource, verb, namespace: options.config.namespace }, signal),
          passed => ({ passed, detail: "Required execution permission must be allowed" }))) return report;
      }
    }
    const policy = runtimePolicyFor(options.config);
    if (policy.kind === "kata" && !await check("runtime-class",
      () => api.readRuntimeClass(policy.runtimeClassName, signal),
      runtime => ({ passed: runtime.handler === policy.runtimeHandler,
        detail: "Configured RuntimeClass must have the expected handler" }))) return report;
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
    for (const variant of [...unsafeAdmissionVariants(probe), ...runtimeAdmissionVariants(probe, policy)]) {
      await check(`admission:${variant.id}`, () => api.dryRunCreatePod(
        options.config.namespace, variant.pod, signal), result => admission(result, "rejected"));
      if (signal.aborted) return report;
    }
    report.passed = report.checks.every(value => value.outcome === "passed");
    return report;
  } finally {
    clearTimeout(timeout);
  }
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
