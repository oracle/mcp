/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { EventEmitter, getEventListeners, once } from "node:events";
import { connect } from "node:net";
import test from "node:test";
import { Server, ServerCredentials } from "@grpc/grpc-js";
import { RUNNER_SERVICE } from "../src/grpc.ts";
import type { RunnerTlsBootstrap } from "../src/grpc-tls.ts";
import type {
  KubernetesApi,
  KubernetesPod,
  ResourceAttributes
} from "../src/isolation/kubernetes-api.ts";
import { ClientNodeKubernetesApi } from "../src/isolation/kubernetes-api.ts";
import type {
  KubernetesGrpcTunnel,
  KubernetesRunnerHandle
} from "../src/isolation/kubernetes-grpc.ts";
import { ClientNodeKubernetesGrpcTransport } from "../src/isolation/kubernetes-grpc.ts";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import type { RunnerServer } from "../src/generated/runner.ts";
import type { SandboxResult } from "../src/types.ts";
import { runJavaScript } from "../src/sandbox.ts";
import { conformingPodAdmission, validKataEnvironment } from "./kata-fixtures.ts";
import { StartupKubernetesApi, StartupWebSocket } from "./kubernetes-startup-fixture.ts";

test("Kata preflight requires exec and port-forward only on the trusted host", async () => {
  const api = new FakeKubernetesApi();
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  assert.equal(provider.descriptor?.profile, "kata-in-cluster");
  for (const subresource of ["exec", "portforward"]) {
    for (const verb of ["create", "get"]) {
      assert(api.permissions.some(permission =>
        permission.resource === "pods"
        && permission.subresource === subresource
        && permission.verb === verb
      ));
    }
  }
  assert.equal(api.createdPods.length, 0);
});

test("Kubernetes never starts a runner after readiness watch EOF", async () => {
  const api = new FakeKubernetesApi();
  const adapter = new ClientNodeKubernetesApi(
    { readNamespacedPod: async () => ({ status: { phase: "Pending" } }) } as unknown as
      ConstructorParameters<typeof ClientNodeKubernetesApi>[0],
    {} as ConstructorParameters<typeof ClientNodeKubernetesApi>[1],
    {} as ConstructorParameters<typeof ClientNodeKubernetesApi>[2],
    { watch: async (_path: string, _query: unknown, _event: unknown, done: () => void) => {
      done();
      return new AbortController();
    } } as unknown as ConstructorParameters<typeof ClientNodeKubernetesApi>[3],
    {} as ConstructorParameters<typeof ClientNodeKubernetesApi>[4]
  );
  api.waitForPodRunning = (...args: Parameters<KubernetesApi["waitForPodRunning"]>) =>
    adapter.waitForPodRunning(...args);
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const execution = provider.run("42", runOptions());
  assert.equal((await execution.result).error?.message, "isolation provider failed");
  assert.deepEqual(api.lifecycle, ["create"]);
  await execution.terminate();
  assert.equal(api.pods.size, 0);
});

test("Kubernetes preflight starts reconciliation and stop prevents later cycles", async t => {
  t.mock.timers.enable({ apis: ["setInterval"] });
  const api = new FakeKubernetesApi();
  const list = t.mock.method(api, "listManagedPods");
  const provider = createProvider(api);
  t.after(() => provider.stopReconciliation());
  await provider.preflight();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(list.mock.callCount(), 2, "preflight sweep and immediate background cycle");
  t.mock.timers.tick(60_000);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(list.mock.callCount(), 3);
  provider.stopReconciliation();
  provider.stopReconciliation();
  t.mock.timers.tick(120_000);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(list.mock.callCount(), 3);
});

test("Kubernetes cleanup starts every resource concurrently with one deadline and is idempotent", async () => {
  const api = new FakeKubernetesApi();
  const runnerStop = deferred<void>();
  const tunnelStop = deferred<void>();
  const confirmation = deferred<void>();
  api.runnerStopGate = runnerStop.promise;
  api.tunnelStopGate = tunnelStop.promise;
  api.confirmationGate = confirmation.promise;
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const options = runOptions();
  const execution = provider.run("40 + 2", options);
  const result = await execution.result;
  assert.deepEqual(result, successResult(42));
  assert.deepEqual(api.lifecycle, ["create", "running", "runner", "tunnel", "grpc"]);
  const firstStop = once(api.cleanupEvents, "tunnel-stop");
  const deadlineMs = Date.now() + 1000;
  const cleanup = execution.terminate(deadlineMs);
  assert.equal(execution.terminate(deadlineMs + 10_000), cleanup);
  let finished = false;
  void cleanup.then(() => { finished = true; }, () => { finished = true; });
  try {
    await firstStop;
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(api.lifecycle.slice(5).sort(), ["confirm", "delete", "runner-stop", "tunnel-stop"]);
    assert.deepEqual(api.cleanupDeadlines.sort((a, b) => a.resource.localeCompare(b.resource)), [
      { resource: "confirm", deadlineMs },
      { resource: "runner", deadlineMs },
      { resource: "tunnel", deadlineMs }
    ]);
    assert.equal(finished, false);
    assert.equal(api.pods.size, 0);
  } finally {
    runnerStop.resolve();
    tunnelStop.resolve();
    confirmation.resolve();
    await cleanup;
  }
  assert.equal(execution.terminate(), cleanup);
  assert.equal(getEventListeners(options.signal, "abort").length, 0);
  assert.equal(api.pods.size, 0);
  assert.equal(execution.terminationTimeoutMs, 30_000);
});

test("Kubernetes confirms pod deletion while a real runner websocket is stuck CLOSING", async () => {
  const api = new StartupKubernetesApi();
  // Keep the actual returned transport handle; only the external exec API is fake.
  api.startRunner = (...args) => api.transport.startRunner(...args);
  api.openTunnel = async () => { throw new Error("private tunnel failure"); };
  let deletionConfirmed = false;
  const waitForPodDeleted = api.waitForPodDeleted.bind(api);
  api.waitForPodDeleted = async () => {
    deletionConfirmed = await waitForPodDeleted();
    return deletionConfirmed;
  };
  const provider = new KubernetesIsolationProvider(
    parseKubernetesConfig(validKataEnvironment()), api, () => undefined
  );
  await provider.preflight({ startReconciliation: false });
  const execution = provider.run("42", runOptions());
  assert.equal((await execution.result).error?.message, "isolation provider failed");
  api.websocket.readyState = api.websocket.CLOSING;
  const stopping = once(api.output, "close");
  const deadlineMs = Date.now() + 1000;
  const cleanup = execution.terminate(deadlineMs);
  const rejected = assert.rejects(cleanup, /Kubernetes execution cleanup failed/);
  let settled = false;
  void cleanup.then(() => { settled = true; }, () => { settled = true; });
  try {
    await stopping;
    assert.equal(api.deleted, true, "pod deletion waited for runner closure");
    assert.equal(deletionConfirmed, true, "NotFound confirmation waited for runner closure");
    assert(Date.now() < deadlineMs, "deletion consumed the cleanup allowance");
    assert.equal(api.websocket.readyState, api.websocket.CLOSING);
    assert.equal(settled, false);
    assert.equal(execution.terminate(deadlineMs + 10_000), cleanup);
    await rejected;
    assert.equal(api.deleted, true);
  } finally {
    await rejected;
    api.websocket.readyState = 3;
    api.websocket.emit("close");
  }
});

test("Kubernetes confirms pod deletion while a real tunnel websocket is stuck CLOSING", async t => {
  const api = new StartupKubernetesApi();
  const websocket = new StartupWebSocket();
  websocket.close = () => { websocket.readyState = websocket.CLOSING; };
  const acquired = Promise.withResolvers<void>();
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => assert.fail("unused exec") }),
    () => ({ portForward: async () => { acquired.resolve(); return websocket as never; } })
  );
  let client: ReturnType<typeof connect> | undefined;
  api.openTunnel = async () => {
    const tunnel = await transport.openTunnel("execution", "pod", 50051, Date.now() + 5000, new AbortController().signal);
    const [host, port] = tunnel.address.split(":");
    client = connect(Number(port), host);
    client.on("error", () => {});
    await once(client, "connect");
    await acquired.promise;
    await new Promise(resolve => setImmediate(resolve));
    api.failRunner("error");
    return tunnel;
  };
  const provider = new KubernetesIsolationProvider(parseKubernetesConfig(validKataEnvironment()), api, () => undefined);
  await provider.preflight({ startReconciliation: false });
  const execution = provider.run("42", runOptions());
  assert.equal((await execution.result).error?.message, "isolation provider failed");
  t.mock.timers.enable({ apis: ["Date", "setTimeout"] });
  const cleanup = execution.terminate(Date.now() + 1000);
  const rejected = assert.rejects(cleanup, /Kubernetes execution cleanup failed/);
  let finished = false;
  void cleanup.then(() => { finished = true; }, () => { finished = true; });
  t.after(() => { client?.destroy(); websocket.readyState = 3; websocket.emit("close"); });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(api.deleted, true);
  assert.equal(await api.waitForPodDeleted(), true);
  assert.equal(websocket.readyState, websocket.CLOSING);
  assert.equal(finished, false);
  t.mock.timers.tick(1000);
  await rejected;
});

for (const resource of ["runner", "tunnel"] as const) {
  test(`Kubernetes deletes independently of unresolved ${resource} acquisition`, async () => {
    const api = new FakeKubernetesApi();
    const acquisition = deferred<void>();
    const requested = deferred<void>();
    if (resource === "runner") {
      const original = api.startRunner.bind(api);
      api.startRunner = async (...args) => {
        const handle = await original(...args);
        requested.resolve();
        await acquisition.promise;
        return handle;
      };
    } else {
      const original = api.openTunnel.bind(api);
      api.openTunnel = async (...args) => {
        const handle = await original(...args);
        requested.resolve();
        await acquisition.promise;
        return handle;
      };
    }
    const provider = createProvider(api);
    await provider.preflight({ startReconciliation: false });
    const options = runOptions();
    const execution = provider.run("42", options);
    await requested.promise;
    const deleted = once(api.cleanupEvents, "confirm");
    const deadlineMs = Date.now() + 1000;
    const cleanup = execution.terminate(deadlineMs);
    const rejected = assert.rejects(cleanup, /cleanup failed/);
    try {
      await Promise.race([deleted, cleanup.catch(() => undefined)]);
      assert.equal(api.pods.size, 0, "pending acquisition skipped pod deletion");
      assert(api.lifecycle.includes("confirm"));
      assert(Date.now() < deadlineMs, "deletion waited for acquisition deadline");
      if (resource === "tunnel") assert(api.lifecycle.includes("runner-stop"));
      await rejected;
    } finally {
      await rejected;
      acquisition.resolve();
      await new Promise(resolve => setImmediate(resolve));
      assert.equal(api.lifecycle.filter(event => event === `${resource}-stop`).length, 1);
      assert(api.cleanupDeadlines.some(item => item.resource === resource && item.deadlineMs === deadlineMs));
      assert.equal((await execution.result).timedOut, true);
      assert.equal(getEventListeners(options.signal, "abort").length, 0);
    }
  });
}

test("Kubernetes collects pending cleanup outcomes after an immediate stop failure", async () => {
  const api = new FakeKubernetesApi();
  const tunnelStop = deferred<void>();
  api.tunnelStopGate = tunnelStop.promise;
  api.cleanupFailure = "runner-stop";
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const execution = provider.run("42", runOptions());
  assert.deepEqual(await execution.result, successResult(42));
  const tunnelStopping = once(api.cleanupEvents, "tunnel-stop");
  const cleanup = execution.terminate(Date.now() + 1000);
  const rejected = assert.rejects(cleanup, /cleanup failed/);
  let settled = false;
  void cleanup.then(() => { settled = true; }, () => { settled = true; });
  try {
    await tunnelStopping;
    await new Promise(resolve => setImmediate(resolve));
    assert(api.lifecycle.includes("runner-stop"));
    assert(api.lifecycle.includes("confirm"));
    assert.equal(api.pods.size, 0);
    assert.equal(settled, false, "cleanup returned before collecting the pending stop");
  } finally {
    tunnelStop.resolve();
    await rejected;
  }
});

for (const timing of ["during", "after"] as const) {
  test(`Kubernetes compensates for pod creation settling ${timing} primary cleanup`, async () => {
    const api = new FakeKubernetesApi();
    const creation = deferred<void>();
    const requested = deferred<void>();
    const created = deferred<void>();
    const confirmation = deferred<void>();
    if (timing === "during") api.confirmationGate = confirmation.promise;
    const original = api.createPod.bind(api);
    api.createPod = async (...args) => {
      requested.resolve();
      await creation.promise;
      await original(...args);
      created.resolve();
    };
    const provider = createProvider(api);
    await provider.preflight({ startReconciliation: false });
    const execution = provider.run("42", runOptions());
    await requested.promise;
    const primaryDeleted = once(api.cleanupEvents, "confirm");
    const cleanup = execution.terminate(Date.now() + 1000);
    const outcome = timing === "during"
      ? assert.rejects(cleanup, /cleanup failed/)
      : cleanup;
    await primaryDeleted;
    if (timing === "after") await outcome;
    const lateDeleted = once(api.cleanupEvents, "confirm");
    creation.resolve();
    await created.promise;
    await new Promise(resolve => setImmediate(resolve));
    confirmation.resolve();
    await outcome;
    await lateDeleted;
    assert.equal(api.createdPods.length, 1);
    assert.equal(api.pods.size, 0);
    assert.equal(api.lifecycle.filter(event => event === "delete").length, 2);
    assert.equal(api.lifecycle.includes("runner"), false);
    assert.equal((await execution.result).timedOut, true);
  });
}

for (const failure of ["runner-stop", "tunnel-stop", "delete", "confirm"] as const) {
  test(`Kubernetes ${failure} failure remains authoritative after successful execution`, async () => {
    const api = new FakeKubernetesApi();
    api.cleanupFailure = failure;
    const provider = createProvider(api);
    await provider.preflight({ startReconciliation: false });
    const result = await runJavaScript("42", {
      isolationProvider: provider,
      hostRpc: async () => null
    });
    assert.equal(result.error?.message, "isolation provider cleanup failed");
    assert.equal(result.exitCode, 1);
    assert.equal(result.result, null);
    for (const event of ["grpc", "runner-stop", "tunnel-stop", "delete"]) {
      assert.equal(api.lifecycle.filter(value => value === event).length, 1, `${event} was not attempted once`);
    }
    assert.equal(api.lifecycle.includes("confirm"), failure !== "delete");
  });
}

test("simultaneous Kubernetes executions use unique pods and TLS identities", async () => {
  const api = new FakeKubernetesApi();
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const first = provider.run("first", runOptions());
  const second = provider.run("second", runOptions());
  const results = await Promise.all([first.result, second.result]);
  assert.deepEqual(results.map(result => result.result), [42, 42]);
  assert.equal(new Set(api.createdPods.map(pod => pod.metadata?.name)).size, 2);
  assert.equal(new Set(api.clientCertificates).size, 2);
  await Promise.all([first.terminate(), second.terminate()]);
  assert.equal(api.pods.size, 0);
});

test("Kubernetes startup failures are sanitized and pod cleanup remains authoritative", async () => {
  for (const failure of ["create", "running", "runner", "tunnel"] as const) {
    const api = new FakeKubernetesApi();
    api.failure = failure;
    const provider = createProvider(api);
    await provider.preflight({ startReconciliation: false });
    const execution = provider.run("secret", runOptions());
    assert.deepEqual(await execution.result, {
      result: null,
      error: { message: "isolation provider failed" },
      stdout: "",
      stderr: "",
      exitCode: 1,
      timedOut: false
    });
    await execution.terminate();
    assert.equal(api.pods.size, 0);
  }
});

test("Kubernetes cancellation returns a timeout result and deletes the pod", async () => {
  const api = new FakeKubernetesApi();
  api.holdGrpc = true;
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const controller = new AbortController();
  const execution = provider.run("wait", { ...runOptions(), signal: controller.signal });
  while (!api.lifecycle.includes("grpc")) await new Promise(resolve => setImmediate(resolve));
  controller.abort();
  const result = await execution.result;
  assert.equal(result.timedOut, true);
  assert.equal(result.error?.message, "sandbox run deadline exceeded");
  await execution.terminate();
  assert.equal(api.pods.size, 0);
});

for (const fault of ["output", "error", "exit"] as const) {
  test(`Kubernetes runner ${fault} fails while tunnel creation is pending`, async () => {
    const api = new StartupKubernetesApi();
    const phases: string[] = [];
    const provider = new KubernetesIsolationProvider(
      parseKubernetesConfig(validKataEnvironment()), api, event => {
        if (event.outcome === "started") phases.push(event.phase);
      }
    );
    await provider.preflight({ startReconciliation: false });
    const execution = provider.run("42", runOptions());
    while (!api.resolveTunnel) await new Promise(resolve => setImmediate(resolve));
    api.failRunner(fault);
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      const result = await Promise.race([
        execution.result,
        new Promise<never>((_resolve, reject) => {
          timer = setTimeout(() => reject(new Error("runner failure did not settle pending tunnel")), 500);
        })
      ]);
      assert.equal(result.error?.message, "isolation provider failed");
      assert.equal(result.timedOut, false);
    } finally {
      clearTimeout(timer);
      const cleanupDeadlineMs = Date.now() + 1000;
      const cleanup = execution.terminate(cleanupDeadlineMs);
      api.resolveTunnel();
      await cleanup;
      await execution.result;
      assert.deepEqual(api.stopped.sort((a, b) => a.resource.localeCompare(b.resource)), [
        { resource: "runner", deadlineMs: cleanupDeadlineMs },
        { resource: "tunnel", deadlineMs: cleanupDeadlineMs }
      ]);
      assert.equal(api.deleted, true);
      assert.equal(phases.includes("executing"), false);
    }
  });
}

for (const resource of ["runner", "tunnel"] as const) {
  test(`Kubernetes stops a ${resource} delivered after termination deadline`, async () => {
    const api = new StartupKubernetesApi();
    api.holdRunner = resource === "runner";
    const provider = new KubernetesIsolationProvider(
      parseKubernetesConfig(validKataEnvironment()), api, () => undefined
    );
    await provider.preflight({ startReconciliation: false });
    const controller = new AbortController();
    const execution = provider.run("42", { ...runOptions(), signal: controller.signal });
    while (resource === "runner" ? !api.resolveRunner : !api.resolveTunnel) {
      await new Promise(resolve => setImmediate(resolve));
    }
    controller.abort();
    const cleanupDeadlineMs = Date.now() + 30;
    await assert.rejects(execution.terminate(cleanupDeadlineMs), /cleanup failed/);
    if (resource === "runner") {
      api.failRunner("error");
      api.resolveRunner!();
    }
    else api.resolveTunnel!();
    await new Promise(resolve => setImmediate(resolve));
    assert(api.stopped.some(item => item.resource === resource && item.deadlineMs === cleanupDeadlineMs));
    assert.equal((await execution.result).timedOut, true);
    assert.equal(api.tunnelStarted, resource === "tunnel");
  });
}

test("Kubernetes runner exit before final gRPC status rejects a result frame", async () => {
  const api = new FakeKubernetesApi();
  api.holdFinalStatus = true;
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const execution = provider.run("42", runOptions());
  while (!api.lifecycle.includes("grpc")) await new Promise(resolve => setImmediate(resolve));
  api.closeRunner!();
  const result = await execution.result;
  assert.equal(result.error?.message, "isolation provider failed");
  assert.equal(result.timedOut, false);
  await execution.terminate();
  assert.equal(api.pods.size, 0);
});

test("Kubernetes preserves a valid final gRPC status when lifecycle promises reject later", async () => {
  const api = new FakeKubernetesApi();
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const execution = provider.run("42", runOptions());
  assert.deepEqual(await execution.result, successResult(42));
  api.failRunner!();
  api.failTunnel!();
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(await execution.result, successResult(42));
  await execution.terminate();
  assert.equal(api.pods.size, 0);
});

function createProvider(api: FakeKubernetesApi): KubernetesIsolationProvider {
  return new KubernetesIsolationProvider(
    parseKubernetesConfig(validKataEnvironment()),
    api,
    () => undefined
  );
}

function runOptions() {
  return {
    deadlineMs: Date.now() + 10_000,
    signal: new AbortController().signal,
    hostRpc: async () => null,
    reflectionManifest: { services: {} }
  };
}

function successResult(result: number): SandboxResult {
  return {
    result,
    error: null,
    stdout: "",
    stderr: "",
    exitCode: 0,
    timedOut: false
  };
}

function deferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  const promise = new Promise<T>(value => { resolve = value; });
  return { promise, resolve };
}

class FakeKubernetesApi implements KubernetesApi {
  permissions: ResourceAttributes[] = [];
  createdPods: KubernetesPod[] = [];
  pods = new Map<string, KubernetesPod>();
  lifecycle: string[] = [];
  clientCertificates: string[] = [];
  failure: "create" | "running" | "runner" | "tunnel" | undefined;
  holdGrpc = false;
  holdFinalStatus = false;
  readonly cleanupEvents = new EventEmitter();
  readonly cleanupDeadlines: Array<{ resource: string; deadlineMs: number }> = [];
  runnerStopGate: Promise<void> | undefined;
  tunnelStopGate: Promise<void> | undefined;
  confirmationGate: Promise<void> | undefined;
  cleanupFailure: "runner-stop" | "tunnel-stop" | "delete" | "confirm" | undefined;
  closeRunner: (() => void) | undefined;
  failRunner: (() => void) | undefined;
  failTunnel: (() => void) | undefined;
  #bootstraps = new Map<string, RunnerTlsBootstrap>();
  #servers = new Map<string, Server>();

  async readNamespace(): Promise<void> {}
  async readRuntimeClass(): Promise<{ handler: string }> {
    return { handler: "kata-qemu-runtime-rs" };
  }
  async selfCan(attributes: ResourceAttributes): Promise<boolean> {
    this.permissions.push(attributes);
    return true;
  }
  async dryRunCreatePod(_namespace: string, pod: KubernetesPod): Promise<boolean> {
    return conformingPodAdmission(pod, "kata-in-cluster");
  }
  async createPod(_namespace: string, pod: KubernetesPod): Promise<void> {
    this.lifecycle.push("create");
    if (this.failure === "create") throw new Error("private create failure");
    const copy = structuredClone(pod);
    this.createdPods.push(copy);
    this.pods.set(copy.metadata!.name!, copy);
  }
  async waitForPodRunning(
    _namespace: string, _name: string, _deadlineMs: number, _signal: AbortSignal
  ): Promise<void> {
    this.lifecycle.push("running");
    if (this.failure === "running") throw new Error("private image failure");
  }
  async startRunner(
    _namespace: string,
    podName: string,
    bootstrap: RunnerTlsBootstrap
  ): Promise<KubernetesRunnerHandle> {
    this.lifecycle.push("runner");
    if (this.failure === "runner") throw new Error("private exec failure");
    this.#bootstraps.set(podName, bootstrap);
    this.clientCertificates.push(bootstrap.clientCert);
    let resolve!: (status: { exitCode: number | null; signal: string | null }) => void;
    const closed = new Promise<{ exitCode: number | null; signal: string | null }>(
      (value, reject) => {
        resolve = value;
        this.failRunner = () => reject(new Error("private runner failure"));
      }
    );
    this.closeRunner = () => resolve({ exitCode: 0, signal: null });
    let stopped: Promise<void> | undefined;
    return {
      closed,
      stop: deadlineMs => stopped ??= Promise.resolve().then(async () => {
        this.lifecycle.push("runner-stop");
        this.cleanupDeadlines.push({ resource: "runner", deadlineMs });
        this.cleanupEvents.emit("runner-stop");
        if (this.cleanupFailure === "runner-stop") throw new Error("private runner stop failure");
        await this.runnerStopGate;
        resolve({ exitCode: 0, signal: null });
      })
    };
  }
  async openTunnel(
    _namespace: string,
    podName: string
  ): Promise<KubernetesGrpcTunnel> {
    this.lifecycle.push("tunnel");
    if (this.failure === "tunnel") throw new Error("private port-forward failure");
    const bootstrap = this.#bootstraps.get(podName)!;
    const server = new Server();
    const handlers: RunnerServer = {
      session: call => {
        call.on("error", () => undefined);
        call.on("data", message => {
          if (!message.execute) return;
          this.lifecycle.push("grpc");
          if (!this.holdGrpc) {
            call.write({
              result: {
                resultJson: Buffer.from("42"),
                errorJson: Buffer.from("null"),
                exitCode: 0,
                timedOut: false,
                stdoutUtf16le: Buffer.alloc(0),
                stderrUtf16le: Buffer.alloc(0)
              }
            });
            if (!this.holdFinalStatus) call.end();
          }
        });
      }
    };
    server.addService(RUNNER_SERVICE, handlers);
    const port = await new Promise<number>((resolve, reject) => {
      server.bindAsync(
        "127.0.0.1:0",
        ServerCredentials.createSsl(
          Buffer.from(bootstrap.clientCert),
          [{
            private_key: Buffer.from(bootstrap.serverKey),
            cert_chain: Buffer.from(bootstrap.serverCert)
          }],
          true
        ),
        (error, value) => error ? reject(error) : resolve(value)
      );
    });
    this.#servers.set(podName, server);
    let resolveClosed!: () => void;
    const closed = new Promise<void>((resolve, reject) => {
      resolveClosed = resolve;
      this.failTunnel = () => reject(new Error("private tunnel failure"));
    });
    let stopped: Promise<void> | undefined;
    return {
      address: `127.0.0.1:${port}`,
      closed,
      stop: deadlineMs => stopped ??= Promise.resolve().then(async () => {
        this.lifecycle.push("tunnel-stop");
        this.cleanupDeadlines.push({ resource: "tunnel", deadlineMs });
        this.cleanupEvents.emit("tunnel-stop");
        server.forceShutdown();
        if (this.cleanupFailure === "tunnel-stop") throw new Error("private tunnel stop failure");
        await this.tunnelStopGate;
        resolveClosed();
      })
    };
  }
  async deletePod(_namespace: string, name: string): Promise<void> {
    this.lifecycle.push("delete");
    this.#servers.get(name)?.forceShutdown();
    if (this.cleanupFailure === "delete") throw new Error("private delete failure");
    this.pods.delete(name);
  }
  async podExists(_namespace: string, name: string): Promise<boolean> {
    return this.pods.has(name);
  }
  async waitForPodDeleted(_namespace: string, name: string, deadlineMs: number): Promise<boolean> {
    this.lifecycle.push("confirm");
    this.cleanupDeadlines.push({ resource: "confirm", deadlineMs });
    this.cleanupEvents.emit("confirm");
    await this.confirmationGate;
    if (this.cleanupFailure === "confirm") return false;
    return !this.pods.has(name);
  }
  async listManagedPods(): Promise<KubernetesPod[]> {
    return [];
  }
}
