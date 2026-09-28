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
  MAX_STDERR_BYTES,
  MAX_STDOUT_BYTES,
  normalizeTimeoutMs,
  withDeadline
} from "./sandbox-common.ts";
import { SANDBOX_BOOTSTRAP } from "./sandbox-prelude.ts";
import type { Json, OciReflectionManifest, SandboxResult } from "./types.ts";

type SandboxApi = {
  encodeLastResult: ivm.Reference<() => Json>;
  run: ivm.Reference<(code: string) => Promise<void>>;
};

type RunState = {
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
        new ivm.Reference((
          request: ivm.Reference<unknown>,
          resolve: ivm.Reference<(result: Json) => void>
        ) => dispatchHostRpc(options.hostRpc, request, resolve)),
        new ivm.ExternalCopy(options.reflectionManifest ?? { services: {} }).copyInto()
      ],
      {
        result: { reference: true },
        timeout: timeoutMs
      }
    ) as ivm.Reference<Record<string, unknown>>;

    api = {
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
      return {
        result,
        error: null,
        stdout: output.stdout,
        stderr: output.stderr,
        exitCode: output.exceeded ? 1 : 0,
        timedOut: false
      };
    } catch (error) {
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
    api?.encodeLastResult.release();
    api?.run.release();
    isolate.dispose();
  }
}

function dispatchHostRpc(
  hostRpc: (request: unknown) => Promise<Json>,
  requestReference: ivm.Reference<unknown>,
  resolveReference: ivm.Reference<(result: Json) => void>
): void {
  void (async () => {
    let result: Json;
    try {
      const request = await requestReference.copy();
      result = await hostRpc(request);
    } catch {
      result = { ok: false, error: { message: "OCI call failed" } };
    }

    try {
      await resolveReference.apply(undefined, [result], {
        arguments: { copy: true }
      });
    } catch {
      // The isolate may already have been disposed after timeout or cancellation.
    } finally {
      for (const reference of [requestReference, resolveReference]) {
        try {
          reference.release();
        } catch {
          // Release is best-effort after isolate disposal.
        }
      }
    }
  })();
}

function remainingRunMs(state: RunState): number {
  const remainingMs = state.deadlineMs - Date.now();
  if (remainingMs <= 0) {
    throw new Error("sandbox run deadline exceeded");
  }
  return remainingMs;
}
