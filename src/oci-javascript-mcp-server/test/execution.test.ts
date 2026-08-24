/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { runJavaScript } from "../src/execution.ts";
import { OciSdkRuntime } from "../src/oci.ts";
import { admitProvider } from "../src/isolation/admission.ts";
import { AppleContainerIsolationProvider } from "../src/isolation/apple-container.ts";
import { ProcessIsolationProvider } from "../src/isolation/process.ts";
import type { OciInvokePayload, ReflectionManifest } from "../src/types.ts";

const manifest: ReflectionManifest = {
  services: {
    identity: {
      clients: {
        IdentityClient: {
          operations: ["listRegionSubscriptions"],
          requestFields: { listRegionSubscriptions: ["tenancyId", "limit"] }
        }
      }
    },
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

function mockRuntime(): OciSdkRuntime {
  const instance = new OciSdkRuntime(() => ({ sdk: {}, common: {} }), () => ({}));
  Object.defineProperties(instance, {
    manifest: { value: () => manifest },
    config: { value: () => ({ tenancyId: "tenancy", region: "us-phoenix-1" }) },
    invoke: {
      value: async (payload: OciInvokePayload) => ({
        service: payload.service,
        client: payload.client.name,
        operation: payload.operation,
        region: payload.client.options?.region ?? null,
        request: payload.request ?? {}
      })
    }
  });
  return instance;
}

function provider(): ProcessIsolationProvider {
  return new ProcessIsolationProvider({ allowInsecure: true });
}

async function run(code: string, timeoutSeconds = 3) {
  return runJavaScript(code, {
    provider: provider(),
    runtime: mockRuntime(),
    mode: "development",
    timeoutSeconds
  });
}

test("executes final expressions and captures stdout and stderr", async () => {
  const result = await run('console.log("hello", 7); console.error("oops"); 20 + 22');
  assert.equal(result.result, 42);
  assert.equal(result.stdout, "hello 7\n");
  assert.equal(result.stderr, "oops\n");
  assert.equal(result.exitCode, 0);
  assert.equal(result.error, null);
});

test("supports oci.config, static calls, constructed clients, and shallow reflection", async () => {
  const result = await run(`
    const config = await oci.config();
    const direct = await oci.identity.IdentityClient.listRegionSubscriptions({tenancyId: config.tenancyId});
    const compute = new oci.core.ComputeClient({region: "us-ashburn-1"});
    const instances = await compute.listInstances({compartmentId: "c1", limit: 2});
    ({
      config,
      direct,
      instances,
      services: Object.keys(oci),
      identityClients: Object.keys(oci.identity),
      computeOperations: Object.keys(compute)
    })
  `);
  assert.equal((result.result as any).config.tenancyId, "tenancy");
  assert.equal((result.result as any).direct.operation, "listRegionSubscriptions");
  assert.equal((result.result as any).instances.region, "us-ashburn-1");
  assert.ok((result.result as any).services.includes("config"));
  assert.ok((result.result as any).services.includes("core"));
  assert.deepEqual((result.result as any).identityClients, ["IdentityClient"]);
  assert.ok((result.result as any).computeOperations.includes("listInstances"));
});

test("does not expose Node globals or arbitrary client endpoints", async () => {
  const globals = await run("({process: typeof process, require: typeof require, fetch: typeof fetch})");
  assert.deepEqual(JSON.parse(JSON.stringify(globals.result)), {
    process: "undefined", require: "undefined", fetch: "undefined"
  });
  const endpoint = await run('new oci.core.ComputeClient({endpoint: "https://evil.example"})');
  assert.match(endpoint.error?.message ?? "", /only support region/);
});

test("returns structured JavaScript errors", async () => {
  const result = await run('throw new Error("boom")');
  assert.equal(result.result, null);
  assert.equal(result.exitCode, 1);
  assert.equal(result.timedOut, false);
  assert.match(result.error?.message ?? "", /boom/);
});

test("bounds captured output", async () => {
  const result = await run('console.log("x".repeat(1100000)); "done"');
  assert.equal(result.result, "done");
  assert.ok(Buffer.byteLength(result.stdout, "utf8") <= 1024 * 1024);
});

test("times out and tears down a pending runner", async () => {
  const result = await run("await new Promise(() => {})", 1);
  assert.equal(result.timedOut, true);
  assert.equal(result.exitCode, -1);
  assert.match(result.error?.message ?? "", /timed out/);
});

test("AbortSignal cancels and tears down the runner", async () => {
  const controller = new AbortController();
  const promise = runJavaScript("await new Promise(() => {})", {
    provider: provider(), runtime: mockRuntime(), mode: "development",
    timeoutSeconds: 10, signal: controller.signal
  });
  setTimeout(() => controller.abort(), 50);
  const result = await promise;
  assert.match(result.error?.message ?? "", /cancelled/);
  assert.equal(result.timedOut, false);
});

test("direct raw-channel mutation is denied after runner compromise", async () => {
  const rawRunner = fileURLToPath(new URL("./raw-runner.ts", import.meta.url));
  const result = await runJavaScript("0", {
    provider: new ProcessIsolationProvider({ allowInsecure: true, runnerPath: rawRunner }),
    runtime: mockRuntime(),
    mode: "development",
    timeoutSeconds: 3
  });
  assert.match((result.result as any).message, /read-only/);
});

test("local provider requires opt-in and is rejected in production", () => {
  assert.throws(() => new ProcessIsolationProvider({ allowInsecure: false }), /requires/);
  assert.throws(() => admitProvider(provider(), "production"), /not admitted in production/);
  assert.doesNotThrow(() => admitProvider(provider(), "development"));
  assert.doesNotThrow(() => admitProvider({
    capabilities: {
      provider: "test-vm",
      boundary: "virtual-machine",
      developmentOnly: false,
      separateGuestKernel: true,
      hardwareVirtualization: true,
      networkCreationBlocked: true
    },
    async start() { throw new Error("not used"); }
  }, "production"));
});

test("Apple container provider runs over pipes with hardened development capabilities", async () => {
  const fakeCli = fileURLToPath(new URL("./fake-apple-container.ts", import.meta.url));
  const appleProvider = new AppleContainerIsolationProvider({
    cliPath: fakeCli,
    image: "test-runner:dev",
    network: "test-internal"
  });
  const result = await runJavaScript("20 + 22", {
    provider: appleProvider,
    runtime: mockRuntime(),
    mode: "development",
    timeoutSeconds: 3
  });
  assert.equal(result.result, 42);
  assert.deepEqual(appleProvider.capabilities, {
    provider: "apple-container",
    boundary: "virtual-machine",
    developmentOnly: true,
    separateGuestKernel: true,
    hardwareVirtualization: true,
    networkCreationBlocked: false
  });
  assert.throws(() => admitProvider(appleProvider, "production"), /not admitted in production/);
});

test("Apple container provider rejects unsafe CLI-controlled values", () => {
  assert.throws(
    () => new AppleContainerIsolationProvider({ image: "--volume=/Users" }),
    /image is invalid/
  );
  assert.throws(
    () => new AppleContainerIsolationProvider({ network: "bad network" }),
    /network is invalid/
  );
  assert.throws(
    () => new AppleContainerIsolationProvider({ cliPath: "" }),
    /CLI path is invalid/
  );
});
