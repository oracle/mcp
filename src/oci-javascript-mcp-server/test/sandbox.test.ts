/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import childProcess from "node:child_process";
import { EventEmitter } from "node:events";
import { syncBuiltinESMExports } from "node:module";
import { PassThrough } from "node:stream";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { Server, ServerCredentials } from "@grpc/grpc-js";
import { PodmanIsolationProvider } from "../src/isolation/podman.ts";
import { RUNNER_SERVICE, RunnerClient } from "../src/grpc.ts";
import type { RunnerServer } from "../src/generated/runner.ts";
import { MAX_CODE_BYTES, MAX_STDERR_BYTES, MAX_STDOUT_BYTES } from "../src/sandbox-common.ts";
import { runJavaScriptInIsolate } from "../src/sandbox-isolate.ts";
import { runJavaScript as runJavaScriptWithProvider } from "../src/sandbox.ts";
import type {
  HostRpcRequest,
  IsolationProvider,
  IsolationRunOptions,
  OciReflectionManifest,
  SandboxResult
} from "../src/types.ts";

const TEST_PODMAN_PROVIDER = new PodmanIsolationProvider({
  cliPath: fileURLToPath(new URL("./fake-podman.ts", import.meta.url)),
  image: "test-runner:dev"
});

type RunOptions = Parameters<typeof runJavaScriptWithProvider>[1];
type TestRunOptions = Omit<RunOptions, "isolationProvider"> & {
  isolationProvider?: IsolationProvider;
};

function runJavaScript(code: string, options: TestRunOptions): Promise<SandboxResult> {
  return runJavaScriptWithProvider(code, {
    ...options,
    isolationProvider: options.isolationProvider ?? TEST_PODMAN_PROVIDER
  });
}

function testProvider(run: IsolationProvider["run"]): IsolationProvider {
  return { run };
}

test("Podman provider rejects unsafe executable and image inputs", () => {
  assert.throws(() => new PodmanIsolationProvider({ cliPath: "" }), /CLI path is invalid/);
  assert.throws(
    () => new PodmanIsolationProvider({ image: "--privileged" }),
    /image is invalid/
  );
});

test("Podman removes the execution network even when creation reports failure", async t => {
  const spawn = t.mock.method(childProcess, "spawn", (_command: string, args: string[]) => {
    const child = new EventEmitter();
    queueMicrotask(() => child.emit("close", args[1] === "create" ? 1 : 0));
    return child as childProcess.ChildProcess;
  });
  syncBuiltinESMExports();
  t.after(() => {
    t.mock.restoreAll();
    syncBuiltinESMExports();
  });
  const execution = new PodmanIsolationProvider().run("42", {
    deadlineMs: Date.now() + 10_000,
    signal: new AbortController().signal,
    hostRpc: async () => null
  });
  await assert.rejects(execution.result, /Podman command exited unsuccessfully/);
  await execution.terminate();
  const commands = spawn.mock.calls.map(call => call.arguments[1]);
  const network = commands[0].at(-1);
  assert.deepEqual(commands, [
    ["network", "create", "--internal", "--disable-dns", network],
    ["network", "rm", "--ignore", network]
  ]);
});

for (const scenario of ["early exit", "spawn error", "missing input", "cancel"] as const) {
  test(`Podman owns process and resource cleanup: ${scenario}`, { timeout: 5000 }, async t => {
    const controller = new AbortController();
    const runner = new childProcess.ChildProcess();
    runner.stdin = scenario === "missing input" ? null : new PassThrough();
    const kill = t.mock.method(runner, "kill", () => {
      Object.assign(runner, { signalCode: "SIGKILL" });
      queueMicrotask(() => runner.emit("close", null, "SIGKILL"));
      return true;
    });
    const spawn = t.mock.method(childProcess, "spawn", (_command: string, args: string[]) => {
      if (args[0] === "run") {
        queueMicrotask(() => {
          if (scenario === "cancel") controller.abort();
          if (scenario === "spawn error") runner.emit("error", new Error("private runtime error"));
          if (scenario === "early exit" || scenario === "spawn error") {
            Object.assign(runner, { exitCode: 1 });
            runner.emit("close", 1, null);
          }
        });
        return runner;
      }
      const command = new EventEmitter();
      queueMicrotask(() => command.emit("close", 0));
      return command as childProcess.ChildProcess;
    });
    syncBuiltinESMExports();
    t.after(() => { t.mock.restoreAll(); syncBuiltinESMExports(); });
    const execution = new PodmanIsolationProvider().run("42", {
      deadlineMs: Date.now() + 30_000,
      signal: controller.signal,
      hostRpc: async () => assert.fail("no OCI calls expected")
    });
    if (scenario === "cancel") {
      assert.equal((await execution.result).timedOut, true);
    } else {
      await assert.rejects(execution.result, /sandbox runner (exited|failed|input)/);
    }
    await Promise.all([execution.terminate(), execution.terminate()]);
    const commands = spawn.mock.calls.map(call => call.arguments[1]);
    const name = commands[0].at(-1);
    assert.deepEqual(commands.slice(-2), [
      ["rm", "--force", "--ignore", name],
      ["network", "rm", "--ignore", name]
    ]);
    assert.equal(commands.length, 4);
    assert.equal(kill.mock.callCount(), scenario === "missing input" || scenario === "cancel" ? 1 : 0);
  });
}

test("Podman removes resources when its run CLI never closes", { timeout: 5000 }, async t => {
  const runner = new childProcess.ChildProcess();
  runner.stdin = new PassThrough();
  const kill = t.mock.method(runner, "kill", () => true);
  let started!: () => void;
  const running = new Promise<void>(resolve => { started = resolve; });
  const spawn = t.mock.method(childProcess, "spawn", (_command: string, args: string[]) => {
    if (args[0] === "run") {
      queueMicrotask(started);
      return runner;
    }
    const command = new EventEmitter();
    queueMicrotask(() => command.emit("close", 0));
    return command as childProcess.ChildProcess;
  });
  syncBuiltinESMExports();
  t.after(() => { t.mock.restoreAll(); syncBuiltinESMExports(); });
  const execution = new PodmanIsolationProvider().run("42", {
    deadlineMs: Date.now() + 30_000,
    signal: new AbortController().signal,
    hostRpc: async () => null
  });
  await running;
  await assert.rejects(execution.terminate(), /sandbox runner did not close/);
  const commands = spawn.mock.calls.map(call => call.arguments[1]);
  const name = commands[0].at(-1);
  assert.deepEqual(commands.slice(-2), [
    ["rm", "--force", "--ignore", name],
    ["network", "rm", "--ignore", name]
  ]);
  assert.equal(kill.mock.callCount(), 1);
});

test("Podman trusts gRPC status after receiving a result", { timeout: 5000 }, async t => {
  const runner = new childProcess.ChildProcess();
  runner.stdin = new PassThrough();
  const server = new Server();
  const handlers: RunnerServer = { session(call) {
    call.on("error", () => {});
    call.on("data", message => {
      if (message.execute) call.write({ result: {
        resultJson: Buffer.from("42"), errorJson: Buffer.from("null"),
        exitCode: 0, timedOut: false, stdoutUtf16le: Buffer.alloc(0), stderrUtf16le: Buffer.alloc(0)
      } });
    });
    call.on("end", () => {
      runner.emit("close", 0, null);
      setTimeout(() => call.end(), 10);
    });
  } };
  server.addService(RUNNER_SERVICE, handlers);
  let port = 0;
  let bootstrap = "";
  runner.stdin.on("data", chunk => { bootstrap += String(chunk); });
  const bound = new Promise<void>((resolve, reject) => runner.stdin!.on("end", () => {
    const tls = JSON.parse(bootstrap) as { clientCert: string; serverKey: string; serverCert: string };
    server.bindAsync(`127.0.0.1:${port}`, ServerCredentials.createSsl(
      Buffer.from(tls.clientCert),
      [{ private_key: Buffer.from(tls.serverKey), cert_chain: Buffer.from(tls.serverCert) }],
      true
    ), error => error ? reject(error) : resolve());
  }));
  const spawn = t.mock.method(childProcess, "spawn", (_command: string, args: string[]) => {
    if (args[0] === "run") {
      port = Number(args[args.indexOf("--publish") + 1].split(":")[1]);
      return runner;
    }
    const command = new EventEmitter();
    queueMicrotask(() => command.emit("close", 0));
    return command as childProcess.ChildProcess;
  });
  syncBuiltinESMExports();
  t.after(() => { server.forceShutdown(); t.mock.restoreAll(); syncBuiltinESMExports(); });
  const execution = new PodmanIsolationProvider().run("42", {
    deadlineMs: Date.now() + 5000,
    signal: new AbortController().signal,
    hostRpc: async () => null
  });
  await bound;
  const result = await execution.result;
  await execution.terminate();
  assert.equal(result.result, 42);
  assert.equal(result.exitCode, 0);
  assert.equal(spawn.mock.callCount(), 4);
});

test("sandbox delegates execution through the selected isolation provider", async () => {
  const expected: SandboxResult = {
    result: 42,
    error: null,
    stdout: "",
    stderr: "",
    exitCode: 0,
    timedOut: false
  };
  const reflectionManifest: OciReflectionManifest = { services: {} };
  const hostRpc = async () => null;
  const calls: Array<{ code: string; options: IsolationRunOptions }> = [];
  let terminated = false;
  const provider = testProvider((code, options) => {
    calls.push({ code, options });
    return {
      result: Promise.resolve(expected),
      async terminate() {
        terminated = true;
      }
    };
  });

  const result = await runJavaScript("40 + 2;", {
    timeoutSeconds: 10,
    hostRpc,
    reflectionManifest,
    isolationProvider: provider
  });

  assert.equal(result, expected); // The transport already validated this result.
  assert.equal(terminated, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].code, "40 + 2;");
  assert.equal(calls[0].options.reflectionManifest, reflectionManifest);
  assert.notEqual(calls[0].options.hostRpc, hostRpc);
  assert.equal(calls[0].options.signal.aborted, true);
  assert(calls[0].options.deadlineMs > Date.now());
});

test("sandbox enforces the OCI call budget above isolation providers", async () => {
  let hostCalls = 0;
  const request: HostRpcRequest = {
    binding: "oracle",
    namespace: "oci",
    operation: "config",
    payload: {}
  };
  const provider = testProvider((_code, options) => ({
    result: (async (): Promise<SandboxResult> => {
      let finalRpcResult = null;
      for (let index = 0; index < 101; index += 1) {
        finalRpcResult = await options.hostRpc(request);
      }
      return {
        result: finalRpcResult,
        error: null,
        stdout: "",
        stderr: "",
        exitCode: 0,
        timedOut: false
      };
    })(),
    async terminate() {}
  }));

  const result = await runJavaScript("0;", {
    timeoutSeconds: 10,
    hostRpc: async () => {
      hostCalls += 1;
      return {};
    },
    isolationProvider: provider
  });

  assert.equal(hostCalls, 100);
  assert.deepEqual(result.result, {
    ok: false,
    error: "OCI call limit exceeded (100)"
  });
});

for (const cancellation of [false, true]) {
  test(`sandbox aborts and drains OCI work on ${cancellation ? "cancellation" : "deadline"}`, { timeout: 5000 }, async () => {
    const controller = new AbortController();
    let signal: AbortSignal | undefined;
    let rpcSettled = false;
    let terminateCalls = 0;
    let hostCalls = 0;
    const request: HostRpcRequest = {
      binding: "oracle",
      namespace: "oci",
      operation: "config",
      payload: {}
    };
    const provider = testProvider((_code, options) => {
      signal = options.signal;
      void options.hostRpc(request);
      return {
        result: new Promise(() => undefined),
        async terminate() {
          terminateCalls += 1;
          // Teardown must not admit new OCI work after aborting the accepted call.
          await options.hostRpc(request);
        }
      };
    });

    const startedAt = Date.now();
    const result = await runJavaScript("while (true) {}", {
      timeoutSeconds: cancellation ? 30 : 1,
      signal: controller.signal,
      hostRpc: async (_request, rpcSignal) => new Promise<null>(resolve => {
        hostCalls += 1;
        rpcSignal?.addEventListener("abort", () => {
          setTimeout(() => {
            rpcSettled = true;
            resolve(null);
          }, 25);
        }, { once: true });
        if (cancellation) controller.abort();
      }),
      isolationProvider: provider
    });

    assert.equal(result.timedOut, !cancellation);
    assert.equal(result.exitCode, cancellation ? 1 : -1);
    assert.equal(result.error?.message, cancellation ? "sandbox execution cancelled" : "sandbox run deadline exceeded");
    assert.equal(signal?.aborted, true);
    assert.equal(rpcSettled, true);
    assert.equal(terminateCalls, 1);
    assert.equal(hostCalls, 1);
    assert(Date.now() - startedAt < 5000);
  });
}

test("a pre-cancelled execution never starts the provider", async () => {
  const result = await runJavaScript("42", {
    signal: AbortSignal.abort(),
    hostRpc: async () => assert.fail("OCI must not start"),
    isolationProvider: testProvider(() => assert.fail("provider must not start"))
  });
  assert.equal(result.error?.message, "sandbox execution cancelled");
  assert.equal(result.timedOut, false);
});

test("sandbox reports isolation provider cleanup failures", async () => {
  const provider = testProvider(() => ({
    result: Promise.resolve({
      result: 42,
      error: null,
      stdout: "",
      stderr: "",
      exitCode: 0,
      timedOut: false
    }),
    async terminate() {
      throw new Error("cleanup broke");
    }
  }));

  const result = await runJavaScript("40 + 2;", {
    hostRpc: async () => null,
    isolationProvider: provider
  });

  assert.equal(result.result, null);
  assert.equal(result.exitCode, 1);
  assert.equal(result.error?.message, "isolation provider cleanup failed");
});

test("sandbox does not hide cleanup failures behind a timeout result", async () => {
  const provider = testProvider(() => ({
    result: Promise.resolve({
      result: null,
      error: { message: "sandbox run deadline exceeded" },
      stdout: "",
      stderr: "",
      exitCode: -1,
      timedOut: true
    }),
    async terminate() {
      throw new Error("cleanup broke after timeout");
    }
  }));

  const result = await runJavaScript("0;", {
    hostRpc: async () => null,
    isolationProvider: provider
  });

  assert.equal(result.timedOut, false);
  assert.equal(result.error?.message, "isolation provider cleanup failed");
});

test("sandbox preserves source and log strings across gRPC", async () => {
  const text = "\ud800|\udfff|😀|é|e\u0301|\0";
  const result = await runJavaScript(
    `const text = "${text}"; console.log(text); console.error(String.fromCharCode(0xdfff)); text;`,
    { timeoutSeconds: 10, hostRpc: async () => null }
  );
  assert.equal(result.exitCode, 0);
  assert.equal(result.error, null);
  assert.equal(result.result, text);
  assert.equal(result.stdout, text + "\n");
  assert.equal(result.stderr, "\udfff\n");
});

test("sandbox accepts source, combined logs, and result within their byte limits", async () => {
  const prefix = `console.log("x".repeat(${MAX_STDOUT_BYTES - 2}));
    console.error("x".repeat(${MAX_STDERR_BYTES - 2})); return "x".repeat(${1024 * 1024 - 2});\n`;
  const code = prefix + "\n".repeat(MAX_CODE_BYTES - Buffer.byteLength(prefix));
  const result = await runJavaScript(code, { timeoutSeconds: 10, hostRpc: async () => null });
  assert.equal(Buffer.byteLength(code), MAX_CODE_BYTES);
  assert.equal(result.exitCode, 0);
  assert.equal(Buffer.byteLength(JSON.stringify(result.result)), 1024 * 1024);
  assert.equal(Buffer.byteLength(result.stdout), MAX_STDOUT_BYTES - 1);
  assert.equal(Buffer.byteLength(result.stderr), MAX_STDERR_BYTES - 1);
});

test("caught output-limit errors remain structured script failures", async () => {
  const result = await runJavaScript(
    `try { console.log("x".repeat(${MAX_STDOUT_BYTES})); } catch {} 42;`,
    { hostRpc: async () => null }
  );
  assert.equal(result.exitCode, 1);
  assert.equal(result.error?.message, "Sandbox output exceeded limit");
  assert.equal(Buffer.byteLength(result.stdout), MAX_STDOUT_BYTES);
});

for (const invalid of ["manifest", "missing deadline"] as const) {
  test(`worker rejects invalid host input: ${invalid}`, async t => {
    if (invalid === "missing deadline") {
      const session = RunnerClient.prototype.session;
      t.mock.method(RunnerClient.prototype, "session", function (this: RunnerClient, ...args: Parameters<RunnerClient["session"]>) {
        return session.call(this, args[0]);
      });
    }
    const result = await runJavaScript("42", {
      timeoutSeconds: 10,
      hostRpc: async () => null,
      reflectionManifest: invalid === "manifest" ? [] as unknown as OciReflectionManifest : undefined
    });
    assert.equal(result.exitCode, 1);
    assert.equal(result.error?.message, "sandbox protocol failed");
  });
}

test("sandbox runs JavaScript and calls host OCI RPC", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const compute = new oci.core.ComputeClient();
    const response = await compute.listInstances({ compartmentId: "ocid1.compartment" });
    console.error("guest diagnostic");
    console.log(response.items[0].displayName);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async request => {
        requests.push(request);
        return { items: [{ displayName: "bulletproof-tiger" }] };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "guest diagnostic\n");
  assert.equal(result.stdout.trim(), "bulletproof-tiger");
  assert.deepEqual(requests, [
    {
      binding: "oracle",
      namespace: "oci",
      operation: "invoke",
      payload: {
        service: "core",
        client: { name: "ComputeClient" },
        operation: "listInstances",
        request: { compartmentId: "ocid1.compartment" }
      }
    }
  ]);
});

test("sandbox reports uncaught JavaScript errors without internal frames", async () => {
  const result = await runJavaScript(
    "missingTenantId;",
    {
      timeoutSeconds: 10,
      hostRpc: async () => ({})
    }
  );

  assert.equal(result.result, null);
  assert.deepEqual(result.error, {
    name: "ReferenceError",
    message: "missingTenantId is not defined"
  });
  assert.equal(result.exitCode, 1);
  assert.equal(result.stderr, "");
});

test("sandbox sends client initialization region in OCI RPC payloads", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const compute = new oci.core.ComputeClient({ region: "us-phoenix-1" });
    const DynamicComputeClient = oci.core.ComputeClient;
    const dynamic = new DynamicComputeClient({ region: "us-ashburn-1" });
    await compute.listInstances({ compartmentId: "ocid1.compartment" });
    await dynamic.getInstance({ instanceId: "ocid1.instance" });
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async request => {
        requests.push(request);
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(requests.map(request => request.payload), [
    {
      service: "core",
      client: {
        name: "ComputeClient",
        options: { region: "us-phoenix-1" }
      },
      operation: "listInstances",
      request: { compartmentId: "ocid1.compartment" }
    },
    {
      service: "core",
      client: {
        name: "ComputeClient",
        options: { region: "us-ashburn-1" }
      },
      operation: "getInstance",
      request: { instanceId: "ocid1.instance" }
    }
  ]);
});

test("sandbox rejects unsupported client initialization options before host RPC", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    try {
      new oci.core.ComputeClient({ endpoint: "https://example.invalid" });
    } catch (error) {
      console.log(error.message);
    }
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.match(result.stdout, /Unsupported OCI client option 'endpoint'/);
  assert.match(result.stdout, /Client options only support region/);
  assert.equal(hostCalls, 0);
});

test("sandbox rejects malformed client regions before host RPC", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    try {
      new oci.core.ComputeClient({ region: "example.com" });
    } catch (error) {
      console.log(error.message);
    }
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.match(result.stdout, /Invalid OCI client option region 'example.com'/);
  assert.equal(hostCalls, 0);
});

test("sandbox does not expose Node process or inherited environment", async () => {
  process.env.OCI_JAVASCRIPT_SANDBOX_TEST_SECRET = "secret";
  const result = await runJavaScript(
    `console.log(typeof process);`,
    {
      timeoutSeconds: 10,
      hostRpc: async () => null
    }
  );

  delete process.env.OCI_JAVASCRIPT_SANDBOX_TEST_SECRET;
  assert.equal(result.exitCode, 0);
  assert.equal(result.stdout.trim(), "undefined");
});

test("sandbox returns an explicit return value as structured result", async () => {
  const result = await runJavaScript(
    `
    const value = 41;
    return value + 1;
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => null
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(result.stdout, "");
  assert.equal(result.result, 42);
});

test("sandbox returns a trailing expression as structured result", async () => {
  const result = await runJavaScript(
    `
    const value = 41;
    value + 1;
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => null
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(result.result, 42);
});

test("sandbox rejects oversized structured results before host RPC", async () => {
  const result = await runJavaScript(
    `"x".repeat(1024 * 1024);`,
    {
      timeoutSeconds: 10,
      hostRpc: async () => null
    }
  );

  assert.equal(result.result, null);
  assert.match(result.error?.message ?? "", /exceeding result limit 1048576 bytes/);
  assert.equal(result.exitCode, 1);
  assert.equal(result.timedOut, false);
});

test("sandbox infers a trailing expression when helper functions use return", async () => {
  const result = await runJavaScript(
    `
    function value() {
      return 41;
    }
    value() + 1;
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => null
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(result.result, 42);
});

test("sandbox bounds final expression inference inside isolate", async () => {
  const start = Date.now();
  const result = await runJavaScript(
    "let value;\n".repeat(50_000),
    {
      timeoutSeconds: 1,
      hostRpc: async () => null
    }
  );

  assert.equal(result.timedOut, true);
  assert(Date.now() - start < 5000);
});

test("sandbox returns explicit OCI results without stdout parsing", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const response = await oci.core.ComputeClient.listInstances({
      compartmentId: "ocid1.compartment",
      limit: 5
    });
    return response.items.map(instance => instance.displayName);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async request => {
        requests.push(request);
        return { items: [{ displayName: "zavala" }] };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(result.stdout, "");
  assert.deepEqual(result.result, ["zavala"]);
  assert.equal(requests.length, 1);
});

test("sandbox returns trailing OCI expressions without stdout parsing", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const response = await oci.core.ComputeClient.listInstances({
      compartmentId: "ocid1.compartment",
      limit: 5
    });
    response.items.map(instance => instance.displayName);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async request => {
        requests.push(request);
        return { items: [{ displayName: "zavala" }] };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(result.stdout, "");
  assert.deepEqual(result.result, ["zavala"]);
  assert.equal(requests.length, 1);
});

test("sandbox follows OCI list page tokens through normal RPC calls", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const compute = new oci.core.ComputeClient();
    const first = await compute.listInstances({
      compartmentId: "ocid1.compartment",
      limit: 2
    });
    const second = await compute.listInstances({
      compartmentId: "ocid1.compartment",
      limit: 2,
      page: first.opcNextPage
    });
    [...first.items, ...second.items].map(item => item.id);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async request => {
        requests.push(request);
        if (requests.length === 1) {
          return { items: [{ id: "a" }], opcNextPage: "next" };
        }
        return { items: [{ id: "b" }], opcNextPage: null };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.result, ["a", "b"]);
  assert.deepEqual(requests.map(request => request.payload), [
    {
      service: "core",
      client: { name: "ComputeClient" },
      operation: "listInstances",
      request: {
        compartmentId: "ocid1.compartment",
        limit: 2
      }
    },
    {
      service: "core",
      client: { name: "ComputeClient" },
      operation: "listInstances",
      request: {
        compartmentId: "ocid1.compartment",
        limit: 2,
        page: "next"
      }
    }
  ]);
});

test("sandbox exposes only allowlisted host RPC error details", async () => {
  const result = await runJavaScript(
    `
    try {
      await oci.core.ComputeClient.listInstances({ compartmentId: "ocid1.compartment" });
    } catch (error) {
      return {
        message: error.message,
        name: error.name,
        statusCode: error.statusCode,
        serviceCode: error.serviceCode,
        opcRequestId: error.opcRequestId,
        keys: Object.keys(error).sort(),
        serialized: JSON.stringify(error)
      };
    }
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        const error = new Error("bad request");
        Object.defineProperties(error, {
          statusCode: { value: 400 },
          serviceCode: { value: "InvalidParameter" },
          opcRequestId: { value: "req1" },
          requestEndpoint: { value: "https://internal.example/signed?token=secret" },
          response: {
            value: {
              headers: { authorization: "secret authorization" },
              body: { message: "secret response body" }
            }
          },
          cause: { value: new Error("secret cause") }
        });
        throw error;
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.result, {
    message: "OCI call failed",
    name: "Error",
    statusCode: 400,
    serviceCode: "InvalidParameter",
    opcRequestId: "req1",
    keys: ["opcRequestId", "serviceCode", "statusCode"],
    serialized: "{\"statusCode\":400,\"serviceCode\":\"InvalidParameter\",\"opcRequestId\":\"req1\"}"
  });
});

test("sandbox returns multiline explicit results", async () => {
  const result = await runJavaScript(
    `
    const response = await oci.identity.IdentityClient.listRegions({ limit: 100 });
    return response.items.map(region => ({
      key: region.key,
      name: region.name
    }));
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => ({
        items: [
          { key: "IAD", name: "us-ashburn-1" },
          { key: "SJC", name: "us-sanjose-1" }
        ]
      })
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(result.stdout, "");
  assert.deepEqual(result.result, [
    { key: "IAD", name: "us-ashburn-1" },
    { key: "SJC", name: "us-sanjose-1" }
  ]);
});

test("sandbox reflects OCI services clients and operations from manifest", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    return {
      services: Object.keys(oci),
      hasCore: "core" in oci,
      hasUnknownService: "notAService" in oci,
      unknownServiceType: typeof oci.notAService,
      coreClients: Object.keys(oci.core),
      computeFactoryKeys: Object.keys(oci.core.ComputeClient),
      computeClientKeys: Object.keys(oci.core.ComputeClient()),
      computeOwnKeys: Reflect.ownKeys(oci.core.ComputeClient()).filter(key => typeof key === "string"),
      hasListInstances: "listInstances" in oci.core.ComputeClient()
    };
    `,
    {
      timeoutSeconds: 10,
      reflectionManifest: {
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
            clients: {
              IdentityClient: {
                operations: ["listRegions"]
              }
            }
          }
        }
      },
      hostRpc: async () => {
        hostCalls += 1;
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.result, {
    services: ["config", "core", "identity"],
    hasCore: true,
    hasUnknownService: false,
    unknownServiceType: "undefined",
    coreClients: ["ComputeClient", "VirtualNetworkClient"],
    computeFactoryKeys: ["getInstance", "listInstances"],
    computeClientKeys: ["getInstance", "listInstances"],
    computeOwnKeys: ["getInstance", "listInstances"],
    hasListInstances: true
  });
  assert.equal(hostCalls, 0);
});

test("sandbox does not expose custom OCI client helper", async () => {
  const result = await runJavaScript(
    `
    return {
      clientType: typeof oci.client,
      hasClient: "client" in oci
    };
    `,
    {
      timeoutSeconds: 10,
      reflectionManifest: {
        services: {
          core: {
            clients: {
              ComputeClient: {
                operations: ["listInstances"]
              }
            }
          }
        }
      },
      hostRpc: async () => ({})
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.result, {
    clientType: "undefined",
    hasClient: false
  });
});

test("sandbox OCI proxies are not mistaken for promises", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const binding = await oci;
    const service = await oci.core;
    const factory = await oci.core.ComputeClient;
    const client = await new oci.core.ComputeClient();
    return {
      bindingKeys: Object.keys(binding),
      serviceKeys: Object.keys(service),
      factoryKeys: Object.keys(factory),
      clientKeys: Object.keys(client),
      clientThenType: typeof client.then,
      clientJsonType: typeof client.toJSON
    };
    `,
    {
      timeoutSeconds: 10,
      reflectionManifest: {
        services: {
          core: {
            clients: {
              ComputeClient: {
                operations: ["listInstances"]
              }
            }
          }
        }
      },
      hostRpc: async request => {
        requests.push(request);
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(requests.length, 0);
  assert.deepEqual(result.result, {
    bindingKeys: ["config", "core"],
    serviceKeys: ["ComputeClient"],
    factoryKeys: ["listInstances"],
    clientKeys: ["listInstances"],
    clientThenType: "undefined",
    clientJsonType: "undefined"
  });
});

test("sandbox does not extend execution for RPC calls triggered during result serialization", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    const value = {
      get name() {
        oci.core.ComputeClient.listInstances({ compartmentId: "ocid1.compartment" });
        return "zavala";
      }
    };
    return value;
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        return { items: [] };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.deepEqual(result.result, { name: "zavala" });
  assert.equal(hostCalls, 0);
});

test("sandbox blocks Node built-ins and network access", async () => {
  const result = await runJavaScript(
    `
    console.log(typeof process);
    console.log(typeof require);
    console.log(typeof fetch);
    console.log(typeof WebSocket);
    try {
      await import("node:fs");
      console.log("fs imported");
    } catch (error) {
      console.log("fs blocked");
    }
    try {
      await import("node:net");
      console.log("net imported");
    } catch (error) {
      console.log("net blocked");
    }
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => null
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.stdout.trim().split("\n"), [
    "undefined",
    "undefined",
    "undefined",
    "undefined",
    "fs blocked",
    "net blocked"
  ]);
});

test("sandbox does not expose host RPC bridge internals", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    console.log(typeof __hostRpc);
    console.log(typeof __ociSandboxDone);
    try {
      oci = {};
    } catch (error) {
      console.log("oci hardened");
    }
    console.log(typeof oci.core.ComputeClient.listInstances);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.stdout.trim().split("\n"), [
    "undefined",
    "undefined",
    "oci hardened",
    "function"
  ]);
  assert.equal(hostCalls, 0);
});

test("sandbox rejects fire-and-forget host RPC calls after draining them", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    oci.core.ComputeClient.listInstances({ compartmentId: "ocid1.compartment" });
    console.log("user code returned");
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
        hostCalls += 1;
        return { items: [] };
      }
    }
  );

  assert.equal(result.exitCode, 1);
  assert.equal(result.error?.message, "JavaScript completed with unawaited OCI calls");
  assert.equal(result.stderr, "");
  assert.equal(result.stdout, "");
  assert.equal(hostCalls, 1);
});

test("sandbox rejects provider completion while accepted OCI work is pending", async () => {
  let rpcSettled = false;
  const provider = testProvider((_code, options) => {
    queueMicrotask(() => {
      void options.hostRpc({
        binding: "oracle",
        namespace: "oci",
        operation: "config",
        payload: {}
      });
    });
    return {
      result: Promise.resolve({
        result: "completed",
        error: null,
        stdout: "",
        stderr: "",
        exitCode: 0,
        timedOut: false
      }),
      async terminate() {}
    };
  });

  const result = await runJavaScript("0;", {
    timeoutSeconds: 10,
    hostRpc: async () => {
      await new Promise(resolve => setTimeout(resolve, 25));
      rpcSettled = true;
      return {};
    },
    isolationProvider: provider
  });

  assert.equal(result.result, null);
  assert.equal(result.exitCode, 1);
  assert.equal(result.error?.message, "JavaScript completed with unawaited OCI calls");
  assert.equal(rpcSettled, true);
});

test("sandbox bounds cleanup when accepted OCI work ignores cancellation", { timeout: 10_000 }, async () => {
  const provider = testProvider((_code, options) => {
    queueMicrotask(() => void options.hostRpc({
      binding: "oracle",
      namespace: "oci",
      operation: "config",
      payload: {}
    }));
    return {
      result: Promise.resolve({
        result: "completed",
        error: null,
        stdout: "",
        stderr: "",
        exitCode: 0,
        timedOut: false
      }),
      async terminate() {}
    };
  });
  const result = await runJavaScript("0;", {
    hostRpc: async () => new Promise(() => {}),
    isolationProvider: provider
  });
  assert.equal(result.error?.message, "OCI cleanup did not complete");
  assert.equal(result.exitCode, 1);
});

test("sandbox supports explicitly awaited host RPC chains", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    await oci.core.ComputeClient.listInstances({ compartmentId: "ocid1.compartment" })
      .then(() => oci.core.ComputeClient.getInstance({ instanceId: "ocid1.instance" }));
    console.log("user code returned");
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.equal(result.stdout.trim(), "user code returned");
  assert.equal(hostCalls, 2);
});

test("sandbox caps concurrent host OCI RPC calls", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    const calls = Array.from({ length: 8 }, () =>
      oci.core.ComputeClient.listInstances({ compartmentId: "ocid1.compartment" })
    );
    const results = await Promise.allSettled(calls);
    const rejected = results.find(result => result.status === "rejected");
    console.log(rejected.reason.message);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        await new Promise(resolve => setTimeout(resolve, 100));
        return { items: [] };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.match(result.stdout, /too many concurrent OCI calls/);
  assert.equal(hostCalls, 4);
});

test("sandbox rejects oversized direct host RPC requests", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    try {
      await oci.core.ComputeClient.listInstances({ value: "x".repeat(1024 * 1024) });
    } catch (error) {
      console.log(error.message);
    }
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        return {};
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.match(result.stdout, /OCI request exceeded/);
  assert.equal(hostCalls, 0);
});

test("sandbox serializes non-JSON request values and deserializes host results", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const response = await oci.core.ComputeClient.listInstances({
      when: new Date("2026-06-03T00:00:00.000Z"),
      page: undefined,
      big: 123n,
      bytes: new Uint8Array([1, 2, 3]),
      tags: new Map([["a", 1]])
    });
    console.log(response.when instanceof Date);
    console.log(response.big === 123n);
    console.log(response.bytes[2]);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async request => {
        requests.push(request);
        return {
          when: { __oci_wire_type: "datetime", value: "2026-06-03T00:00:00.000Z" },
          big: { __oci_wire_type: "bigint", value: "123" },
          bytes: { __oci_wire_type: "bytes", encoding: "base64", value: "AQID" }
        };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.stdout.trim().split("\n"), ["true", "true", "3"]);
  assert.deepEqual(requests[0].payload.request, {
    when: { __oci_wire_type: "datetime", value: "2026-06-03T00:00:00.000Z" },
    big: { __oci_wire_type: "bigint", value: "123" },
    bytes: { __oci_wire_type: "bytes", encoding: "base64", value: "AQID" },
    tags: { __oci_wire_type: "map", items: [["a", 1]] }
  });
});

test("sandbox OCI bridge does not depend on user-mutated globals", async () => {
  const result = await runJavaScript(
    `
    globalThis.String = () => { throw "polluted String"; };
    globalThis.Date = null;
    globalThis.Uint8Array = null;
    globalThis.BigInt = null;
    globalThis.Map = null;
    globalThis.Set = null;
    globalThis.Error = null;
    globalThis.Proxy = null;
    globalThis.Promise = null;

    const response = await oci.core.ComputeClient.listInstances({
      compartmentId: "ocid1.compartment"
    });
    return {
      when: response.when.toISOString(),
      big: response.big === 123n,
      byte: response.bytes[2],
      tag: response.tags.get("a"),
      hasCompute: Object.keys(oci.core).includes("ComputeClient")
    };
    `,
    {
      timeoutSeconds: 10,
      reflectionManifest: {
        services: {
          core: {
            clients: {
              ComputeClient: {
                operations: ["listInstances"]
              }
            }
          }
        }
      },
      hostRpc: async () => ({
        when: { __oci_wire_type: "datetime", value: "2026-06-03T00:00:00.000Z" },
        big: { __oci_wire_type: "bigint", value: "123" },
        bytes: { __oci_wire_type: "bytes", encoding: "base64", value: "AQID" },
        tags: { __oci_wire_type: "map", items: [["a", 1]] }
      })
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.deepEqual(result.result, {
    when: "2026-06-03T00:00:00.000Z",
    big: true,
    byte: 3,
    tag: 1,
    hasCompute: true
  });
});

test("sandbox rejects unknown tagged host result values", async () => {
  const result = await runJavaScript(
    `
    try {
      await oci.core.ComputeClient.getInstance({ instanceId: "ocid1.instance" });
    } catch (error) {
      console.log(error.message);
    }
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => ({
        value: { __oci_wire_type: "mystery", value: "x" }
      })
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.match(result.stdout, /Unknown OCI wire type 'mystery'/);
});

test("sandbox caps request serialization depth", async () => {
  const requests: HostRpcRequest[] = [];
  const result = await runJavaScript(
    `
    const root = {};
    let cursor = root;
    for (let index = 0; index < 100; index += 1) {
      cursor.next = {};
      cursor = cursor.next;
    }
    await oci.core.ComputeClient.listInstances(root);
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async request => {
        requests.push(request);
        return { items: [] };
      }
    }
  );

  assert.equal(result.exitCode, 0);
  assert.equal(result.stderr, "");
  assert.match(JSON.stringify(requests[0].payload.request), /\[MaxDepth]/);
});

test("sandbox rejects non-finite timeout values", async () => {
  let providerCalls = 0;
  const provider = testProvider(() => {
    providerCalls += 1;
    throw new Error("provider must not run");
  });
  await assert.rejects(
    runJavaScript("console.log('nope');", {
      timeoutSeconds: Number.NaN,
      hostRpc: async () => null,
      isolationProvider: provider
    }),
    /timeout must be a finite number/
  );
  assert.equal(providerCalls, 0);
});

test("sandbox rejects oversized source before spawning a worker", async () => {
  await assert.rejects(
    runJavaScript("x".repeat(1024 * 1024 + 1), {
      hostRpc: async () => null
    }),
    /JavaScript code exceeds 1048576 bytes/
  );
});

test("sandbox caps the total number of OCI calls", async () => {
  let hostCalls = 0;
  const result = await runJavaScript(
    `
    let message = "";
    for (let index = 0; index < 101; index += 1) {
      try {
        await oci.core.ComputeClient.listInstances({ compartmentId: "ocid1.compartment" });
      } catch (error) {
        message = error.message;
      }
    }
    message;
    `,
    {
      timeoutSeconds: 10,
      hostRpc: async () => {
        hostCalls += 1;
        return { items: [] };
      }
    }
  );

  assert.equal(hostCalls, 100);
  assert.match(String(result.result), /OCI call limit exceeded \(100\)/);
});
