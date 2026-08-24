/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { HostExecutionBroker, developmentPolicy, productionPolicy } from "./policy.ts";
import { admitProvider } from "./isolation/admission.ts";
import { OciSdkRuntime } from "./oci.ts";
import type { ExecutionPolicy, ExecutionResult, IsolationProvider } from "./types.ts";

const MAX_CODE_BYTES = 1024 * 1024;
const MAX_RESULT_BYTES = 1024 * 1024;
const MAX_OUTPUT_BYTES = 1024 * 1024;

export async function runJavaScript(
  code: string,
  options: {
    timeoutSeconds?: number;
    provider: IsolationProvider;
    runtime?: OciSdkRuntime;
    mode?: "development" | "production";
    policy?: ExecutionPolicy;
    signal?: AbortSignal;
  }
): Promise<ExecutionResult> {
  if (typeof code !== "string") throw new Error("code must be a string");
  if (Buffer.byteLength(code, "utf8") > MAX_CODE_BYTES) {
    throw new Error(`code exceeds ${MAX_CODE_BYTES} bytes`);
  }
  const timeoutSeconds = options.timeoutSeconds ?? 30;
  if (!Number.isFinite(timeoutSeconds) || timeoutSeconds < 1 || timeoutSeconds > 120) {
    throw new Error("timeout must be between 1 and 120 seconds");
  }
  const mode = options.mode ?? "production";
  admitProvider(options.provider, mode);
  const runtime = options.runtime ?? new OciSdkRuntime();
  const manifest = runtime.manifest();
  const deadlineMs = Date.now() + Math.ceil(timeoutSeconds * 1000);
  const policy = options.policy ?? (mode === "development"
    ? developmentPolicy(manifest, deadlineMs, {
      allowMutations: process.env.OCI_JAVASCRIPT_ALLOW_MUTATIONS === "1"
    })
    : productionPolicy(deadlineMs));
  const broker = new HostExecutionBroker(runtime, policy);
  const execution = await options.provider.start({
    code,
    manifest,
    deadlineMs,
    maxResultBytes: MAX_RESULT_BYTES,
    maxOutputBytes: MAX_OUTPUT_BYTES,
    broker: request => broker.handle(request),
    signal: options.signal
  });
  try {
    return await execution.result;
  } finally {
    broker.cancel();
    await execution.destroy();
  }
}
