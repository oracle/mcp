/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";
import {
  DEFAULT_DECODE_LIMITS,
  FrameDecoder,
  ProtocolError,
  assertExactFields,
  encodeFrame,
  protocolMessage
} from "../protocol.ts";
import {
  CappedUtf8Accumulator,
  MAX_STDERR_BYTES,
  MAX_STDOUT_BYTES
} from "../sandbox-common.ts";
import type {
  IsolationExecution,
  IsolationRunOptions,
  Json,
  JsonObject,
  SandboxResult
} from "../types.ts";
import type { WorkerChannel } from "./worker-channel.ts";

export function startChannelExecution(
  channel: WorkerChannel,
  code: string,
  input: IsolationRunOptions & {
    memoryLimitMb: number;
    terminationTimeoutMs?: number;
  }
): IsolationExecution {
  const decoder = new FrameDecoder({
    ...DEFAULT_DECODE_LIMITS,
    maxFrameBytes: input.channelLimits.maxFrameBytes
  });
  const stdout = new CappedUtf8Accumulator(MAX_STDOUT_BYTES);
  const stderr = new CappedUtf8Accumulator(MAX_STDERR_BYTES);
  const writer = new ChannelWriter(channel, input);
  const seenRpcIds = new Set<number>();
  const rpcTasks = new Set<Promise<void>>();
  let phase: "WAIT_HEALTH" | "RUNNING" | "TERMINAL" = "WAIT_HEALTH";
  let ingressBytes = 0;
  let acceptedMessages = 0;
  let logBytes = 0;
  let settled = false;
  let closed = false;
  let terminalWrite: Promise<void> | undefined;
  let resolveResult!: (value: SandboxResult) => void;
  const result = new Promise<SandboxResult>(resolve => {
    resolveResult = resolve;
  });
  const close = channel.closed.then(
    () => { closed = true; },
    () => {
      closed = true;
      throw new ChannelRunnerError();
    }
  );
  void close.catch(() => undefined);
  let cleanup: Promise<void> | undefined;
  const terminate = (cleanupDeadlineMs?: number) => cleanup ??= (async () => {
    phase = "TERMINAL";
    await terminalWrite?.catch(() => undefined);
    await channel.stop(cleanupDeadlineMs ?? Date.now() + (input.terminationTimeoutMs ?? 5_000));
    if (!closed) {
      await close;
    }
  })();

  const finish = (value: SandboxResult, stop = false) => {
    if (settled) {
      return;
    }
    settled = true;
    phase = "TERMINAL";
    clearTimeout(timeout);
    input.signal.removeEventListener("abort", abort);
    resolveResult({ ...value, stdout: stdout.text, stderr: stderr.text });
    if (stop) {
      void terminate().catch(() => undefined);
    }
  };
  const fail = (message: string, stop = true) => finish({
    result: null,
    error: { message },
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  }, stop);

  const handleFailure = (error: unknown) => {
    if (settled) {
      void terminate().catch(() => undefined);
      return;
    }
    if (error instanceof ChannelDeadlineError) {
      finish(timeoutResult(), true);
    } else if (error instanceof ChannelRunnerError) {
      fail("sandbox runner failed", false);
    } else {
      fail("sandbox protocol failed");
    }
  };

  const startRpc = (id: number, request: JsonObject) => {
    const task = (async () => {
      let rpcResult: Json;
      try {
        rpcResult = await input.hostRpc(copyToPlainJson(request) as JsonObject);
      } catch {
        rpcResult = { ok: false, error: { message: "OCI call failed" } };
      }
      if (phase !== "RUNNING" || Date.now() >= input.deadlineMs) {
        return;
      }
      await writer.write(
        "rpc_result",
        { id, result: rpcResult },
        () => phase === "RUNNING" && Date.now() < input.deadlineMs
      );
    })();
    rpcTasks.add(task);
    void task.catch(handleFailure).finally(() => rpcTasks.delete(task));
  };

  const handleWorkerMessage = async (message: JsonObject): Promise<void> => {
    if (message.type === "health") {
      assertPhase(phase, "WAIT_HEALTH");
      assertExactFields(message, ["version", "type", "status"]);
      if (message.status !== "ready") {
        throw new ProtocolError("invalid sandbox worker health status");
      }
      phase = "RUNNING";
      await writer.write("execute", {
        code,
        timeoutMs: Math.max(1, input.deadlineMs - Date.now()),
        reflectionManifest: input.reflectionManifest ?? { services: {} },
        memoryLimitMb: input.memoryLimitMb,
        maxResultBytes: input.channelLimits.maxResultBytes
      });
      return;
    }

    assertPhase(phase, "RUNNING");
    if (message.type === "log") {
      assertExactFields(message, ["version", "type", "stream", "text"]);
      if (
        (message.stream !== "stdout" && message.stream !== "stderr")
        || typeof message.text !== "string"
      ) {
        throw new ProtocolError("invalid sandbox log message");
      }
      const bytes = Buffer.byteLength(message.text, "utf8");
      logBytes += bytes;
      if (logBytes > input.channelLimits.maxLogBytes) {
        throw new ProtocolError("sandbox channel log budget exceeded");
      }
      (message.stream === "stdout" ? stdout : stderr).append(message.text);
      return;
    }
    if (message.type === "rpc") {
      assertExactFields(message, ["version", "type", "id", "request"]);
      if (
        !Number.isSafeInteger(message.id)
        || (message.id as number) <= 0
        || !isObject(message.request)
      ) {
        throw new ProtocolError("invalid sandbox RPC message");
      }
      const id = message.id as number;
      if (seenRpcIds.has(id)) {
        throw new ProtocolError("sandbox RPC id was reused");
      }
      seenRpcIds.add(id);
      startRpc(id, message.request);
      return;
    }
    if (message.type === "result") {
      assertExactFields(message, ["version", "type", "result", "error", "exitCode", "timedOut"]);
      if (
        !Number.isInteger(message.exitCode)
        || typeof message.timedOut !== "boolean"
        || (message.error !== null && !isObject(message.error))
      ) {
        throw new ProtocolError("invalid sandbox result message");
      }
      if (
        encodedJsonBytes(message.result ?? null) + encodedJsonBytes(message.error)
          > input.channelLimits.maxResultBytes
      ) {
        throw new ProtocolError("sandbox result payload exceeded its configured limit");
      }
      phase = "TERMINAL";
      finish({
        result: message.result ?? null,
        error: message.error as SandboxResult["error"],
        stdout: "",
        stderr: "",
        exitCode: message.exitCode as number,
        timedOut: message.timedOut as boolean
      });
      return;
    }
    if (message.type === "protocol_error") {
      assertExactFields(message, ["version", "type", "error"]);
      if (!isObject(message.error) || typeof message.error.message !== "string") {
        throw new ProtocolError("invalid sandbox protocol error message");
      }
      throw new ProtocolError("sandbox worker reported a protocol failure");
    }
    throw new ProtocolError(`unsupported sandbox message type '${String(message.type)}'`);
  };

  const pump = async () => {
    try {
      for await (const value of channel.output) {
        const chunk = typeof value === "string" ? Buffer.from(value) : value as Buffer;
        ingressBytes += chunk.byteLength;
        if (ingressBytes > input.channelLimits.maxIngressBytes) {
          throw new ProtocolError("sandbox channel ingress budget exceeded");
        }
        for (const message of decoder.push(chunk)) {
          await Promise.resolve();
          await writer.ready();
          if (phase === "TERMINAL") {
            void terminate().catch(() => undefined);
            return;
          }
          acceptedMessages += 1;
          if (acceptedMessages > input.channelLimits.maxAcceptedMessages) {
            throw new ProtocolError("sandbox channel message budget exceeded");
          }
          await handleWorkerMessage(message);
        }
      }
      decoder.end();
      if (!settled) {
        const status = await channel.closed;
        fail(
          `sandbox runner exited before returning a result (${status.signal ?? status.exitCode ?? "unknown"})`,
          false
        );
      }
    } catch (error) {
      handleFailure(error);
    }
  };

  const timeout = setTimeout(() => {
    finish(timeoutResult(), true);
  }, Math.max(1, input.deadlineMs - Date.now()));
  const abort = () => {
    if (!settled && channel.input.writable) {
      terminalWrite = writer.write("cancel");
    }
    finish(timeoutResult(), true);
  };
  input.signal.addEventListener("abort", abort, { once: true });
  channel.input.once("error", () => handleFailure(new ChannelRunnerError()));
  channel.output.once("error", () => handleFailure(new ChannelRunnerError()));
  void channel.closed.then(
    status => setImmediate(() => {
      if (settled) {
        return;
      }
      try {
        decoder.end();
      } catch (error) {
        handleFailure(error);
        return;
      }
      fail(
        `sandbox runner exited before returning a result (${status.signal ?? status.exitCode ?? "unknown"})`,
        false
      );
    }),
    () => handleFailure(new ChannelRunnerError())
  );
  void pump();
  if (input.signal.aborted) {
    abort();
  }

  return { result, terminate, terminationTimeoutMs: input.terminationTimeoutMs };
}

function encodedJsonBytes(value: Json): number {
  return Buffer.byteLength(JSON.stringify(value), "utf8");
}

export function startPipeExecution(
  child: ChildProcessWithoutNullStreams,
  code: string,
  input: IsolationRunOptions & {
    memoryLimitMb: number;
    terminationTimeoutMs?: number;
  },
  afterClose?: () => Promise<void>
): IsolationExecution {
  return startChannelExecution(childProcessChannel(child, afterClose), code, input);
}

export function childProcessChannel(
  child: ChildProcessWithoutNullStreams,
  afterClose?: () => Promise<void>
): WorkerChannel {
  let statusResolve!: (value: { exitCode: number | null; signal: string | null }) => void;
  const closed = new Promise<{ exitCode: number | null; signal: string | null }>(resolve => {
    statusResolve = resolve;
  });
  child.once("close", (exitCode, signal) => statusResolve({ exitCode, signal }));
  let stopped: Promise<void> | undefined;
  return {
    output: child.stdout,
    input: child.stdin,
    closed,
    stop(_cleanupDeadlineMs: number) {
      return stopped ??= (async () => {
        killChildTree(child);
        await closed;
        await afterClose?.();
      })();
    }
  };
}

export function runnerEnvironment(): NodeJS.ProcessEnv {
  const environment: NodeJS.ProcessEnv = {};
  for (const name of ["PATH", "TMPDIR", "TMP", "TEMP", "NODE_V8_COVERAGE"]) {
    if (process.env[name]) {
      environment[name] = process.env[name];
    }
  }
  return environment;
}

export function runCleanupCommand(command: string, args: string[]): Promise<void> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const cleanup = spawn(command, args, {
      env: runnerEnvironment(),
      stdio: "ignore"
    });
    const finish = (error?: Error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    };
    cleanup.once("error", () => finish(new Error("Podman cleanup command failed")));
    cleanup.once("close", code => finish(
      code === 0 ? undefined : new Error("Podman cleanup command exited unsuccessfully")
    ));
    const timeout = setTimeout(() => {
      cleanup.kill("SIGKILL");
      finish(new Error("Podman cleanup command timed out"));
    }, 5_000);
    timeout.unref();
  });
}

class ChannelWriter {
  readonly #channel: WorkerChannel;
  readonly #input: IsolationRunOptions;
  #egressBytes = 0;
  #queuedWrites = 0;
  #tail: Promise<void> = Promise.resolve();
  #backpressure: Promise<void> | undefined;
  #failure: unknown;

  constructor(channel: WorkerChannel, input: IsolationRunOptions) {
    this.#channel = channel;
    this.#input = input;
  }

  async ready(): Promise<void> {
    if (this.#backpressure) {
      await this.#backpressure;
    }
    if (this.#failure) {
      throw this.#failure;
    }
  }

  write(
    type: string,
    fields: JsonObject = {},
    stillAllowed: () => boolean = () => true
  ): Promise<void> {
    if (this.#queuedWrites >= this.#input.channelLimits.maxAcceptedMessages + 2) {
      return Promise.reject(new ProtocolError("sandbox channel write queue budget exceeded"));
    }
    this.#queuedWrites += 1;
    const operation = this.#tail.then(async () => {
      if (this.#failure) {
        throw this.#failure;
      }
      if (!stillAllowed()) {
        return;
      }
      const frame = encodeFrame(
        protocolMessage(type, fields),
        this.#input.channelLimits.maxFrameBytes
      );
      this.#egressBytes += frame.byteLength;
      if (this.#egressBytes > this.#input.channelLimits.maxEgressBytes) {
        throw new ProtocolError("sandbox channel egress budget exceeded");
      }
      if (!this.#channel.input.writable) {
        throw new ProtocolError("sandbox runner channel is closed");
      }
      let accepted: boolean;
      try {
        accepted = this.#channel.input.write(frame);
      } catch {
        throw new ChannelRunnerError();
      }
      if (!accepted) {
        this.#channel.output.pause();
        this.#backpressure = waitForDrain(
          this.#channel,
          this.#input.deadlineMs,
          this.#input.signal
        );
        try {
          await this.#backpressure;
        } finally {
          this.#backpressure = undefined;
          if (!this.#channel.output.destroyed) {
            this.#channel.output.resume();
          }
        }
      }
    });
    this.#tail = operation;
    void operation.catch(error => {
      this.#failure ??= error;
    });
    return operation.finally(() => {
      this.#queuedWrites -= 1;
    });
  }
}

class ChannelDeadlineError extends Error {}
class ChannelRunnerError extends Error {}

function waitForDrain(
  channel: WorkerChannel,
  deadlineMs: number,
  signal: AbortSignal
): Promise<void> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (error?: Error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      channel.input.removeListener("drain", drained);
      channel.input.removeListener("error", failed);
      signal.removeEventListener("abort", aborted);
      if (error) {
        reject(error);
      } else {
        resolve();
      }
    };
    const drained = () => finish();
    const failed = () => finish(new ChannelRunnerError());
    const aborted = () => finish(new ChannelDeadlineError());
    const remainingMs = deadlineMs - Date.now();
    const timeout = setTimeout(aborted, Math.max(1, remainingMs));
    channel.input.once("drain", drained);
    channel.input.once("error", failed);
    signal.addEventListener("abort", aborted, { once: true });
    void channel.closed.then(failed, failed);
    if (signal.aborted || remainingMs <= 0) {
      aborted();
    }
  });
}

function assertPhase(
  actual: "WAIT_HEALTH" | "RUNNING" | "TERMINAL",
  expected: "WAIT_HEALTH" | "RUNNING"
): void {
  if (actual !== expected) {
    throw new ProtocolError(`sandbox message is invalid during ${actual}`);
  }
}

function killChildTree(child: ChildProcessWithoutNullStreams): void {
  if (child.exitCode !== null || child.signalCode !== null) {
    return;
  }
  if (process.platform !== "win32" && child.pid) {
    try {
      process.kill(-child.pid, "SIGKILL");
      return;
    } catch {
      // Fall back to killing the direct child.
    }
  }
  child.kill("SIGKILL");
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

function copyToPlainJson(value: Json): Json {
  if (Array.isArray(value)) {
    return value.map(copyToPlainJson);
  }
  if (!isObject(value)) {
    return value;
  }
  const result: JsonObject = {};
  for (const [key, child] of Object.entries(value)) {
    result[key] = copyToPlainJson(child);
  }
  return result;
}
