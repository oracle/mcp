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
  const api = new Proxy({
    async listManagedPods() {
      calls.push("list");
      listAttempts += 1;
      if (listAttempts === 1) {
        throw new Error("temporary outage with raw endpoint");
      }
      return [{
        metadata: {
          name: "expired",
          namespace: "execution",
          labels: {
            [MANAGED_BY_LABEL]: "oci-javascript-mcp",
            [PROVIDER_LABEL]: "kubernetes",
            [PROFILE_LABEL]: "kata-in-cluster"
          },
          annotations: { [EXPIRY_ANNOTATION]: new Date(Date.now() - 1000).toISOString() }
        }
      }];
    },
    async deletePod() { calls.push("delete"); },
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
  assert.deepEqual(calls, ["list", "list", "delete", "get"]);
  assert.deepEqual(events.map(event => event.outcome), ["failed", "succeeded"]);
  assert.equal(JSON.stringify(events).includes("raw endpoint"), false);
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
