/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { PassThrough, Writable } from "node:stream";
import test from "node:test";
import { startChannelExecution } from "../src/isolation/pipe-execution.ts";
import {
  WORKER_CHANNEL_CONTRACT_VERSION,
  type WorkerChannel,
  type WorkerChannelStatus
} from "../src/isolation/worker-channel.ts";
import { encodeFrame, protocolMessage } from "../src/protocol.ts";
import type { JsonObject, SandboxResult, WorkerChannelLimits } from "../src/types.ts";

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
  assert.equal(
    ((await raceExecution.result) as SandboxResult).error?.message,
    "sandbox protocol failed"
  );
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

test("channel rejects every pre-health message without invoking host RPC", async () => {
  const messages = [
    protocolMessage("log", { stream: "stdout", text: "early" }),
    protocolMessage("rpc", { id: 1, request: { request: "early" } }),
    protocolMessage("result", validResult("early")),
    protocolMessage("protocol_error", { error: { message: "early" } })
  ];
  for (const [index, message] of messages.entries()) {
    let rpcCalls = 0;
    const channel = controlledChannel();
    const execution = startChannelExecution(channel, "1", {
      ...runOptions(),
      async hostRpc() {
        rpcCalls += 1;
        return null;
      }
    });
    channel.output.write(encodeFrame(message));
    const result = await execution.result as SandboxResult;
    assert.equal(result.error?.message, "sandbox protocol failed", `message ${index}`);
    assert.equal(rpcCalls, 0, `message ${index}`);
    await execution.terminate();
  }
});

test("channel rejects unsafe, in-flight duplicate, and completed RPC ids", async () => {
  for (const id of [0, -1, 1.5, Number.MAX_SAFE_INTEGER + 1]) {
    let rpcCalls = 0;
    const channel = controlledChannel();
    const execution = startChannelExecution(channel, "1", {
      ...runOptions(),
      async hostRpc() {
        rpcCalls += 1;
        return null;
      }
    });
    channel.output.write(Buffer.concat([
      encodeFrame(protocolMessage("health", { status: "ready" })),
      encodeFrame(protocolMessage("rpc", { id, request: {} }))
    ]));
    assert.equal((await execution.result as SandboxResult).error?.message, "sandbox protocol failed");
    assert.equal(rpcCalls, 0);
    await execution.terminate();
  }

  let release!: () => void;
  let calls = 0;
  const inFlight = controlledChannel();
  const inFlightExecution = startChannelExecution(inFlight, "1", {
    ...runOptions(),
    async hostRpc() {
      calls += 1;
      return await new Promise<null>(resolve => { release = () => resolve(null); });
    }
  });
  inFlight.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    encodeFrame(protocolMessage("rpc", { id: 7, request: {} })),
    encodeFrame(protocolMessage("rpc", { id: 7, request: {} }))
  ]));
  assert.equal((await inFlightExecution.result as SandboxResult).error?.message, "sandbox protocol failed");
  assert.equal(calls, 1);
  release();
  await inFlightExecution.terminate();

  calls = 0;
  const completed = controlledChannel();
  const completedExecution = startChannelExecution(completed, "1", {
    ...runOptions(),
    async hostRpc() {
      calls += 1;
      return null;
    }
  });
  completed.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    encodeFrame(protocolMessage("rpc", { id: 9, request: {} }))
  ]));
  await new Promise(resolve => setImmediate(resolve));
  completed.output.write(encodeFrame(protocolMessage("rpc", { id: 9, request: {} })));
  assert.equal((await completedExecution.result as SandboxResult).error?.message, "sandbox protocol failed");
  assert.equal(calls, 1);
  await completedExecution.terminate();
});

test("terminal authority rejects same-buffer and replayed work without replacing the result", async () => {
  for (const trailing of [
    encodeFrame(protocolMessage("rpc", { id: 2, request: {} })),
    rawJsonFrame("{not-json"),
    encodeFrame(protocolMessage("result", validResult("duplicate")))
  ]) {
    let rpcCalls = 0;
    const channel = controlledChannel();
    const execution = startChannelExecution(channel, "1", {
      ...runOptions(),
      async hostRpc() {
        rpcCalls += 1;
        return null;
      }
    });
    channel.output.write(Buffer.concat([
      encodeFrame(protocolMessage("health", { status: "ready" })),
      encodeFrame(protocolMessage("result", validResult("authoritative"))),
      trailing
    ]));
    const result = await execution.result as SandboxResult;
    assert.equal(result.result, "authoritative");
    assert.equal(rpcCalls, 0);
    await execution.terminate();
    assert.equal(channel.stopCalls, 1);
  }

  let replayCalls = 0;
  const replay = controlledChannel();
  const replayExecution = startChannelExecution(replay, "1", {
    ...runOptions(),
    async hostRpc() {
      replayCalls += 1;
      return null;
    }
  });
  replay.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    encodeFrame(protocolMessage("result", validResult("done")))
  ]));
  assert.equal((await replayExecution.result as SandboxResult).result, "done");
  replay.output.write(encodeFrame(protocolMessage("rpc", { id: 1, request: {} })));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(replayCalls, 0);
  await replayExecution.terminate();
});

test("ordered acceptance preserves four concurrent RPC completions", async () => {
  const channel = controlledChannel();
  let active = 0;
  let peak = 0;
  const releases: Array<() => void> = [];
  const execution = startChannelExecution(channel, "1", {
    ...runOptions(),
    async hostRpc() {
      active += 1;
      peak = Math.max(peak, active);
      await new Promise<void>(resolve => releases.push(resolve));
      active -= 1;
      return null;
    }
  });
  channel.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    ...Array.from({ length: 4 }, (_, index) => encodeFrame(protocolMessage("rpc", {
      id: index + 1,
      request: {}
    })))
  ]));
  await waitFor(() => releases.length === 4);
  assert.equal(peak, 4);
  releases.forEach(resolve => resolve());
  await new Promise(resolve => setImmediate(resolve));
  channel.output.write(encodeFrame(protocolMessage("result", validResult(4))));
  assert.equal((await execution.result as SandboxResult).result, 4);
  await execution.terminate();
});

test("host terminal acceptance independently enforces the configured result limit", async () => {
  for (const [label, payload, maxResultBytes] of [
    ["below", validResult("a"), 8],
    ["exact", validResult("ab"), 8]
  ] as const) {
    const channel = controlledChannel();
    const execution = startChannelExecution(channel, "1", {
      ...runOptions({ ...testChannelLimits(), maxResultBytes })
    });
    channel.output.write(Buffer.concat([
      encodeFrame(protocolMessage("health", { status: "ready" })),
      encodeFrame(protocolMessage("result", payload))
    ]));
    assert.equal((await execution.result as SandboxResult).result, payload.result, label);
    await execution.terminate();
  }

  const oversizedPayloads = [
    validResult("abc"),
    { result: null, error: { message: "too large" }, exitCode: 1, timedOut: false }
  ];
  for (const [index, payload] of oversizedPayloads.entries()) {
    const channel = controlledChannel();
    let rpcCalls = 0;
    const execution = startChannelExecution(channel, "1", {
      ...runOptions({ ...testChannelLimits(), maxResultBytes: 8 }),
      async hostRpc() {
        rpcCalls += 1;
        return null;
      }
    });
    channel.output.write(Buffer.concat([
      encodeFrame(protocolMessage("health", { status: "ready" })),
      encodeFrame(protocolMessage("result", payload))
    ]));
    assert.equal(
      (await execution.result as SandboxResult).error?.message,
      "sandbox protocol failed",
      `oversized payload ${index}`
    );
    assert.equal(rpcCalls, 0, `oversized payload ${index}`);
    await waitFor(() => channel.stopCalls === 1);
  }

  for (const [label, totalBytes, accepted] of [
    ["below combined limit", 99, true],
    ["exact combined limit", 100, true],
    ["above combined limit", 101, false]
  ] as const) {
    const payload = terminalPayloadWithEncodedBytes(totalBytes);
    assert(encodedJsonBytes(payload.result) < 100);
    assert(encodedJsonBytes(payload.error) < 100);
    const channel = controlledChannel();
    const execution = startChannelExecution(channel, "1", {
      ...runOptions({ ...testChannelLimits(), maxResultBytes: 100 })
    });
    channel.output.write(Buffer.concat([
      encodeFrame(protocolMessage("health", { status: "ready" })),
      encodeFrame(protocolMessage("result", payload))
    ]));
    const result = await execution.result as SandboxResult;
    assert.equal(
      result.error?.message,
      accepted ? payload.error.message : "sandbox protocol failed",
      label
    );
    await execution.terminate();
  }
});

test("channel budgets bound valid floods and keep capped logs byte-correct", async () => {
  const logChannel = controlledChannel();
  const logExecution = startChannelExecution(logChannel, "1", {
    ...runOptions({
      ...testChannelLimits(),
      maxAcceptedMessages: 20,
      maxLogBytes: 1024 * 1024 + 9
    })
  });
  logChannel.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    encodeFrame(protocolMessage("log", { stream: "stdout", text: "x".repeat(1024 * 1024) })),
    ...Array.from({ length: 10 }, () => encodeFrame(protocolMessage("log", {
      stream: "stdout",
      text: "z"
    })))
  ]));
  const logResult = await logExecution.result as SandboxResult;
  assert.equal(logResult.error?.message, "sandbox protocol failed");
  assert.equal(Buffer.byteLength(logResult.stdout, "utf8"), 1024 * 1024);
  assert.equal(logResult.stdout.endsWith("z"), false);
  await logExecution.terminate();

  const messageChannel = controlledChannel();
  const messageExecution = startChannelExecution(messageChannel, "1", {
    ...runOptions({ ...testChannelLimits(), maxAcceptedMessages: 4 })
  });
  messageChannel.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    ...Array.from({ length: 4 }, () => encodeFrame(protocolMessage("log", {
      stream: "stderr",
      text: "flood"
    })))
  ]));
  assert.equal(
    (await messageExecution.result as SandboxResult).error?.message,
    "sandbox protocol failed"
  );
  await messageExecution.terminate();

  let rejectedRequests = 0;
  const rpcChannel = controlledChannel();
  const rpcExecution = startChannelExecution(rpcChannel, "1", {
    ...runOptions({ ...testChannelLimits(), maxAcceptedMessages: 8 }),
    async hostRpc() {
      rejectedRequests += 1;
      return { ok: false, error: "rejected" };
    }
  });
  rpcChannel.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    ...Array.from({ length: 8 }, (_, index) => encodeFrame(protocolMessage("rpc", {
      id: index + 1,
      request: { rejected: true }
    })))
  ]));
  assert.equal((await rpcExecution.result as SandboxResult).error?.message, "sandbox protocol failed");
  assert.equal(rejectedRequests, 7);
  await rpcExecution.terminate();

  for (const limits of [
    { ...testChannelLimits(), maxIngressBytes: 4 },
    { ...testChannelLimits(), maxEgressBytes: 4 }
  ]) {
    const bounded = controlledChannel();
    const boundedExecution = startChannelExecution(bounded, "1", {
      ...runOptions(limits)
    });
    bounded.output.write(encodeFrame(protocolMessage("health", { status: "ready" })));
    assert.equal(
      (await boundedExecution.result as SandboxResult).error?.message,
      "sandbox protocol failed"
    );
    await boundedExecution.terminate();
  }
});

test("writer honors backpressure within the absolute deadline", async () => {
  const channel = stalledChannel();
  const execution = startChannelExecution(channel, "1", {
    ...runOptions(),
    deadlineMs: Date.now() + 80
  });
  channel.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    encodeFrame(protocolMessage("result", validResult("must-not-be-accepted")))
  ]));
  await waitFor(() => channel.writes === 1);
  assert.equal(channel.output.isPaused(), true);
  assert.equal(channel.writes, 1);
  assert(channel.peakWritableLength <= channel.firstWriteBytes);
  assert.deepEqual(await execution.result, {
    result: null,
    error: { message: "sandbox run deadline exceeded" },
    stdout: "",
    stderr: "",
    exitCode: -1,
    timedOut: true
  });
  await execution.terminate();
  assert.equal(channel.stopCalls, 1);
});

test("one backpressured execution cannot alter a concurrent healthy exchange", async () => {
  const hostile = stalledChannel();
  const healthy = controlledChannel();
  const hostileExecution = startChannelExecution(hostile, "hostile", {
    ...runOptions(),
    deadlineMs: Date.now() + 80
  });
  const healthyExecution = startChannelExecution(healthy, "healthy", runOptions());
  hostile.output.write(encodeFrame(protocolMessage("health", { status: "ready" })));
  healthy.output.write(Buffer.concat([
    encodeFrame(protocolMessage("health", { status: "ready" })),
    encodeFrame(protocolMessage("log", { stream: "stdout", text: "independent" })),
    encodeFrame(protocolMessage("result", validResult("healthy")))
  ]));
  const healthyResult = await healthyExecution.result as SandboxResult;
  assert.equal(healthyResult.result, "healthy");
  assert.equal(healthyResult.stdout, "independent");
  assert.equal((await hostileExecution.result as SandboxResult).timedOut, true);
  await Promise.all([healthyExecution.terminate(), hostileExecution.terminate()]);
  assert.equal(healthy.stopCalls, 1);
  assert.equal(hostile.stopCalls, 1);
});

function runOptions(channelLimits = testChannelLimits()) {
  return {
    deadlineMs: Date.now() + 5000,
    signal: new AbortController().signal,
    async hostRpc() { return null; },
    memoryLimitMb: 128,
    channelLimits
  };
}

function testChannelLimits(): WorkerChannelLimits {
  return Object.freeze({
    maxFrameBytes: 2 * 1024 * 1024,
    maxIngressBytes: 32 * 1024 * 1024,
    maxAcceptedMessages: 128,
    maxLogBytes: 2 * 1024 * 1024,
    maxEgressBytes: 32 * 1024 * 1024,
    maxResultBytes: 1024 * 1024
  });
}

function rawJsonFrame(json: string): Buffer {
  const body = Buffer.from(json, "utf8");
  const header = Buffer.alloc(4);
  header.writeUInt32BE(body.length);
  return Buffer.concat([header, body]);
}

function validResult(result: string | number): JsonObject {
  return { result, error: null, exitCode: 0, timedOut: false };
}

function terminalPayloadWithEncodedBytes(totalBytes: number) {
  const result = "combined";
  const baseError = { message: "" };
  const fillerBytes = totalBytes - encodedJsonBytes(result) - encodedJsonBytes(baseError);
  assert(fillerBytes >= 0);
  return {
    result,
    error: { message: "e".repeat(fillerBytes) },
    exitCode: 1,
    timedOut: false
  };
}

function encodedJsonBytes(value: unknown): number {
  return Buffer.byteLength(JSON.stringify(value), "utf8");
}

async function waitFor(predicate: () => boolean): Promise<void> {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (predicate()) {
      return;
    }
    await new Promise(resolve => setImmediate(resolve));
  }
  assert.fail("condition was not reached");
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

function stalledChannel(): WorkerChannel & {
  input: Writable;
  output: PassThrough;
  writes: number;
  firstWriteBytes: number;
  peakWritableLength: number;
  stopCalls: number;
} {
  const output = new PassThrough();
  let resolve!: (status: WorkerChannelStatus) => void;
  const closed = new Promise<WorkerChannelStatus>(value => { resolve = value; });
  let stopped: Promise<void> | undefined;
  const input = new Writable({
    highWaterMark: 1,
    write(chunk, _encoding, _callback) {
      channel.writes += 1;
      channel.firstWriteBytes ||= chunk.byteLength;
      channel.peakWritableLength = Math.max(channel.peakWritableLength, input.writableLength);
    }
  });
  const channel = {
    input,
    output,
    closed,
    writes: 0,
    firstWriteBytes: 0,
    peakWritableLength: 0,
    stopCalls: 0,
    stop() {
      return stopped ??= (async () => {
        channel.stopCalls += 1;
        input.destroy();
        output.end();
        resolve({ exitCode: null, signal: "stopped" });
      })();
    }
  };
  return channel;
}
