#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { PassThrough } from "node:stream";
import type {
  KubernetesApi,
  KubernetesPod,
  ResourceAttributes
} from "../src/isolation/kubernetes-api.ts";
import type { KubernetesProfile } from "../src/isolation/kubernetes-config.ts";
import { createIsolationProvider } from "../src/isolation/provider-factory.ts";
import type { WorkerChannel, WorkerChannelStatus } from "../src/isolation/worker-channel.ts";
import { FrameDecoder, encodeFrame, protocolMessage } from "../src/protocol.ts";
import { startServer } from "../src/server.ts";
import {
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

  constructor(profile: KubernetesProfile) {
    this.profile = profile;
  }

  async readNamespace() {}
  async readRuntimeClass() { return { handler: "kata-qemu-runtime-rs" }; }
  async selfCan(_attributes: ResourceAttributes) { return true; }
  async dryRunCreatePod(_namespace: string, pod: KubernetesPod) {
    return safePod(pod, this.profile);
  }
  async createPod(_namespace: string, pod: KubernetesPod) {
    this.pods.set(pod.metadata!.name!, structuredClone(pod));
  }
  async waitForPodRunning() {}
  async openExecChannel() { return workerChannel(); }
  async deletePod(_namespace: string, name: string) { this.pods.delete(name); }
  async podExists(_namespace: string, name: string) { return this.pods.has(name); }
  async waitForPodDeleted(_namespace: string, name: string) { return !this.pods.has(name); }
  async listManagedPods() { return []; }
}

function safePod(pod: KubernetesPod, profile: KubernetesProfile): boolean {
  const container = pod.spec?.containers[0];
  const expectedImage = profile === "local-development"
    ? "oci-javascript-mcp-runner:dev"
    : `registry.example/runner@sha256:${"a".repeat(64)}`;
  return container?.image === expectedImage
    && (profile === "kata-in-cluster"
      ? pod.spec?.runtimeClassName === "kata-qemu-runtime-rs"
      : pod.spec?.runtimeClassName === undefined)
    && pod.spec?.serviceAccountName === "oci-js-runner"
    && pod.spec?.automountServiceAccountToken === false
    && pod.spec?.hostNetwork === false
    && pod.spec?.volumes?.length === 1
    && container.env === undefined
    && container.command?.[0] === "node"
    && container.securityContext?.allowPrivilegeEscalation === false;
}

function workerChannel(): WorkerChannel {
  const input = new PassThrough();
  const output = new PassThrough();
  const decoder = new FrameDecoder();
  let resolve!: (status: WorkerChannelStatus) => void;
  const closed = new Promise<WorkerChannelStatus>(value => { resolve = value; });
  let pendingRpc = false;
  let permanentlyPendingRpc = false;
  input.on("data", chunk => {
    for (const message of decoder.push(chunk)) {
      if (message.type === "execute") {
        const code = message.code;
        if (code === "provider-failure") {
          output.end();
          resolve({ exitCode: 1, signal: null });
        } else if (code === "rpc" || code === "rpc-pending") {
          pendingRpc = true;
          permanentlyPendingRpc = code === "rpc-pending";
          output.write(encodeFrame(protocolMessage("rpc", {
            id: 1,
            request: {
              binding: "oracle",
              namespace: "oci",
              operation: "config",
              payload: code === "rpc-pending" ? { testPending: true } : {}
            }
          })));
        } else {
          if (code === "log") {
            output.write(encodeFrame(protocolMessage("log", { stream: "stdout", text: "stdout-log" })));
            output.write(encodeFrame(protocolMessage("log", { stream: "stderr", text: "stderr-log" })));
          }
          output.write(encodeFrame(protocolMessage("result", code === "script-error" ? {
            result: null,
            error: { message: "script failed" },
            exitCode: 1,
            timedOut: false
          } : code === "timeout" ? {
            result: null,
            error: { message: "sandbox run deadline exceeded" },
            exitCode: -1,
            timedOut: true
          } : {
            result: 42,
            error: null,
            exitCode: 0,
            timedOut: false
          })));
        }
      } else if (message.type === "rpc_result" && pendingRpc && !permanentlyPendingRpc) {
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
  setImmediate(() => output.write(encodeFrame(protocolMessage("health", { status: "ready" }))));
  return channel;
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
