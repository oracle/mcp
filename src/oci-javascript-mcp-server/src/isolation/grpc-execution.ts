/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import {
  Metadata,
  status,
  type ChannelCredentials,
  type ClientDuplexStream
} from "@grpc/grpc-js";
import {
  RunnerClient,
  MAX_GRPC_MESSAGE_BYTES,
  decodeText,
  encodeText,
  validateEnvelope,
  type HostMessage,
  type RunnerMessage
} from "../grpc.ts";
import {
  DEFAULT_DECODE_LIMITS,
  ProtocolError,
  decodeJson,
  encodePayload
} from "../protocol.ts";
import {
  MAX_CODE_BYTES,
  MAX_HOST_RPC_CALLS,
  MAX_HOST_RPC_REQUEST_BYTES,
  MAX_STDERR_BYTES,
  MAX_STDOUT_BYTES
} from "../sandbox-common.ts";
import type {
  HostRpcRequest,
  IsolationExecution,
  IsolationRunOptions,
  Json,
  JsonObject,
  SandboxResult
} from "../types.ts";

const GRPC_OPTIONS = {
  "grpc.enable_retries": 0,
  "grpc.max_receive_message_length": MAX_GRPC_MESSAGE_BYTES,
  "grpc.max_send_message_length": MAX_GRPC_MESSAGE_BYTES,
  "grpc.ssl_target_name_override": "oci-javascript-runner"
} as const;

export function startGrpcExecution(
  address: string,
  credentials: ChannelCredentials,
  code: string,
  input: IsolationRunOptions & { memoryLimitMb: number; maxResultBytes: number },
  onResponseStarted?: () => void
): IsolationExecution {
  const client = new RunnerClient(address, credentials, GRPC_OPTIONS);
  const call = client.session(new Metadata({ waitForReady: true }), { deadline: input.deadlineMs });
  let settled = false;
  // Leave one frame for the guest to receive the normal call-limit error.
  let remainingRpcFrames = MAX_HOST_RPC_CALLS + 1;
  let workerResult: SandboxResult | undefined;
  let resolveResult!: (value: SandboxResult) => void;
  const result = new Promise<SandboxResult>(resolve => {
    resolveResult = resolve;
  });
  const finish = (value: SandboxResult) => {
    if (settled) {
      return;
    }
    settled = true;
    input.signal.removeEventListener("abort", abort);
    resolveResult(value);
    call.cancel();
    client.close();
  };
  const fail = (message: string) => finish({
    result: null,
    error: { message },
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  });

  const abort = () => finish(timeoutResult());
  if (onResponseStarted) call.once("metadata", onResponseStarted);
  call.on("data", message => {
    if (settled || workerResult) {
      return;
    }
    try {
      validateEnvelope(message);
      if (message.rpc && --remainingRpcFrames < 0) {
        throw new ProtocolError("sandbox RPC call limit exceeded");
      }
      void handleWorkerMessage(message, call, input, value => {
        workerResult = value;
        call.end();
      }).catch(() => fail("sandbox protocol failed"));
    } catch {
      fail("sandbox protocol failed");
    }
  });
  call.once("error", () => {}); // The final status below determines the outcome.
  call.once("status", completion => {
    if (completion.code === status.OK && workerResult) {
      finish(workerResult);
    } else if (completion.code === status.DEADLINE_EXCEEDED) {
      finish(timeoutResult());
    } else {
      fail("sandbox protocol failed");
    }
  });
  input.signal.addEventListener("abort", abort, { once: true });
  if (input.signal.aborted) {
    abort();
  } else {
    try {
      send(call, { execute: {
        codeUtf16le: encodeText(code, MAX_CODE_BYTES),
        reflectionManifestJson: encodePayload(input.reflectionManifest ?? { services: {} }),
        memoryLimitMb: input.memoryLimitMb,
        maxResultBytes: input.maxResultBytes
      } });
    } catch {
      fail("sandbox protocol failed");
    }
  }

  return { result, async terminate() { abort(); } };
}

async function handleWorkerMessage(
  message: RunnerMessage,
  call: ClientDuplexStream<HostMessage, RunnerMessage>,
  input: IsolationRunOptions & { maxResultBytes: number },
  finish: (result: SandboxResult) => void
): Promise<void> {
  if (message.rpc) {
    const { id, requestJson } = message.rpc;
    if (id === undefined || id === 0) {
      throw new ProtocolError("invalid sandbox RPC message");
    }
    let rpcResult: Json;
    if (requestJson.byteLength > MAX_HOST_RPC_REQUEST_BYTES) {
      rpcResult = { ok: false, error: `OCI request exceeded ${MAX_HOST_RPC_REQUEST_BYTES} bytes` };
    } else {
      const request = decodeJson(requestJson);
      if (!isRpcRequest(request)) {
        rpcResult = { ok: false, error: "invalid OCI bridge request" };
      } else {
        try {
          rpcResult = await input.hostRpc(request);
        } catch {
          rpcResult = { ok: false, error: { message: "OCI call failed" } };
        }
      }
    }
    send(call, { rpcResult: { id, resultJson: encodePayload(rpcResult) } });
    return;
  }
  if (message.result) {
    const { resultJson, errorJson, exitCode, timedOut, stdoutUtf16le, stderrUtf16le } = message.result;
    if (exitCode === undefined || timedOut === undefined) {
      throw new ProtocolError("invalid sandbox result message");
    }
    const limits = {
      ...DEFAULT_DECODE_LIMITS,
      maxStringBytes: input.maxResultBytes
    };
    const error = decodeJson(errorJson, limits);
    if (error !== null && (
      !isObject(error) || typeof error.message !== "string" || !error.message
      || errorJson.byteLength > input.maxResultBytes
    )) {
      throw new ProtocolError("invalid sandbox result error");
    }
    if ((exitCode === 0) !== (error === null) || (timedOut && !error)) {
      throw new ProtocolError("inconsistent sandbox result status");
    }
    finish({
      result: decodeJson(resultJson, { ...limits, maxFrameBytes: input.maxResultBytes }),
      error: error as SandboxResult["error"],
      stdout: decodeText(stdoutUtf16le, MAX_STDOUT_BYTES),
      stderr: decodeText(stderrUtf16le, MAX_STDERR_BYTES),
      exitCode,
      timedOut
    });
    return;
  }
  throw new ProtocolError("unsupported sandbox message body");
}

function send(
  call: ClientDuplexStream<HostMessage, RunnerMessage>,
  message: HostMessage
): void {
  if (call.destroyed || call.writableEnded) {
    throw new Error("sandbox runner channel is closed");
  }
  // Do not accumulate replies for a runner that stops reading.
  if (!call.write(message)) {
    throw new ProtocolError("sandbox runner channel backpressure exceeded");
  }
}

function timeoutResult(): SandboxResult {
  return {
    result: null,
    error: { message: "sandbox run deadline exceeded" },
    stdout: "",
    stderr: "",
    exitCode: -1,
    timedOut: true
  };
}

function isObject(value: Json | undefined): value is JsonObject {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isRpcRequest(value: Json): value is HostRpcRequest {
  return isObject(value)
    && value.binding === "oracle"
    && value.namespace === "oci"
    && (value.operation === "invoke" || value.operation === "config" || value.operation === "discover")
    && isObject(value.payload);
}
