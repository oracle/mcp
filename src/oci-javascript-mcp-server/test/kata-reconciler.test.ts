/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import type { KubernetesApi } from "../src/isolation/kubernetes-api.ts";
import type { KubernetesDiagnosticEvent } from "../src/isolation/kubernetes-diagnostics.ts";
import {
  EXPIRY_ANNOTATION,
  MANAGED_BY_LABEL,
  PROFILE_LABEL,
  PROVIDER_LABEL
} from "../src/isolation/kubernetes-pod.ts";
import { main, runCleanupReconciler } from "../src/kubernetes-reconciler.ts";

test("cleanup-only reconciler recovers, uses only list/get/delete, and stops without leaks", async () => {
  const calls: string[] = [];
  let listAttempts = 0;
  let firstDeleteAttempts = 0;
  const pod = (name: string) => ({
    metadata: {
      name,
      namespace: "execution",
      labels: {
        [MANAGED_BY_LABEL]: "oci-javascript-mcp",
        [PROVIDER_LABEL]: "kubernetes",
        [PROFILE_LABEL]: "kata-in-cluster"
      },
      annotations: { [EXPIRY_ANNOTATION]: new Date(Date.now() - 1000).toISOString() }
    }
  });
  const api = new Proxy({
    async listManagedPods() {
      calls.push("list");
      listAttempts += 1;
      return listAttempts === 1 ? [pod("failed-first"), pod("deleted-later")] : [pod("failed-first")];
    },
    async deletePod(_namespace: string, name: string) {
      calls.push("delete");
      if (name === "failed-first" && firstDeleteAttempts++ === 0) {
        throw new Error("temporary outage with raw endpoint");
      }
    },
    async waitForPodDeleted() {
      calls.push("get");
      return true;
    }
  }, {
    get(target, property, receiver) {
      if (!(property in target)) {
        throw new Error(`cleanup identity attempted forbidden API ${String(property)}`);
      }
      return Reflect.get(target, property, receiver);
    }
  }) as unknown as KubernetesApi;
  const controller = new AbortController();
  const events: KubernetesDiagnosticEvent[] = [];
  const running = runCleanupReconciler(
    api,
    { profile: "kata-in-cluster", namespace: "execution", reconcileIntervalMs: 5 },
    controller.signal,
    event => {
      events.push(event);
      if (events.length === 2) {
        controller.abort();
      }
    }
  );
  await running;
  assert.deepEqual(calls, ["list", "delete", "delete", "get", "list", "delete", "get"]);
  assert.deepEqual(events.map(event => event.outcome), ["failed", "succeeded"]);
  assert.deepEqual(events.map(event => event.reconciliation), [
    { successCount: 1, failureCount: 1 },
    { successCount: 1, failureCount: 0 }
  ]);
  assert.equal(JSON.stringify(events).includes("raw endpoint"), false);
  assert.equal(JSON.stringify(events).includes("failed-first"), false);
});

test("cleanup-only reconciler exits immediately when already aborted", async () => {
  const controller = new AbortController();
  controller.abort();
  await runCleanupReconciler({} as KubernetesApi, {
    profile: "in-cluster",
    namespace: "execution",
    reconcileIntervalMs: 5
  }, controller.signal, () => assert.fail("must not emit"));
});

test("cleanup-only reconciler sanitizes list failures and resumes on the next interval", async () => {
  let listAttempts = 0;
  const api = {
    async listManagedPods() {
      listAttempts += 1;
      if (listAttempts === 1) {
        throw new Error("https://cluster.internal/pods?token=secret");
      }
      return [];
    }
  } as unknown as KubernetesApi;
  const controller = new AbortController();
  const events: KubernetesDiagnosticEvent[] = [];

  await runCleanupReconciler(
    api,
    { profile: "in-cluster", namespace: "execution", reconcileIntervalMs: 1 },
    controller.signal,
    event => {
      events.push(event);
      if (events.length === 2) {
        controller.abort();
      }
    }
  );

  assert.equal(listAttempts, 2);
  assert.deepEqual(events.map(event => [event.outcome, event.reason, event.reconciliation]), [
    ["failed", "cleanup", { successCount: 0, failureCount: 1 }],
    ["succeeded", "none", { successCount: 0, failureCount: 0 }]
  ]);
  assert.equal(JSON.stringify(events).includes("cluster.internal"), false);
  assert.equal(JSON.stringify(events).includes("secret"), false);
});

test("cleanup-only main accepts injected in-cluster seams for deterministic operation", async () => {
  const controller = new AbortController();
  controller.abort();
  await main({
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "in-cluster",
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: "execution"
  }, {
    api: {} as KubernetesApi,
    signal: controller.signal,
    diagnostics: () => assert.fail("must not emit")
  });
});
