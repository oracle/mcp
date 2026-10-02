#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { Server, ServerCredentials } from "@grpc/grpc-js";
import { RUNNER_SERVICE, decodeText, encodeText } from "../src/grpc.ts";
import type { RunnerTlsBootstrap } from "../src/grpc-tls.ts";
import type { RunnerServer } from "../src/generated/runner.ts";
import type {
  KubernetesApi,
  KubernetesPod,
  ResourceAttributes
} from "../src/isolation/kubernetes-api.ts";
import type {
  KubernetesGrpcTunnel,
  KubernetesRunnerHandle
} from "../src/isolation/kubernetes-grpc.ts";
import type { KubernetesProfile } from "../src/isolation/kubernetes-config.ts";
import { createIsolationProvider } from "../src/isolation/provider-factory.ts";
import { startServer } from "../src/server.ts";
import {
  conformingPodAdmission,
  validInClusterEnvironment,
  validKataEnvironment,
  validLocalEnvironment
} from "./kata-fixtures.ts";

const profile = process.env.OCI_JAVASCRIPT_TEST_FAKE_PROFILE as KubernetesProfile | undefined;
if (profile !== "local-development" && profile !== "in-cluster" && profile !== "kata-in-cluster") {
  throw new Error("OCI_JAVASCRIPT_TEST_FAKE_PROFILE must name an exact Kubernetes profile");
}
const environment = profile === "local-development"
  ? validLocalEnvironment()
  : profile === "in-cluster" ? validInClusterEnvironment() : validKataEnvironment();
if (process.env.OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS) {
  environment.OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS =
    process.env.OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS;
}

class FakeKubernetesApi implements KubernetesApi {
  readonly profile: KubernetesProfile;
  readonly pods = new Map<string, KubernetesPod>();
  readonly bootstraps = new Map<string, RunnerTlsBootstrap>();

  constructor(profile: KubernetesProfile) {
    this.profile = profile;
  }
  async readNamespace() {}
  async readRuntimeClass() { return { handler: "kata-qemu-runtime-rs" }; }
  async selfCan(_attributes: ResourceAttributes) { return true; }
  async dryRunCreatePod(_namespace: string, pod: KubernetesPod) {
    return conformingPodAdmission(pod, this.profile);
  }
  async createPod(_namespace: string, pod: KubernetesPod) {
    this.pods.set(pod.metadata!.name!, structuredClone(pod));
  }
  async waitForPodRunning() {}
  async startRunner(
    _namespace: string,
    podName: string,
    bootstrap: RunnerTlsBootstrap
  ): Promise<KubernetesRunnerHandle> {
    this.bootstraps.set(podName, bootstrap);
    let resolve!: (status: { exitCode: number | null; signal: string | null }) => void;
    const closed = new Promise<{ exitCode: number | null; signal: string | null }>(
      value => { resolve = value; }
    );
    return {
      closed,
      async stop() { resolve({ exitCode: 0, signal: null }); }
    };
  }
  async openTunnel(_namespace: string, podName: string): Promise<KubernetesGrpcTunnel> {
    const tls = this.bootstraps.get(podName)!;
    const server = new Server();
    let close!: () => void;
    const closed = new Promise<void>(resolve => { close = resolve; });
    const handlers: RunnerServer = {
      session(call) {
        call.on("error", () => undefined);
        let code = "";
        call.on("data", message => {
          if (message.execute) {
            code = decodeText(message.execute.codeUtf16le, 1024 * 1024);
            if (code === "provider-failure") {
              close();
              server.forceShutdown();
              return;
            }
            if (code === "rpc" || code === "rpc-pending") {
              call.write({ rpc: {
                id: 1,
                requestJson: Buffer.from(JSON.stringify({
                  binding: "oracle",
                  namespace: "oci",
                  operation: "config",
                  payload: code === "rpc-pending" ? { testPending: true } : {}
                }))
              } });
              return;
            }
            sendResult(call, code);
          } else if (message.rpcResult && code === "rpc") {
            sendResult(call, code);
          }
        });
      }
    };
    server.addService(RUNNER_SERVICE, handlers);
    const port = await new Promise<number>((resolve, reject) => server.bindAsync(
      "127.0.0.1:0",
      ServerCredentials.createSsl(
        Buffer.from(tls.clientCert),
        [{ private_key: Buffer.from(tls.serverKey), cert_chain: Buffer.from(tls.serverCert) }],
        true
      ),
      (error, value) => error ? reject(error) : resolve(value)
    ));
    return {
      address: `127.0.0.1:${port}`,
      closed,
      async stop() {
        server.forceShutdown();
        close();
      }
    };
  }
  async deletePod(_namespace: string, name: string) { this.pods.delete(name); }
  async podExists(_namespace: string, name: string) { return this.pods.has(name); }
  async waitForPodDeleted(_namespace: string, name: string) { return !this.pods.has(name); }
  async listManagedPods() { return []; }
}

function sendResult(call: Parameters<RunnerServer["session"]>[0], code: string): void {
  const result = code === "script-error"
    ? { result: null, error: { message: "script failed" }, exitCode: 1, timedOut: false }
    : code === "timeout"
      ? {
          result: null,
          error: { message: "sandbox run deadline exceeded" },
          exitCode: -1,
          timedOut: true
        }
      : { result: 42, error: null, exitCode: 0, timedOut: false };
  call.write({ result: {
    resultJson: Buffer.from(JSON.stringify(result.result)),
    errorJson: Buffer.from(JSON.stringify(result.error)),
    exitCode: result.exitCode,
    timedOut: result.timedOut,
    stdoutUtf16le: encodeText(code === "log" ? "stdout-log" : "", 1024 * 1024),
    stderrUtf16le: encodeText(code === "log" ? "stderr-log" : "", 1024 * 1024)
  } });
  call.end();
}

const provider = await createIsolationProvider(environment, {
  kubernetesApi: new FakeKubernetesApi(profile),
  kubernetesDiagnostics: () => undefined,
  startReconciliation: false
});

await startServer({
  isolationProvider: provider,
  ...(process.env.OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS
    ? { reflectionManifest: { services: {} } }
    : {}),
  hostRpc: async request => (
    request.payload.testPending === true
      ? new Promise(() => undefined)
      : { ok: true, internalControlPlane: "must-not-leak" }
  )
});
