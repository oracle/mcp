/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import { createOciFacade, inferFinalExpression } from "../src/facade.ts";
import type { Json, JsonObject, ReflectionManifest } from "../src/types.ts";

const manifest: ReflectionManifest = {
  services: {
    core: {
      clients: {
        ComputeClient: {
          operations: ["listInstances"],
          requestFields: { listInstances: ["compartmentId"] }
        }
      }
    }
  }
};

test("facade exposes reflective static and constructed OCI calls", async () => {
  const calls: Array<{ operation: string; payload: JsonObject }> = [];
  const facade = createOciFacade(manifest, async (operation, payload): Promise<Json> => {
    calls.push({ operation, payload });
    if (operation === "config") return { tenancyId: "t1" };
    return { items: [] };
  }) as any;
  assert.deepEqual(Object.keys(facade), ["config", "core"]);
  assert.deepEqual(Object.keys(facade.core), ["ComputeClient"]);
  assert.deepEqual(Object.keys(new facade.core.ComputeClient()), ["listInstances"]);
  assert.equal((await facade.config()).tenancyId, "t1");
  await facade.core.ComputeClient.listInstances({ compartmentId: "c1" });
  await new facade.core.ComputeClient({ region: "us-ashburn-1" }).listInstances({ compartmentId: "c2" });
  assert.equal(calls[1]?.payload.operation, "listInstances");
  assert.equal((calls[2]?.payload.client as any).options.region, "us-ashburn-1");
  assert.equal(facade.unknown, undefined);
  assert.equal(facade.core.UnknownClient.then, undefined);
});

test("facade rejects invalid names and options", () => {
  const facade = createOciFacade(manifest, async () => null) as any;
  assert.throws(() => new facade.core.ComputeClient({ endpoint: "https://evil.example" }), /only support region/);
  assert.throws(() => new facade.core.ComputeClient({ region: "not-a-region" }), /Invalid/);
  assert.throws(() => facade.core["bad-name"], /Invalid OCI client/);
});

test("final-expression inference handles expressions, statements, strings, and comments", () => {
  assert.match(inferFinalExpression("const x = 1;\nx + 2;"), /return \(x \+ 2\)/);
  assert.match(inferFinalExpression("({ value: ';' })"), /return \(\(\{ value/);
  assert.match(inferFinalExpression("const x = 1; // comment\nx"), /return \(x\)/);
  assert.equal(inferFinalExpression("throw new Error('x')"), "throw new Error('x')");
});
