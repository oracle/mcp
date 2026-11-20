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
  deletedPodNames: string[];
  deletedSecretNames: string[];
  failureCount: number;
};

export async function reconcileExpiredExecutions(
  api: KubernetesApi,
  namespace: string,
  profile: KubernetesProfile,
  nowMs = Date.now(),
  candidateTimeoutMs = 5_000,
  signal?: AbortSignal
): Promise<ReconciliationSummary> {
  if (signal?.aborted) throw new Error("Kubernetes reconciliation cancelled");
  const summary: ReconciliationSummary = { deletedPodNames: [], deletedSecretNames: [], failureCount: 0 };
  const kinds: Array<"pod" | "secret"> = profile === "local-development" ? ["pod"] : ["pod", "secret"];
  const listings = await Promise.allSettled(kinds.map(async kind => {
    const listing = new AbortController();
    try {
      return await withReconciliationDeadline(kind === "pod"
        ? api.listManagedPods(namespace, profile, listing.signal)
        : api.listManagedSecrets(namespace, profile, listing.signal), Date.now() + 5_000, listing, signal);
    } finally { listing.abort(); }
  }));
  for (const [index, listing] of listings.entries()) {
    if (signal?.aborted) throw new Error("Kubernetes reconciliation cancelled");
    if (listing.status === "rejected") { summary.failureCount += 1; continue; }
    const kind = kinds[index]!;
    for (const pod of listing.value) {
      if (signal?.aborted) throw new Error("Kubernetes reconciliation cancelled");
      const name = expiredManagedPodName(pod, namespace, profile, nowMs);
      if (!name) {
        continue;
      }
      const deadlineMs = Date.now() + candidateTimeoutMs;
      const controller = new AbortController();
      try {
        await withReconciliationDeadline((async () => {
          if (kind === "pod") await api.deletePod(namespace, name, controller.signal);
          else await api.deleteSecret(namespace, name, controller.signal);
          const deleted = kind === "pod"
            ? await api.waitForPodDeleted(namespace, name, deadlineMs, controller.signal)
            : await api.waitForSecretDeleted(namespace, name, deadlineMs, controller.signal);
          if (!deleted) {
            throw new Error("Kubernetes reconciliation could not confirm pod deletion");
          }
        })(), deadlineMs, controller, signal);
        (kind === "pod" ? summary.deletedPodNames : summary.deletedSecretNames).push(name);
      } catch {
        if (signal?.aborted) throw new Error("Kubernetes reconciliation cancelled");
        summary.failureCount += 1;
      } finally { controller.abort(); }
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
      onResult(await reconcileExpiredExecutions(api, namespace, profile));
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

function withReconciliationDeadline<T>(
  promise: Promise<T>,
  deadlineMs: number,
  controller: AbortController,
  signal?: AbortSignal
): Promise<T> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (callback: () => void) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      signal?.removeEventListener("abort", cancelled);
      callback();
    };
    const cancelled = () => finish(() => {
      controller.abort();
      reject(new Error("Kubernetes reconciliation cancelled"));
    });
    const timeout = setTimeout(() => finish(() => {
      controller.abort();
      reject(new Error("Kubernetes reconciliation timed out"));
    }), Math.max(1, deadlineMs - Date.now()));
    signal?.addEventListener("abort", cancelled, { once: true });
    promise.then(value => finish(() => resolve(value)), error => finish(() => reject(error)));
    if (signal?.aborted) cancelled();
  });
}

function expiredManagedPodName(
  pod: Pick<KubernetesPod, "metadata">,
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
