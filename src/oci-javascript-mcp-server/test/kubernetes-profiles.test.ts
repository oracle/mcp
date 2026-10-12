/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import type {
  KubernetesApi,
  KubernetesPod,
  ResourceAttributes
} from "../src/isolation/kubernetes-api.ts";
import { parseKubernetesConfig, type KubernetesProfile } from "../src/isolation/kubernetes-config.ts";
import type { KubernetesDiagnosticEvent } from "../src/isolation/kubernetes-diagnostics.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import {
  EXPIRY_ANNOTATION,
  MANAGED_BY_LABEL,
  PROFILE_LABEL,
  PROVIDER_LABEL
} from "../src/isolation/kubernetes-pod.ts";
import { reconcileExpiredPods, startExpiryReconciliation, type ReconciliationSummary } from "../src/isolation/kubernetes-reconciler.ts";
import {
  validInClusterEnvironment,
  validKataEnvironment,
  validLocalEnvironment
} from "./kata-fixtures.ts";

for (const environment of [validLocalEnvironment(), validInClusterEnvironment(), validKataEnvironment()]) {
  test(`startup uses only operational checks for ${environment.OCI_JAVASCRIPT_KUBERNETES_PROFILE}`, async () => {
    const config = parseKubernetesConfig(environment);
    const api = new ProfileApi();
    // Tripwires remain outside the narrowed execution API to catch accidental policy calls.
    Object.assign(api, {
      readRuntimeClass: async () => { throw new Error("startup must not read RuntimeClass"); },
      dryRunCreatePod: async () => { throw new Error("startup must not probe admission"); }
    });
    const events: KubernetesDiagnosticEvent[] = [];
    const provider = new KubernetesIsolationProvider(config, api, event => events.push(event));
    await provider.preflight({ startReconciliation: false });
    assert.equal(api.permissions.length, 10);
    assert.deepEqual(api.permissions.filter(permission => permission.resource === "namespaces"), [{
      group: undefined, name: config.namespace, namespace: undefined,
      resource: "namespaces", subresource: undefined, verb: "get"
    }]);
    assert(api.permissions.filter(permission => permission.resource === "pods").every(permission =>
      permission.namespace === config.namespace && permission.name === undefined
    ));
    assert.deepEqual(api.listRequests, [{ namespace: config.namespace, profile: config.profile }]);
    assert.equal("descriptor" in provider, false);
    assert.deepEqual(events.map(event => [event.phase, event.outcome]), [
      ["preflight", "started"], ["preflight", "succeeded"]
    ]);
    assert.equal(/assurance|admissionPreflight|externalEvidence|kubeconfig/.test(JSON.stringify(events)), false);
  });
}

test("every shared lifecycle permission is fail-closed for in-cluster profiles", async () => {
  const probe = new ProfileApi();
  const successful = new KubernetesIsolationProvider(
    parseKubernetesConfig(validInClusterEnvironment()),
    probe,
    () => undefined
  );
  await successful.preflight({ startReconciliation: false });
  for (const missing of probe.permissions) {
    const api = new ProfileApi();
    api.permission = value => !samePermission(value, missing);
    await assert.rejects(new KubernetesIsolationProvider(
      parseKubernetesConfig(validInClusterEnvironment()),
      api,
      () => undefined
    ).preflight({ startReconciliation: false }), /authorization/);
  }
});

test("reconciliation adopts only the exact Kubernetes profile and namespace", async () => {
  const now = Date.now();
  const api = new ProfileApi();
  api.pods = [
    managedPod("local-expired", "local-development", "execution", now - 1),
    managedPod("standard-expired", "in-cluster", "execution", now - 1),
    managedPod("kata-expired", "kata-in-cluster", "execution", now - 1),
    managedPod("wrong-namespace", "in-cluster", "other", now - 1),
    managedPod("standard-fresh", "in-cluster", "execution", now + 60_000)
  ];
  assert.deepEqual(
    await reconcileExpiredPods(api, "execution", "in-cluster", now),
    { deletedNames: ["standard-expired"], failureCount: 0 }
  );
  assert.deepEqual(api.listRequests, [{ namespace: "execution", profile: "in-cluster" }]);
  assert.deepEqual(api.deleted, ["standard-expired"]);
});

test("reconciliation bounds each failure and continues through the full candidate set", async () => {
  const now = Date.now();
  const api = new ProfileApi();
  api.pods = [
    managedPod("delete-fails", "in-cluster", "execution", now - 1),
    managedPod("confirmation-fails", "in-cluster", "execution", now - 1),
    managedPod("later-succeeds", "in-cluster", "execution", now - 1),
    managedPod("fresh", "in-cluster", "execution", now + 60_000)
  ];
  api.deleteFailures.add("delete-fails");
  api.confirmationFailures.add("confirmation-fails");
  assert.deepEqual(
    await reconcileExpiredPods(api, "execution", "in-cluster", now),
    { deletedNames: ["later-succeeds"], failureCount: 2 }
  );
  assert.deepEqual(api.deleted, ["confirmation-fails", "later-succeeds"]);

  const stalled = new ProfileApi();
  stalled.pods = [
    managedPod("never-settles", "in-cluster", "execution", now - 1),
    managedPod("bounded-later", "in-cluster", "execution", now - 1)
  ];
  stalled.neverDeletes.add("never-settles");
  assert.deepEqual(
    await reconcileExpiredPods(stalled, "execution", "in-cluster", now, 20),
    { deletedNames: ["bounded-later"], failureCount: 1 }
  );
  assert.equal(stalled.activeDeleteRequests, 0);
  assert.equal(stalled.deleteSignals[0]?.aborted, true);
  assert.notEqual(stalled.deleteSignals[0], stalled.deleteSignals[1]);
  assert.deepEqual(
    await reconcileExpiredPods(stalled, "execution", "in-cluster", now, 20),
    { deletedNames: ["bounded-later"], failureCount: 1 }
  );
  assert.equal(stalled.activeDeleteRequests, 0);
  assert.equal(stalled.deleteSignals[2]?.aborted, true);
});

test("startup preflight fails after attempting every reconciliation candidate", async () => {
  const now = Date.now();
  const api = new ProfileApi();
  api.pods = [
    managedPod("first-fails", "in-cluster", "oci-js-execution", now - 1),
    managedPod("second-deletes", "in-cluster", "oci-js-execution", now - 1)
  ];
  api.deleteFailures.add("first-fails");
  const provider = new KubernetesIsolationProvider(
    parseKubernetesConfig(validInClusterEnvironment()),
    api,
    () => undefined
  );
  await assert.rejects(provider.preflight({ startReconciliation: false }), /cleanup/);
  assert.deepEqual(api.deleted, ["second-deletes"]);
});

for (const stage of ["list", "delete"] as const) {
  test(`background reconciliation does not overlap a pending ${stage} and stops idempotently`, async t => {
    t.mock.timers.enable({ apis: ["setInterval"] });
    const gate = Promise.withResolvers<void>();
    const api = new ProfileApi();
    api.pods = stage === "delete"
      ? [managedPod("expired", "in-cluster", "execution", Date.now() - 1)] : [];
    const list = api.listManagedPods.bind(api);
    api.listManagedPods = async (...args) => {
      const pods = await list(...args);
      if (stage === "list" && api.listRequests.length === 1) await gate.promise;
      return pods;
    };
    const remove = api.deletePod.bind(api);
    api.deletePod = async (...args) => {
      if (stage === "delete" && api.deleted.length === 0) await gate.promise;
      await remove(...args);
    };
    const results: Array<ReconciliationSummary | undefined> = [];
    const stop = startExpiryReconciliation(api, "execution", "in-cluster", 10, result => results.push(result));
    t.after(() => { stop(); gate.resolve(); });
    assert.equal(api.listRequests.length, 1, "first cycle must start immediately");
    await new Promise(resolve => setImmediate(resolve));
    t.mock.timers.tick(100);
    assert.equal(api.listRequests.length, 1);
    assert.equal(results.length, 0);
    gate.resolve();
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(results, [{ deletedNames: stage === "delete" ? ["expired"] : [], failureCount: 0 }]);
    t.mock.timers.tick(10);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(api.listRequests.length, 2);
    assert.equal(results.length, 2);
    stop();
    stop();
    t.mock.timers.tick(100);
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(api.listRequests, [
      { namespace: "execution", profile: "in-cluster" },
      { namespace: "execution", profile: "in-cluster" }
    ]);
  });
}

test("background reconciliation recovers from a failed list on the next interval", async t => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const api = new ProfileApi();
  const list = api.listManagedPods.bind(api);
  api.listManagedPods = async (...args) => {
    const pods = await list(...args);
    if (api.listRequests.length === 1) throw new Error("private-list-secret");
    return pods;
  };
  const results: Array<ReconciliationSummary | undefined> = [];
  const stop = startExpiryReconciliation(api, "execution", "in-cluster", 10, result => results.push(result));
  t.after(stop);
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(results, [undefined]);
  t.mock.timers.tick(10);
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(results, [undefined, { deletedNames: [], failureCount: 0 }]);
  assert.deepEqual(api.listRequests, [
    { namespace: "execution", profile: "in-cluster" },
    { namespace: "execution", profile: "in-cluster" }
  ]);
});

test("background reconciliation aborts a stalled list and recovers on the next interval", async t => {
  t.mock.timers.enable({ apis: ["Date", "setTimeout", "setInterval"] });
  const api = new ProfileApi();
  let calls = 0;
  let listSignal: AbortSignal | undefined;
  api.listManagedPods = async (_namespace, _profile, signal?: AbortSignal) => {
    calls += 1;
    if (calls === 1) {
      listSignal = signal;
      return await new Promise<KubernetesPod[]>(() => {});
    }
    return [];
  };
  const results: Array<ReconciliationSummary | undefined> = [];
  const stop = startExpiryReconciliation(api, "execution", "in-cluster", 100, result => results.push(result));
  t.after(stop);
  await new Promise(resolve => setImmediate(resolve));
  t.mock.timers.tick(5000);
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(results, [undefined]);
  assert.equal(listSignal?.aborted, true);
  assert.equal(calls, 1);
  t.mock.timers.tick(100);
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(results, [undefined, { deletedNames: [], failureCount: 0 }]);
  assert.equal(calls, 2);
});

test("background reconciliation stop permits the active cycle to finish without scheduling another", async t => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const gate = Promise.withResolvers<void>();
  const api = new ProfileApi();
  const list = api.listManagedPods.bind(api);
  api.listManagedPods = async (...args) => { await gate.promise; return list(...args); };
  const results: Array<ReconciliationSummary | undefined> = [];
  const stop = startExpiryReconciliation(api, "execution", "in-cluster", 10, result => results.push(result));
  t.after(() => { stop(); gate.resolve(); });
  stop();
  stop();
  t.mock.timers.tick(100);
  gate.resolve();
  await new Promise(resolve => setImmediate(resolve));
  t.mock.timers.tick(100);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(api.listRequests.length, 1);
  assert.deepEqual(results, [{ deletedNames: [], failureCount: 0 }]);
});

class ProfileApi implements KubernetesApi {
  permissions: ResourceAttributes[] = [];
  permission: (attributes: ResourceAttributes) => boolean = () => true;
  pods: KubernetesPod[] = [];
  deleted: string[] = [];
  deleteFailures = new Set<string>();
  confirmationFailures = new Set<string>();
  neverDeletes = new Set<string>();
  activeDeleteRequests = 0;
  deleteSignals: AbortSignal[] = [];
  listRequests: Array<{ namespace: string; profile: KubernetesProfile }> = [];

  async readNamespace() {}
  async selfCan(attributes: ResourceAttributes) {
    this.permissions.push(attributes);
    return this.permission(attributes);
  }
  async createPod() {}
  async waitForPodRunning() {}
  async startRunner(): Promise<never> { throw new Error("unused"); }
  async openTunnel(): Promise<never> { throw new Error("unused"); }
  async deletePod(_namespace: string, name: string, signal?: AbortSignal) {
    assert(signal);
    this.deleteSignals.push(signal);
    if (this.neverDeletes.has(name)) {
      this.activeDeleteRequests += 1;
      return await new Promise<void>((_resolve, reject) => {
        const cancelled = () => {
          this.activeDeleteRequests -= 1;
          reject(new Error("request aborted"));
        };
        signal.addEventListener("abort", cancelled, { once: true });
        if (signal.aborted) {
          cancelled();
        }
      });
    }
    assert.equal(this.activeDeleteRequests, 0);
    if (this.deleteFailures.has(name)) {
      throw new Error("raw delete failure");
    }
    this.deleted.push(name);
  }
  async podExists() { return false; }
  async waitForPodDeleted(
    _namespace: string,
    name: string,
    _deadlineMs: number,
    signal?: AbortSignal
  ) {
    assert(signal);
    return !this.confirmationFailures.has(name);
  }
  async listManagedPods(namespace: string, profile: KubernetesProfile) {
    this.listRequests.push({ namespace, profile });
    return this.pods.map(pod => structuredClone(pod));
  }
}

function samePermission(left: ResourceAttributes, right: ResourceAttributes): boolean {
  return left.group === right.group
    && left.name === right.name
    && left.namespace === right.namespace
    && left.resource === right.resource
    && left.subresource === right.subresource
    && left.verb === right.verb;
}

function managedPod(
  name: string,
  profile: KubernetesProfile,
  namespace: string,
  expiryMs: number
): KubernetesPod {
  return {
    metadata: {
      name,
      namespace,
      labels: {
        [MANAGED_BY_LABEL]: "oci-javascript-mcp",
        [PROVIDER_LABEL]: "kubernetes",
        [PROFILE_LABEL]: profile
      },
      annotations: { [EXPIRY_ANNOTATION]: new Date(expiryMs).toISOString() }
    }
  };
}
