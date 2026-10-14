/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { createServer, type Server as NetServer, type Socket } from "node:net";
import { PassThrough, Writable } from "node:stream";
import type { Exec, PortForward, V1Status } from "@kubernetes/client-node";
import { RUNNER_READY_LINE, type RunnerTlsBootstrap } from "../grpc-tls.ts";

export type KubernetesRunnerStatus = { exitCode: number | null; signal: string | null };

export interface KubernetesRunnerHandle {
  readonly closed: Promise<KubernetesRunnerStatus>;
  stop(cleanupDeadlineMs: number): Promise<void>;
}

export interface KubernetesGrpcTunnel {
  readonly address: string;
  readonly closed: Promise<void>;
  stop(cleanupDeadlineMs: number): Promise<void>;
}

export interface KubernetesGrpcTransport {
  startRunner(namespace: string, podName: string, bootstrap: RunnerTlsBootstrap,
    deadlineMs: number, signal: AbortSignal): Promise<KubernetesRunnerHandle>;
  openTunnel(namespace: string, podName: string, targetPort: number,
    deadlineMs: number, signal: AbortSignal): Promise<KubernetesGrpcTunnel>;
}

type ExecFactory = (deadlineMs: number, signal: AbortSignal) => Pick<Exec, "exec">;
type PortForwardFactory = (
  deadlineMs: number,
  signal: AbortSignal
) => Pick<PortForward, "portForward">;
type WebSocketLike = {
  readonly CLOSING: number;
  readonly readyState: number;
  close(): void;
  once(event: "close" | "error", listener: (...args: unknown[]) => void): unknown;
};

export class ClientNodeKubernetesGrpcTransport implements KubernetesGrpcTransport {
  readonly #execFactory: ExecFactory;
  readonly #portForwardFactory: PortForwardFactory;

  constructor(execFactory: ExecFactory, portForwardFactory: PortForwardFactory) {
    this.#execFactory = execFactory;
    this.#portForwardFactory = portForwardFactory;
  }

  async startRunner(
    namespace: string,
    podName: string,
    bootstrap: RunnerTlsBootstrap,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<KubernetesRunnerHandle> {
    assertActive(deadlineMs, signal);
    const stdout = new PassThrough();
    const stdin = new PassThrough();
    const stderr = new BoundedSink(64 * 1024);
    let statusResolve!: (status: KubernetesRunnerStatus) => void;
    let statusReject!: (error: Error) => void;
    let statusSettled = false;
    const closed = new Promise<KubernetesRunnerStatus>((resolve, reject) => {
      statusResolve = resolve;
      statusReject = reject;
    });
    // Keep rejection available to consumers even before the handle is returned.
    void closed.catch(() => undefined);
    const prematureClose = closed.then(() => {
      throw new Error("Kubernetes runner failed");
    });
    void prematureClose.catch(() => undefined);
    const settleStatus = (status: KubernetesRunnerStatus) => {
      if (!statusSettled) {
        statusSettled = true;
        statusResolve(status);
      }
    };
    const failStatus = () => {
      if (!statusSettled) {
        statusSettled = true;
        statusReject(new Error("Kubernetes runner failed"));
      }
    };
    const execPromise = Promise.resolve().then(() => this.#execFactory(deadlineMs, signal).exec(
      namespace,
      podName,
      "runner",
      ["node", "--no-node-snapshot", "--experimental-strip-types", "/app/src/sandbox-worker.ts"],
      stdout,
      stderr,
      stdin,
      false,
      (status: V1Status) => settleStatus({ exitCode: statusCode(status), signal: null })
    ));
    let websocket: WebSocketLike;
    try {
      websocket = await withDeadline(Promise.race([execPromise, prematureClose]),
        deadlineMs, signal) as WebSocketLike;
    } catch {
      void execPromise.then(value => closeWebSocket(value as WebSocketLike), () => undefined);
      destroyStreams(stdin, stdout, stderr);
      throw stageError(deadlineMs, signal, "Kubernetes runner failed");
    }
    websocket.once("close", () => settleStatus({ exitCode: null, signal: null }));
    websocket.once("error", failStatus);

    const ready = waitForReady(stdout, deadlineMs, signal);
    stdin.write(`${JSON.stringify(bootstrap)}\n`);
    try {
      await Promise.race([ready, prematureClose]);
    } catch {
      closeWebSocket(websocket);
      destroyStreams(stdin, stdout, stderr);
      throw stageError(deadlineMs, signal, "Kubernetes runner failed");
    }
    stdout.on("data", failStatus);

    let stopping: Promise<void> | undefined;
    return {
      closed,
      stop(cleanupDeadlineMs) {
        return stopping ??= (async () => {
          destroyStreams(stdin, stdout, stderr);
          closeWebSocket(websocket);
          await cleanupDeadline(closed.then(() => undefined, () => undefined), cleanupDeadlineMs,
            "Kubernetes runner cleanup failed");
        })();
      }
    };
  }

  async openTunnel(
    namespace: string,
    podName: string,
    targetPort: number,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<KubernetesGrpcTunnel> {
    assertActive(deadlineMs, signal);
    let accepted: Socket | undefined;
    let websocket: WebSocketLike | undefined;
    let forwarding: Promise<void> | undefined;
    let shuttingDown = false;
    let settled = false;
    let closeResolve!: () => void;
    let closeReject!: (error: Error) => void;
    const closed = new Promise<void>((resolve, reject) => {
      closeResolve = resolve;
      closeReject = reject;
    });
    void closed.catch(() => undefined);
    const finish = (error?: Error) => {
      if (settled) return;
      settled = true;
      error ? closeReject(error) : closeResolve();
    };
    const errors = new BoundedSink(64 * 1024);
    const server = createServer(socket => {
      if (accepted || shuttingDown) {
        socket.destroy();
        return;
      }
      accepted = socket;
      socket.once("close", () => {
        closeWebSocket(websocket);
      });
      socket.once("error", () => finish(new Error("Kubernetes port-forward failed")));
      forwarding = Promise.resolve().then(() => this.#portForwardFactory(deadlineMs, signal).portForward(
        namespace, podName, [targetPort], socket, errors, socket, 0
      )).then(value => {
        websocket = (typeof value === "function" ? value() : value) as WebSocketLike | undefined;
        if (!websocket) {
          socket.destroy();
          finish(new Error("Kubernetes port-forward failed"));
          return;
        }
        const transportClosed = new Promise<void>(resolve => {
          websocket!.once("close", () => { resolve(); finish(); });
          websocket!.once("error", () => finish(new Error("Kubernetes port-forward failed")));
          if (websocket!.readyState > websocket!.CLOSING) { resolve(); finish(); }
        });
        if (shuttingDown || settled || socket.destroyed) closeWebSocket(websocket);
        return transportClosed;
      }).catch(() => {
        socket.destroy();
        finish(new Error("Kubernetes port-forward failed"));
      });
    });
    server.on("error", () => finish(new Error("Kubernetes port-forward failed")));
    try {
      await listen(server, deadlineMs, signal);
    } catch {
      try {
        server.close();
      } catch {
        // The listener may have failed before reaching a closeable state.
      }
      errors.destroy();
      throw stageError(deadlineMs, signal, "Kubernetes port-forward failed");
    }
    const address = server.address();
    if (!address || typeof address === "string") {
      server.close();
      throw new Error("Kubernetes port-forward failed");
    }
    const abort = () => {
      shuttingDown = true;
      accepted?.destroy();
      closeWebSocket(websocket);
      server.close();
      finish(stageError(deadlineMs, signal, "Kubernetes port-forward failed"));
    };
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();

    let stopping: Promise<void> | undefined;
    return {
      address: `127.0.0.1:${address.port}`,
      closed,
      stop(cleanupDeadlineMs) {
        return stopping ??= (async () => {
          shuttingDown = true;
          signal.removeEventListener("abort", abort);
          accepted?.destroy();
          closeWebSocket(websocket);
          errors.destroy();
          await cleanupDeadline(Promise.all([
            closeServer(server), forwarding
          ]).then(() => undefined), cleanupDeadlineMs, "Kubernetes port-forward cleanup failed");
          finish();
        })();
      }
    };
  }
}

function waitForReady(output: PassThrough, deadlineMs: number, signal: AbortSignal): Promise<void> {
  const expected = Buffer.from(RUNNER_READY_LINE);
  return withDeadline(new Promise<void>((resolve, reject) => {
    let buffered = Buffer.alloc(0);
    const cleanup = () => {
      output.off("data", onData);
      output.off("end", fail);
      output.off("error", fail);
      output.off("close", fail);
    };
    const fail = () => {
      cleanup();
      reject(new Error("invalid Kubernetes runner readiness"));
    };
    const onData = (chunk: Buffer | string) => {
      buffered = Buffer.concat([buffered, Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk)]);
      if (buffered.length > expected.length || !expected.subarray(0, buffered.length).equals(buffered)) {
        fail();
      } else if (buffered.length === expected.length) {
        cleanup();
        resolve();
      }
    };
    output.on("data", onData);
    output.once("end", fail);
    output.once("error", fail);
    output.once("close", fail);
  }), deadlineMs, signal);
}

function listen(server: NetServer, deadlineMs: number, signal: AbortSignal): Promise<void> {
  return withDeadline(new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  }), deadlineMs, signal);
}

function closeServer(server: NetServer): Promise<void> {
  if (!server.listening) return Promise.resolve();
  return new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
}

function withDeadline<T>(promise: Promise<T>, deadlineMs: number, signal: AbortSignal): Promise<T> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (callback: () => void) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      signal.removeEventListener("abort", abort);
      callback();
    };
    const abort = () => finish(() => reject(new Error("sandbox run deadline exceeded")));
    const timeout = setTimeout(abort, Math.max(1, deadlineMs - Date.now()));
    signal.addEventListener("abort", abort, { once: true });
    promise.then(value => finish(() => resolve(value)), error => finish(() => reject(error)));
    if (signal.aborted || Date.now() >= deadlineMs) abort();
  });
}

function cleanupDeadline(promise: Promise<void>, deadlineMs: number, message: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error(message)), Math.max(1, deadlineMs - Date.now()));
    promise.then(resolve, reject).finally(() => clearTimeout(timeout));
  });
}

function assertActive(deadlineMs: number, signal: AbortSignal): void {
  if (signal.aborted || Date.now() >= deadlineMs) throw new Error("sandbox run deadline exceeded");
}

function stageError(deadlineMs: number, signal: AbortSignal, fallback: string): Error {
  return new Error(signal.aborted || Date.now() >= deadlineMs
    ? "sandbox run deadline exceeded"
    : fallback);
}

function destroyStreams(...streams: Array<PassThrough | BoundedSink>): void {
  for (const stream of streams) stream.destroy();
}

function closeWebSocket(websocket: WebSocketLike | undefined): void {
  if (websocket && websocket.readyState < websocket.CLOSING) websocket.close();
}

class BoundedSink extends Writable {
  #remaining: number;
  constructor(limit: number) {
    super();
    this.#remaining = limit;
  }
  override _write(chunk: Buffer | string, _encoding: BufferEncoding,
    callback: (error?: Error | null) => void): void {
    this.#remaining = Math.max(0, this.#remaining - Buffer.byteLength(chunk));
    callback();
  }
}

function statusCode(status: V1Status): number | null {
  const cause = status.details?.causes?.find(item => item.reason === "ExitCode");
  const value = cause?.message === undefined ? NaN : Number(cause.message);
  return Number.isSafeInteger(value) ? value : null;
}
