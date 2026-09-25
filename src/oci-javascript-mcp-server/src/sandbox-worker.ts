#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import {
  Server,
  ServerCredentials,
  status,
  type ServerDuplexStream
} from "@grpc/grpc-js";
import {
  RUNNER_SERVICE,
  MAX_GRPC_MESSAGE_BYTES,
  decodeText,
  encodeText,
  validateEnvelope,
  type HostMessage,
  type RunnerMessage
} from "./grpc.ts";
import {
  DEFAULT_DECODE_LIMITS,
  ProtocolError,
  decodeJson,
  encodePayload
} from "./protocol.ts";
import { runJavaScriptInIsolate } from "./sandbox-isolate.ts";
import { MAX_CODE_BYTES, MAX_STDERR_BYTES, MAX_STDOUT_BYTES } from "./sandbox-common.ts";
import type { Json, JsonObject, OciReflectionManifest } from "./types.ts";

type PendingRpc = {
  resolve: (value: Json) => void;
  reject: (error: Error) => void;
};

// The execute frame contains a trusted, host-generated SDK reflection manifest.
// Frames emitted by sandbox code are decoded by the host with tighter defaults.
const decodeLimits = {
  ...DEFAULT_DECODE_LIMITS,
  maxObjectKeys: 100_000,
  maxNodes: 250_000
};
const pendingRpc = new Map<number, PendingRpc>();
let nextRpcId = 1;
let running = false;
let session: ServerDuplexStream<HostMessage, RunnerMessage> | undefined;

const server = new Server({
  "grpc.max_receive_message_length": MAX_GRPC_MESSAGE_BYTES,
  "grpc.max_send_message_length": MAX_GRPC_MESSAGE_BYTES
});
server.addService(RUNNER_SERVICE, { session: openSession });
void startServer().catch(fatal);

function openSession(call: ServerDuplexStream<HostMessage, RunnerMessage>): void {
  if (session) {
    call.end();
    return;
  }
  session = call;
  call.on("data", message => {
    try {
      validateEnvelope(message);
      void handleMessage(message).catch(fatal);
    } catch (error) {
      fatal(error);
    }
  });
  call.on("error", () => {
    rejectPending(new Error("sandbox protocol failure"));
    server.tryShutdown(() => process.exit(70));
  });
  call.on("cancelled", () => {
    rejectPending(new Error("sandbox host channel closed"));
    // A locally ended stream must finish flushing its result/status first.
    if (!call.writableEnded) {
      process.exit(1);
    }
  });
}

async function startServer(): Promise<void> {
  const tls = await loadTls();
  const credentials = ServerCredentials.createSsl(
    Buffer.from(tls.clientCert),
    [{
      private_key: Buffer.from(tls.serverKey),
      cert_chain: Buffer.from(tls.serverCert)
    }],
    true
  );
  const port = Number(process.env.OCI_JAVASCRIPT_RUNNER_PORT ?? 50051);
  if (!isPositiveInteger(port) || port > 65535) {
    throw new Error("invalid sandbox runner port");
  }
  await new Promise<void>((resolve, reject) => {
    server.bindAsync(`0.0.0.0:${port}`, credentials, error => {
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    });
  });
}

async function loadTls(): Promise<{
  serverKey: string;
  serverCert: string;
  clientCert: string;
}> {
  let input = "";
  for await (const chunk of process.stdin) {
    input += String(chunk);
    if (Buffer.byteLength(input, "utf8") > 32 * 1024) {
      throw new Error("sandbox TLS bootstrap is too large");
    }
  }
  const value = JSON.parse(input) as unknown;
  if (!isTlsBootstrap(value)) {
    throw new Error("invalid sandbox TLS bootstrap");
  }
  return value;
}

async function handleMessage(message: HostMessage): Promise<void> {
  if (message.execute) {
    const { codeUtf16le, reflectionManifestJson, memoryLimitMb, maxResultBytes } = message.execute;
    if (running) {
      throw new ProtocolError("sandbox worker accepts exactly one execution");
    }
    const code = decodeText(codeUtf16le, MAX_CODE_BYTES);
    if (!isPositiveInteger(memoryLimitMb) || !isPositiveInteger(maxResultBytes)) {
      throw new ProtocolError("invalid sandbox execute message");
    }
    const reflectionManifest = decodeJson(reflectionManifestJson, decodeLimits);
    if (!isObject(reflectionManifest)) {
      throw new ProtocolError("invalid sandbox reflection manifest");
    }
    running = true;
    await execute(
      code,
      reflectionManifest as unknown as OciReflectionManifest,
      memoryLimitMb,
      maxResultBytes
    );
    return;
  }

  if (message.rpcResult) {
    const { id, resultJson } = message.rpcResult;
    if (id === undefined || id === 0) {
      throw new ProtocolError("invalid sandbox RPC result");
    }
    const pending = pendingRpc.get(id);
    if (!pending) {
      throw new ProtocolError("unknown sandbox RPC response id");
    }
    const result = decodeJson(resultJson, decodeLimits);
    pendingRpc.delete(id);
    pending.resolve(result);
    return;
  }

  throw new ProtocolError("unsupported host message body");
}

async function execute(
  code: string,
  reflectionManifest: OciReflectionManifest,
  memoryLimitMb: number,
  maxResultBytes: number
): Promise<void> {
  const timeoutMs = Number(session!.getDeadline()) - Date.now();
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new ProtocolError("sandbox execution requires a future deadline");
  }
  const result = await runJavaScriptInIsolate(code, {
    timeoutSeconds: timeoutMs / 1000,
    hostRpc,
    reflectionManifest,
    memoryLimitMb,
    maxResultBytes
  });
  sendAndExit({ result: {
    resultJson: encodePayload(result.result),
    errorJson: encodePayload(result.error),
    exitCode: result.exitCode,
    timedOut: result.timedOut,
    stdoutUtf16le: encodeText(result.stdout, MAX_STDOUT_BYTES),
    stderrUtf16le: encodeText(result.stderr, MAX_STDERR_BYTES)
  } }, result.exitCode === 0 ? 0 : 1);
}

function hostRpc(request: unknown): Promise<Json> {
  const id = nextRpcId;
  nextRpcId += 1;
  return new Promise((resolve, reject) => {
    pendingRpc.set(id, { resolve, reject });
    try {
      send({ rpc: {
        id,
        requestJson: encodePayload(request as Json)
      } });
    } catch (error) {
      pendingRpc.delete(id);
      reject(error instanceof Error ? error : new Error(String(error)));
    }
  });
}

function send(message: RunnerMessage): void {
  if (!session || session.destroyed || session.writableEnded) {
    throw new Error("sandbox host channel is closed");
  }
  session.write(message);
}

function sendAndExit(message: RunnerMessage, exitCode: number): void {
  if (!session) {
    process.exit(exitCode);
  }
  session.write(message, () => {
    session?.end();
    server.tryShutdown(() => process.exit(exitCode));
  });
}

function fatal(_error: unknown): void {
  if (!session) {
    process.exit(70);
  }
  session.emit("error", { code: status.INTERNAL, details: "sandbox protocol failure" });
}

function rejectPending(error: Error): void {
  for (const pending of pendingRpc.values()) {
    pending.reject(error);
  }
  pendingRpc.clear();
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value > 0;
}

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isTlsBootstrap(value: unknown): value is {
  serverKey: string;
  serverCert: string;
  clientCert: string;
} {
  return isObject(value)
    && Object.keys(value).length === 3
    && typeof value.serverKey === "string"
    && typeof value.serverCert === "string"
    && typeof value.clientCert === "string";
}
