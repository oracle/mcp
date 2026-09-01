/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import {
  DEFAULT_DECODE_LIMITS,
  FrameDecoder,
  ProtocolError,
  assertExactFields,
  decodePayload,
  encodeFrame,
  protocolMessage
} from "../src/protocol.ts";

test("protocol round trips split and coalesced frames", () => {
  const first = encodeFrame(protocolMessage("health", { status: "ready" }));
  const second = encodeFrame(protocolMessage("log", { stream: "stdout", text: "hello" }));
  const decoder = new FrameDecoder();
  assert.deepEqual([...decoder.push(first.subarray(0, 2))], []);
  const messages = decoder.push(Buffer.concat([first.subarray(2), second]));
  assert.equal(messages.next().value?.type, "health");
  assert.equal(decoder.queuedBytes, 0);
  assert.equal(messages.next().value?.type, "log");
  assert.equal(messages.next().done, true);
  decoder.end();
});

test("protocol assembles highly fragmented frames with bounded queued bytes", () => {
  const limits = { ...DEFAULT_DECODE_LIMITS, maxFrameBytes: 64 * 1024 };
  const frame = encodeFrame(protocolMessage("log", {
    stream: "stdout",
    text: "x".repeat(60 * 1024)
  }), limits.maxFrameBytes);
  const decoder = new FrameDecoder(limits);
  const messages = [];
  for (let offset = 0; offset < frame.length; offset += 1) {
    messages.push(...decoder.push(frame.subarray(offset, offset + 1)));
    assert(decoder.queuedBytes <= limits.maxFrameBytes + 4);
  }
  assert.equal(messages.length, 1);
  assert.equal(messages[0]?.type, "log");
  assert.equal(messages[0]?.text, "x".repeat(60 * 1024));
  assert.equal(decoder.queuedBytes, 0);
  decoder.end();
});

test("protocol keeps a maximum frame within the header-plus-body queue bound", () => {
  const prefix = Buffer.from('{"version":1,"type":"health","status":"ready"}', "utf8");
  const body = Buffer.alloc(DEFAULT_DECODE_LIMITS.maxFrameBytes, 0x20);
  prefix.copy(body);
  const header = Buffer.alloc(4);
  header.writeUInt32BE(body.length);
  const decoder = new FrameDecoder();

  assert.deepEqual([...decoder.push(header)], []);
  assert.equal(decoder.queuedBytes, 0);
  assert.deepEqual([...decoder.push(body.subarray(0, -1))], []);
  assert.equal(decoder.queuedBytes, DEFAULT_DECODE_LIMITS.maxFrameBytes - 1);
  const messages = [...decoder.push(body.subarray(-1))];
  assert.equal(messages[0]?.type, "health");
  assert.equal(decoder.queuedBytes, 0);
  decoder.end();
});

test("protocol rejects oversized frames before receiving a body", () => {
  const header = Buffer.alloc(4);
  header.writeUInt32BE(DEFAULT_DECODE_LIMITS.maxFrameBytes + 1);
  assert.throws(() => [...new FrameDecoder().push(header)], /exceeds limit/);
});

test("protocol rejects malformed, empty, truncated, invalid UTF-8, and unknown versions", () => {
  assert.throws(() => decodePayload(Buffer.from("{")), /valid JSON/);
  assert.throws(() => [...new FrameDecoder().push(Buffer.alloc(4))], /empty frames/);
  const decoder = new FrameDecoder();
  [...decoder.push(Buffer.from([0, 0, 0, 2, 0x7b]))];
  assert.throws(() => decoder.end(), /truncated/);
  assert.throws(() => decodePayload(Buffer.from([0xff])), /UTF-8/);
  assert.throws(
    () => decodePayload(Buffer.from('{"version":2,"type":"health"}')),
    /unsupported protocol version/
  );
});

test("protocol rejects dangerous keys recursively without pollution", () => {
  for (const key of ["__proto__", "prototype", "constructor"]) {
    const body = Buffer.from(
      `{"version":1,"type":"rpc","payload":{"safe":{"${key}":{}}}}`
    );
    assert.throws(() => decodePayload(body), new RegExp(`dangerous key '${key}'`));
  }
  assert.equal(({} as { polluted?: unknown }).polluted, undefined);
});

test("protocol enforces structural and allocation limits", () => {
  const limits = {
    ...DEFAULT_DECODE_LIMITS,
    maxDepth: 2,
    maxStringBytes: 10,
    maxArrayLength: 2,
    maxObjectKeys: 5,
    maxNodes: 8
  };
  assert.throws(
    () => decodePayload(Buffer.from('{"version":1,"type":"12345678901"}'), limits),
    /string/
  );
  assert.throws(
    () => decodePayload(Buffer.from('{"version":1,"type":"x","a":[1,2,3]}'), limits),
    /array/
  );
  assert.throws(
    () => decodePayload(Buffer.from('{"version":1,"type":"x","a":{"b":{"c":1}}}'), limits),
    /depth/
  );
  assert.throws(
    () => decodePayload(Buffer.from('{"version":1,"type":"x","a":1,"b":2,"c":3,"d":4}'), limits),
    /object-key/
  );
  assert.throws(() => encodeFrame({ value: "12345" }, 4), ProtocolError);
});

test("protocol strict schemas reject unknown and missing fields", () => {
  const message = decodePayload(
    Buffer.from('{"version":1,"type":"health","status":"ready","claim":"x"}')
  );
  assert.throws(
    () => assertExactFields(message, ["version", "type", "status"]),
    /unknown field 'claim'/
  );
  assert.throws(
    () => assertExactFields(protocolMessage("health"), ["version", "type", "status"]),
    /missing field 'status'/
  );
});
