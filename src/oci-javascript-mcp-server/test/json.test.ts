/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { fromJson } from "../src/json.ts";

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

test("fromJson decodes arrays, sets, representations, and floating-point tags", () => {
  const decoded = fromJson({
    array: [1, { nested: true }],
    set: { __oci_wire_type: "set", items: ["a", "b"] },
    representation: { __oci_wire_type: "repr", value: "display" },
    nan: { __oci_wire_type: "float", value: "nan" },
    positiveInfinity: { __oci_wire_type: "float", value: "inf" },
    negativeInfinity: { __oci_wire_type: "float", value: "-inf" },
    numericFloat: { __oci_wire_type: "float", value: 12.5 }
  }) as Record<string, unknown>;

  assert.deepEqual(decoded.array, [1, { nested: true }]);
  assert.deepEqual(Array.from(decoded.set as Set<string>), ["a", "b"]);
  assert.equal(decoded.representation, "display");
  assert.equal(Number.isNaN(decoded.nan), true);
  assert.equal(decoded.positiveInfinity, Number.POSITIVE_INFINITY);
  assert.equal(decoded.negativeInfinity, Number.NEGATIVE_INFINITY);
  assert.equal(decoded.numericFloat, 12.5);
});
