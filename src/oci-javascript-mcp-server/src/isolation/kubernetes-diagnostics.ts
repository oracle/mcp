/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { KubernetesConfig, KubernetesProfile } from "./kubernetes-config.ts";
import type { KubernetesRuntimePolicy } from "./kubernetes-runtime-policy.ts";

export type KubernetesPhase =
  | "preflight"
  | "creating"
  | "pending"
  | "running"
  | "connecting"
  | "executing"
  | "closing"
  | "deleting"
  | "deleted"
  | "reconciling";

export type KubernetesOutcome = "started" | "succeeded" | "failed" | "cancelled" | "timed_out";

export type KubernetesReason =
  | "none"
  | "configuration"
  | "namespace"
  | "runtime_class"
  | "authorization"
  | "admission"
  | "api"
  | "scheduling"
  | "exec"
  | "channel"
  | "deadline"
  | "cleanup";

export type KubernetesDiagnosticEvent = {
  provider: "kubernetes";
  profile: KubernetesProfile;
  correlationId: string;
  phase: KubernetesPhase;
  outcome: KubernetesOutcome;
  reason: KubernetesReason;
  durationMs: number;
  reconciliation?: {
    successCount: number;
    failureCount: number;
  };
};

export type KubernetesDiagnosticSink = (event: KubernetesDiagnosticEvent) => void;

export type KubernetesProviderDescriptor = {
  provider: "kubernetes";
  profile: KubernetesProfile;
  credentialMode: "explicit-kubeconfig" | "in-cluster";
  runtimePolicy: "standard" | "kata";
  assurance: "development-only-container" | "in-cluster-container" | "kata-poc";
  nestedIsolatedVm: true;
  executionNamespace: string;
  trustedHostNamespace: string | null;
  namespacesSeparated: boolean | null;
  admissionPreflight: "reviewed-variants-rejected" | "unverified";
  imagePolicy: {
    digestPinned: boolean;
    pullPolicy: "IfNotPresent" | "Never";
    provenanceVerified: false;
  };
  runtimeClass?: string;
  runtimeHandler?: string;
  externalEvidence: {
    kataGuestKernelRequested: boolean;
    kataGuestKernelVerified: false;
    criMappingVerified: false;
    nodeRuntimeVerified: false;
    cniIsolationVerified: false;
    pidLimitVerified: false;
    runtimeOverheadVerified: false;
    imageProvenanceVerified: false;
    admissionPolicyRevisionVerified: false;
  };
};

export function providerDescriptor(
  config: KubernetesConfig,
  policy: KubernetesRuntimePolicy,
  admissionEnforced: boolean
): KubernetesProviderDescriptor {
  const kata = policy.kind === "kata";
  return {
    provider: "kubernetes",
    profile: config.profile,
    credentialMode: config.credentialMode,
    runtimePolicy: policy.kind,
    assurance: config.profile === "local-development"
      ? "development-only-container"
      : kata ? "kata-poc" : "in-cluster-container",
    nestedIsolatedVm: true,
    executionNamespace: config.namespace,
    trustedHostNamespace: config.credentialMode === "in-cluster"
      ? config.trustedHostNamespace
      : null,
    namespacesSeparated: config.credentialMode === "in-cluster" ? true : null,
    admissionPreflight: admissionEnforced ? "reviewed-variants-rejected" : "unverified",
    imagePolicy: {
      digestPinned: config.imageDigestPinned,
      pullPolicy: config.imagePullPolicy,
      provenanceVerified: false
    },
    ...(kata ? {
      runtimeClass: policy.runtimeClassName,
      runtimeHandler: policy.runtimeHandler
    } : {}),
    externalEvidence: {
      kataGuestKernelRequested: kata,
      kataGuestKernelVerified: false,
      criMappingVerified: false,
      nodeRuntimeVerified: false,
      cniIsolationVerified: false,
      pidLimitVerified: false,
      runtimeOverheadVerified: false,
      imageProvenanceVerified: false,
      admissionPolicyRevisionVerified: false
    }
  };
}

export const stderrKubernetesDiagnosticSink: KubernetesDiagnosticSink = event => {
  process.stderr.write(`${JSON.stringify(event)}\n`);
};

export function diagnosticEvent(
  profile: KubernetesProfile,
  correlationId: string,
  phase: KubernetesPhase,
  outcome: KubernetesOutcome,
  reason: KubernetesReason,
  startedMs: number,
  nowMs = Date.now(),
  reconciliation?: { successCount: number; failureCount: number }
): KubernetesDiagnosticEvent {
  return {
    provider: "kubernetes",
    profile,
    correlationId: safeCorrelationId(correlationId),
    phase,
    outcome,
    reason,
    durationMs: Math.max(0, Math.min(24 * 60 * 60 * 1000, Math.round(nowMs - startedMs))),
    ...(reconciliation ? {
      reconciliation: {
        successCount: safeCount(reconciliation.successCount),
        failureCount: safeCount(reconciliation.failureCount)
      }
    } : {})
  };
}

function safeCount(value: number): number {
  return Number.isSafeInteger(value) && value >= 0 ? value : 0;
}

function safeCorrelationId(value: string): string {
  return /^[a-f0-9-]{36}$/.test(value) ? value : "invalid-correlation-id";
}
