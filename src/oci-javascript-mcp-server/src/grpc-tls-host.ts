/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { ChannelCredentials } from "@grpc/grpc-js";
import { credentials } from "@grpc/grpc-js";
import { generate } from "selfsigned";
import type { RunnerTlsBootstrap } from "./grpc-tls.ts";

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
