/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { Server, ServerCredentials } from "@grpc/grpc-js";
import { RUNNER_SERVICE } from "../src/grpc.ts";
import type { RunnerTlsBootstrap } from "../src/grpc-tls.ts";
import type {
  KubernetesApi,
  KubernetesPod,
  ResourceAttributes
} from "../src/isolation/kubernetes-api.ts";
import type {
  KubernetesGrpcTunnel,
  KubernetesRunnerHandle
} from "../src/isolation/kubernetes-grpc.ts";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import { KubernetesIsolationProvider } from "../src/isolation/kubernetes.ts";
import type { RunnerServer } from "../src/generated/runner.ts";
import type { SandboxResult } from "../src/types.ts";
import { conformingPodAdmission, validKataEnvironment } from "./kata-fixtures.ts";

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

test("Kubernetes provider uses runner readiness then gRPC and cleans up in order", async () => {
  const api = new FakeKubernetesApi();
  const provider = createProvider(api);
  await provider.preflight({ startReconciliation: false });
  const execution = provider.run("40 + 2", runOptions());
  const result = await execution.result;
  assert.deepEqual(result, successResult(42));
  await Promise.all([execution.terminate(), execution.terminate()]);
  assert.deepEqual(api.lifecycle, [
    "create", "running", "runner", "tunnel", "grpc", "tunnel-stop", "runner-stop", "delete"
  ]);
  assert.equal(api.pods.size, 0);
  assert.equal(execution.terminationTimeoutMs, 30_000);
});

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

class FakeKubernetesApi implements KubernetesApi {
  permissions: ResourceAttributes[] = [];
  createdPods: KubernetesPod[] = [];
  pods = new Map<string, KubernetesPod>();
  lifecycle: string[] = [];
  clientCertificates: string[] = [];
  failure: "create" | "running" | "runner" | "tunnel" | undefined;
  holdGrpc = false;
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
  async waitForPodRunning(): Promise<void> {
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
      value => { resolve = value; }
    );
    let stopped: Promise<void> | undefined;
    return {
      closed,
      stop: () => stopped ??= Promise.resolve().then(() => {
        this.lifecycle.push("runner-stop");
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
            call.end();
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
    const closed = new Promise<void>(resolve => { resolveClosed = resolve; });
    let stopped: Promise<void> | undefined;
    return {
      address: `127.0.0.1:${port}`,
      closed,
      stop: () => stopped ??= Promise.resolve().then(() => {
        this.lifecycle.push("tunnel-stop");
        server.forceShutdown();
        resolveClosed();
      })
    };
  }
  async deletePod(_namespace: string, name: string): Promise<void> {
    this.lifecycle.push("delete");
    this.#servers.get(name)?.forceShutdown();
    this.pods.delete(name);
  }
  async podExists(_namespace: string, name: string): Promise<boolean> {
    return this.pods.has(name);
  }
  async waitForPodDeleted(_namespace: string, name: string): Promise<boolean> {
    return !this.pods.has(name);
  }
  async listManagedPods(): Promise<KubernetesPod[]> {
    return [];
  }
}
