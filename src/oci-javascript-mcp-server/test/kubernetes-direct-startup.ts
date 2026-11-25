/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */
import type { IsolationProvider, SandboxResult } from "../src/types.ts";

export async function cancelRunningExecution(provider: IsolationProvider, onStarted: () => void): Promise<SandboxResult> {
  const controller = new AbortController();
  const started = Promise.withResolvers<void>();
  const execution = provider.run("await oci.config(); await new Promise(() => {})", {
    deadlineMs: Date.now() + 120_000, signal: controller.signal,
    hostRpc: async () => { started.resolve(); return null; }
  });
  try {
    await Promise.race([started.promise, execution.result.then(() => {
      throw new Error("direct execution ended before the guest RPC handshake");
    })]);
    onStarted();
    controller.abort();
    return await execution.result;
  } finally { controller.abort(); await execution.terminate(); }
}
