/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { EventEmitter } from "node:events";
import type { Duplex, Writable } from "node:stream";
import { RUNNER_READY_LINE, type RunnerTlsBootstrap } from "../src/grpc-tls.ts";
import type { KubernetesApi, KubernetesPod } from "../src/isolation/kubernetes-api.ts";
import {
  ClientNodeKubernetesGrpcTransport,
  type KubernetesGrpcTunnel,
  type KubernetesRunnerHandle
} from "../src/isolation/kubernetes-grpc.ts";
import { conformingPodAdmission } from "./kata-fixtures.ts";

export class StartupWebSocket extends EventEmitter {
  readonly CLOSING = 2;
  readyState = 1;
  close(): void {
    if (this.readyState >= this.CLOSING) return;
    this.readyState = 3;
    queueMicrotask(() => this.emit("close"));
  }
}

export class StartupKubernetesApi implements KubernetesApi {
  readonly websocket = new StartupWebSocket();
  readonly stopped: Array<{ resource: string; deadlineMs: number }> = [];
  deleted = false;
  tunnelStarted = false;
  observeRunner = true;
  beforeReady: "error" | "exit" | undefined;
  holdRunner = false;
  resolveRunner: (() => void) | undefined;
  resolveTunnel: (() => void) | undefined;
  output!: Writable;
  readonly transport = new ClientNodeKubernetesGrpcTransport(
    () => ({
      exec: async (_namespace, _pod, _container, _command, stdout, _stderr, stdin) => {
        this.output = stdout as Writable;
        (stdin as Duplex).once("data", () => {
          if (this.beforeReady) this.failRunner(this.beforeReady);
          else this.output.write(RUNNER_READY_LINE);
        });
        return this.websocket as never;
      }
    }),
    () => ({ portForward: async () => { throw new Error("unused forward"); } })
  );

  async readNamespace(): Promise<void> {}
  async readRuntimeClass(): Promise<{ handler: string }> {
    return { handler: "kata-qemu-runtime-rs" };
  }
  async selfCan(): Promise<boolean> { return true; }
  async dryRunCreatePod(_namespace: string, pod: KubernetesPod): Promise<boolean> {
    return conformingPodAdmission(pod, "kata-in-cluster");
  }
  async createPod(): Promise<void> {}
  async waitForPodRunning(): Promise<void> {}
  async startRunner(namespace: string, name: string, bootstrap: RunnerTlsBootstrap,
    deadlineMs: number, signal: AbortSignal): Promise<KubernetesRunnerHandle> {
    const runner = await this.transport.startRunner(namespace, name, bootstrap, deadlineMs, signal);
    if (this.observeRunner) void runner.closed.catch(() => undefined);
    if (this.holdRunner) await new Promise<void>(resolve => { this.resolveRunner = resolve; });
    return {
      closed: runner.closed,
      stop: async cleanupDeadlineMs => {
        this.stopped.push({ resource: "runner", deadlineMs: cleanupDeadlineMs });
        await runner.stop(cleanupDeadlineMs);
      }
    };
  }
  async openTunnel(): Promise<KubernetesGrpcTunnel> {
    this.tunnelStarted = true;
    await new Promise<void>(resolve => { this.resolveTunnel = resolve; });
    let rejectClosed!: (error: Error) => void;
    const closed = new Promise<void>((_resolve, reject) => { rejectClosed = reject; });
    return {
      address: "127.0.0.1:1",
      closed,
      stop: async deadlineMs => {
        this.stopped.push({ resource: "tunnel", deadlineMs });
        rejectClosed(new Error("private late tunnel failure"));
      }
    };
  }
  async deletePod(): Promise<void> { this.deleted = true; }
  async podExists(): Promise<boolean> { return !this.deleted; }
  async waitForPodDeleted(): Promise<boolean> { return this.deleted; }
  async listManagedPods(): Promise<KubernetesPod[]> { return []; }

  failRunner(fault: "output" | "error" | "exit"): void {
    if (fault === "output") this.output.write("private unexpected runner output\n");
    else if (fault === "error") this.websocket.emit("error", new Error("private websocket failure"));
    else this.websocket.close();
  }
}
