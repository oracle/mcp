/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import test from "node:test";
import { startChannelExecution } from "../src/isolation/pipe-execution.ts";
import {
  WORKER_CHANNEL_CONTRACT_VERSION,
  type WorkerChannel,
  type WorkerChannelStatus
} from "../src/isolation/worker-channel.ts";
import { encodeFrame, protocolMessage } from "../src/protocol.ts";
import type { JsonObject, SandboxResult } from "../src/types.ts";

test("generic worker channel completes one framed exchange and stops idempotently", async () => {
  assert.equal(WORKER_CHANNEL_CONTRACT_VERSION, 1);
  const channel = controlledChannel();
  let hostWrites = Buffer.alloc(0);
  channel.input.on("data", chunk => { hostWrites = Buffer.concat([hostWrites, chunk]); });
  const execution = startChannelExecution(channel, "42", runOptions());
  channel.output.write(encodeFrame(protocolMessage("health", { status: "ready" })));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(hostWrites.readUInt32BE(0) > 0, true);
  assert.match(hostWrites.subarray(4).toString("utf8"), /"type":"execute"/);
  channel.output.write(encodeFrame(protocolMessage("log", { stream: "stdout", text: "ok" })));
  channel.output.write(encodeFrame(protocolMessage("result", {
    result: 42,
    error: null,
    exitCode: 0,
    timedOut: false
  })));
  assert.deepEqual(await execution.result, {
    result: 42,
    error: null,
    stdout: "ok",
    stderr: "",
    exitCode: 0,
    timedOut: false
  });
  await Promise.all([execution.terminate(), execution.terminate()]);
  assert.equal(channel.stopCalls, 1);
});

test("generic channel handles close, duplicate health, closed input, errors, and races once", async () => {
  const closeFirst = controlledChannel();
  const closeExecution = startChannelExecution(closeFirst, "1", runOptions());
  closeFirst.finish({ exitCode: 9, signal: null });
  assert.match(((await closeExecution.result) as SandboxResult).error?.message ?? "", /exited before/);
  await closeExecution.terminate();

  const duplicate = controlledChannel();
  const duplicateExecution = startChannelExecution(duplicate, "1", runOptions());
  duplicate.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    encodeFrame(protocolMessage("health", { status: "ready" }))
  ]));
  assert.equal(((await duplicateExecution.result) as SandboxResult).error?.message, "sandbox protocol failed");
  await duplicateExecution.terminate();

  const closedInput = controlledChannel();
  closedInput.input.end();
  const closedInputExecution = startChannelExecution(closedInput, "1", runOptions());
  closedInput.output.write(encodeFrame(protocolMessage("health", { status: "ready" })));
  assert.equal(((await closedInputExecution.result) as SandboxResult).error?.message, "sandbox protocol failed");
  await closedInputExecution.terminate();

  const errored = controlledChannel();
  const erroredExecution = startChannelExecution(errored, "1", runOptions());
  errored.output.destroy(new Error("raw stream secret"));
  assert.equal(((await erroredExecution.result) as SandboxResult).error?.message, "sandbox runner failed");
  await erroredExecution.terminate();

  const race = controlledChannel();
  const raceExecution = startChannelExecution(race, "1", runOptions());
  race.output.write(encodeFrame(protocolMessage("result", {
    result: "winner",
    error: null,
    exitCode: 0,
    timedOut: false
  })));
  race.finish({ exitCode: 1, signal: null });
  assert.equal(((await raceExecution.result) as SandboxResult).result, "winner");
  await raceExecution.terminate();
});

test("hostile malformed frames fail before host RPC through the generic channel", async () => {
  const hostileFrames = [
    Buffer.from([0, 0, 0, 1, 0xff]),
    Buffer.from([0, 0, 0, 3, 0x7b, 0x7d]),
    rawJsonFrame("{not-json"),
    rawJsonFrame('{"version":1,"type":"health","status":NaN}'),
    encodeFrame({ version: 2, type: "health", status: "ready" }),
    encodeFrame(protocolMessage("unknown")),
    encodeFrame({ version: 1, type: "health" }),
    encodeFrame({ version: 1, type: "health", status: "ready", extra: true }),
    rawJsonFrame('{"version":1,"type":"rpc","id":1,"request":{"__proto__":null}}'),
    encodeFrame({
      version: 1,
      type: "rpc",
      id: 1,
      request: { value: "x".repeat(1024 * 1024 + 1) }
    }),
    encodeFrame({
      version: 1,
      type: "rpc",
      id: 1,
      request: nestedObject(34)
    }),
    Buffer.from([0x7f, 0xff, 0xff, 0xff])
  ];
  for (const [index, frame] of hostileFrames.entries()) {
    let rpcCalls = 0;
    const channel = controlledChannel();
    const execution = startChannelExecution(channel, "1", {
      ...runOptions(),
      async hostRpc() {
        rpcCalls += 1;
        return null;
      }
    });
    channel.output.write(frame);
    channel.finish({ exitCode: 1, signal: null });
    const result = await execution.result as SandboxResult;
    assert.equal(result.error?.message, "sandbox protocol failed", `hostile frame ${index}`);
    assert.equal(rpcCalls, 0);
    await execution.terminate();
  }
});

test("abort sends cancellation when possible and returns the exact timeout shape", async () => {
  const controller = new AbortController();
  const channel = controlledChannel();
  let written = "";
  channel.input.on("data", chunk => { written += chunk.toString("utf8"); });
  const execution = startChannelExecution(channel, "1", {
    ...runOptions(),
    signal: controller.signal
  });
  controller.abort();
  assert.deepEqual(await execution.result, {
    result: null,
    error: { message: "sandbox run deadline exceeded" },
    stdout: "",
    stderr: "",
    exitCode: -1,
    timedOut: true
  });
  await execution.terminate();
  assert.match(written, /cancel/);
});

test("hostile frames during cancellation stay sanitized and never reach host RPC", async () => {
  const hostileFrames = [
    rawJsonFrame("{not-json"),
    encodeFrame({ version: 2, type: "health", status: "ready" }),
    encodeFrame({ version: 1, type: "health", status: "ready", extra: true }),
    Buffer.from([0x7f, 0xff, 0xff, 0xff]),
    Buffer.from([0, 0, 0, 1, 0xff]),
    rawJsonFrame('{"version":1,"type":"rpc","id":1,"request":{"constructor":{}}}'),
    Buffer.from([0, 0, 0, 2, 0x7b])
  ];
  for (const [index, frame] of hostileFrames.entries()) {
    const controller = new AbortController();
    const channel = controlledChannel();
    let rpcCalls = 0;
    const execution = startChannelExecution(channel, "1", {
      ...runOptions(),
      signal: controller.signal,
      async hostRpc() {
        rpcCalls += 1;
        return { internalDiagnostic: "must-not-publish" };
      }
    });
    controller.abort();
    const result = await execution.result as SandboxResult;
    channel.output.write(frame);
    channel.finish({ exitCode: 1, signal: null });
    await new Promise(resolve => setImmediate(resolve));

    assert.deepEqual(result, {
      result: null,
      error: { message: "sandbox run deadline exceeded" },
      stdout: "",
      stderr: "",
      exitCode: -1,
      timedOut: true
    }, `hostile cancellation frame ${index}`);
    assert.equal(rpcCalls, 0, `hostile cancellation frame ${index}`);
    assert.equal(JSON.stringify(result).includes("internalDiagnostic"), false);
    await Promise.all([execution.terminate(), execution.terminate()]);
    assert.equal(channel.stopCalls, 1);
  }
});

function runOptions() {
  return {
    deadlineMs: Date.now() + 5000,
    signal: new AbortController().signal,
    async hostRpc() { return null; },
    memoryLimitMb: 128,
    maxResultBytes: 1024
  };
}

function rawJsonFrame(json: string): Buffer {
  const body = Buffer.from(json, "utf8");
  const header = Buffer.alloc(4);
  header.writeUInt32BE(body.length);
  return Buffer.concat([header, body]);
}

function nestedObject(depth: number): JsonObject {
  let value: JsonObject = {};
  for (let index = 0; index < depth; index += 1) {
    value = { value };
  }
  return value;
}

function controlledChannel(): WorkerChannel & {
  input: PassThrough;
  output: PassThrough;
  stopCalls: number;
  finish(status: WorkerChannelStatus): void;
} {
  const input = new PassThrough();
  const output = new PassThrough();
  let resolve!: (status: WorkerChannelStatus) => void;
  const closed = new Promise<WorkerChannelStatus>(value => { resolve = value; });
  let stopped: Promise<void> | undefined;
  const channel = {
    input,
    output,
    closed,
    stopCalls: 0,
    finish(status: WorkerChannelStatus) { resolve(status); },
    stop() {
      return stopped ??= (async () => {
        channel.stopCalls += 1;
        input.end();
        output.end();
        resolve({ exitCode: null, signal: "stopped" });
      })();
    }
  };
  return channel;
}
