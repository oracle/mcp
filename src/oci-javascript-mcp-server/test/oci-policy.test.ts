/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import { OciSdkRuntime, sanitizeJson } from "../src/oci.ts";
import { HostExecutionBroker, canonicalInvoke, developmentPolicy, productionPolicy } from "../src/policy.ts";
import type { ReflectionManifest } from "../src/types.ts";

const manifest: ReflectionManifest = {
  services: {
    core: {
      clients: {
        ComputeClient: {
          operations: ["listInstances", "terminateInstance"],
          requestFields: {
            listInstances: ["compartmentId", "limit"],
            terminateInstance: ["instanceId"]
          }
        }
      }
    }
  }
};

function runtime() {
  class ComputeClient {
    static lastOptions: unknown;
    constructor(options: unknown) { ComputeClient.lastOptions = options; }
    async listInstances(request: unknown) { return { items: [request], httpResponse: { headers: {}, status: 200 } }; }
    async terminateInstance() { return {}; }
    close() {}
  }
  Object.assign(ComputeClient.prototype, { listInstances: ComputeClient.prototype.listInstances });
  const sdk = { core: { ComputeClient } };
  const provider = {
    region: "us-phoenix-1",
    getTenantId: () => "ocid1.tenancy.oc1..test",
    getUserId: () => "ocid1.user.oc1..test",
    getRegion: () => ({ regionId: "us-phoenix-1" }),
    setRegion(value: string) { this.region = value; }
  };
  return new OciSdkRuntime(() => ({ sdk, common: {} }), () => provider);
}

test("discovers installed SDK services and operation request details", () => {
  const real = new OciSdkRuntime();
  const index = real.discover({});
  assert.ok((index.services as string[]).includes("identity"));
  const client = real.discover({ service: "identity", client: "IdentityClient" });
  assert.ok((client.operations as string[]).includes("listRegionSubscriptions"));
  const operation = real.discover({
    service: "identity",
    client: "IdentityClient",
    operation: "listRegionSubscriptions"
  });
  assert.equal(operation.requestType, "ListRegionSubscriptionsRequest");
  assert.ok((operation.requestFields as Array<{ name: string }>).some(field => field.name === "tenancyId"));
});

test("config exposes identity metadata without credentials", () => {
  assert.deepEqual(JSON.parse(JSON.stringify(runtime().config())), {
    tenancyId: "ocid1.tenancy.oc1..test",
    userId: "ocid1.user.oc1..test",
    region: "us-phoenix-1",
    principal: { type: "user", id: "ocid1.user.oc1..test" }
  });
});

test("runtime invocation pins user agent, region, deadlines, retries, and client teardown", async () => {
  const observations: Record<string, any> = {};
  class CircuitBreaker { constructor(options: unknown) { observations.circuitBreaker = options; } }
  class MaxAttemptsTerminationStrategy {
    constructor(attempts: number) { observations.attempts = attempts; }
  }
  class ComputeClient {
    constructor(options: unknown, configuration: unknown) {
      observations.options = options;
      observations.configuration = configuration;
    }
    async listInstances(request: unknown) {
      observations.request = request;
      return { items: [], authenticationDetailsProvider: "remove", httpResponse: { headers: {}, status: 200 } };
    }
    close() { observations.closed = true; }
  }
  const provider = { setRegion: (region: string) => { observations.region = region; } };
  const sdk = new OciSdkRuntime(() => ({
    sdk: { core: { ComputeClient } },
    common: {
      CircuitBreaker,
      NoRetryConfigurationDetails: { retry: false },
      OciSdkDefaultRetryConfiguration: { retryCondition: () => true },
      MaxAttemptsTerminationStrategy
    }
  }), () => provider);
  const value = await sdk.invoke({
    service: "core",
    client: { name: "ComputeClient", options: { region: "us-ashburn-1" } },
    operation: "listInstances",
    request: { compartmentId: "c1" }
  }, 500, 2);
  assert.equal(observations.region, "us-ashburn-1");
  assert.equal(observations.options.additionalUserAgent, "oci-javascript-mcp/0.1.0");
  assert.equal(observations.attempts, 3);
  assert.equal(observations.closed, true);
  assert.deepEqual(JSON.parse(JSON.stringify(value)), { items: [] });

  await assert.rejects(() => sdk.invoke({
    service: "missing", client: { name: "NoClient" }, operation: "getThing", request: {}
  }, 10), /unavailable/);
});

test("discovery and client option validation fail closed", () => {
  const sdk = new OciSdkRuntime();
  assert.throws(() => sdk.discover({ service: "missing" }), /Unknown OCI SDK service/);
  assert.throws(() => sdk.discover({ service: "bad-name" }), /Invalid OCI service/);
  assert.throws(() => sdk.discover({ unexpected: "claim" } as any), /Unsupported discovery/);
});

test("canonical request validation is allowlisted and read-only", () => {
  const policy = developmentPolicy(manifest, Date.now() + 10_000);
  const valid = canonicalInvoke({
    service: "core",
    client: { name: "ComputeClient", options: { region: "us-ashburn-1" } },
    operation: "listInstances",
    request: { compartmentId: "ocid1.compartment.oc1..test", limit: 5 }
  }, manifest, policy);
  assert.equal(valid.request?.limit, 5);
  assert.equal(Object.getPrototypeOf(valid.request), null);
  assert.throws(() => canonicalInvoke({
    service: "core", client: { name: "ComputeClient" }, operation: "listInstances",
    request: { endpoint: "https://evil.example" }
  }, manifest, policy), /not authorized/);
  assert.throws(() => canonicalInvoke({
    service: "core", client: { name: "ComputeClient", options: { endpoint: "evil" } },
    operation: "listInstances", request: {}
  }, manifest, policy), /only support|Unsupported/);
  assert.throws(() => canonicalInvoke({
    service: "core", client: { name: "ComputeClient" }, operation: "terminateInstance",
    request: { instanceId: "ocid1.instance.oc1..test" }
  }, manifest, policy), /read-only/);
  assert.throws(() => canonicalInvoke({
    service: "core", client: { name: "ComputeClient" }, operation: "listInstances",
    request: { executionId: "another" }
  }, manifest, policy), /identity or policy claim/);
});

test("policy enforces region, tenancy, compartment, resource, and operation scopes", () => {
  const base = developmentPolicy(manifest, Date.now() + 10_000, {
    allowMutations: true,
    allowedRegions: new Set(["us-phoenix-1"]),
    allowedTenancyIds: new Set(["t1"]),
    allowedCompartmentIds: new Set(["c1"]),
    allowedResourceIds: new Set(["i1"])
  });
  assert.throws(() => canonicalInvoke({
    service: "core", client: { name: "ComputeClient", options: { region: "us-ashburn-1" } },
    operation: "listInstances", request: { compartmentId: "c1" }
  }, manifest, base), /region/);
  assert.throws(() => canonicalInvoke({
    service: "core", client: { name: "ComputeClient" }, operation: "listInstances",
    request: { compartmentId: "c2" }
  }, manifest, base), /compartment/);
  assert.throws(() => canonicalInvoke({
    service: "core", client: { name: "ComputeClient" }, operation: "terminateInstance",
    request: { instanceId: "i2" }
  }, manifest, base), /resource/);
  assert.equal(productionPolicy(Date.now() + 1000).allowedOperations.size, 0);
});

test("broker enforces call, concurrency, request, response, deadline, and cancellation budgets", async () => {
  const sdk = runtime();
  Object.defineProperty(sdk, "manifest", { value: () => manifest });
  const oneCall = developmentPolicy(manifest, Date.now() + 10_000, { maxCalls: 1 });
  const broker = new HostExecutionBroker(sdk, oneCall);
  const request = {
    operation: "invoke" as const,
    payload: {
      service: "core", client: { name: "ComputeClient" }, operation: "listInstances",
      request: { compartmentId: "c1" }
    }
  };
  await broker.handle(request);
  await assert.rejects(() => broker.handle(request), /call limit/);
  const cancelled = new HostExecutionBroker(sdk, developmentPolicy(manifest, Date.now() + 10_000));
  cancelled.cancel();
  await assert.rejects(() => cancelled.handle(request), /cancelled/);
  const expired = new HostExecutionBroker(sdk, developmentPolicy(manifest, Date.now() - 1));
  await assert.rejects(() => expired.handle(request), /deadline/);
  const tiny = new HostExecutionBroker(sdk, developmentPolicy(manifest, Date.now() + 10_000, { maxRequestBytes: 2 }));
  await assert.rejects(() => tiny.handle(request), /request exceeds/);

  const largeResponseRuntime = runtime();
  Object.defineProperties(largeResponseRuntime, {
    manifest: { value: () => manifest },
    invoke: { value: async () => ({ value: "x".repeat(100) }) }
  });
  const responseLimited = new HostExecutionBroker(
    largeResponseRuntime,
    developmentPolicy(manifest, Date.now() + 10_000, { maxResponseBytes: 10 })
  );
  await assert.rejects(() => responseLimited.handle(request), /response exceeds/);

  let release!: () => void;
  const blockedRuntime = runtime();
  Object.defineProperties(blockedRuntime, {
    manifest: { value: () => manifest },
    invoke: { value: () => new Promise(resolve => { release = () => resolve({}); }) }
  });
  const concurrent = new HostExecutionBroker(
    blockedRuntime,
    developmentPolicy(manifest, Date.now() + 10_000, { maxConcurrentCalls: 1 })
  );
  const first = concurrent.handle(request);
  await new Promise(resolve => setImmediate(resolve));
  await assert.rejects(() => concurrent.handle(request), /concurrency limit/);
  release();
  await first;
});

test("response sanitizer removes credentials, transports, cycles, and unsupported values", () => {
  const value: Record<string, unknown> = {
    ok: true,
    privateKey: "secret",
    response: { headers: {}, status: 200 },
    date: new Date("2026-01-01T00:00:00.000Z"),
    bytes: new Uint8Array([1, 2])
  };
  value.self = value;
  assert.deepEqual(JSON.parse(JSON.stringify(sanitizeJson(value))), {
    ok: true,
    date: "2026-01-01T00:00:00.000Z",
    bytes: "AQI=",
    self: "[Circular]"
  });
  assert.equal(sanitizeJson(12n), "12");
  assert.equal(sanitizeJson(Number.POSITIVE_INFINITY), "Infinity");
  assert.equal(sanitizeJson(undefined), "undefined");
  assert.equal((sanitizeJson({ nested: { value: 1 } }, 0) as any).nested, "[MaxDepth]");
});
