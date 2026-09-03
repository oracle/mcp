/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";
import {
  FrameDecoder,
  encodeFrame,
  protocolMessage
} from "../src/protocol.ts";
import type { JsonObject } from "../src/types.ts";

const WORKER_PATH = fileURLToPath(new URL("../src/sandbox-worker.ts", import.meta.url));

test("sandbox worker rejects invalid host messages with one sanitized protocol error", async () => {
  const invalidMessages = [
    protocolMessage("execute", {
      ...validExecute(),
      timeoutMs: 0
    }),
    protocolMessage("rpc_result", { id: "one", result: null }),
    protocolMessage("rpc_result", { id: 1, result: null }),
    protocolMessage("unsupported", {})
  ];

  for (const [index, message] of invalidMessages.entries()) {
    const worker = startWorker();
    try {
      assert.deepEqual(toPlain(await worker.next("health")), protocolMessage("health", { status: "ready" }));
      worker.child.stdin.write(encodeFrame(message));
      assert.deepEqual(
        toPlain(await worker.next("protocol_error")),
        protocolMessage("protocol_error", {
          error: { message: "sandbox protocol failure" }
        }),
        `invalid message ${index}`
      );
      assert.deepEqual(await worker.closed, { code: 70, signal: null });
      assert.equal(worker.stderr.includes("invalid message"), false);
    } finally {
      worker.stop();
    }
  }
});

test("sandbox worker rejects malformed and truncated frames without exposing parser details", async () => {
  for (const [index, input] of [
    Buffer.from([0, 0, 0, 1, 0xff]),
    Buffer.from([0, 0, 0, 4, 0x7b])
  ].entries()) {
    const worker = startWorker();
    try {
      await worker.next("health");
      worker.child.stdin.end(input);
      const response = await worker.next("protocol_error");
      assert.deepEqual(toPlain(response), protocolMessage("protocol_error", {
        error: { message: "sandbox protocol failure" }
      }), `invalid frame ${index}`);
      assert.deepEqual(await worker.closed, { code: 70, signal: null });
      assert.equal(JSON.stringify(response).includes("UTF"), false);
      assert.equal(JSON.stringify(response).includes("truncated"), false);
    } finally {
      worker.stop();
    }
  }
});

test("sandbox worker cancellation rejects pending RPC and preserves its terminal status", async () => {
  const worker = startWorker();
  try {
    await worker.next("health");
    worker.child.stdin.write(encodeFrame(protocolMessage("execute", {
      ...validExecute(),
      code: "await oci.config();",
      timeoutMs: 100
    })));
    await worker.next("rpc");
    worker.child.stdin.write(encodeFrame(protocolMessage("cancel", {})));
    assert.deepEqual(await worker.closed, { code: 124, signal: null });
  } finally {
    worker.stop();
  }
});

test("sandbox worker rejects a second execution and clears pending RPC work", async () => {
  const worker = startWorker();
  try {
    await worker.next("health");
    worker.child.stdin.write(Buffer.concat([
      encodeFrame(protocolMessage("execute", {
        ...validExecute(),
        code: "await oci.config();",
        timeoutMs: 100
      })),
      encodeFrame(protocolMessage("execute", validExecute()))
    ]));
    await worker.next("rpc");
    assert.deepEqual(toPlain(await worker.next("protocol_error")), protocolMessage("protocol_error", {
      error: { message: "sandbox protocol failure" }
    }));
    assert.deepEqual(await worker.closed, { code: 70, signal: null });
  } finally {
    worker.stop();
  }
});

function validExecute(): JsonObject {
  return {
    code: "40 + 2;",
    timeoutMs: 10_000,
    reflectionManifest: { services: {} },
    memoryLimitMb: 128,
    maxResultBytes: 1024 * 1024
  };
}

function toPlain(value: JsonObject): JsonObject {
  return JSON.parse(JSON.stringify(value)) as JsonObject;
}

function startWorker(): {
  child: ChildProcessWithoutNullStreams;
  closed: Promise<{ code: number | null; signal: NodeJS.Signals | null }>;
  next(type: string): Promise<JsonObject>;
  stop(): void;
  readonly stderr: string;
} {
  const child = spawn(process.execPath, [
    "--no-node-snapshot",
    "--experimental-strip-types",
    WORKER_PATH
  ], {
    env: process.env,
    stdio: ["pipe", "pipe", "pipe"]
  });
  const decoder = new FrameDecoder();
  const messages: JsonObject[] = [];
  const waiters = new Set<{
    type: string;
    resolve: (message: JsonObject) => void;
    reject: (error: Error) => void;
    timeout: NodeJS.Timeout;
  }>();
  let stderr = "";

  child.stdout.on("data", chunk => {
    for (const message of decoder.push(chunk)) {
      const waiter = Array.from(waiters).find(candidate => candidate.type === message.type);
      if (waiter) {
        clearTimeout(waiter.timeout);
        waiters.delete(waiter);
        waiter.resolve(message);
      } else {
        messages.push(message);
      }
    }
  });
  child.stderr.on("data", chunk => {
    stderr += chunk.toString("utf8");
  });
  const closed = new Promise<{ code: number | null; signal: NodeJS.Signals | null }>(resolve => {
    child.once("close", (code, signal) => {
      for (const waiter of waiters) {
        clearTimeout(waiter.timeout);
        waiter.reject(new Error(`sandbox worker closed before ${waiter.type}`));
      }
      waiters.clear();
      resolve({ code, signal });
    });
  });

  return {
    child,
    closed,
    next(type: string) {
      const index = messages.findIndex(message => message.type === type);
      if (index !== -1) {
        return Promise.resolve(messages.splice(index, 1)[0]);
      }
      return new Promise((resolve, reject) => {
        const waiter = {
          type,
          resolve,
          reject,
          timeout: setTimeout(() => {
            waiters.delete(waiter);
            reject(new Error(`timed out waiting for sandbox worker ${type}`));
          }, 5_000)
        };
        waiters.add(waiter);
      });
    },
    stop() {
      if (child.exitCode === null && child.signalCode === null) {
        child.kill("SIGKILL");
      }
    },
    get stderr() {
      return stderr;
    }
  };
}
