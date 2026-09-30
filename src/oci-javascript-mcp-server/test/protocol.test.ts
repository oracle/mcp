/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import {
  DEFAULT_DECODE_LIMITS,
  decodeJson,
  encodePayload
} from "../src/protocol.ts";

test("JSON payloads round trip into validated plain objects without rebuilding them", t => {
  const value = { items: [null, true, false, 42, "hello", { nested: {} }] };
  const decoded = decodeJson(encodePayload(value));
  assert.equal(JSON.stringify(decoded), JSON.stringify(value));
  assert.deepEqual(decoded, value);
  const parsed = JSON.parse(JSON.stringify(value));
  t.mock.method(JSON, "parse", () => parsed);
  assert.equal(decodeJson(encodePayload(value)), parsed);
});

test("JSON payloads reject malformed, empty, truncated, invalid UTF-8, and oversized input", () => {
  for (const text of ["", "{", '["x"']) {
    assert.throws(() => decodeJson(Buffer.from(text)), /valid JSON/);
  }
  assert.throws(() => decodeJson(Buffer.from([0xff])), /UTF-8/);
  assert.throws(() => decodeJson(Buffer.alloc(DEFAULT_DECODE_LIMITS.maxFrameBytes + 1)), /exceeds limit/);
  assert.throws(() => encodePayload({ value: "12345" }, 4), /exceeds limit/);
  assert.throws(() => decodeJson(Buffer.from("1e999")), /non-finite/);
});

test("JSON payloads reject dangerous keys recursively without pollution", () => {
  for (const key of ["__proto__", "prototype", "constructor"]) {
    assert.throws(
      () => decodeJson(Buffer.from(`{"safe":{"${key}":{}}}`)),
      new RegExp(`dangerous key '${key}'`)
    );
  }
  assert.equal(({} as { polluted?: unknown }).polluted, undefined);
});

test("JSON payloads enforce structural and allocation limits", () => {
  const limits = {
    ...DEFAULT_DECODE_LIMITS,
    maxDepth: 2,
    maxStringBytes: 10,
    maxArrayLength: 2,
    maxObjectKeys: 5,
    maxNodes: 8
  };
  for (const [text, pattern] of [
    ['"12345678901"', /string/],
    ['{"12345678901":0}', /object key/],
    ["[1,2,3]", /array/],
    ['{"a":{"b":{"c":1}}}', /depth/],
    ['{"a":1,"b":2,"c":3,"d":4,"e":5,"f":6}', /object-key/],
    ['{"a":[1,2],"b":[3,4],"c":[5,6]}', /node/]
  ] as const) {
    assert.throws(() => decodeJson(Buffer.from(text), limits), pattern);
  }
});
