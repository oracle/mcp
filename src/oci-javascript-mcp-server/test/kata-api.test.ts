/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import test from "node:test";
import type {
  AuthorizationV1Api,
  CoreV1Api,
  Exec,
  NodeV1Api,
  V1Pod,
  V1Status,
  Watch
} from "@kubernetes/client-node";
import { ClientNodeKubernetesApi, isNotFound } from "../src/isolation/kubernetes-api.ts";

test("client-node adapter maps namespace, RuntimeClass, authorization, create, and list APIs", async () => {
  const harness = apiHarness();
  await harness.api.readNamespace("execution");
  assert.deepEqual(harness.core.readNamespaceCalls, [{ name: "execution" }]);
  assert.deepEqual(await harness.api.readRuntimeClass("kata"), { handler: "kata-handler" });
  assert.equal(await harness.api.selfCan({
    group: "",
    namespace: "execution",
    resource: "pods",
    verb: "create"
  }), true);
  assert.equal(harness.authorization.reviews[0]?.spec.resourceAttributes?.namespace, "execution");

  const pod: V1Pod = { metadata: { name: "pod" } };
  assert.equal(await harness.api.dryRunCreatePod("execution", pod), true);
  assert.deepEqual(harness.core.createCalls[0], {
    namespace: "execution",
    body: pod,
    dryRun: "All"
  });
  await harness.api.createPod("execution", pod);
  assert.equal(harness.core.createCalls[1]?.dryRun, undefined);
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

test("client-node exec adapts non-TTY streams, bounds stderr, reports status, and stops idempotently", async () => {
  const harness = apiHarness();
  const channel = await harness.api.openExecChannel("execution", "pod");
  assert.equal(harness.exec.calls[0]?.tty, false);
  assert.deepEqual(harness.exec.calls[0]?.command, [
    "node", "--no-node-snapshot", "--experimental-strip-types", "/app/src/sandbox-worker.ts"
  ]);
  let output = "";
  channel.output.on("data", chunk => { output += chunk.toString("utf8"); });
  harness.exec.calls[0]!.stdout.write("worker");
  harness.exec.calls[0]!.stderr.write(Buffer.alloc(128 * 1024));
  assert.equal(output, "worker");
  harness.exec.calls[0]!.status({
    details: { causes: [{ reason: "ExitCode", message: "7" }] }
  });
  assert.deepEqual(await channel.closed, { exitCode: 7, signal: null });
  await Promise.all([channel.stop(), channel.stop()]);
  assert.equal(harness.exec.webSocket.closeCalls, 1);

  const errored = apiHarness();
  const errorChannel = await errored.api.openExecChannel("execution", "pod");
  errored.exec.webSocket.emit("error", new Error("raw websocket"));
  await assert.rejects(errorChannel.closed, /exec channel failed/);
  await errorChannel.stop();
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

function apiHarness() {
  const core = new FakeCore();
  const node = new FakeNode();
  const authorization = new FakeAuthorization();
  const watch = new FakeWatch();
  const exec = new FakeExec();
  return {
    core,
    node,
    authorization,
    watch,
    exec,
    api: new ClientNodeKubernetesApi(
      core as unknown as CoreV1Api,
      node as unknown as NodeV1Api,
      authorization as unknown as AuthorizationV1Api,
      watch as unknown as Watch,
      exec as unknown as Exec
    )
  };
}

class FakeCore {
  readNamespaceCalls: Array<{ name: string }> = [];
  createCalls: Array<{ namespace: string; body: V1Pod; dryRun?: string }> = [];
  deleteCalls: Array<{ name: string; namespace: string; gracePeriodSeconds?: number }> = [];
  listCalls: Array<{ namespace: string; labelSelector?: string }> = [];
  createError: unknown;
  deleteError: unknown;
  readError: unknown;
  readPod: V1Pod = { status: { phase: "Pending" } };

  async readNamespace(request: { name: string }) {
    this.readNamespaceCalls.push(request);
    return { metadata: { name: request.name } };
  }

  async createNamespacedPod(request: { namespace: string; body: V1Pod; dryRun?: string }) {
    this.createCalls.push(request);
    if (this.createError) {
      throw this.createError;
    }
    return request.body;
  }

  async deleteNamespacedPod(request: { name: string; namespace: string; gracePeriodSeconds?: number }) {
    this.deleteCalls.push(request);
    if (this.deleteError) {
      throw this.deleteError;
    }
    return {};
  }

  async readNamespacedPod() {
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
    return this.abortController;
  }

  emitPod(pod: V1Pod, event = "MODIFIED"): void {
    this.#callback?.(event, pod);
  }

  finish(error: unknown): void {
    this.#done?.(error);
  }
}

class FakeWebSocket extends EventEmitter {
  readyState = 1;
  readonly CLOSING = 2;
  closeCalls = 0;

  close(): void {
    this.closeCalls += 1;
    this.readyState = 3;
    this.emit("close");
  }
}

class FakeExec {
  webSocket = new FakeWebSocket();
  calls: Array<{
    namespace: string;
    name: string;
    command: string[];
    stdout: NodeJS.WritableStream;
    stderr: NodeJS.WritableStream;
    stdin: NodeJS.ReadableStream;
    tty: boolean;
    status: (status: V1Status) => void;
  }> = [];

  async exec(
    namespace: string,
    name: string,
    _container: string,
    command: string[],
    stdout: NodeJS.WritableStream,
    stderr: NodeJS.WritableStream,
    stdin: NodeJS.ReadableStream,
    tty: boolean,
    status: (value: V1Status) => void
  ) {
    this.calls.push({ namespace, name, command, stdout, stderr, stdin, tty, status });
    return this.webSocket;
  }
}
