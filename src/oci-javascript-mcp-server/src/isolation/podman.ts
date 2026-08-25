/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { DEFAULT_MAX_FRAME_BYTES } from "../protocol.ts";
import { positiveIntegerEnv } from "../sandbox-common.ts";
import type { IsolationExecution, IsolationProvider } from "../types.ts";
import {
  runCleanupCommand,
  runnerEnvironment,
  startPipeExecution
} from "./pipe-execution.ts";

const DEFAULT_IMAGE = "localhost/oci-javascript-mcp-runner:dev";
const DEFAULT_MEMORY_LIMIT_MB = 128;
const DEFAULT_RESULT_BYTES = 1024 * 1024;
const MAX_PROTOCOL_RESULT_BYTES = DEFAULT_MAX_FRAME_BYTES - 64 * 1024;
const SAFE_IMAGE_REFERENCE = /^[A-Za-z0-9][A-Za-z0-9._/:@-]{0,255}$/;
const PODMAN_TERMINATION_TIMEOUT_MS = 6000;

export class PodmanIsolationProvider implements IsolationProvider {
  readonly #cliPath: string;
  readonly #image: string;

  constructor(options: { cliPath?: string; image?: string } = {}) {
    this.#cliPath = options.cliPath ?? "podman";
    if (!this.#cliPath || this.#cliPath.includes("\0")) {
      throw new Error("Podman CLI path is invalid");
    }
    this.#image = validateImage(options.image ?? DEFAULT_IMAGE);
  }

  run(
    code: string,
    options: Parameters<IsolationProvider["run"]>[1]
  ): IsolationExecution {
    const name = `oci-javascript-${randomUUID()}`;
    const configuredResultBytes = positiveIntegerEnv(
      "OCI_JAVASCRIPT_MAX_RESULT_BYTES",
      DEFAULT_RESULT_BYTES
    );
    const child = spawn(this.#cliPath, [
      "run",
      "--rm",
      "--interactive",
      "--pull", "never",
      "--log-driver", "none",
      "--name", name,
      "--cpus", "1",
      "--memory", "512m",
      "--pids-limit", "64",
      "--read-only",
      "--cap-drop", "ALL",
      "--security-opt", "no-new-privileges",
      "--network", "none",
      "--user", "65532:65532",
      "--ulimit", "nofile=64:64",
      "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
      this.#image
    ], {
      env: runnerEnvironment(),
      stdio: ["pipe", "pipe", "pipe"],
      detached: process.platform !== "win32"
    });
    return startPipeExecution(child, code, {
      ...options,
      memoryLimitMb: positiveIntegerEnv(
        "OCI_JAVASCRIPT_ISOLATE_MEMORY_MB",
        DEFAULT_MEMORY_LIMIT_MB
      ),
      maxResultBytes: Math.min(configuredResultBytes, MAX_PROTOCOL_RESULT_BYTES),
      terminationTimeoutMs: PODMAN_TERMINATION_TIMEOUT_MS
    }, () => runCleanupCommand(this.#cliPath, ["rm", "--force", "--ignore", name]));
  }
}

function validateImage(value: string): string {
  if (!SAFE_IMAGE_REFERENCE.test(value)) {
    throw new Error("Podman image is invalid");
  }
  return value;
}
