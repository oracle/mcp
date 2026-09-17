#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { startServer } from "../src/server.ts";
import type { IsolationProvider, SandboxResult } from "../src/types.ts";

let activeExecutions = 0;
const fakeKataProvider: IsolationProvider = {
  run(code, options) {
    const result = (async (): Promise<SandboxResult> => {
      activeExecutions += 1;
      if (activeExecutions > 1) {
        activeExecutions -= 1;
        throw new Error("fake Kata provider observed unbounded server concurrency");
      }
      try {
      if (code.includes("delay")) {
        await new Promise(resolve => setTimeout(resolve, 25));
      }
      if (code.includes("timeout")) {
        return {
          result: null,
          error: { message: "sandbox run deadline exceeded" },
          stdout: "",
          stderr: "",
          exitCode: -1,
          timedOut: true
        };
      }
      if (code.includes("script-error")) {
        return {
          result: null,
          error: { message: "script failed" },
          stdout: "",
          stderr: "",
          exitCode: 1,
          timedOut: false
        };
      }
      if (code.includes("rpc")) {
        await options.hostRpc({ request: "fake-kata-rpc" });
      }
      return {
        result: 42,
        error: null,
        stdout: code.includes("log") ? "stdout-log" : "",
        stderr: code.includes("log") ? "stderr-log" : "",
        exitCode: 0,
        timedOut: false
      };
      } finally {
        activeExecutions -= 1;
      }
    })();
    return {
      result,
      terminationTimeoutMs: 30_000,
      async terminate() {}
    };
  }
};

await startServer({
  isolationProvider: fakeKataProvider,
  hostRpc: async () => ({ ok: true, internalControlPlane: "must-not-leak" })
});
