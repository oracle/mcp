/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import test from "node:test";
import type {
  KubernetesApi,
  KubernetesPod,
  ResourceAttributes
} from "../src/isolation/kubernetes-api.ts";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import type { KubernetesDiagnosticEvent } from "../src/isolation/kubernetes-diagnostics.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import {
  EXPIRY_ANNOTATION,
  MANAGED_BY_LABEL,
  PROFILE_LABEL,
  PROVIDER_LABEL
} from "../src/isolation/kubernetes-pod.ts";
import {
  reconcileExpiredPods,
  startExpiryReconciliation
} from "../src/isolation/kubernetes-reconciler.ts";
import type { WorkerChannel, WorkerChannelStatus } from "../src/isolation/worker-channel.ts";
import { FrameDecoder, encodeFrame, protocolMessage } from "../src/protocol.ts";
import { runJavaScript } from "../src/sandbox.ts";
import type { JsonObject, SandboxResult } from "../src/types.ts";
import { conformingPodAdmission, validKataEnvironment } from "./kata-fixtures.ts";

test("Kata preflight validates exact resources, permissions, admission, and descriptor", async () => {
  const api = new FakeKubernetesApi();
  const events: KubernetesDiagnosticEvent[] = [];
  const provider = createProvider(api, events);
  await provider.preflight({ startReconciliation: false });
  assert.equal(provider.descriptor?.provider, "kubernetes");
  assert.equal(provider.descriptor?.profile, "kata-in-cluster");
  assert.deepEqual(provider.descriptor?.externalEvidence, {
    kataGuestKernelRequested: true,
    kataGuestKernelVerified: false,
    criMappingVerified: false,
    nodeRuntimeVerified: false,
    cniIsolationVerified: false,
    pidLimitVerified: false,
    runtimeOverheadVerified: false,
    imageProvenanceVerified: false,
    admissionPolicyRevisionVerified: false
  });
  assert.equal(api.permissions.length, 9);
  assert.equal(api.permissions.some(item => item.resource === "pods" && item.verb === "create"), true);
  assert.equal(api.permissions.some(
    item => item.resource === "pods" && item.subresource === "exec" && item.verb === "create"
  ), true);
  assert.equal(api.permissions.some(
    item => item.resource === "runtimeclasses"
      && item.group === "node.k8s.io"
      && item.name === "kata-qemu-runtime-rs"
  ), true);
  assert.equal(api.permissions.some(
    item => item.resource === "namespaces" && item.name === "oci-js-execution"
  ), true);
  assert.equal(api.permissions.filter(item => item.resource === "pods").every(
    item => item.name === undefined && item.namespace === "oci-js-execution"
  ), true);
  assert.equal(api.dryRunPods.length, 65);
  assert.equal(api.createdPods.length, 0);
  assert.deepEqual(events.map(event => [event.phase, event.outcome]), [
    ["preflight", "started"],
    ["preflight", "succeeded"]
  ]);
  assert.equal(JSON.stringify(events).includes("registry.example"), false);
});

test("Kata preflight fails closed for runtime, authorization, conforming, and unsafe probes", async () => {
  const wrongRuntime = new FakeKubernetesApi();
  wrongRuntime.runtimeHandler = "wrong";
  await assert.rejects(createProvider(wrongRuntime).preflight({ startReconciliation: false }), /runtime_class/);

  const denied = new FakeKubernetesApi();
  denied.permission = attributes => attributes.verb !== "watch";
  await assert.rejects(createProvider(denied).preflight({ startReconciliation: false }), /authorization/);

  const conformingRejected = new FakeKubernetesApi();
  conformingRejected.admission = () => false;
  await assert.rejects(
    createProvider(conformingRejected).preflight({ startReconciliation: false }),
    /admission/
  );

  const unsafeAccepted = new FakeKubernetesApi();
  unsafeAccepted.admission = () => true;
  await assert.rejects(
    createProvider(unsafeAccepted).preflight({ startReconciliation: false }),
    /admission/
  );

  const unavailable = new FakeKubernetesApi();
  unavailable.namespaceError = new Error("https://cluster.internal/token=secret");
  const events: KubernetesDiagnosticEvent[] = [];
  await assert.rejects(
    createProvider(unavailable, events).preflight({ startReconciliation: false }),
    /preflight failed \(api\)/
  );
  assert.equal(JSON.stringify(events).includes("cluster.internal"), false);
});

test("Kata lifecycle creates a fresh pod, exchanges framed RPC, and confirms idempotent deletion", async () => {
  const api = new FakeKubernetesApi();
  const events: KubernetesDiagnosticEvent[] = [];
  const provider = createProvider(api, events);
  await provider.preflight({ startReconciliation: false });
  let rpcCalls = 0;
  const execution = provider.run("40 + 2", {
    ...runOptions(),
    reflectionManifest: { services: {} },
    async hostRpc(request) {
      rpcCalls += 1;
      assert.deepEqual(request, { request: "safe" });
      return { ok: true };
    }
  });
  assert.equal(execution.terminationTimeoutMs, 30_000);
  assert.deepEqual(await execution.result, {
    result: 42,
    error: null,
    stdout: "worker-log",
    stderr: "",
    exitCode: 0,
    timedOut: false
  });
  await Promise.all([execution.terminate(), execution.terminate()]);
  assert.equal(rpcCalls, 1);
  assert.equal(api.createdPods.length, 1);
  assert.equal(api.deletedNames.length, 1);
  assert.equal(api.pods.size, 0);
  assert.deepEqual(events.filter(event => event.outcome === "started").map(event => event.phase), [
    "preflight", "creating", "pending", "running", "connecting", "executing", "closing",
    "deleting", "deleted"
  ]);
});

test("simultaneous Kata executions use unique pods and isolated channels", async () => {
  const api = new FakeKubernetesApi();
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const first = provider.run("first", runOptions());
  const second = provider.run("second", runOptions());
  const [firstResult, secondResult] = await Promise.all([first.result, second.result]);
  assert.equal((firstResult as { result: unknown }).result, 42);
  assert.equal((secondResult as { result: unknown }).result, 42);
  assert.equal(new Set(api.createdPods.map(pod => pod.metadata?.name)).size, 2);
  await Promise.all([first.terminate(), second.terminate()]);
  assert.equal(api.pods.size, 0);
});

test("one cancelled Kata execution does not affect a concurrent execution", async () => {
  const api = new FakeKubernetesApi();
  let channelNumber = 0;
  api.channelFactory = () => ++channelNumber === 1
    ? waitingWorkerChannel()
    : successfulWorkerChannel();
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const cancelledController = new AbortController();
  const cancelled = provider.run("cancelled", {
    ...runOptions(),
    signal: cancelledController.signal
  });
  const successful = provider.run("successful", runOptions());
  await new Promise(resolve => setImmediate(resolve));
  cancelledController.abort();
  const [cancelledResult, successfulResult] = await Promise.all([
    cancelled.result,
    successful.result
  ]) as Array<{ result: unknown; timedOut: boolean }>;
  assert.equal(cancelledResult?.timedOut, true);
  assert.equal(successfulResult?.result, 42);
  await Promise.all([cancelled.terminate(), successful.terminate()]);
  assert.equal(api.pods.size, 0);
});

test("shared coordinator bounds pending OCI work and confirms Kubernetes cleanup", {
  timeout: 4000
}, async () => {
  const api = new FakeKubernetesApi();
  api.channelFactory = () => rpcWorkerChannel([{
    binding: "oracle",
    namespace: "oci",
    operation: "config",
    payload: {}
  }], true, 42);
  const environment = validKataEnvironment();
  environment.OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS = "1";
  const events: KubernetesDiagnosticEvent[] = [];
  const provider = new KubernetesIsolationProvider(
    parseKubernetesConfig(environment),
    api,
    event => events.push(event)
  );
  await provider.preflight({ startReconciliation: false });

  const startedAt = Date.now();
  const result = await runJavaScript("pending", {
    timeoutSeconds: 1,
    isolationProvider: provider,
    async hostRpc() {
      return new Promise(() => undefined);
    }
  });
  const elapsedMs = Date.now() - startedAt;

  assert.deepEqual(result, {
    result: null,
    error: { message: "sandbox run deadline exceeded" },
    stdout: "",
    stderr: "",
    exitCode: -1,
    timedOut: true
  });
  assert(elapsedMs < 2800, `Kubernetes cleanup exceeded one tail after ${elapsedMs}ms`);
  assert.equal(api.deletedNames.length, 1);
  assert.equal(api.pods.size, 0);
  assert.equal(events.some(event => event.phase === "closing"), true);
  assert.equal(events.some(event => event.phase === "deleted" && event.outcome === "succeeded"), true);
});

test("Kata failures and cancellation are sanitized and cleanup remains authoritative", async () => {
  for (const operation of ["create", "wait", "exec"] as const) {
    const api = new FakeKubernetesApi();
    api.failure = operation;
    const provider = createProvider(api);
    await provider.preflight({ startReconciliation: false });
    const execution = provider.run("secret-code", runOptions());
    const result = await execution.result as { error: { message: string }; stdout: string; stderr: string };
    assert.deepEqual(result, {
      result: null,
      error: { message: "isolation provider failed" },
      stdout: "",
      stderr: "",
      exitCode: 1,
      timedOut: false
    });
    await execution.terminate();
  }

  const lost = new FakeKubernetesApi();
  lost.channelFactory = closedWorkerChannel;
  const lostProvider = createProvider(lost);
  await lostProvider.preflight({ startReconciliation: false });
  const lostExecution = lostProvider.run("secret-code", runOptions());
  assert.equal(
    (await lostExecution.result as { error: { message: string } }).error.message,
    "isolation provider failed"
  );
  await lostExecution.terminate();

  const api = new FakeKubernetesApi();
  let releaseCreate!: () => void;
  api.createBarrier = new Promise(resolve => { releaseCreate = resolve; });
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const controller = new AbortController();
  const execution = provider.run("secret-code", {
    ...runOptions(),
    signal: controller.signal
  });
  controller.abort();
  releaseCreate();
  assert.deepEqual(await execution.result, {
    result: null,
    error: { message: "sandbox run deadline exceeded" },
    stdout: "",
    stderr: "",
    exitCode: -1,
    timedOut: true
  });
  await execution.terminate();

  const unconfirmed = new FakeKubernetesApi();
  unconfirmed.preserveAfterDelete = true;
  const cleanupProvider = createProvider(unconfirmed);
  await cleanupProvider.preflight({ startReconciliation: false });
  const cleanupExecution = cleanupProvider.run("1", runOptions());
  await cleanupExecution.result;
  await assert.rejects(cleanupExecution.terminate(), /cleanup failed/);
});

test("Kubernetes pod creation is bounded and late or ambiguous outcomes trigger fresh deletion", async () => {
  const never = new FakeKubernetesApi();
  never.createHonorsAbort = true;
  never.createBarrier = new Promise(() => undefined);
  const neverProvider = createProvider(never);
  await neverProvider.preflight({ startReconciliation: false });
  const startedAt = Date.now();
  const neverExecution = neverProvider.run("never-created", {
    ...runOptions(),
    deadlineMs: Date.now() + 40
  });
  const neverResult = await neverExecution.result as SandboxResult;
  await neverExecution.terminate(Date.now() + 80);
  assert.equal(neverResult.timedOut, true);
  assert.equal(never.createSignals[0]?.aborted, true);
  assert.equal(never.deletedNames.length, 2);
  assert(Date.now() - startedAt < 300, "never-settling creation exceeded its lifecycle bound");

  const late = new FakeKubernetesApi();
  let releaseCreate!: () => void;
  late.createBarrier = new Promise(resolve => { releaseCreate = resolve; });
  const lateProvider = createProvider(late);
  await lateProvider.preflight({ startReconciliation: false });
  const lateExecution = lateProvider.run("late-created", runOptions());
  await new Promise(resolve => setImmediate(resolve));
  const primaryCleanup = lateExecution.terminate(Date.now() + 100);
  const authoritative = structuredClone(await lateExecution.result as SandboxResult);
  await primaryCleanup;
  assert.equal(late.deletedNames.length, 1);
  releaseCreate();
  await waitFor(() => late.deletedNames.length === 2 && late.pods.size === 0);
  assert.equal(late.createdPods.length, 1);
  assert.equal(late.waitForRunningCalls, 0);
  assert.equal(late.openExecCalls, 0);
  assert.deepEqual(await lateExecution.result, authoritative);

  const ambiguous = new FakeKubernetesApi();
  let releaseAmbiguousCreate!: () => void;
  ambiguous.createBarrier = new Promise(resolve => { releaseAmbiguousCreate = resolve; });
  ambiguous.rejectCreateAfterPersist = true;
  const ambiguousProvider = createProvider(ambiguous);
  await ambiguousProvider.preflight({ startReconciliation: false });
  const ambiguousExecution = ambiguousProvider.run("ambiguous-create", runOptions());
  await new Promise(resolve => setImmediate(resolve));
  const ambiguousCleanup = ambiguousExecution.terminate(Date.now() + 100);
  const ambiguousResult = structuredClone(await ambiguousExecution.result as SandboxResult);
  await ambiguousCleanup;
  assert.equal(ambiguous.deletedNames.length, 1);
  releaseAmbiguousCreate();
  await waitFor(() => ambiguous.deletedNames.length === 2 && ambiguous.pods.size === 0);
  assert.equal(ambiguous.createdPods.length, 1);
  assert.equal(ambiguous.waitForRunningCalls, 0);
  assert.equal(ambiguous.openExecCalls, 0);
  assert.deepEqual(await ambiguousExecution.result, ambiguousResult);
});

test("Kubernetes cleanup deletes independently of pending or failed channel stop", async () => {
  const pendingApi = new FakeKubernetesApi();
  let releaseExec!: () => void;
  pendingApi.execBarrier = new Promise(resolve => { releaseExec = resolve; });
  const pendingProvider = createProvider(pendingApi);
  await pendingProvider.preflight({ startReconciliation: false });
  const pendingExecution = pendingProvider.run("pending", runOptions());
  await new Promise(resolve => setImmediate(resolve));
  const pendingTermination = pendingExecution.terminate(Date.now() + 50);
  await waitFor(() => pendingApi.deletedNames.length === 1);
  await assert.rejects(pendingTermination, /cleanup failed/);
  assert.equal(pendingApi.pods.size, 0);
  releaseExec();
  assert.equal((await pendingExecution.result as SandboxResult).timedOut, true);

  for (const channelFactory of [rejectingStopWorkerChannel, neverStoppingWorkerChannel]) {
    const api = new FakeKubernetesApi();
    api.channelFactory = channelFactory;
    const provider = createProvider(api);
    await provider.preflight({ startReconciliation: false });
    const execution = provider.run("cleanup", runOptions());
    await execution.result;
    await assert.rejects(execution.terminate(Date.now() + 50), /cleanup failed/);
    assert.equal(api.deletedNames.length, 1);
    assert.equal(api.pods.size, 0);
  }
});

test("Kubernetes cleanup failures override success and timeout only when cleanup is unconfirmed", async () => {
  const channelFailure = new FakeKubernetesApi();
  channelFailure.channelFactory = rejectingStopWorkerChannel;
  const channelProvider = createProvider(channelFailure);
  await channelProvider.preflight({ startReconciliation: false });
  assert.deepEqual(await runJavaScript("cleanup", {
    isolationProvider: channelProvider,
    async hostRpc() { return null; }
  }), {
    result: null,
    error: { message: "isolation provider cleanup failed" },
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  });
  assert.equal(channelFailure.deletedNames.length, 1);

  const deletionFailure = new FakeKubernetesApi();
  deletionFailure.preserveAfterDelete = true;
  const deletionProvider = createProvider(deletionFailure);
  await deletionProvider.preflight({ startReconciliation: false });
  assert.deepEqual(await runJavaScript("cleanup", {
    isolationProvider: deletionProvider,
    async hostRpc() { return null; }
  }), {
    result: null,
    error: { message: "isolation provider cleanup failed" },
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  });
});

test("abort remains authoritative while pending and while connecting", async () => {
  for (const stage of ["wait", "exec"] as const) {
    const api = new FakeKubernetesApi();
    let release!: () => void;
    const barrier = new Promise<void>(resolve => { release = resolve; });
    if (stage === "wait") {
      api.waitBarrier = barrier;
    } else {
      api.execBarrier = barrier;
    }
    const provider = createProvider(api);
    await provider.preflight({ startReconciliation: false });
    const controller = new AbortController();
    const execution = provider.run(stage, { ...runOptions(), signal: controller.signal });
    await new Promise(resolve => setImmediate(resolve));
    controller.abort();
    release();
    const result = await execution.result as { timedOut: boolean; error: { message: string } };
    assert.equal(result.timedOut, true);
    assert.equal(result.error.message, "sandbox run deadline exceeded");
    await execution.terminate();
  }
});

test("expiry reconciliation deletes only expired managed pods and tolerates overlap", async () => {
  const api = new FakeKubernetesApi();
  const now = Date.now();
  api.seedPod(managedPod("expired", now - 1));
  api.seedPod(managedPod("fresh", now + 60_000));
  api.seedPod(managedPod("malformed", NaN));
  const unrelated = managedPod("unrelated", now - 1);
  unrelated.metadata!.labels![PROVIDER_LABEL] = "podman";
  api.seedPod(unrelated);
  const otherProfile = managedPod("other-profile", now - 1);
  otherProfile.metadata!.labels![PROFILE_LABEL] = "in-cluster";
  api.seedPod(otherProfile);
  assert.deepEqual(
    await reconcileExpiredPods(api, "oci-js-execution", "kata-in-cluster", now),
    { deletedNames: ["expired"], failureCount: 0 }
  );
  assert.equal(api.pods.has("fresh"), true);
  assert.equal(api.pods.has("malformed"), true);
  assert.equal(api.pods.has("unrelated"), true);
  assert.equal(api.pods.has("other-profile"), true);

  let errors = 0;
  api.seedPod(managedPod("periodic", Date.now() - 1));
  const stop = startExpiryReconciliation(
    api,
    "oci-js-execution",
    "kata-in-cluster",
    5,
    summary => {
      if (!summary || summary.failureCount > 0) {
        errors += 1;
      }
    }
  );
  await new Promise(resolve => setTimeout(resolve, 20));
  stop();
  assert.equal(api.pods.has("periodic"), false);
  assert.equal(errors, 0);
});

test("adversarial Kata channels remain under host request, call, concurrency, and result budgets", async () => {
  const baseRequest = (id: number): JsonObject => ({
    binding: "oracle",
    namespace: "oci",
    operation: "invoke",
    payload: { id }
  });

  const concurrentApi = new FakeKubernetesApi();
  concurrentApi.channelFactory = () => rpcWorkerChannel(
    Array.from({ length: 5 }, (_, index) => baseRequest(index)),
    false,
    42
  );
  const concurrentProvider = createProvider(concurrentApi);
  await concurrentProvider.preflight({ startReconciliation: false });
  let inFlight = 0;
  let maximumInFlight = 0;
  let concurrentCalls = 0;
  const concurrentResult = await runJavaScript("adversarial", {
    isolationProvider: concurrentProvider,
    async hostRpc() {
      concurrentCalls += 1;
      inFlight += 1;
      maximumInFlight = Math.max(maximumInFlight, inFlight);
      await new Promise(resolve => setTimeout(resolve, 10));
      inFlight -= 1;
      return null;
    }
  });
  assert.equal(concurrentResult.result, 42);
  assert.equal(concurrentCalls, 4);
  assert.equal(maximumInFlight, 4);

  const budgetApi = new FakeKubernetesApi();
  budgetApi.channelFactory = () => rpcWorkerChannel(
    Array.from({ length: 101 }, (_, index) => baseRequest(index)),
    true,
    42
  );
  const budgetProvider = createProvider(budgetApi);
  await budgetProvider.preflight({ startReconciliation: false });
  let budgetCalls = 0;
  const budgetResult = await runJavaScript("adversarial", {
    isolationProvider: budgetProvider,
    async hostRpc() {
      budgetCalls += 1;
      return null;
    }
  });
  assert.equal(budgetResult.result, 42);
  assert.equal(budgetCalls, 100);

  const oversizedRequestApi = new FakeKubernetesApi();
  oversizedRequestApi.channelFactory = () => rpcWorkerChannel([{
    ...baseRequest(1),
    payload: { value: "x".repeat(1024 * 1024 + 1) }
  }], true, 42);
  const oversizedRequestProvider = createProvider(oversizedRequestApi);
  await oversizedRequestProvider.preflight({ startReconciliation: false });
  let oversizedRequestCalls = 0;
  const oversizedRequestResult = await runJavaScript("adversarial", {
    isolationProvider: oversizedRequestProvider,
    async hostRpc() {
      oversizedRequestCalls += 1;
      return null;
    }
  });
  assert.equal(oversizedRequestResult.error?.message, "sandbox protocol failed");
  assert.equal(oversizedRequestCalls, 0);

  const unsupportedApi = new FakeKubernetesApi();
  unsupportedApi.channelFactory = () => rpcWorkerChannel([{
    binding: "oracle",
    namespace: "oci",
    operation: "invoke",
    payload: { client: { options: { endpoint: "https://forbidden" } } }
  }], true, 42);
  const unsupportedProvider = createProvider(unsupportedApi);
  await unsupportedProvider.preflight({ startReconciliation: false });
  let sdkCalls = 0;
  const unsupportedResult = await runJavaScript("adversarial", {
    isolationProvider: unsupportedProvider,
    async hostRpc(request) {
      if ((request.payload.client as JsonObject | undefined)?.options) {
        throw new Error("unsupported client option");
      }
      sdkCalls += 1;
      return null;
    }
  });
  assert.equal(unsupportedResult.result, 42);
  assert.equal(sdkCalls, 0);

  const oversizedResultApi = new FakeKubernetesApi();
  oversizedResultApi.channelFactory = () => rpcWorkerChannel([], true, "x".repeat(1024 * 1024 + 1));
  const oversizedResultProvider = createProvider(oversizedResultApi);
  await oversizedResultProvider.preflight({ startReconciliation: false });
  const oversizedResult = await runJavaScript("adversarial", {
    isolationProvider: oversizedResultProvider,
    async hostRpc() { return null; }
  });
  assert.equal(oversizedResult.error?.message, "sandbox protocol failed");
});

test("fake Kubernetes raw channel rejects every protocol corruption with one public shape", async () => {
  const recursive = `{"version":1,"type":"log","stream":"stdout","text":"x","extra":${"[".repeat(70)}null${"]".repeat(70)}}`;
  const oversizedHeader = Buffer.alloc(4);
  oversizedHeader.writeUInt32BE((2 * 1024 * 1024) + 1);
  const truncated = Buffer.alloc(7);
  truncated.writeUInt32BE(32);
  truncated.write("bad", 4);
  const hostileFrames = [
    rawJsonFrame("{not-json"),
    rawJsonFrame('{"version":1,"type":"health","status":NaN}'),
    rawJsonFrame('{"version":2,"type":"log","stream":"stdout","text":"x"}'),
    rawJsonFrame('{"version":1,"type":"unknown"}'),
    rawJsonFrame('{"version":1,"type":"log","stream":"stdout","text":"x","extra":true}'),
    rawJsonFrame('{"version":1,"type":"log","stream":"stdout"}'),
    oversizedHeader,
    Buffer.concat([Buffer.from([0, 0, 0, 1]), Buffer.from([0xff])]),
    rawJsonFrame('{"version":1,"type":"rpc","id":1,"request":{"constructor":{}}}'),
    rawJsonFrame(recursive),
    truncated
  ];
  const api = new FakeKubernetesApi();
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  let hostCalls = 0;
  for (const [index, hostileFrame] of hostileFrames.entries()) {
    api.channelFactory = () => rawWorkerChannel(hostileFrame);
    assert.deepEqual(await runJavaScript("hostile", {
      isolationProvider: provider,
      async hostRpc() {
        hostCalls += 1;
        return null;
      }
    }), {
      result: null,
      error: { message: "sandbox protocol failed" },
      stdout: "",
      stderr: "",
      exitCode: 1,
      timedOut: false
    }, `hostile raw frame ${index}`);
  }
  assert.equal(hostCalls, 0);
});

function createProvider(api: FakeKubernetesApi, events: KubernetesDiagnosticEvent[] = []) {
  return new KubernetesIsolationProvider(
    parseKubernetesConfig(validKataEnvironment()),
    api,
    event => events.push(event)
  );
}

function runOptions() {
  return {
    deadlineMs: Date.now() + 5000,
    signal: new AbortController().signal,
    async hostRpc() { return null; },
    channelLimits: testChannelLimits()
  };
}

function testChannelLimits() {
  return Object.freeze({
    maxFrameBytes: 2 * 1024 * 1024,
    maxIngressBytes: 32 * 1024 * 1024,
    maxAcceptedMessages: 128,
    maxLogBytes: 2 * 1024 * 1024,
    maxEgressBytes: 32 * 1024 * 1024,
    maxResultBytes: 1024 * 1024
  });
}

async function waitFor(predicate: () => boolean): Promise<void> {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (predicate()) {
      return;
    }
    await new Promise(resolve => setImmediate(resolve));
  }
  assert.fail("condition was not reached");
}

function managedPod(name: string, expiryMs: number): KubernetesPod {
  return {
    metadata: {
      name,
      namespace: "oci-js-execution",
      labels: {
        [MANAGED_BY_LABEL]: "oci-javascript-mcp",
        [PROVIDER_LABEL]: "kubernetes",
        [PROFILE_LABEL]: "kata-in-cluster"
      },
      annotations: {
        [EXPIRY_ANNOTATION]: Number.isFinite(expiryMs)
          ? new Date(expiryMs).toISOString()
          : "malformed"
      }
    }
  };
}

class FakeKubernetesApi implements KubernetesApi {
  runtimeHandler = "kata-qemu-runtime-rs";
  permission: (attributes: ResourceAttributes) => boolean = () => true;
  admission: (pod: KubernetesPod) => boolean = pod => (
    conformingPodAdmission(pod, "kata-in-cluster")
  );
  namespaceError: Error | undefined;
  failure: "create" | "wait" | "exec" | undefined;
  rejectCreateAfterPersist = false;
  createBarrier: Promise<void> | undefined;
  createHonorsAbort = false;
  waitBarrier: Promise<void> | undefined;
  execBarrier: Promise<void> | undefined;
  preserveAfterDelete = false;
  channelFactory: () => WorkerChannel = successfulWorkerChannel;
  permissions: ResourceAttributes[] = [];
  dryRunPods: KubernetesPod[] = [];
  createdPods: KubernetesPod[] = [];
  createSignals: AbortSignal[] = [];
  waitForRunningCalls = 0;
  openExecCalls = 0;
  deletedNames: string[] = [];
  pods = new Map<string, KubernetesPod>();

  async readNamespace(): Promise<void> {
    if (this.namespaceError) {
      throw this.namespaceError;
    }
  }

  async readRuntimeClass(): Promise<{ handler: string }> {
    return { handler: this.runtimeHandler };
  }

  async selfCan(attributes: ResourceAttributes): Promise<boolean> {
    this.permissions.push(attributes);
    return this.permission(attributes);
  }

  async dryRunCreatePod(_namespace: string, pod: KubernetesPod): Promise<boolean> {
    this.dryRunPods.push(structuredClone(pod));
    return this.admission(pod);
  }

  async createPod(
    _namespace: string,
    pod: KubernetesPod,
    _deadlineMs: number,
    signal: AbortSignal
  ): Promise<void> {
    this.createSignals.push(signal);
    if (this.failure === "create") {
      throw new Error("raw create failure");
    }
    if (this.createBarrier && this.createHonorsAbort) {
      await new Promise<void>((resolve, reject) => {
        const aborted = () => reject(new Error("create aborted"));
        signal.addEventListener("abort", aborted, { once: true });
        if (signal.aborted) {
          aborted();
          return;
        }
        void this.createBarrier!.then(
          () => {
            signal.removeEventListener("abort", aborted);
            resolve();
          },
          reject
        );
      });
    } else {
      await this.createBarrier;
    }
    const copy = structuredClone(pod);
    this.createdPods.push(copy);
    this.pods.set(copy.metadata!.name!, copy);
    if (this.rejectCreateAfterPersist) {
      throw new Error("create response was lost after the pod was persisted");
    }
  }

  async waitForPodRunning(): Promise<void> {
    this.waitForRunningCalls += 1;
    await this.waitBarrier;
    if (this.failure === "wait") {
      throw new Error("raw image pull secret");
    }
  }

  async openExecChannel(): Promise<WorkerChannel> {
    this.openExecCalls += 1;
    await this.execBarrier;
    if (this.failure === "exec") {
      throw new Error("raw websocket endpoint");
    }
    return this.channelFactory();
  }

  async deletePod(_namespace: string, name: string): Promise<void> {
    this.deletedNames.push(name);
    if (!this.preserveAfterDelete) {
      this.pods.delete(name);
    }
  }

  async podExists(_namespace: string, name: string): Promise<boolean> {
    return this.pods.has(name);
  }

  async waitForPodDeleted(_namespace: string, name: string): Promise<boolean> {
    return !this.pods.has(name);
  }

  async listManagedPods(): Promise<KubernetesPod[]> {
    return [...this.pods.values()].map(pod => structuredClone(pod));
  }

  seedPod(pod: KubernetesPod): void {
    this.pods.set(pod.metadata!.name!, structuredClone(pod));
  }
}

function successfulWorkerChannel(): WorkerChannel {
  const input = new PassThrough();
  const output = new PassThrough();
  const decoder = new FrameDecoder();
  let resolve!: (status: WorkerChannelStatus) => void;
  const closed = new Promise<WorkerChannelStatus>(value => { resolve = value; });
  let sentRpc = false;
  input.on("data", chunk => {
    for (const message of decoder.push(chunk)) {
      if (message.type === "execute") {
        sentRpc = true;
        output.write(encodeFrame(protocolMessage("log", { stream: "stdout", text: "worker-log" })));
        output.write(encodeFrame(protocolMessage("rpc", { id: 1, request: { request: "safe" } })));
      } else if (message.type === "rpc_result" && sentRpc) {
        output.write(encodeFrame(protocolMessage("result", {
          result: 42,
          error: null,
          exitCode: 0,
          timedOut: false
        })));
      }
    }
  });
  let stopped: Promise<void> | undefined;
  const channel: WorkerChannel = {
    input,
    output,
    closed,
    stop() {
      return stopped ??= (async () => {
        input.end();
        output.end();
        resolve({ exitCode: 0, signal: null });
      })();
    }
  };
  setImmediate(() => {
    if (!output.writableEnded) {
      output.write(encodeFrame(protocolMessage("health", { status: "ready" })));
    }
  });
  return channel;
}

function rpcWorkerChannel(
  requests: JsonObject[],
  sequential: boolean,
  finalResult: string | number
): WorkerChannel {
  const input = new PassThrough();
  const output = new PassThrough();
  const decoder = new FrameDecoder();
  let resolve!: (status: WorkerChannelStatus) => void;
  const closed = new Promise<WorkerChannelStatus>(value => { resolve = value; });
  let sent = 0;
  let received = 0;
  const sendRequest = () => {
    const request = requests[sent];
    if (request) {
      sent += 1;
      output.write(encodeFrame(protocolMessage("rpc", { id: sent, request })));
    }
  };
  const finish = () => output.write(encodeFrame(protocolMessage("result", {
    result: finalResult,
    error: null,
    exitCode: 0,
    timedOut: false
  })));
  input.on("data", chunk => {
    for (const message of decoder.push(chunk)) {
      if (message.type === "execute") {
        if (requests.length === 0) {
          finish();
        } else if (sequential) {
          sendRequest();
        } else {
          while (sent < requests.length) {
            sendRequest();
          }
        }
      } else if (message.type === "rpc_result") {
        received += 1;
        if (sequential && sent < requests.length) {
          sendRequest();
        } else if (received === requests.length) {
          finish();
        }
      }
    }
  });
  let stopped: Promise<void> | undefined;
  const channel: WorkerChannel = {
    input,
    output,
    closed,
    stop() {
      return stopped ??= (async () => {
        input.end();
        output.end();
        resolve({ exitCode: 0, signal: null });
      })();
    }
  };
  setImmediate(() => {
    if (!output.writableEnded) {
      output.write(encodeFrame(protocolMessage("health", { status: "ready" })));
    }
  });
  return channel;
}

function rawWorkerChannel(hostileFrame: Buffer): WorkerChannel {
  const input = new PassThrough();
  const output = new PassThrough();
  let resolve!: (status: WorkerChannelStatus) => void;
  const closed = new Promise<WorkerChannelStatus>(value => { resolve = value; });
  let stopped: Promise<void> | undefined;
  const channel: WorkerChannel = {
    input,
    output,
    closed,
    stop() {
      return stopped ??= (async () => {
        input.end();
        output.end();
        resolve({ exitCode: 0, signal: null });
      })();
    }
  };
  setImmediate(() => {
    output.end(Buffer.concat([
      encodeFrame(protocolMessage("health", { status: "ready" })),
      hostileFrame
    ]));
    resolve({ exitCode: 0, signal: null });
  });
  return channel;
}

function rawJsonFrame(value: string): Buffer {
  const body = Buffer.from(value);
  const header = Buffer.alloc(4);
  header.writeUInt32BE(body.byteLength);
  return Buffer.concat([header, body]);
}

function waitingWorkerChannel(): WorkerChannel {
  const input = new PassThrough();
  const output = new PassThrough();
  let resolve!: (status: WorkerChannelStatus) => void;
  const closed = new Promise<WorkerChannelStatus>(value => { resolve = value; });
  let stopped: Promise<void> | undefined;
  const channel: WorkerChannel = {
    input,
    output,
    closed,
    stop() {
      return stopped ??= (async () => {
        input.end();
        output.end();
        resolve({ exitCode: null, signal: "stopped" });
      })();
    }
  };
  setImmediate(() => {
    if (!output.writableEnded) {
      output.write(encodeFrame(protocolMessage("health", { status: "ready" })));
    }
  });
  return channel;
}

function closedWorkerChannel(): WorkerChannel {
  const input = new PassThrough();
  const output = new PassThrough();
  const closed = Promise.resolve<WorkerChannelStatus>({ exitCode: null, signal: null });
  return {
    input,
    output,
    closed,
    async stop() {
      input.end();
      output.end();
    }
  };
}

function rejectingStopWorkerChannel(): WorkerChannel {
  const channel = successfulWorkerChannel();
  return {
    ...channel,
    async stop() {
      throw new Error("raw WebSocket close details");
    }
  };
}

function neverStoppingWorkerChannel(): WorkerChannel {
  const channel = successfulWorkerChannel();
  return {
    ...channel,
    async stop() {
      return await new Promise<void>(() => undefined);
    }
  };
}
