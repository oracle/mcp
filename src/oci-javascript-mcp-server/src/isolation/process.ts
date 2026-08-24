/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { runnerEnvironment, startPipeExecution } from "./pipe-execution.ts";
import type {
  IsolationExecution,
  IsolationProvider,
  ProviderCapabilities
} from "../types.ts";

const RUNNER_PATH = fileURLToPath(new URL("../runner.ts", import.meta.url));

export class ProcessIsolationProvider implements IsolationProvider {
  readonly #runnerPath: string;
  readonly capabilities: ProviderCapabilities = Object.freeze({
    provider: "process",
    boundary: "process",
    developmentOnly: true,
    separateGuestKernel: false,
    hardwareVirtualization: false,
    networkCreationBlocked: false
  });

  constructor(options: { allowInsecure: boolean; runnerPath?: string }) {
    if (!options.allowInsecure) {
      throw new Error(
        "local process isolation is insecure and requires OCI_JAVASCRIPT_ALLOW_INSECURE_PROCESS=1"
      );
    }
    this.#runnerPath = options.runnerPath ?? RUNNER_PATH;
  }

  async start(input: Parameters<IsolationProvider["start"]>[0]): Promise<IsolationExecution> {
    const child = spawn(process.execPath, [
      "--experimental-strip-types",
      "--max-old-space-size=256",
      this.#runnerPath
    ], {
      env: runnerEnvironment(),
      stdio: ["pipe", "pipe", "pipe"],
      detached: process.platform !== "win32"
    });
    return startPipeExecution(child, input);
  }
}
