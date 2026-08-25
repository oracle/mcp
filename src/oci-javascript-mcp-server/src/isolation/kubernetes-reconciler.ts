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

export async function reconcileExpiredPods(
  api: KubernetesApi,
  namespace: string,
  profile: KubernetesProfile,
  nowMs = Date.now()
): Promise<string[]> {
  const deleted: string[] = [];
  const pods = await api.listManagedPods(namespace, profile);
  for (const pod of pods) {
    const name = expiredManagedPodName(pod, namespace, profile, nowMs);
    if (!name) {
      continue;
    }
    await api.deletePod(namespace, name);
    if (!await api.waitForPodDeleted(namespace, name, Date.now() + 5000)) {
      throw new Error("Kubernetes reconciliation could not confirm pod deletion");
    }
    deleted.push(name);
  }
  return deleted;
}

export function startExpiryReconciliation(
  api: KubernetesApi,
  namespace: string,
  profile: KubernetesProfile,
  intervalMs: number,
  onError: () => void = () => undefined
): () => void {
  let stopped = false;
  let running = false;
  const reconcile = async () => {
    if (stopped || running) {
      return;
    }
    running = true;
    try {
      await reconcileExpiredPods(api, namespace, profile);
    } catch {
      onError();
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
