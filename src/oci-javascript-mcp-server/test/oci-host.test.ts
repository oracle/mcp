/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { createOciReflectionManifest, createOciSdkHostRpc } from "../src/oci-host.ts";

test("host RPC config returns principal from config-file user", async () => {
  class Provider {
    getTenantId() {
      return "ocid1.tenancy.oc1..example";
    }

    getUser() {
      return "ocid1.user.oc1..example";
    }

    getFingerprint() {
      return "aa:bb:cc";
    }

    getRegion() {
      return { regionId: "us-ashburn-1" };
    }
  }

  const result = await withTemporaryOciConfig(
    "[DEFAULT]\ntenancy=ocid1.tenancy.oc1..example\nregion=us-ashburn-1\n",
    async () => {
      const hostRpc = createOciSdkHostRpc(() => ({
        sdk: {
          ConfigFileAuthenticationDetailsProvider: Provider
        },
        common: {}
      }));
      return hostRpc({
        binding: "oracle",
        namespace: "oci",
        operation: "config",
        payload: {}
      });
    }
  );

  assert.deepEqual(result, {
    tenancyId: "ocid1.tenancy.oc1..example",
    userId: "ocid1.user.oc1..example",
    fingerprint: "aa:bb:cc",
    region: "us-ashburn-1",
    principal: {
      type: "user",
      id: "ocid1.user.oc1..example"
    }
  });
});

test("host RPC config derives only principal id from session token", async () => {
  const token = fakeJwt({
    sub: "ocid1.user.oc1..sessionuser",
    email: "user@example.com",
    privateClaim: "do-not-return"
  });

  class SessionProvider {
    getTenantId() {
      return "ocid1.tenancy.oc1..example";
    }

    getUser() {
      return "";
    }

    getFingerprint() {
      return "aa:bb:cc";
    }

    getRegion() {
      return { regionId: "us-ashburn-1" };
    }

    get sessionToken() {
      return token;
    }
  }

  const result = await withTemporaryOciConfig(
    [
      "[DEFAULT]",
      "tenancy=ocid1.tenancy.oc1..example",
      "region=us-ashburn-1",
      "security_token_file=/not/read/by/mock"
    ].join("\n"),
    async () => {
      const hostRpc = createOciSdkHostRpc(() => ({
        sdk: {},
        common: {
          SessionAuthDetailProvider: SessionProvider
        }
      }));
      return hostRpc({
        binding: "oracle",
        namespace: "oci",
        operation: "config",
        payload: {}
      });
    }
  );

  assert.deepEqual(result, {
    tenancyId: "ocid1.tenancy.oc1..example",
    userId: "ocid1.user.oc1..sessionuser",
    fingerprint: "aa:bb:cc",
    region: "us-ashburn-1",
    principal: {
      type: "user",
      id: "ocid1.user.oc1..sessionuser"
    }
  });
  assert.equal(JSON.stringify(result).includes(token), false);
  assert.equal(JSON.stringify(result).includes("user@example.com"), false);
  assert.equal(JSON.stringify(result).includes("do-not-return"), false);
});

test("host RPC invokes OCI JavaScript SDK clients", async () => {
  const calls: unknown[] = [];
  class ComputeClient {
    constructor(options: unknown) {
      calls.push({ constructor: options });
    }

    async listInstances(request: unknown) {
      calls.push({ listInstances: request });
      return { items: [{ displayName: "zavala" }], opcNextPage: "next" };
    }

    close() {
      calls.push({ close: true });
    }
  }

  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient }
    },
    common: {}
  }));

  const result = await hostRpc({
    binding: "oracle",
    namespace: "oci",
    operation: "invoke",
    payload: {
      service: "core",
      client: { name: "ComputeClient" },
      operation: "listInstances",
      request: {
        compartmentId: "ocid1.compartment.oc1..example",
        when: { __oci_wire_type: "datetime", value: "2026-06-03T00:00:00.000Z" }
      }
    }
  });

  assert.deepEqual(result, {
    items: [{ displayName: "zavala" }],
    opcNextPage: "next"
  });
  assert.equal(
    (calls[0] as { constructor: { additionalUserAgent?: string } }).constructor.additionalUserAgent,
    "oci-javascript-mcp/0.1.0"
  );
  assert.deepEqual(calls[1], {
      listInstances: {
        compartmentId: "ocid1.compartment.oc1..example",
        when: new Date("2026-06-03T00:00:00.000Z")
      }
  });
  assert.deepEqual(calls[2], { close: true });
});

test("host RPC applies per-client region to a fresh provider", async () => {
  const calls: unknown[] = [];
  class Provider {
    setRegion(region: string) {
      calls.push({ setRegion: region });
    }
  }
  class ComputeClient {
    constructor(options: unknown) {
      calls.push({ constructor: options });
    }

    async listInstances(request: unknown) {
      calls.push({ listInstances: request });
      return { items: [] };
    }
  }

  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: Provider,
      core: { ComputeClient }
    },
    common: {}
  }));

  await hostRpc({
    binding: "oracle",
    namespace: "oci",
    operation: "invoke",
    payload: {
      service: "core",
      client: {
        name: "ComputeClient",
        options: { region: "us-phoenix-1" }
      },
      operation: "listInstances",
      request: { compartmentId: "ocid1.compartment.oc1..example" }
    }
  });

  assert.deepEqual(calls[0], { setRegion: "us-phoenix-1" });
  assert.deepEqual(calls[2], {
    listInstances: {
      compartmentId: "ocid1.compartment.oc1..example"
    }
  });
});

test("host RPC applies trusted deadline context to OCI client configuration", async () => {
  const calls: unknown[] = [];
  class CircuitBreaker {
    circuit = {};

    constructor(options: unknown) {
      calls.push({ circuitBreaker: options });
    }
  }
  class ComputeClient {
    constructor(options: unknown, clientConfiguration: unknown) {
      calls.push({ constructor: { options, clientConfiguration } });
    }

    async listInstances(request: unknown) {
      calls.push({ listInstances: request });
      return { items: [] };
    }
  }

  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient }
    },
    common: { CircuitBreaker }
  }));
  await hostRpc({
    binding: "oracle",
    namespace: "oci",
    operation: "invoke",
    payload: {
      service: "core",
      client: { name: "ComputeClient" },
      operation: "listInstances",
      request: { compartmentId: "ocid1.compartment.oc1..example" }
    }
  }, 1234.2);

  assert.deepEqual(calls[0], { circuitBreaker: { timeout: 1235 } });
  const constructorCall = calls[1] as {
    constructor: {
      clientConfiguration: {
        circuitBreaker: unknown;
        httpOptions?: unknown;
      };
    };
  };
  assert.equal(constructorCall.constructor.clientConfiguration.circuitBreaker instanceof CircuitBreaker, true);
  assert.equal(constructorCall.constructor.clientConfiguration.httpOptions, undefined);
});

test("host RPC rejects unsupported client options", async () => {
  const hostRpc = createOciSdkHostRpc(() => ({ sdk: {}, common: {} }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: {
          name: "ComputeClient",
          options: { endpoint: "https://example.invalid" } as never
        },
        operation: "listInstances",
        request: {}
      }
    }),
    /Unsupported OCI client option 'endpoint'.*Client options only support region/
  );
});

test("host RPC rejects malformed client regions", async () => {
  const hostRpc = createOciSdkHostRpc(() => ({ sdk: {}, common: {} }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: {
          name: "ComputeClient",
          options: { region: "example.com" }
        },
        operation: "listInstances",
        request: {}
      }
    }),
    /Invalid OCI client option region 'example.com'/
  );
});

test("host RPC redacts HTTP transport artifacts without changing normal fields", async () => {
  class ComputeClient {
    async getInstance() {
      const response: any = {
        request: { id: "business-request-field" },
        httpRequest: {
          method: "GET",
          url: "https://iaas.example.invalid",
          headers: { authorization: "redacted" }
        },
        nested: {
          authenticationDetailsProvider: {
            privateKey: "redacted"
          },
          request: {
            method: "POST",
            url: "https://iaas.example.invalid",
            headers: { authorization: "redacted" }
          },
          value: 1
        },
        signer: { sessionToken: "redacted" }
      };
      response.self = response;
      return response;
    }
  }

  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient }
    },
    common: {}
  }));

  const result = await hostRpc({
    binding: "oracle",
    namespace: "oci",
    operation: "invoke",
    payload: {
      service: "core",
      client: { name: "ComputeClient" },
      operation: "getInstance",
      request: { instanceId: "ocid1.instance.oc1..example" }
    }
  });

  assert.deepEqual(result, {
    request: { id: "business-request-field" },
    nested: { value: 1 },
    self: "[Circular]"
  });
});

test("host RPC rejects SDK helper methods before invocation", async () => {
  let helperCalled = false;
  class ComputeClient {
    createWaiters() {
      helperCalled = true;
      return {
        authenticationDetailsProvider: {
          privateKey: "do-not-return",
          sessionToken: "do-not-return"
        }
      };
    }
  }

  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient }
    },
    common: {}
  }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: { name: "ComputeClient" },
        operation: "createWaiters",
        request: {}
      }
    }),
    /Unknown OCI SDK operation 'core.ComputeClient.createWaiters'/
  );
  assert.equal(helperCalled, false);
});

test("host RPC points SDK pagination helpers to direct list page tokens", async () => {
  let helperCalled = false;
  class ComputeClient {
    listInstances() {}

    listAllInstances() {
      helperCalled = true;
    }
  }

  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient }
    },
    common: {}
  }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: { name: "ComputeClient" },
        operation: "listAllInstances",
        request: {}
      }
    }),
    /call ComputeClient\.listInstances directly and pass response\.opcNextPage as request\.page/
  );
  assert.equal(helperCalled, false);
});

async function withTemporaryOciConfig<T>(
  contents: string,
  callback: () => Promise<T>
): Promise<T> {
  const directory = mkdtempSync(join(tmpdir(), "oci-javascript-mcp-server-"));
  const configPath = join(directory, "config");
  const previousConfigFile = process.env.OCI_CONFIG_FILE;
  const previousConfigProfile = process.env.OCI_CONFIG_PROFILE;
  try {
    writeFileSync(configPath, contents, "utf8");
    process.env.OCI_CONFIG_FILE = configPath;
    process.env.OCI_CONFIG_PROFILE = "DEFAULT";
    return await callback();
  } finally {
    if (previousConfigFile === undefined) {
      delete process.env.OCI_CONFIG_FILE;
    } else {
      process.env.OCI_CONFIG_FILE = previousConfigFile;
    }
    if (previousConfigProfile === undefined) {
      delete process.env.OCI_CONFIG_PROFILE;
    } else {
      process.env.OCI_CONFIG_PROFILE = previousConfigProfile;
    }
    rmSync(directory, { recursive: true, force: true });
  }
}

function fakeJwt(payload: Record<string, unknown>): string {
  return [
    base64UrlJson({ alg: "none", typ: "JWT" }),
    base64UrlJson(payload),
    "signature"
  ].join(".");
}

function base64UrlJson(value: Record<string, unknown>): string {
  return Buffer.from(JSON.stringify(value), "utf8")
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

test("host RPC rejects invalid identifiers before SDK lookup", async () => {
  const hostRpc = createOciSdkHostRpc(() => ({ sdk: {}, common: {} }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core;bad",
        client: { name: "ComputeClient" },
        operation: "listInstances",
        request: {}
      }
    }),
    /Invalid OCI service/
  );
});

test("host RPC discovers services and clients", async () => {
  class ComputeClient {
    listInstances() {}
  }
  class VirtualNetworkClient {
    getVcn() {}
  }
  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      core: { ComputeClient, VirtualNetworkClient },
      identity: {}
    },
    common: {}
  }));

  assert.deepEqual(
    await hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "discover",
      payload: {}
    }),
    { type: "index", services: ["core", "identity"] }
  );

  assert.deepEqual(
    await hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "discover",
      payload: { service: "core" }
    }),
    {
      type: "service",
      service: "core",
      clients: ["ComputeClient", "VirtualNetworkClient"]
    }
  );
});

test("host RPC discovers JavaScript SDK request and response shapes", async () => {
  const hostRpc = createOciSdkHostRpc();

  const result = await hostRpc({
    binding: "oracle",
    namespace: "oci",
    operation: "discover",
    payload: {
      service: "core",
      client: "ComputeClient",
      operation: "launchInstance"
    }
  });
  assert.ok(result && typeof result === "object" && !Array.isArray(result));
  const details = result as Record<string, any>;

  assert.equal(details.type, "operation");
  assert.equal(details.requestType, "LaunchInstanceRequest");
  assert.deepEqual(details.responseShape, {
    bodyKey: "instance",
    bodyModel: "Instance",
    requestIdField: "opcRequestId"
  });
  assert.deepEqual(details.requestFields, [
    {
      name: "launchInstanceDetails",
      required: true,
      type: "model.LaunchInstanceDetails",
      modelRefs: ["LaunchInstanceDetails"]
    },
    {
      name: "opcRetryToken",
      required: false,
      type: "string"
    }
  ]);

  const models = details.models as Record<string, { fields: Array<{ name: string }> }>;
  assert.ok(models.LaunchInstanceDetails.fields.some(field => field.name === "createVnicDetails"));
  assert.ok(models.LaunchInstanceDetails.fields.some(field => field.name === "sourceDetails"));
  assert.ok(models.LaunchInstanceDetails.fields.some(field => field.name === "shapeConfig"));
  assert.ok(models.CreateVnicDetails.fields.some(field => field.name === "subnetId"));
  assert.deepEqual(details.exampleRequest, {
    launchInstanceDetails: {
      availabilityDomain: "<availabilityDomain>",
      compartmentId: "<compartmentId>"
    }
  });
});

test("host builds reflection manifest from installed SDK shape", () => {
  class ComputeClient {
    listInstances() {}
    getInstance() {}
    _privateOperation() {}
  }
  class VirtualNetworkClient {
    getVcn() {}
  }

  const manifest = createOciReflectionManifest(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient, VirtualNetworkClient },
      identity: {}
    },
    common: {}
  }));

  assert.deepEqual(manifest, {
    services: {
      core: {
        clients: {
          ComputeClient: {
            operations: ["getInstance", "listInstances"]
          },
          VirtualNetworkClient: {
            operations: ["getVcn"]
          }
        }
      },
      identity: {
        clients: {}
      }
    }
  });
});

test("host RPC rejects unsupported envelopes", async () => {
  const hostRpc = createOciSdkHostRpc(() => ({ sdk: {}, common: {} }));
  await assert.rejects(
    hostRpc({
      binding: "other" as never,
      namespace: "oci",
      operation: "discover",
      payload: {}
    }),
    /Unsupported host RPC binding other\/oci/
  );
  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "other" as never,
      payload: {}
    }),
    /Unsupported OCI host RPC operation other/
  );
});

test("host RPC reports unknown invoke targets", async () => {
  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: { core: {} },
    common: {}
  }));
  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "missing",
        client: { name: "ComputeClient" },
        operation: "listInstances",
        request: {}
      }
    }),
    /Unknown OCI SDK service 'missing'/
  );
  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: { name: "MissingClient" },
        operation: "listInstances",
        request: {}
      }
    }),
    /Unknown OCI SDK client 'core.MissingClient'/
  );
});

test("host RPC reports unknown discovery targets and client operations", async () => {
  class ComputeClient {
    listInstances() {}
  }
  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: { core: { ComputeClient } },
    common: {}
  }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "discover",
      payload: { service: "missing" }
    }),
    /Unknown OCI SDK service 'missing'/
  );
  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "discover",
      payload: { service: "core", client: "MissingClient" }
    }),
    /Unknown OCI SDK client 'core.MissingClient'/
  );
  assert.deepEqual(
    await hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "discover",
      payload: { service: "core", client: "ComputeClient" }
    }),
    {
      type: "client",
      service: "core",
      client: "ComputeClient",
      operations: ["listInstances"]
    }
  );
  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "discover",
      payload: {
        service: "core",
        client: "ComputeClient",
        operation: "missingOperation"
      }
    }),
    /Unknown OCI SDK operation 'core.ComputeClient.missingOperation'/
  );
});

test("host RPC rejects oversized OCI responses", async () => {
  class ComputeClient {
    async listInstances() {
      return { items: ["x".repeat(1024 * 1024)] };
    }

    close() {}
  }
  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient }
    },
    common: {}
  }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: { name: "ComputeClient" },
        operation: "listInstances",
        request: {}
      }
    }),
    /exceeding response limit 1048576 bytes.*smaller limit/
  );
});

test("host RPC handles an SDK operation disappearing from a client instance", async () => {
  class ComputeClient {
    constructor() {
      (this as any).listInstances = undefined;
    }

    listInstances() {}
  }
  const hostRpc = createOciSdkHostRpc(() => ({
    sdk: {
      ConfigFileAuthenticationDetailsProvider: class Provider {},
      core: { ComputeClient }
    },
    common: {}
  }));

  await assert.rejects(
    hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: { name: "ComputeClient" },
        operation: "listInstances",
        request: {}
      }
    }),
    /Unknown OCI SDK operation 'core.ComputeClient.listInstances'/
  );
});
