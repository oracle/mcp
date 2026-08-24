/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import {
  runCleanupCommand,
  runnerEnvironment,
  startPipeExecution
} from "./pipe-execution.ts";
import type {
  IsolationExecution,
  IsolationProvider,
  ProviderCapabilities
} from "../types.ts";

const DEFAULT_IMAGE = "localhost/oci-javascript-mcp-runner:dev";
const DEFAULT_NETWORK = "oci-javascript-mcp-internal";
const SAFE_IMAGE_REFERENCE = /^[A-Za-z0-9][A-Za-z0-9._/:@-]{0,255}$/;
const SAFE_NETWORK_NAME = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,62}$/;

export class AppleContainerIsolationProvider implements IsolationProvider {
  readonly #cliPath: string;
  readonly #image: string;
  readonly #network: string;
  readonly capabilities: ProviderCapabilities = Object.freeze({
    provider: "apple-container",
    boundary: "virtual-machine",
    developmentOnly: true,
    separateGuestKernel: true,
    hardwareVirtualization: true,
    networkCreationBlocked: false
  });

  constructor(options: {
    cliPath?: string;
    image?: string;
    network?: string;
  } = {}) {
    this.#cliPath = options.cliPath ?? "container";
    if (!this.#cliPath || this.#cliPath.includes("\0")) {
      throw new Error("Apple container CLI path is invalid");
    }
    this.#image = validateName(
      options.image ?? DEFAULT_IMAGE,
      SAFE_IMAGE_REFERENCE,
      "Apple container image"
    );
    this.#network = validateName(
      options.network ?? DEFAULT_NETWORK,
      SAFE_NETWORK_NAME,
      "Apple container network"
    );
  }

  async start(input: Parameters<IsolationProvider["start"]>[0]): Promise<IsolationExecution> {
    const name = `oci-javascript-${randomUUID()}`;
    const child = spawn(this.#cliPath, [
      "run",
      "--rm",
      "--interactive",
      "--name", name,
      "--cpus", "1",
      "--memory", "512M",
      "--read-only",
      "--cap-drop", "ALL",
      "--no-dns",
      "--network", this.#network,
      "--user", "65532:65532",
      "--ulimit", "nofile=64:64",
      this.#image
    ], {
      env: runnerEnvironment(),
      stdio: ["pipe", "pipe", "pipe"],
      detached: process.platform !== "win32"
    });
    return startPipeExecution(
      child,
      input,
      () => runCleanupCommand(this.#cliPath, ["delete", "--force", name])
    );
  }
}

function validateName(value: string, pattern: RegExp, label: string): string {
  if (!pattern.test(value)) throw new Error(`${label} is invalid`);
  return value;
}
