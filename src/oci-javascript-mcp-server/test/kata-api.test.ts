/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { getEventListeners } from "node:events";
import test from "node:test";
import {
  HttpMethod,
  RequestContext,
  type ConfigurationOptions,
  type AuthorizationV1Api,
  type CoreV1Api,
  type NodeV1Api,
  type ResponseContext,
  type V1Pod,
  type Watch
} from "@kubernetes/client-node";
import { ClientNodeKubernetesApi, isNotFound } from "../src/isolation/kubernetes-api.ts";

test("client-node adapter maps namespace, RuntimeClass, authorization, create, and list APIs", async () => {
  const harness = apiHarness();
  await harness.api.readNamespace("execution");
  assert.deepEqual(harness.core.readNamespaceCalls, [{ name: "execution" }]);
  assert.deepEqual(await harness.api.readRuntimeClass("kata"), { handler: "kata-handler" });
  assert.equal(await harness.api.selfCan({
    name: "execution",
    resource: "namespaces",
    verb: "get"
  }), true);
  assert.equal(await harness.api.selfCan({
    group: "node.k8s.io",
    name: "kata-runtime",
    resource: "runtimeclasses",
    verb: "get"
  }), true);
  assert.equal(await harness.api.selfCan({
    namespace: "execution",
    resource: "pods",
    verb: "create"
  }), true);
  assert.deepEqual(harness.authorization.reviews.map(review => (
    review.spec.resourceAttributes
  )), [{
    group: "",
    name: "execution",
    namespace: undefined,
    resource: "namespaces",
    subresource: undefined,
    verb: "get"
  }, {
    group: "node.k8s.io",
    name: "kata-runtime",
    namespace: undefined,
    resource: "runtimeclasses",
    subresource: undefined,
    verb: "get"
  }, {
    group: "",
    name: undefined,
    namespace: "execution",
    resource: "pods",
    subresource: undefined,
    verb: "create"
  }]);

  const pod: V1Pod = { metadata: { name: "pod" } };
  assert.equal(await harness.api.dryRunCreatePod("execution", pod), true);
  assert.deepEqual(harness.core.createCalls[0], {
    namespace: "execution",
    body: pod,
    dryRun: "All"
  });
  const createController = new AbortController();
  await harness.api.createPod(
    "execution",
    pod,
    Date.now() + 1000,
    createController.signal
  );
  assert.equal(harness.core.createCalls[1]?.dryRun, undefined);
  assert(harness.core.createOptions[1]);
  assert.deepEqual(
    await harness.api.listManagedPods("execution", "kata-in-cluster"),
    [{ metadata: { name: "listed" } }]
  );
  assert.match(harness.core.listCalls[0]?.labelSelector ?? "", /isolation-provider=kubernetes/);
  assert.match(harness.core.listCalls[0]?.labelSelector ?? "", /kubernetes-profile=kata-in-cluster/);
});

test("client-node admission probes distinguish rejection from API failure", async () => {
  const rejected = apiHarness();
  rejected.core.createError = { statusCode: 422 };
  assert.equal(await rejected.api.dryRunCreatePod("execution", {}), false);

  const forbidden = apiHarness();
  forbidden.core.createError = { response: { statusCode: 403 } };
  assert.equal(await forbidden.api.dryRunCreatePod("execution", {}), false);

  const unavailable = apiHarness();
  unavailable.core.createError = new Error("connection refused");
  await assert.rejects(unavailable.api.dryRunCreatePod("execution", {}), /connection refused/);
});

test("client-node pod creation propagates cancellation and deadline to the HTTP request", async () => {
  const alreadyAborted = apiHarness();
  const aborted = new AbortController();
  aborted.abort();
  await assert.rejects(
    alreadyAborted.api.createPod("execution", {}, Date.now() + 1000, aborted.signal),
    /deadline exceeded/
  );
  assert.equal(alreadyAborted.core.createCalls.length, 0);

  const cancelled = apiHarness();
  let releaseCancelled!: () => void;
  cancelled.core.createBarrier = new Promise(resolve => { releaseCancelled = resolve; });
  const controller = new AbortController();
  const cancellation = cancelled.api.createPod(
    "execution",
    {},
    Date.now() + 1000,
    controller.signal
  );
  await new Promise(resolve => setImmediate(resolve));
  const cancellationSignal = await configuredSignal(cancelled.core.createOptions[0]);
  assert.equal(cancellationSignal?.aborted, false);
  controller.abort();
  assert.equal(cancellationSignal?.aborted, true);
  releaseCancelled();
  await cancellation;

  const expired = apiHarness();
  let releaseExpired!: () => void;
  expired.core.createBarrier = new Promise(resolve => { releaseExpired = resolve; });
  const deadline = expired.api.createPod(
    "execution",
    {},
    Date.now() + 20,
    new AbortController().signal
  );
  await new Promise(resolve => setTimeout(resolve, 30));
  const deadlineSignal = await configuredSignal(expired.core.createOptions[0]);
  assert.equal(deadlineSignal?.aborted, true);
  releaseExpired();
  await deadline;
});

test("client-node pod readiness handles current state, watch state, failure, abort, and watch errors", async () => {
  const running = apiHarness();
  running.core.readPod = { status: { phase: "Running" } };
  await running.api.waitForPodRunning("execution", "pod", Date.now() + 1000, new AbortController().signal);
  assert.equal(running.watch.calls.length, 0);

  const failed = apiHarness();
  failed.core.readPod = { status: { phase: "Failed" } };
  await assert.rejects(
    failed.api.waitForPodRunning("execution", "pod", Date.now() + 1000, new AbortController().signal),
    /failed before running/
  );

  const watched = apiHarness();
  const watchedPromise = watched.api.waitForPodRunning(
    "execution", "pod", Date.now() + 1000, new AbortController().signal
  );
  await new Promise(resolve => setImmediate(resolve));
  watched.watch.emitPod({ status: { phase: "Running" } });
  await watchedPromise;
  assert.equal(watched.watch.abortController.signal.aborted, true);

  const imagePull = apiHarness();
  const imagePullPromise = imagePull.api.waitForPodRunning(
    "execution", "pod", Date.now() + 1000, new AbortController().signal
  );
  await new Promise(resolve => setImmediate(resolve));
  imagePull.watch.emitPod({
    status: { containerStatuses: [{
      name: "runner",
      image: "runner",
      imageID: "",
      ready: false,
      restartCount: 0,
      state: { waiting: { reason: "ImagePullBackOff" } }
    }] }
  });
  await assert.rejects(imagePullPromise, /failed before running/);

  const aborted = apiHarness();
  const controller = new AbortController();
  const abortedPromise = aborted.api.waitForPodRunning(
    "execution", "pod", Date.now() + 1000, controller.signal
  );
  controller.abort();
  await assert.rejects(abortedPromise, /deadline exceeded/);

  const watchError = apiHarness();
  const errorPromise = watchError.api.waitForPodRunning(
    "execution", "pod", Date.now() + 1000, new AbortController().signal
  );
  await new Promise(resolve => setImmediate(resolve));
  watchError.watch.finish(new Error("raw watch details"));
  await assert.rejects(errorPromise, /pod watch failed/);
});

test("client-node readiness rejects normal watch EOF before Running", async () => {
  const harness = apiHarness();
  const ready = harness.api.waitForPodRunning(
    "execution", "pod", Date.now() + 1000, new AbortController().signal
  );
  const rejected = assert.rejects(ready, /Kubernetes pod watch failed/);
  await new Promise(resolve => setImmediate(resolve));
  harness.watch.finish(undefined);
  await rejected;
  assert.equal(harness.watch.abortController.signal.aborted, true);
});

test("client-node readiness does not read after cancellation or expiry", async () => {
  for (const cancelled of [false, true]) {
    const harness = apiHarness();
    harness.core.readPod = { status: { phase: "Running" } };
    const controller = new AbortController();
    if (cancelled) controller.abort();
    await assert.rejects(harness.api.waitForPodRunning(
      "execution", "pod", Date.now() + (cancelled ? 1000 : -1), controller.signal
    ), /deadline exceeded/);
    assert.equal(harness.core.readOptions.length, 0);
    assert.equal(harness.watch.calls.length, 0);
  }
});

for (const cause of ["cancellation", "deadline"] as const) {
  test(`client-node readiness bounds its initial GET on ${cause}`, async t => {
    const harness = apiHarness();
    const controller = new AbortController();
    let release!: () => void;
    harness.core.readBarrier = new Promise(resolve => { release = resolve; });
    harness.core.readPod = { status: { phase: "Running" } };
    t.after(release);
    if (cause === "deadline") t.mock.timers.enable({ apis: ["Date", "setTimeout"] });
    const ready = harness.api.waitForPodRunning(
      "execution", "pod", Date.now() + 1000, controller.signal
    );
    const rejected = assert.rejects(ready, /deadline exceeded/);
    await new Promise(resolve => setImmediate(resolve));
    const requestSignal = await configuredSignal(harness.core.readOptions[0]);
    assert.equal(requestSignal?.aborted, false);
    if (cause === "deadline") t.mock.timers.tick(1001);
    else controller.abort();
    assert.equal(requestSignal?.aborted, true);
    release();
    await rejected;
    assert.equal(harness.watch.calls.length, 0);
    assert.equal(getEventListeners(controller.signal, "abort").length, 0);
  });
}

test("client-node readiness aborts a watch handle delivered after cancellation", async () => {
  const harness = apiHarness();
  let deliver!: (value: AbortController) => void;
  harness.watch.result = new Promise(resolve => { deliver = resolve; });
  const controller = new AbortController();
  const ready = harness.api.waitForPodRunning(
    "execution", "pod", Date.now() + 1000, controller.signal
  );
  const rejected = assert.rejects(ready, /deadline exceeded/);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(harness.watch.calls.length, 1);
  controller.abort();
  await rejected;
  deliver(harness.watch.abortController);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(harness.watch.abortController.signal.aborted, true);
  assert.equal(getEventListeners(controller.signal, "abort").length, 0);
});

test("client-node readiness rejects Running observed after the deadline", async t => {
  t.mock.timers.enable({ apis: ["Date"] });
  const harness = apiHarness();
  const deadlineMs = Date.now() + 1000;
  const controller = new AbortController();
  const ready = harness.api.waitForPodRunning("execution", "pod", deadlineMs, controller.signal);
  const rejected = assert.rejects(ready, /deadline exceeded/);
  await new Promise(resolve => setImmediate(resolve));
  t.mock.timers.setTime(deadlineMs + 1);
  harness.watch.emitPod({ status: { phase: "Running" } });
  await rejected;
  assert.equal(harness.watch.abortController.signal.aborted, true);
  assert.equal(getEventListeners(controller.signal, "abort").length, 0);
});

test("client-node deletion and NotFound confirmation fail closed", async () => {
  const harness = apiHarness();
  await harness.api.deletePod("execution", "pod");
  assert.equal(harness.core.deleteCalls[0]?.gracePeriodSeconds, 0);
  assert.equal(await harness.api.podExists("execution", "pod"), true);

  const deletion = harness.api.waitForPodDeleted("execution", "pod", Date.now() + 1000);
  await new Promise(resolve => setImmediate(resolve));
  harness.watch.emitPod({ metadata: { name: "pod" } }, "DELETED");
  assert.equal(await deletion, true);

  harness.core.readError = { code: 404 };
  assert.equal(await harness.api.podExists("execution", "pod"), false);
  assert.equal(await harness.api.waitForPodDeleted("execution", "pod", Date.now() + 1000), true);
  harness.core.deleteError = { statusCode: 404 };
  await harness.api.deletePod("execution", "missing");

  harness.core.deleteError = new Error("delete denied");
  await assert.rejects(harness.api.deletePod("execution", "pod"), /delete denied/);
  harness.core.readError = new Error("read denied");
  await assert.rejects(harness.api.podExists("execution", "pod"), /read denied/);
  assert.equal(isNotFound(null), false);
  assert.equal(isNotFound({ response: { statusCode: 404 } }), true);
});

test("client-node deletion propagates cancellation to HTTP requests and watches", async () => {
  const harness = apiHarness();
  const controller = new AbortController();
  await harness.api.deletePod("execution", "pod", controller.signal);
  assert.equal(await configuredSignal(harness.core.deleteOptions[0]), controller.signal);
  assert.equal(await harness.api.podExists("execution", "pod", controller.signal), true);
  assert.equal(await configuredSignal(harness.core.readOptions[0]), controller.signal);

  const deletion = harness.api.waitForPodDeleted(
    "execution",
    "pod",
    Date.now() + 1000,
    controller.signal
  );
  await new Promise(resolve => setImmediate(resolve));
  controller.abort();
  await assert.rejects(deletion, /confirmation cancelled/);
  assert.equal(harness.watch.abortController.signal.aborted, true);
  assert.equal(await configuredSignal(harness.core.readOptions[1]), controller.signal);
});

test("client-node deletion confirmation handles every watch completion path", async () => {
  const alreadyCancelled = apiHarness();
  const cancelledController = new AbortController();
  cancelledController.abort();
  await assert.rejects(
    alreadyCancelled.api.waitForPodDeleted(
      "execution", "pod", Date.now() + 1000, cancelledController.signal
    ),
    /confirmation cancelled/
  );
  assert.equal(alreadyCancelled.core.readOptions.length, 0);

  const deleted = apiHarness();
  let deletedSettled = false;
  const deletion = deleted.api.waitForPodDeleted("execution", "pod", Date.now() + 1000)
    .finally(() => { deletedSettled = true; });
  await new Promise(resolve => setImmediate(resolve));
  deleted.watch.emitPod({ metadata: { name: "another-pod" } }, "DELETED");
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(deletedSettled, false);
  deleted.watch.emitPod({ metadata: { name: "pod" } }, "DELETED");
  assert.equal(await deletion, true);

  const notFound = apiHarness();
  const notFoundDeletion = notFound.api.waitForPodDeleted(
    "execution", "pod", Date.now() + 1000
  );
  await new Promise(resolve => setImmediate(resolve));
  notFound.watch.finish({ statusCode: 404 });
  assert.equal(await notFoundDeletion, true);

  const watchError = apiHarness();
  const failedDeletion = watchError.api.waitForPodDeleted(
    "execution", "pod", Date.now() + 1000
  );
  await new Promise(resolve => setImmediate(resolve));
  watchError.watch.finish(new Error("wss://cluster.internal/token=secret"));
  await assert.rejects(failedDeletion, /Kubernetes deletion watch failed/);

  const fallbackGone = apiHarness();
  const fallbackDeletion = fallbackGone.api.waitForPodDeleted(
    "execution", "pod", Date.now() + 1000
  );
  await new Promise(resolve => setImmediate(resolve));
  fallbackGone.core.readError = { code: 404 };
  fallbackGone.watch.finish(undefined);
  assert.equal(await fallbackDeletion, true);

  const fallbackFailed = apiHarness();
  const fallbackFailure = fallbackFailed.api.waitForPodDeleted(
    "execution", "pod", Date.now() + 1000
  );
  await new Promise(resolve => setImmediate(resolve));
  fallbackFailed.core.readError = new Error("raw read failure");
  fallbackFailed.watch.finish(undefined);
  await assert.rejects(fallbackFailure, /Kubernetes deletion confirmation failed/);

  const rejectedWatch = apiHarness();
  rejectedWatch.watch.error = new Error("raw watch setup failure");
  await assert.rejects(
    rejectedWatch.api.waitForPodDeleted("execution", "pod", Date.now() + 1000),
    /Kubernetes deletion watch failed/
  );
});

test("client-node aborts a deletion watch that connects after the result settles", async () => {
  const harness = apiHarness();
  let connect!: (controller: AbortController) => void;
  harness.watch.result = new Promise(resolve => { connect = resolve; });
  const deletion = harness.api.waitForPodDeleted("execution", "pod", Date.now() + 1000);
  await new Promise(resolve => setImmediate(resolve));
  harness.watch.emitPod({ metadata: { name: "pod" } }, "DELETED");
  assert.equal(await deletion, true);
  connect(harness.watch.abortController);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(harness.watch.abortController.signal.aborted, true);
});

test("client-node request middleware preserves responses after attaching cancellation", async () => {
  const harness = apiHarness();
  const controller = new AbortController();
  await harness.api.deletePod("execution", "pod", controller.signal);
  const middleware = harness.core.deleteOptions[0]?.middleware?.[0];
  assert(middleware);
  const response = {} as ResponseContext;
  assert.equal(await middleware.post(response).toPromise(), response);
});

function apiHarness() {
  const core = new FakeCore();
  const node = new FakeNode();
  const authorization = new FakeAuthorization();
  const watch = new FakeWatch();
  return {
    core,
    node,
    authorization,
    watch,
    api: new ClientNodeKubernetesApi(
      core as unknown as CoreV1Api,
      node as unknown as NodeV1Api,
      authorization as unknown as AuthorizationV1Api,
      watch as unknown as Watch,
      {
        startRunner: async () => { throw new Error("unused"); },
        openTunnel: async () => { throw new Error("unused"); }
      }
    )
  };
}

class FakeCore {
  readNamespaceCalls: Array<{ name: string }> = [];
  createCalls: Array<{ namespace: string; body: V1Pod; dryRun?: string }> = [];
  createOptions: Array<ConfigurationOptions | undefined> = [];
  deleteCalls: Array<{ name: string; namespace: string; gracePeriodSeconds?: number }> = [];
  deleteOptions: Array<ConfigurationOptions | undefined> = [];
  readOptions: Array<ConfigurationOptions | undefined> = [];
  listCalls: Array<{ namespace: string; labelSelector?: string }> = [];
  createError: unknown;
  createBarrier: Promise<void> | undefined;
  deleteError: unknown;
  readError: unknown;
  readBarrier: Promise<void> | undefined;
  readPod: V1Pod = { status: { phase: "Pending" } };

  async readNamespace(request: { name: string }) {
    this.readNamespaceCalls.push(request);
    return { metadata: { name: request.name } };
  }

  async createNamespacedPod(
    request: { namespace: string; body: V1Pod; dryRun?: string },
    options?: ConfigurationOptions
  ) {
    this.createCalls.push(request);
    this.createOptions.push(options);
    if (this.createError) {
      throw this.createError;
    }
    await this.createBarrier;
    return request.body;
  }

  async deleteNamespacedPod(
    request: { name: string; namespace: string; gracePeriodSeconds?: number },
    options?: ConfigurationOptions
  ) {
    this.deleteCalls.push(request);
    this.deleteOptions.push(options);
    if (this.deleteError) {
      throw this.deleteError;
    }
    return {};
  }

  async readNamespacedPod(_request?: unknown, options?: ConfigurationOptions) {
    this.readOptions.push(options);
    await this.readBarrier;
    if (this.readError) {
      throw this.readError;
    }
    return this.readPod;
  }

  async listNamespacedPod(request: { namespace: string; labelSelector?: string }) {
    this.listCalls.push(request);
    return { items: [{ metadata: { name: "listed" } }] };
  }
}

async function configuredSignal(options: ConfigurationOptions | undefined): Promise<AbortSignal | undefined> {
  const middleware = options?.middleware?.[0];
  assert(middleware);
  const context = new RequestContext("https://cluster.invalid/pod", HttpMethod.GET);
  return (await middleware.pre(context).toPromise()).getSignal();
}

class FakeNode {
  async readRuntimeClass() {
    return { handler: "kata-handler" };
  }
}

class FakeAuthorization {
  reviews: Array<{ spec: { resourceAttributes?: Record<string, string> } }> = [];

  async createSelfSubjectAccessReview(request: { body: { spec: { resourceAttributes?: Record<string, string> } } }) {
    this.reviews.push(request.body);
    return { status: { allowed: true } };
  }
}

class FakeWatch {
  calls: unknown[] = [];
  abortController = new AbortController();
  result: Promise<AbortController> | undefined;
  error: Error | undefined;
  #callback: ((_phase: string, pod: V1Pod) => void) | undefined;
  #done: ((error: unknown) => void) | undefined;

  async watch(
    path: string,
    query: Record<string, unknown>,
    callback: (_phase: string, pod: V1Pod) => void,
    done: (error: unknown) => void
  ) {
    this.calls.push({ path, query });
    this.#callback = callback;
    this.#done = done;
    if (this.error) {
      throw this.error;
    }
    return await (this.result ?? Promise.resolve(this.abortController));
  }

  emitPod(pod: V1Pod, event = "MODIFIED"): void {
    this.#callback?.(event, pod);
  }

  finish(error: unknown): void {
    this.#done?.(error);
  }
}
