/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { fromJson, toJson } from "../src/json.ts";

test("toJson serializes non-JSON JavaScript values with type tags", () => {
  const encoded = toJson({
    date: new Date("2026-06-03T12:00:00.000Z"),
    big: 123n,
    bytes: new Uint8Array([1, 2, 3]),
    set: new Set(["a", "b"]),
    nan: Number.NaN
  });

  assert.deepEqual(encoded, {
    date: { __oci_wire_type: "datetime", value: "2026-06-03T12:00:00.000Z" },
    big: { __oci_wire_type: "bigint", value: "123" },
    bytes: { __oci_wire_type: "bytes", encoding: "base64", value: "AQID" },
    set: { __oci_wire_type: "set", items: ["a", "b"] },
    nan: { __oci_wire_type: "float", value: "nan" }
  });
});

test("toJson preserves request-shaped fields", () => {
  assert.deepEqual(toJson({
    value: 1,
    omitted: undefined,
    array: [undefined],
    request: {
      id: "request-id",
      page: undefined
    }
  }), {
    value: 1,
    array: [null],
    request: { id: "request-id" }
  });
});

test("toJson handles circular container values", () => {
  const array: unknown[] = [];
  array.push(array);
  const map = new Map<unknown, unknown>();
  map.set("self", map);

  assert.deepEqual(toJson({ array, map }), {
    array: [{ __oci_wire_type: "repr", value: "[Circular]" }],
    map: {
      __oci_wire_type: "map",
      items: [["self", { __oci_wire_type: "repr", value: "[Circular]" }]]
    }
  });
});

test("fromJson decodes tagged request values", () => {
  const decoded = fromJson({
    when: { __oci_wire_type: "datetime", value: "2026-06-03T00:00:00.000Z" },
    big: { __oci_wire_type: "bigint", value: "123" },
    bytes: { __oci_wire_type: "bytes", encoding: "base64", value: "AQID" },
    tags: { __oci_wire_type: "map", items: [["a", 1]] }
  }) as Record<string, unknown>;

  assert(decoded.when instanceof Date);
  assert.equal((decoded.when as Date).toISOString(), "2026-06-03T00:00:00.000Z");
  assert.equal(decoded.big, 123n);
  assert.deepEqual(Array.from(decoded.bytes as Buffer), [1, 2, 3]);
  assert(decoded.tags instanceof Map);
  assert.equal((decoded.tags as Map<string, number>).get("a"), 1);
});

test("fromJson rejects unknown tagged values", () => {
  assert.throws(
    () => fromJson({ __oci_wire_type: "mystery", value: "x" }),
    /Unknown OCI wire type 'mystery'/
  );
});
