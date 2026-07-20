/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import ivm from "isolated-vm";
import {
  appendCapped,
  formatError,
  isTimeoutError,
  MAX_CODE_BYTES,
  normalizeTimeoutMs,
  withDeadline
} from "./sandbox-common.ts";
import { SANDBOX_BOOTSTRAP } from "./sandbox-prelude.ts";
import type { Json, OciReflectionManifest, SandboxResult } from "./types.ts";

const MAX_STDOUT_BYTES = 1024 * 1024;
const MAX_STDERR_BYTES = 1024 * 1024;
type SandboxApi = {
  drain: ivm.Reference<() => Promise<void>>;
  encodeLastResult: ivm.Reference<() => Json>;
  run: ivm.Reference<(code: string) => Promise<void>>;
};

type RunState = {
  accepting: boolean;
  deadlineMs: number;
};

export async function runJavaScriptInIsolate(
  code: string,
  options: {
    timeoutSeconds?: number;
    hostRpc: (request: unknown) => Promise<Json>;
    reflectionManifest?: OciReflectionManifest;
    memoryLimitMb: number;
    maxResultBytes: number;
  }
): Promise<SandboxResult> {
  if (Buffer.byteLength(code, "utf8") > MAX_CODE_BYTES) {
    throw new Error(`JavaScript code exceeds ${MAX_CODE_BYTES} bytes`);
  }

  const timeoutMs = normalizeTimeoutMs(options.timeoutSeconds);
  const state: RunState = {
    accepting: true,
    deadlineMs: Date.now() + timeoutMs
  };
  const output = {
    stdout: "",
    stderr: "",
    exceeded: false
  };

  const isolate = new ivm.Isolate({ memoryLimit: options.memoryLimitMb });
  let api: SandboxApi | undefined;
  try {
    const context = await isolate.createContext();
    const global = context.global;
    await global.set("globalThis", global.derefInto());

    const bootstrap = await context.evalClosure(
      SANDBOX_BOOTSTRAP,
      [
        new ivm.Reference((line: unknown) => {
          output.stdout = appendCapped(output.stdout, String(line), MAX_STDOUT_BYTES);
          if (Buffer.byteLength(output.stdout, "utf8") >= MAX_STDOUT_BYTES) {
            output.exceeded = true;
            throw new Error("Sandbox stdout exceeded limit");
          }
        }),
        new ivm.Reference((line: unknown) => {
          output.stderr = appendCapped(output.stderr, String(line), MAX_STDERR_BYTES);
          if (Buffer.byteLength(output.stderr, "utf8") >= MAX_STDERR_BYTES) {
            output.exceeded = true;
            throw new Error("Sandbox stderr exceeded limit");
          }
        }),
        new ivm.Reference(async (request: unknown) => {
          return options.hostRpc(request);
        }),
        new ivm.ExternalCopy(options.reflectionManifest ?? { services: {} }).copyInto()
      ],
      {
        result: { reference: true },
        timeout: timeoutMs
      }
    ) as ivm.Reference<Record<string, unknown>>;

    api = {
      drain: await bootstrap.get("drain", { reference: true }) as ivm.Reference<() => Promise<void>>,
      encodeLastResult: await bootstrap.get("encodeLastResult", {
        reference: true
      }) as ivm.Reference<() => Json>,
      run: await bootstrap.get("run", { reference: true }) as ivm.Reference<
        (code: string) => Promise<void>
      >
    };
    bootstrap.release();

    try {
      const evalTimeoutMs = remainingRunMs(state);
      await withDeadline(
        api.run.apply(undefined, [code], {
          arguments: { copy: true },
          result: { promise: true, copy: true },
          timeout: evalTimeoutMs
        }),
        evalTimeoutMs
      );
      await drainHostRpc(api, state);
      const resultTimeoutMs = remainingRunMs(state);
      const result = await withDeadline(
        api.encodeLastResult.apply(undefined, [], {
          result: { copy: true },
          timeout: resultTimeoutMs
        }),
        resultTimeoutMs
      ) as Json;
      const resultBytes = Buffer.byteLength(JSON.stringify(result), "utf8");
      if (resultBytes > options.maxResultBytes) {
        throw new Error(
          `Sandbox result was ${resultBytes} bytes, exceeding result limit ${options.maxResultBytes} bytes`
        );
      }
      await drainHostRpc(api, state);
      return {
        result,
        error: null,
        stdout: output.stdout,
        stderr: output.stderr,
        exitCode: output.exceeded ? 1 : 0,
        timedOut: false
      };
    } catch (error) {
      state.accepting = false;
      const timedOut = isTimeoutError(error);
      return {
        result: null,
        error: formatError(error),
        stdout: output.stdout,
        stderr: output.stderr,
        exitCode: timedOut ? -1 : 1,
        timedOut
      };
    }
  } finally {
    state.accepting = false;
    api?.drain.release();
    api?.encodeLastResult.release();
    api?.run.release();
    isolate.dispose();
  }
}

async function drainHostRpc(
  api: SandboxApi,
  state: RunState
): Promise<void> {
  const remainingMs = remainingRunMs(state);
  await withDeadline(
    api.drain.apply(undefined, [], {
      result: { promise: true, copy: true },
      timeout: remainingMs
    }),
    remainingMs
  );
}

function remainingRunMs(state: RunState): number {
  const remainingMs = state.deadlineMs - Date.now();
  if (remainingMs <= 0) {
    throw new Error("sandbox run deadline exceeded");
  }
  return remainingMs;
}
