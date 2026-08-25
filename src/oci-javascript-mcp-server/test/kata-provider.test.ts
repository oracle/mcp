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
import type { JsonObject } from "../src/types.ts";
import { validKataEnvironment } from "./kata-fixtures.ts";

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
    imageProvenanceVerified: false
  });
  assert.equal(api.permissions.length, 9);
  assert.equal(api.permissions.some(item => item.resource === "pods" && item.verb === "create"), true);
  assert.equal(api.permissions.some(
    item => item.resource === "pods" && item.subresource === "exec" && item.verb === "create"
  ), true);
  assert.equal(api.permissions.some(
    item => item.resource === "runtimeclasses" && item.group === "node.k8s.io"
  ), true);
  assert.equal(api.dryRunPods.length, 10);
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
    deadlineMs: Date.now() + 5000,
    signal: new AbortController().signal,
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
  await assert.rejects(cleanupExecution.terminate(), /not confirmed/);
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
    ["expired"]
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
    () => { errors += 1; }
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
    async hostRpc() { return null; }
  };
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
  admission: (pod: KubernetesPod) => boolean = safeAdmissionShape;
  namespaceError: Error | undefined;
  failure: "create" | "wait" | "exec" | undefined;
  createBarrier: Promise<void> | undefined;
  waitBarrier: Promise<void> | undefined;
  execBarrier: Promise<void> | undefined;
  preserveAfterDelete = false;
  channelFactory: () => WorkerChannel = successfulWorkerChannel;
  permissions: ResourceAttributes[] = [];
  dryRunPods: KubernetesPod[] = [];
  createdPods: KubernetesPod[] = [];
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

  async createPod(_namespace: string, pod: KubernetesPod): Promise<void> {
    if (this.failure === "create") {
      throw new Error("raw create failure");
    }
    await this.createBarrier;
    const copy = structuredClone(pod);
    this.createdPods.push(copy);
    this.pods.set(copy.metadata!.name!, copy);
  }

  async waitForPodRunning(): Promise<void> {
    await this.waitBarrier;
    if (this.failure === "wait") {
      throw new Error("raw image pull secret");
    }
  }

  async openExecChannel(): Promise<WorkerChannel> {
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

function safeAdmissionShape(pod: KubernetesPod): boolean {
  const container = pod.spec?.containers[0];
  return container?.image?.includes("@sha256:") === true
    && pod.spec?.runtimeClassName === "kata-qemu-runtime-rs"
    && pod.spec.serviceAccountName === "oci-js-runner"
    && pod.spec.automountServiceAccountToken === false
    && pod.spec.hostNetwork === false
    && pod.spec.volumes?.length === 1
    && container.env === undefined
    && container.command?.[0] === "node"
    && container.securityContext?.allowPrivilegeEscalation === false;
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
