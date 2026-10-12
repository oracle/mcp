/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */
import assert from "node:assert/strict";
import test from "node:test";
import { Server, ServerCredentials } from "@grpc/grpc-js";
import type { V1Secret } from "@kubernetes/client-node";
import { RUNNER_SERVICE } from "../src/grpc.ts";
import type { KubernetesApi, KubernetesPod } from "../src/isolation/kubernetes-api.ts";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import { KubernetesIsolationProvider, podGrpcAddress } from "../src/isolation/kubernetes.ts";
import { validInClusterEnvironment, validKataEnvironment } from "./kata-fixtures.ts";
import { createGrpcTlsBootstrap } from "../src/grpc-tls-host.ts";
import type { RunnerServer } from "../src/generated/runner.ts";
import { cancelRunningExecution } from "./kubernetes-direct-startup.ts";
import type { IsolationProvider, SandboxResult } from "../src/types.ts";

class DirectApi implements KubernetesApi {
  events: string[] = [];
  secret: V1Secret | undefined;
  pod: KubernetesPod | undefined;
  server: Server | undefined;
  secretGate: Promise<void> | undefined;
  podGate: Promise<void> | undefined;
  endpointGate: Promise<void> | undefined;
  rejectSecret = false;
  failPod = false;
  failDeleteSecret = false;
  holdResult = false;
  badPeer = false;
  async readNamespace() {}
  async selfCan() { return true; }
  async listManagedPods() { return []; }
  async listManagedSecrets() { return []; }
  async createSecret(_namespace: string, secret: V1Secret) {
    this.events.push("secret-create");
    await this.secretGate;
    this.secret = secret;
    if (this.rejectSecret) throw new Error("private uncertain Secret creation");
  }
  async createPod(_namespace: string, pod: KubernetesPod) {
    this.events.push("pod-create");
    await this.podGate;
    if (this.failPod) throw new Error("private pod creation");
    this.pod = pod;
    return "original-uid";
  }
  async waitForPodEndpoint() {
    this.events.push("endpoint");
    await this.endpointGate;
    const tls = this.badPeer ? createGrpcTlsBootstrap().runner : {
      serverKey: Buffer.from(this.secret!.data!.serverKey!, "base64").toString(),
      serverCert: Buffer.from(this.secret!.data!.serverCert!, "base64").toString(),
      clientCert: Buffer.from(this.secret!.data!.clientCert!, "base64").toString()
    };
    const server = this.server = new Server();
    server.addService(RUNNER_SERVICE, { session: (call: Parameters<RunnerServer["session"]>[0]) => {
      call.on("error", () => undefined);
      call.on("data", message => {
        if (!message.execute) return;
        this.events.push("execute");
        if (this.holdResult) return;
        call.write({ result: { resultJson: Buffer.from("42"), errorJson: Buffer.from("null"),
          exitCode: 0, timedOut: false, stdoutUtf16le: Buffer.alloc(0), stderrUtf16le: Buffer.alloc(0) } });
        call.end();
      });
    } });
    await new Promise<void>((resolve, reject) => server.bindAsync("[::1]:50051",
      ServerCredentials.createSsl(Buffer.from(tls.clientCert), [{ private_key: Buffer.from(tls.serverKey), cert_chain: Buffer.from(tls.serverCert) }], true),
      error => error ? reject(error) : resolve()));
    return { uid: "original-uid", ip: "::1" };
  }
  async waitForPodRunning() { assert.fail("direct profile must not use local readiness"); }
  async startRunner(): Promise<never> { assert.fail("direct profile must not exec"); }
  async openTunnel(): Promise<never> { assert.fail("direct profile must not port-forward"); }
  async deletePod() { this.events.push("pod-delete"); this.server?.forceShutdown(); this.pod = undefined; }
  async podExists() { return !!this.pod; }
  async waitForPodDeleted() { return !this.pod; }
  async deleteSecret() {
    this.events.push("secret-delete");
    if (this.failDeleteSecret) throw new Error("private Secret deletion");
    this.secret = undefined;
  }
  async waitForSecretDeleted() { return !this.secret; }
}

const options = () => ({ deadlineMs: Date.now() + 3000, signal: new AbortController().signal, hostRpc: async () => null });
async function setup(api: DirectApi, environment = validInClusterEnvironment()) {
  const provider = new KubernetesIsolationProvider(parseKubernetesConfig(environment), api, () => undefined);
  await provider.preflight({ startReconciliation: false });
  return provider;
}

test("direct endpoint formatting validates IPv4 and IPv6", () => {
  assert.equal(podGrpcAddress("10.1.2.3"), "10.1.2.3:50051");
  assert.equal(podGrpcAddress("::1"), "[::1]:50051");
  for (const ip of ["hostname", "127.0.0.1:1234", ""]) assert.throws(() => podGrpcAddress(ip));
});

for (const environment of [validInClusterEnvironment(), validKataEnvironment()]) {
  test(`direct ${environment.OCI_JAVASCRIPT_KUBERNETES_PROFILE} uses its own Secret without exec or tunnel`, async () => {
    const api = new DirectApi();
    const provider = await setup(api, environment);
    const execution = provider.run("40 + 2", options());
    try {
      assert.equal((await execution.result).result, 42);
      assert.deepEqual(api.events, ["secret-create", "pod-create", "endpoint", "execute"]);
      assert.equal(api.pod?.spec?.runtimeClassName, environment.OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS);
    } finally { await execution.terminate(); }
    assert.equal(api.secret, undefined);
    assert.equal(api.pod, undefined);
  });
}

test("uncertain Secret creation and partial pod creation clean up independently", async () => {
  for (const fault of ["secret", "pod", "delete"] as const) {
    const api = new DirectApi();
    api.rejectSecret = fault === "secret";
    api.failPod = fault !== "secret";
    api.failDeleteSecret = fault === "delete";
    const provider = await setup(api);
    const execution = provider.run("42", options());
    assert.equal((await execution.result).error?.message, "isolation provider failed");
    if (fault === "delete") await assert.rejects(execution.terminate(), /cleanup failed/);
    else await execution.terminate();
    assert(api.events.includes("pod-delete"));
    assert(api.events.includes("secret-delete"));
    assert.equal(api.events.includes("execute"), false);
  }
});

for (const resource of ["secret", "pod"] as const) {
  test(`late ${resource} creation after cleanup is deleted again without execution`, async () => {
    const api = new DirectApi();
    let release!: () => void;
    const gate = new Promise<void>(resolve => { release = resolve; });
    if (resource === "secret") api.secretGate = gate;
    else api.podGate = gate;
    const provider = await setup(api);
    const execution = provider.run("42", options());
    while (!api.events.includes(`${resource}-create`)) await new Promise(resolve => setImmediate(resolve));
    const cleanup = execution.terminate(Date.now() + 100);
    assert.equal(execution.terminate(), cleanup);
    await cleanup;
    assert.equal((await execution.result).timedOut, true);
    release();
    await new Promise(resolve => setTimeout(resolve, 20));
    assert.equal(api.secret, undefined);
    assert.equal(api.pod, undefined);
    assert.equal(api.events.filter(event => event === `${resource}-delete`).length, 2);
    assert.equal(api.events.includes("endpoint"), false);
  });
}

test("direct cancellation closes gRPC and deletes both resources", async () => {
  const api = new DirectApi(); api.holdResult = true;
  const provider = await setup(api);
  const controller = new AbortController();
  const execution = provider.run("42", { ...options(), signal: controller.signal });
  try {
    while (!api.events.includes("execute")) await new Promise(resolve => setImmediate(resolve));
    controller.abort();
    assert.equal((await execution.result).timedOut, true);
  } finally { await execution.terminate(); }
  assert.equal(api.secret, undefined);
  assert.equal(api.pod, undefined);
});

test("wrong execution TLS peer never receives an execute message", async () => {
  const api = new DirectApi(); api.badPeer = true;
  const provider = await setup(api);
  const execution = provider.run("42", { ...options(), deadlineMs: Date.now() + 600 });
  try {
    assert.equal((await execution.result).result, null);
    assert.equal(api.events.includes("execute"), false);
  } finally { await execution.terminate(); }
});

test("live cancellation harness waits for guest RPC and resource assertions before aborting", async () => {
  const events: string[] = [];
  const provider: IsolationProvider = {
    run(_code, input) {
      events.push("created");
      const result = Promise.withResolvers<SandboxResult>();
      input.signal.addEventListener("abort", () => {
        events.push("cancelled");
        result.resolve({ result: null, error: { message: "sandbox run deadline exceeded" },
          stdout: "", stderr: "", exitCode: -1, timedOut: true });
      }, { once: true });
      queueMicrotask(() => {
        if (input.signal.aborted) return;
        events.push("guest-started");
        void input.hostRpc({ binding: "oracle", namespace: "oci", operation: "config", payload: {} });
      });
      return { result: result.promise, async terminate() { events.push("terminated"); } };
    }
  };
  assert.equal((await cancelRunningExecution(provider, () => events.push("resources-confirmed"))).timedOut, true);
  assert.deepEqual(events, ["created", "guest-started", "resources-confirmed", "cancelled", "terminated"]);
});
