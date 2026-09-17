/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { KubernetesApi, KubernetesPod } from "./kubernetes-api.ts";
import type { KubernetesProfile } from "./kubernetes-config.ts";
import {
  EXPIRY_ANNOTATION,
  MANAGED_BY_LABEL,
  PROFILE_LABEL,
  PROVIDER_LABEL
} from "./kubernetes-pod.ts";

export type ReconciliationSummary = {
  deletedNames: string[];
  failureCount: number;
};

export async function reconcileExpiredPods(
  api: KubernetesApi,
  namespace: string,
  profile: KubernetesProfile,
  nowMs = Date.now(),
  candidateTimeoutMs = 5_000
): Promise<ReconciliationSummary> {
  const summary: ReconciliationSummary = { deletedNames: [], failureCount: 0 };
  const pods = await api.listManagedPods(namespace, profile);
  for (const pod of pods) {
    const name = expiredManagedPodName(pod, namespace, profile, nowMs);
    if (!name) {
      continue;
    }
    const deadlineMs = Date.now() + candidateTimeoutMs;
    const controller = new AbortController();
    try {
      await withCandidateDeadline((async () => {
        await api.deletePod(namespace, name, controller.signal);
        if (!await api.waitForPodDeleted(namespace, name, deadlineMs, controller.signal)) {
          throw new Error("Kubernetes reconciliation could not confirm pod deletion");
        }
      })(), deadlineMs, controller);
      summary.deletedNames.push(name);
    } catch {
      summary.failureCount += 1;
    }
  }
  return summary;
}

export function startExpiryReconciliation(
  api: KubernetesApi,
  namespace: string,
  profile: KubernetesProfile,
  intervalMs: number,
  onResult: (summary: ReconciliationSummary | undefined) => void = () => undefined
): () => void {
  let stopped = false;
  let running = false;
  const reconcile = async () => {
    if (stopped || running) {
      return;
    }
    running = true;
    try {
      onResult(await reconcileExpiredPods(api, namespace, profile));
    } catch {
      onResult(undefined);
    } finally {
      running = false;
    }
  };
  void reconcile();
  const timer = setInterval(() => void reconcile(), intervalMs);
  timer.unref();
  return () => {
    stopped = true;
    clearInterval(timer);
  };
}

function withCandidateDeadline<T>(
  promise: Promise<T>,
  deadlineMs: number,
  controller: AbortController
): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(
      () => {
        controller.abort();
        reject(new Error("Kubernetes reconciliation candidate timed out"));
      },
      Math.max(1, deadlineMs - Date.now())
    );
    promise.then(resolve, reject).finally(() => clearTimeout(timeout));
  });
}

function expiredManagedPodName(
  pod: KubernetesPod,
  namespace: string,
  profile: KubernetesProfile,
  nowMs: number
): string | undefined {
  if (
    pod.metadata?.namespace !== namespace
    || pod.metadata.labels?.[MANAGED_BY_LABEL] !== "oci-javascript-mcp"
    || pod.metadata.labels?.[PROVIDER_LABEL] !== "kubernetes"
    || pod.metadata.labels?.[PROFILE_LABEL] !== profile
    || !pod.metadata.name
  ) {
    return undefined;
  }
  const expiry = pod.metadata.annotations?.[EXPIRY_ANNOTATION];
  if (!expiry || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(expiry)) {
    return undefined;
  }
  const expiryMs = Date.parse(expiry);
  return Number.isFinite(expiryMs) && expiryMs <= nowMs ? pod.metadata.name : undefined;
}
