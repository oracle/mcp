/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { createServer } from "node:net";
import test from "node:test";
import { Client, Server, ServerCredentials, credentials, status } from "@grpc/grpc-js";
import {
  RUNNER_SERVICE,
  RunnerClient,
  decodeText,
  encodeText,
  validateEnvelope,
  type HostMessage,
  type RunnerMessage
} from "../src/grpc.ts";
import { DEFAULT_DECODE_LIMITS, decodeJson, encodePayload } from "../src/protocol.ts";
import type { RunnerServer } from "../src/generated/runner.ts";
import { startGrpcExecution } from "../src/isolation/grpc-execution.ts";
import { runJavaScript } from "../src/sandbox.ts";

const method = RUNNER_SERVICE.session;

test("v4 service is bidirectional and distinct from earlier endpoints", () => {
  assert.equal(method.path, "/oracle.oci.mcp.runner.v4.Runner/Session");
  assert.equal(method.requestStream, true);
  assert.equal(method.responseStream, true);
});

// These fixtures pin all existing field numbers and encodings. Additive schema
// changes are fine; changing these requires a new version, not refreshed fixtures.
const hostFixtures: [HostMessage, string][] = [
  [{ execute: {
    codeUtf16le: encodeText("x", 1), reflectionManifestJson: Buffer.from("{}"),
    memoryLimitMb: 128, maxResultBytes: 1024
  } }, "0a0e1a027b7d20800128800832027800"],
  [{ rpcResult: { id: 1, resultJson: Buffer.from("null") } }, "1208080112046e756c6c"]
];
const runnerFixtures: [RunnerMessage, string][] = [
  [{ rpc: { id: 7, requestJson: Buffer.from("{}") } }, "1206080712027b7d"],
  [{ result: { resultJson: Buffer.from("null"), errorJson: Buffer.from("null"), exitCode: 0,
    timedOut: false, stdoutUtf16le: Buffer.alloc(0), stderrUtf16le: Buffer.alloc(0) } },
    "22100a046e756c6c12046e756c6c18002000"],
  [{ result: { resultJson: Buffer.from("null"), errorJson: encodePayload({ message: "e" }), exitCode: -1,
    timedOut: true, stdoutUtf16le: Buffer.alloc(0), stderrUtf16le: Buffer.alloc(0) } },
    "221b0a046e756c6c120f7b226d657373616765223a2265227d18012001"],
  [{ result: { resultJson: Buffer.from("null"), errorJson: Buffer.from("null"), exitCode: 0,
    timedOut: false, stdoutUtf16le: encodeText("x", 1), stderrUtf16le: encodeText("y", 1) } },
    "22180a046e756c6c12046e756c6c180020002a02780032027900"]
];

test("host protobuf messages preserve their wire contract", () => {
  for (const [message, hex] of hostFixtures) {
    assert.equal(method.requestSerialize(message).toString("hex"), hex);
    const decoded = method.requestDeserialize(Buffer.from(hex, "hex"));
    validateEnvelope(decoded);
    assert.equal(method.requestSerialize(decoded).toString("hex"), hex);
  }
});

test("runner protobuf messages preserve their wire contract", () => {
  for (const [message, hex] of runnerFixtures) {
    assert.equal(method.responseSerialize(message).toString("hex"), hex);
    const decoded = method.responseDeserialize(Buffer.from(hex, "hex"));
    validateEnvelope(decoded);
    assert.equal(method.responseSerialize(decoded).toString("hex"), hex);
  }
});

test("protobuf preserves omission versus zero, false, and empty text", () => {
  const missing = method.responseDeserialize(Buffer.from("2200", "hex"));
  assert.equal(missing.result?.exitCode, undefined);
  assert.equal(missing.result?.timedOut, undefined);
  const present = method.responseDeserialize(method.responseSerialize({ result: {
    ...runnerFixtures[1][0].result!, exitCode: 0, timedOut: false
  } }));
  assert.equal(present.result?.exitCode, 0);
  assert.equal(present.result?.timedOut, false);
  assert.equal(decodeJson(present.result!.resultJson!), null);
  assert.equal(decodeJson(present.result!.errorJson!), null);
  assert.equal(decodeText(present.result!.stdoutUtf16le, 0), "");
  assert.equal(decodeText(present.result!.stderrUtf16le, 0), "");
});

test("source and log payloads preserve JavaScript strings exactly", () => {
  for (const text of ["", "ASCII", "é e\u0301 😀\0", "\ud800", "\udfff", "a\ud800b\udfff", "\\uD800"]) {
    const execute = method.requestDeserialize(method.requestSerialize({ execute: {
      ...hostFixtures[0][0].execute!, codeUtf16le: encodeText(text, Buffer.byteLength(text, "utf8"))
    } })).execute!;
    const result = method.responseDeserialize(method.responseSerialize({ result: {
      ...runnerFixtures[1][0].result!,
      stdoutUtf16le: encodeText(text, Buffer.byteLength(text, "utf8")),
      stderrUtf16le: encodeText(text, Buffer.byteLength(text, "utf8"))
    } })).result!;
    assert.equal(decodeText(execute.codeUtf16le, Buffer.byteLength(text, "utf8")), text);
    assert.equal(decodeText(result.stdoutUtf16le, Buffer.byteLength(text, "utf8")), text);
    assert.equal(decodeText(result.stderrUtf16le, Buffer.byteLength(text, "utf8")), text);
  }
});

test("empty, unknown-only, and multiple known message bodies fail closed", () => {
  for (const bytes of [Buffer.alloc(0), Buffer.from("1a00", "hex"), Buffer.from("0a001200", "hex")]) {
    assert.throws(() => validateEnvelope(method.requestDeserialize(bytes)), /exactly one/);
  }
  for (const hex of ["0a00", "1a00", "2a00", "12002200"]) {
    assert.throws(() => validateEnvelope(method.responseDeserialize(Buffer.from(hex, "hex"))), /exactly one/);
  }
  assert.throws(() => method.responseDeserialize(Buffer.from("2205ff", "hex")));
  assert.throws(() => method.responseDeserialize(Buffer.from('{"version":1,"type":"result"}')));
});

test("unknown protobuf fields do not become application fields", () => {
  const message = method.responseDeserialize(Buffer.from("1206080712027b7d3a0178", "hex"));
  validateEnvelope(message);
  assert.deepEqual(Object.entries(message).filter(([, value]) => value !== undefined),
    [["rpc", { id: 7, requestJson: Buffer.from("{}") }]]);
});

test("opaque JSON fields keep UTF-8, structure, dangerous-key, and size checks", () => {
  for (const payload of [
    Buffer.alloc(0), Buffer.from([0xff]), Buffer.from("{"), Buffer.from('{"constructor":{}}'),
    Buffer.from("[".repeat(34) + "0" + "]".repeat(34)),
    Buffer.from('["' + "x".repeat(DEFAULT_DECODE_LIMITS.maxStringBytes + 1) + '"]')
  ]) {
    const request = method.responseDeserialize(method.responseSerialize({ rpc: { id: 1, requestJson: payload } }));
    assert.throws(() => decodeJson(request.rpc!.requestJson));
  }
  assert.throws(() => decodeJson(Buffer.alloc(DEFAULT_DECODE_LIMITS.maxFrameBytes + 1)), /exceeds limit/);
  assert.throws(() => encodePayload("xxxx", 4), /exceeds limit/);
  const data = { items: [{ name: "instance", value: null }], more: false };
  assert.equal(JSON.stringify(decodeJson(encodePayload(data))), JSON.stringify(data));
});

test("bounded text rejects malformed and oversized UTF-16LE", () => {
  assert.throws(() => decodeText(Buffer.from([0]), 1), /invalid bounded/);
  assert.throws(() => decodeText(Buffer.alloc(4), 1), /invalid bounded/);
  assert.throws(() => decodeText(Buffer.from("😀", "utf16le"), 3), /exceeds limit/);
  assert.throws(() => encodeText("xxxx", 3), /exceeds limit/);
});

test("generated service interoperates and rejects earlier endpoints", async t => {
  const server = new Server();
  let sessions = 0;
  const handlers: RunnerServer = { session(call) {
    sessions += 1;
    call.on("error", () => {});
    call.on("data", message => {
      validateEnvelope(message);
      assert.deepEqual(message.execute, hostFixtures[0][0].execute);
      call.write(runnerFixtures[1][0]);
      call.end();
    });
  } };
  server.addService(RUNNER_SERVICE, handlers);
  t.after(() => server.forceShutdown());
  const port = await new Promise<number>((resolve, reject) => {
    server.bindAsync("127.0.0.1:0", ServerCredentials.createInsecure(), (error, bound) => {
      if (error) reject(error); else resolve(bound);
    });
  });
  const client = new RunnerClient(`127.0.0.1:${port}`, credentials.createInsecure());
  t.after(() => client.close());
  const call = client.session({ deadline: Date.now() + 5000 });
  await new Promise<void>((resolve, reject) => {
    call.on("error", reject);
    call.on("data", message => {
      assert.deepEqual(message.result, runnerFixtures[1][0].result);
      call.end();
    });
    call.on("end", resolve);
    call.write(hostFixtures[0][0]);
  });
  const old = new Client(`127.0.0.1:${port}`, credentials.createInsecure());
  t.after(() => old.close());
  for (const version of ["v1", "v2", "v3"]) {
    const legacy = old.makeBidiStreamRequest<Buffer, Buffer>(
      `/oracle.oci.mcp.runner.${version}.Runner/Session`, value => value, value => value,
      { deadline: Date.now() + 5000 }
    );
    await new Promise<void>((resolve, reject) => legacy.on("error", error => {
      if (error.code === status.UNIMPLEMENTED) resolve(); else reject(error);
    }));
  }
  assert.equal(sessions, 1);
});

for (const scenario of ["delayed runner", "deadline", "abort", "pre-aborted", "terminate"] as const) {
  test(`native gRPC lifecycle before readiness: ${scenario}`, { timeout: 10_000 }, async t => {
    const reservation = createServer();
    await new Promise<void>(resolve => reservation.listen(0, "127.0.0.1", resolve));
    const port = (reservation.address() as { port: number }).port;
    await new Promise<void>(resolve => reservation.close(() => resolve()));
    const address = `127.0.0.1:${port}`;
    const controller = new AbortController();
    if (scenario === "pre-aborted") controller.abort();
    const server = new Server();
    t.after(() => server.forceShutdown());
    let executions = 0;
    let remainingMs = 0;
    const handlers: RunnerServer = { session(call) {
      call.on("error", () => {});
      call.on("data", message => {
        assert(message.execute);
        executions += 1;
        remainingMs = Number(call.getDeadline()) - Date.now();
        call.write(runnerFixtures[1][0]);
        call.end();
      });
    } };
    server.addService(RUNNER_SERVICE, handlers);
    const execution = startGrpcExecution(address, credentials.createInsecure(), "42", {
      deadlineMs: Date.now() + (scenario === "delayed runner" ? 5000 : 200),
      signal: controller.signal,
      hostRpc: async () => assert.fail("no OCI calls expected"),
      memoryLimitMb: 128,
      maxResultBytes: 1024
    });
    t.after(() => execution.terminate());
    if (scenario === "delayed runner") {
      await new Promise(resolve => setTimeout(resolve, 100));
      await new Promise<void>((resolve, reject) => {
        server.bindAsync(address, ServerCredentials.createInsecure(), error => error ? reject(error) : resolve());
      });
    } else if (scenario === "abort") {
      controller.abort();
    } else if (scenario === "terminate") {
      await execution.terminate();
    }
    const result = await execution.result;
    await execution.terminate();
    const successful = scenario === "delayed runner";
    assert.equal(result.exitCode, successful ? 0 : -1);
    assert.equal(result.timedOut, !successful);
    assert.equal(executions, successful ? 1 : 0);
    if (successful) assert(remainingMs > 0 && remainingMs < 4950);
  });
}

const invalidResults: Record<string, Partial<NonNullable<RunnerMessage["result"]>>> = {
  "non-finite result": { resultJson: Buffer.from("1e999") },
  "dangerous result key": { resultJson: Buffer.from('{"nested":{"__proto__":{}}}') },
  "invalid error": { errorJson: encodePayload("bad"), exitCode: 1 },
  "empty error message": { errorJson: encodePayload({ message: "" }), exitCode: 1 },
  "oversized error": { errorJson: encodePayload({ message: "x".repeat(512 * 1024), detail: "x".repeat(512 * 1024) }), exitCode: 1 },
  "success with error": { errorJson: encodePayload({ message: "failed" }) },
  "failure without error": { exitCode: 1 },
  "timeout without error": { timedOut: true },
  "missing timeout": { timedOut: undefined }
};

for (const scenario of [
  ...Object.keys(invalidResults),
  "malformed result", "oversized result", "oversized logs", "gRPC error", "deadline", "MCP cancellation",
  "result then error", "result without status", "OK without result", "tiny result budget",
  "invalid RPC", "oversized RPC", "dangerous RPC", "late RPC", "backpressure", "drained RPC flood", "normal"
] as const) {
  test(`host session enforces lifecycle and buffering: ${scenario}`, { timeout: 10_000 }, async t => {
    const controller = new AbortController();
    let hostCalls = 0;
    let executions = 0;
    let cancelled = false;
    let replies = 0;
    const rpc = { rpc: { id: 1, requestJson: encodePayload({
      binding: "oracle", namespace: "oci", operation: "config", payload: {}
    }) } };
    if (scenario === "invalid RPC") rpc.rpc.requestJson = encodePayload({ operation: "invoke" });
    if (scenario === "drained RPC flood") rpc.rpc.requestJson = encodePayload({ operation: "invoke" });
    if (scenario === "oversized RPC") rpc.rpc.requestJson = Buffer.alloc(1024 * 1024 + 1, 0xff);
    if (scenario === "dangerous RPC") rpc.rpc.requestJson = Buffer.from('{"__proto__":{}}');
    const result = { result: {
      resultJson: encodePayload(42), errorJson: encodePayload(null), exitCode: 0, timedOut: false,
      stdoutUtf16le: encodeText("log\n", 4), stderrUtf16le: encodeText("\ud800", 3)
    } };
    const server = new Server();
    const handlers: RunnerServer = { session(call) {
      call.on("error", () => {});
      call.on("cancelled", () => { cancelled = true; });
      call.on("data", message => {
        if (message.execute) {
          executions += 1;
          if (scenario in invalidResults) {
            call.write({ result: { ...result.result, ...invalidResults[scenario] } });
            call.end();
          } else if (scenario === "backpressure") {
            call.pause();
            // A compromised runner keeps requesting work without draining replies.
            for (let id = 1; id <= 2000; id += 1) {
              call.write({ rpc: { ...rpc.rpc, id } });
            }
          } else if (scenario === "malformed result") {
            call.write({ result: { ...result.result, exitCode: undefined } });
          } else if (scenario === "oversized result") {
            call.write({ result: { ...result.result, resultJson: encodePayload("x".repeat(1024 * 1024)) } });
            call.end();
          } else if (scenario === "oversized logs") {
            call.write({ result: { ...result.result, stdoutUtf16le: Buffer.alloc(2 * (1024 * 1024 + 1)) } });
          } else if (scenario === "gRPC error") {
            call.emit("error", { code: status.INTERNAL, details: "private runner details" });
          } else if (scenario === "deadline") {
            // Leave the stream open; the host must cancel it natively.
          } else if (scenario === "MCP cancellation") {
            controller.abort();
          } else if (scenario === "result then error") {
            call.write(result, () => call.emit("error", { code: status.INTERNAL, details: "private details" }));
          } else if (scenario === "result without status") {
            call.write(result);
          } else if (scenario === "OK without result") {
            call.end();
          } else if (scenario === "tiny result budget") {
            call.write(result);
            call.end();
          } else if (scenario === "late RPC") {
            call.write(result);
            call.write(rpc);
            call.end();
          } else {
            call.write(rpc);
          }
        } else if (message.rpcResult) {
          if (scenario === "drained RPC flood") {
            replies += 1;
            call.write({ rpc: { ...rpc.rpc, id: replies + 1 } });
            return;
          }
          if (scenario === "invalid RPC" || scenario === "oversized RPC") {
            assert.deepEqual(decodeJson(message.rpcResult.resultJson), {
              ok: false,
              error: scenario === "invalid RPC" ? "invalid OCI bridge request" : "OCI request exceeded 1048576 bytes"
            });
          }
          call.write(result);
          call.end();
        }
      });
    } };
    server.addService(RUNNER_SERVICE, handlers);
    t.after(() => server.forceShutdown());
    const port = await new Promise<number>((resolve, reject) => {
      server.bindAsync("127.0.0.1:0", ServerCredentials.createInsecure(), (error, bound) => {
        if (error) reject(error); else resolve(bound);
      });
    });
    const timedOut = scenario === "deadline" || scenario === "result without status";
    const outcome = await runJavaScript("42", {
      timeoutSeconds: timedOut ? 1 : 5,
      signal: controller.signal,
      hostRpc: async () => {
        hostCalls += 1;
        return "x".repeat(64 * 1024);
      },
      isolationProvider: { run(code, options) {
        return startGrpcExecution(`127.0.0.1:${port}`, credentials.createInsecure(), code,
          { ...options, memoryLimitMb: 128, maxResultBytes: scenario === "tiny result budget" ? 2 : 1024 * 1024 });
      } }
    });
    const successful = ["normal", "late RPC", "tiny result budget", "invalid RPC", "oversized RPC"].includes(scenario);
    assert.equal(outcome.exitCode, successful ? 0 : timedOut ? -1 : 1);
    assert.equal(outcome.timedOut, timedOut);
    assert.equal(outcome.result, successful ? 42 : null);
    assert.equal(outcome.error?.message, successful ? undefined
      : timedOut ? "sandbox run deadline exceeded"
      : scenario === "MCP cancellation" ? "sandbox execution cancelled" : "sandbox protocol failed");
    assert.equal(outcome.stdout, successful ? "log\n" : "");
    assert.equal(outcome.stderr, successful ? "\ud800" : "");
    assert.equal(executions, 1);
    if (scenario !== "backpressure") {
      assert.equal(hostCalls, scenario === "normal" ? 1 : 0);
    }
    if (scenario === "drained RPC flood") assert.equal(replies, 101);
    if (timedOut || scenario === "MCP cancellation") {
      // Cancellation is delivered asynchronously after provider teardown.
      await new Promise<void>(resolve => server.tryShutdown(() => resolve()));
      assert.equal(cancelled, true);
    }
  });
}
