/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { spawn, type ChildProcess } from "node:child_process";
import { randomUUID } from "node:crypto";
import { createServer } from "node:net";
import { credentials } from "@grpc/grpc-js";
import { generate } from "selfsigned";
import { MAX_RESULT_BYTES, positiveIntegerEnv } from "../sandbox-common.ts";
import type { IsolationExecution, IsolationProvider } from "../types.ts";
import { startGrpcExecution } from "./grpc-execution.ts";

const DEFAULT_IMAGE = "localhost/oci-javascript-mcp-runner:dev";
const DEFAULT_MEMORY_LIMIT_MB = 128;
const RUNNER_PORT = 50051;
const SAFE_IMAGE_REFERENCE = /^[A-Za-z0-9][A-Za-z0-9._/:@-]{0,255}$/;

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
    const id = randomUUID();
    const name = `oci-javascript-${id}`;
    const network = `oci-javascript-${id}`;
    const tls = createTlsBootstrap();
    let active: IsolationExecution | undefined;
    let child: ChildProcess | undefined;
    let close = Promise.resolve();
    let closed = true;
    let completed = false;
    let responseStarted = false;
    let stopping = false;
    let startupError: unknown;
    const ready = (async () => {
      await runPodman(this.#cliPath, [
        "network", "create", "--internal", "--disable-dns", network
      ]);
      if (stopping) {
        throw new Error("sandbox execution cancelled");
      }
      const port = await availablePort();
      child = spawn(this.#cliPath, [
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
        "--network", network,
        "--publish", `127.0.0.1:${port}:${RUNNER_PORT}`,
        "--user", "65532:65532",
        "--ulimit", "nofile=64:64",
        "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=16m",
        this.#image
      ], {
        env: runnerEnvironment(),
        stdio: ["pipe", "ignore", "ignore"],
        detached: process.platform !== "win32"
      });
      closed = false;
      const failed = new Promise<Error>(resolveFailure => {
        child!.once("error", () => {
          if (!responseStarted) resolveFailure(new Error("sandbox runner failed"));
        });
        close = new Promise<void>(resolveClose => child!.once("close", () => {
          closed = true;
          resolveClose();
          if (!responseStarted) {
            resolveFailure(new Error("sandbox runner exited before completing its session"));
          }
        }));
      });
      if (!child.stdin) {
        throw new Error("sandbox runner input is unavailable");
      }
      child.stdin.on("error", () => {});
      child.stdin.end(`${JSON.stringify(tls.runner)}\n`);
      const session = startGrpcExecution(
        `127.0.0.1:${port}`,
        tls.credentials,
        code,
        {
          ...options,
          memoryLimitMb: positiveIntegerEnv(
            "OCI_JAVASCRIPT_ISOLATE_MEMORY_MB",
            DEFAULT_MEMORY_LIMIT_MB
          ),
          maxResultBytes: MAX_RESULT_BYTES
        },
        () => { responseStarted = true; }
      );
      active = {
        result: Promise.race([session.result, failed.then(error => { throw error; })]),
        terminate: session.terminate
      };
      return active;
    })().catch(error => {
      startupError = error;
      return undefined;
    });
    const result = ready.then(execution => {
      if (!execution) {
        throw startupError;
      }
      return execution.result.then(value => {
        completed = true;
        return value;
      });
    });
    let cleanup: Promise<void> | undefined;
    const terminate = () => cleanup ??= (async () => {
      stopping = true;
      await ready;
      await active?.terminate();
      if (child) {
        if (completed && !closed) await waitForClose(close, 500);
        if (!closed) killChildTree(child);
      }
      const errors: unknown[] = [];
      if (child) {
        await runPodman(this.#cliPath, ["rm", "--force", "--ignore", name])
          .catch(error => errors.push(error));
        if (!closed) await waitForClose(close, 500);
        if (!closed) errors.push(new Error("sandbox runner did not close"));
      }
      await runPodman(this.#cliPath, ["network", "rm", "--ignore", network])
        .catch(error => errors.push(error));
      if (errors.length > 0) {
        throw errors[0];
      }
    })();
    return { result, terminate };
  }
}

function killChildTree(child: ChildProcess): void {
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

function waitForClose(close: Promise<void>, timeoutMs: number): Promise<void> {
  return new Promise(resolve => {
    const timeout = setTimeout(resolve, timeoutMs);
    timeout.unref();
    close.finally(() => {
      clearTimeout(timeout);
      resolve();
    });
  });
}

function createTlsBootstrap() {
  const certificate = (commonName: string) => generate(
    [{ name: "commonName", value: commonName }],
    {
      algorithm: "sha256",
      days: 1,
      keySize: 2048,
      extensions: [
        { name: "basicConstraints", cA: true },
        { name: "keyUsage", keyCertSign: true, digitalSignature: true, keyEncipherment: true },
        { name: "extKeyUsage", serverAuth: true, clientAuth: true },
        {
          name: "subjectAltName",
          altNames: [{ type: 2, value: commonName }]
        }
      ]
    }
  );
  const server = certificate("oci-javascript-runner");
  const client = certificate("oci-javascript-host");
  return {
    credentials: credentials.createSsl(
      Buffer.from(server.cert),
      Buffer.from(client.private),
      Buffer.from(client.cert)
    ),
    runner: {
      serverKey: server.private,
      serverCert: server.cert,
      clientCert: client.cert
    }
  };
}

function runPodman(command: string, args: string[]): Promise<void> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const child = spawn(command, args, { env: runnerEnvironment(), stdio: "ignore" });
    const finish = (error?: Error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      error ? reject(error) : resolve();
    };
    child.once("error", () => finish(new Error("Podman command failed")));
    child.once("close", code => finish(
      code === 0 ? undefined : new Error("Podman command exited unsuccessfully")
    ));
    const timeout = setTimeout(() => {
      child.kill("SIGKILL");
      finish(new Error("Podman command timed out"));
    }, 5_000);
    timeout.unref();
  });
}

function availablePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.unref();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(error => {
        if (error || !address || typeof address === "string") {
          reject(error ?? new Error("failed to allocate sandbox port"));
        } else {
          resolve(address.port);
        }
      });
    });
  });
}

function runnerEnvironment(): NodeJS.ProcessEnv {
  const environment: NodeJS.ProcessEnv = {};
  for (const name of ["PATH", "TMPDIR", "TMP", "TEMP", "NODE_V8_COVERAGE"]) {
    if (process.env[name]) {
      environment[name] = process.env[name];
    }
  }
  return environment;
}

function validateImage(value: string): string {
  if (!SAFE_IMAGE_REFERENCE.test(value)) {
    throw new Error("Podman image is invalid");
  }
  return value;
}
