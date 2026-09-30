/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { EventEmitter, once } from "node:events";
import { connect } from "node:net";
import type { Duplex, Writable } from "node:stream";
import test from "node:test";
import { RUNNER_READY_LINE, type RunnerTlsBootstrap } from "../src/grpc-tls.ts";
import { ClientNodeKubernetesGrpcTransport } from "../src/isolation/kubernetes-grpc.ts";

class FakeWebSocket extends EventEmitter {
  readonly CLOSING = 2;
  readyState = 1;
  close(): void {
    if (this.readyState >= this.CLOSING) return;
    this.readyState = 3;
    queueMicrotask(() => this.emit("close"));
  }
}

const bootstrap: RunnerTlsBootstrap = {
  serverKey: "key",
  serverCert: "server",
  clientCert: "client"
};

test("Kubernetes runner receives one bootstrap line without stdin EOF", async () => {
  const websocket = new FakeWebSocket();
  let input!: Duplex;
  let command: string[] = [];
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({
      async exec(_namespace, _pod, container, value, stdout, _stderr, stdin) {
        assert.equal(container, "runner");
        command = value as string[];
        input = stdin as Duplex;
        input.once("data", chunk => {
          assert.equal(String(chunk), `${JSON.stringify(bootstrap)}\n`);
          (stdout as Writable).write(RUNNER_READY_LINE);
        });
        return websocket as never;
      }
    }),
    () => ({ portForward: async () => assert.fail("not used") })
  );
  const handle = await transport.startRunner(
    "sandbox", "pod", bootstrap, Date.now() + 5000, new AbortController().signal
  );
  assert.deepEqual(command, [
    "node", "--no-node-snapshot", "--experimental-strip-types", "/app/src/sandbox-worker.ts"
  ]);
  assert.equal(input.readableEnded, false);
  await handle.stop(Date.now() + 5000);
});

test("Kubernetes runner fails closed on unexpected readiness output", async () => {
  const websocket = new FakeWebSocket();
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({
      async exec(_namespace, _pod, _container, _command, stdout) {
        queueMicrotask(() => (stdout as Writable).write("NOT READY\n"));
        return websocket as never;
      }
    }),
    () => ({ portForward: async () => assert.fail("not used") })
  );
  await assert.rejects(
    transport.startRunner(
      "sandbox", "pod", bootstrap, Date.now() + 5000, new AbortController().signal
    ),
    /Kubernetes runner failed/
  );
});

test("Kubernetes runner fails closed on output after readiness", async () => {
  const websocket = new FakeWebSocket();
  let runnerOutput!: Writable;
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({
      async exec(_namespace, _pod, _container, _command, stdout, _stderr, stdin) {
        runnerOutput = stdout as Writable;
        (stdin as Duplex).once("data", () => runnerOutput.write(RUNNER_READY_LINE));
        return websocket as never;
      }
    }),
    () => ({ portForward: async () => assert.fail("not used") })
  );
  const handle = await transport.startRunner(
    "sandbox", "pod", bootstrap, Date.now() + 5000, new AbortController().signal
  );
  const closed = assert.rejects(handle.closed, /Kubernetes runner failed/);
  runnerOutput.write(RUNNER_READY_LINE);
  await closed;
  await handle.stop(Date.now() + 5000);
});

test("Kubernetes runner reports status and sanitizes exec establishment failures", async () => {
  const websocket = new FakeWebSocket();
  let reportStatus!: (status: { details?: { causes?: Array<{ reason?: string; message?: string }> } }) => void;
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({
      async exec(_namespace, _pod, _container, _command, stdout, _stderr, stdin, _tty, status) {
        reportStatus = status!;
        (stdin as Duplex).once("data", () => (stdout as Writable).write(RUNNER_READY_LINE));
        return websocket as never;
      }
    }),
    () => ({ portForward: async () => assert.fail("not used") })
  );
  const handle = await transport.startRunner(
    "sandbox", "pod", bootstrap, Date.now() + 5000, new AbortController().signal
  );
  reportStatus({ details: { causes: [{ reason: "ExitCode", message: "7" }] } });
  assert.deepEqual(await handle.closed, { exitCode: 7, signal: null });
  await handle.stop(Date.now() + 5000);

  const failed = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => { throw new Error("private endpoint"); } }),
    () => ({ portForward: async () => assert.fail("not used") })
  );
  await assert.rejects(
    failed.startRunner(
      "sandbox", "pod", bootstrap, Date.now() + 5000, new AbortController().signal
    ),
    error => String(error) === "Error: Kubernetes runner failed"
  );
  const aborted = new AbortController();
  aborted.abort();
  await assert.rejects(
    failed.startRunner("sandbox", "pod", bootstrap, Date.now() + 5000, aborted.signal),
    /deadline exceeded/
  );
});

test("Kubernetes runner closes an exec websocket that arrives after cancellation", async () => {
  const websocket = new FakeWebSocket();
  let resolveExec!: (value: FakeWebSocket) => void;
  const controller = new AbortController();
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => await new Promise<FakeWebSocket>(resolve => { resolveExec = resolve; }) as never }),
    () => ({ portForward: async () => assert.fail("not used") })
  );
  const starting = transport.startRunner(
    "sandbox", "pod", bootstrap, Date.now() + 5000, controller.signal
  );
  while (!resolveExec) await new Promise(resolve => setImmediate(resolve));
  controller.abort();
  await assert.rejects(starting, /deadline exceeded/);
  resolveExec(websocket);
  await once(websocket, "close");
  assert.equal(websocket.readyState, 3);
});

test("Kubernetes tunnel is loopback-only and accepts one connection", async () => {
  const websocket = new FakeWebSocket();
  let forwardedPort = 0;
  let forwardedInput: Duplex | undefined;
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => assert.fail("not used") }),
    () => ({
      async portForward(_namespace, _pod, ports, _output, _errors, input) {
        forwardedPort = ports[0];
        forwardedInput = input as Duplex;
        return websocket as never;
      }
    })
  );
  const tunnel = await transport.openTunnel(
    "sandbox", "pod", 50051, Date.now() + 5000, new AbortController().signal
  );
  assert.match(tunnel.address, /^127\.0\.0\.1:\d+$/);
  const [host, portText] = tunnel.address.split(":");
  const first = connect(Number(portText), host);
  await once(first, "connect");
  while (!forwardedInput) await new Promise(resolve => setImmediate(resolve));
  assert.equal(forwardedPort, 50051);
  const second = connect(Number(portText), host);
  await once(second, "close");
  const firstClosed = once(first, "close");
  await tunnel.stop(Date.now() + 5000);
  await firstClosed;
  assert.equal(first.destroyed, true);
  assert.equal(websocket.readyState, 3);
});

test("Kubernetes tunnel sanitizes forward failure and abort", async () => {
  const failed = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => assert.fail("not used") }),
    () => ({ portForward: async () => { throw new Error("private endpoint"); } })
  );
  const tunnel = await failed.openTunnel(
    "sandbox", "pod", 50051, Date.now() + 5000, new AbortController().signal
  );
  const [host, portText] = tunnel.address.split(":");
  const failedClosed = assert.rejects(tunnel.closed, /Kubernetes port-forward failed/);
  const socket = connect(Number(portText), host);
  await once(socket, "close");
  await failedClosed;
  await tunnel.stop(Date.now() + 5000);

  const controller = new AbortController();
  const waiting = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => assert.fail("not used") }),
    () => ({ portForward: async () => assert.fail("not used") })
  );
  const aborted = await waiting.openTunnel(
    "sandbox", "pod", 50051, Date.now() + 5000, controller.signal
  );
  const abortedClosed = assert.rejects(aborted.closed, /deadline exceeded/);
  controller.abort();
  await abortedClosed;
  await aborted.stop(Date.now() + 5000);
});

test("Kubernetes tunnel accepts lazy websocket handles and rejects missing handles", async () => {
  const websocket = new FakeWebSocket();
  const lazy = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => assert.fail("not used") }),
    () => ({ portForward: async () => (() => websocket as never) })
  );
  const tunnel = await lazy.openTunnel(
    "sandbox", "pod", 50051, Date.now() + 5000, new AbortController().signal
  );
  const [host, portText] = tunnel.address.split(":");
  const socket = connect(Number(portText), host);
  socket.on("error", () => {});
  await once(socket, "connect");
  await tunnel.stop(Date.now() + 5000);

  const missing = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => assert.fail("not used") }),
    () => ({ portForward: async () => undefined as never })
  );
  const missingTunnel = await missing.openTunnel(
    "sandbox", "pod", 50051, Date.now() + 5000, new AbortController().signal
  );
  const [missingHost, missingPortText] = missingTunnel.address.split(":");
  const missingClosed = assert.rejects(missingTunnel.closed, /Kubernetes port-forward failed/);
  const missingSocket = connect(Number(missingPortText), missingHost);
  const socketClosed = new Promise<void>(resolve => missingSocket.once("close", resolve));
  missingSocket.on("error", () => {});
  await socketClosed;
  await missingClosed;
  await missingTunnel.stop(Date.now() + 5000);
});

test("Kubernetes tunnel closes a forwarding websocket that arrives after cleanup", async () => {
  const websocket = new FakeWebSocket();
  let resolveForward!: (value: FakeWebSocket) => void;
  const transport = new ClientNodeKubernetesGrpcTransport(
    () => ({ exec: async () => assert.fail("not used") }),
    () => ({
      portForward: async () => await new Promise<FakeWebSocket>(resolve => { resolveForward = resolve; }) as never
    })
  );
  const tunnel = await transport.openTunnel(
    "sandbox", "pod", 50051, Date.now() + 5000, new AbortController().signal
  );
  const [host, portText] = tunnel.address.split(":");
  const socket = connect(Number(portText), host);
  socket.on("error", () => {});
  await once(socket, "connect");
  while (!resolveForward) await new Promise(resolve => setImmediate(resolve));
  await tunnel.stop(Date.now() + 5000);
  resolveForward(websocket);
  await once(websocket, "close");
  assert.equal(websocket.readyState, 3);
});
