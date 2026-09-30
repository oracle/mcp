/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { ChannelCredentials } from "@grpc/grpc-js";
import { credentials } from "@grpc/grpc-js";
import type { Readable } from "node:stream";
import { generate } from "selfsigned";

export const RUNNER_READY_LINE = "READY\n" as const;
const MAX_TLS_BOOTSTRAP_BYTES = 32 * 1024;

export type RunnerTlsBootstrap = {
  serverKey: string;
  serverCert: string;
  clientCert: string;
};

export type GrpcTlsBootstrap = {
  credentials: ChannelCredentials;
  runner: RunnerTlsBootstrap;
};

export function createGrpcTlsBootstrap(): GrpcTlsBootstrap {
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
        { name: "subjectAltName", altNames: [{ type: 2, value: commonName }] }
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

export function readRunnerTlsBootstrap(input: Readable): Promise<RunnerTlsBootstrap> {
  return new Promise((resolve, reject) => {
    let buffered = Buffer.alloc(0);
    let settled = false;
    const finish = (error?: Error, value?: RunnerTlsBootstrap) => {
      if (settled) return;
      settled = true;
      input.off("data", onData);
      input.off("end", onEnd);
      input.off("error", onError);
      error ? reject(error) : resolve(value!);
    };
    const invalid = () => finish(new Error("invalid sandbox TLS bootstrap"));
    const onError = () => invalid();
    const onEnd = () => invalid();
    const onData = (chunk: Buffer | string) => {
      const bytes = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      buffered = Buffer.concat([buffered, bytes]);
      if (buffered.length > MAX_TLS_BOOTSTRAP_BYTES) {
        invalid();
        return;
      }
      const newline = buffered.indexOf(0x0a);
      if (newline === -1) return;
      if (newline !== buffered.length - 1) {
        invalid();
        return;
      }
      try {
        const value = JSON.parse(buffered.subarray(0, newline).toString("utf8")) as unknown;
        if (!isRunnerTlsBootstrap(value)) {
          invalid();
          return;
        }
        finish(undefined, value);
      } catch {
        invalid();
      }
    };
    input.on("data", onData);
    input.once("end", onEnd);
    input.once("error", onError);
  });
}

function isRunnerTlsBootstrap(value: unknown): value is RunnerTlsBootstrap {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const record = value as Record<string, unknown>;
  return Object.keys(record).length === 3
    && typeof record.serverKey === "string"
    && typeof record.serverCert === "string"
    && typeof record.clientCert === "string";
}
