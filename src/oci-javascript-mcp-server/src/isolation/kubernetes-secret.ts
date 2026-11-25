/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */
import type { V1Pod, V1Secret } from "@kubernetes/client-node";
import type { RunnerTlsBootstrap } from "../grpc-tls.ts";

export function executionSecretName(podName: string): string {
  return `${podName}-tls`;
}

export function buildExecutionSecret(pod: V1Pod, tls: RunnerTlsBootstrap): V1Secret {
  const metadata = pod.metadata!;
  return {
    apiVersion: "v1", kind: "Secret", type: "Opaque", immutable: true,
    metadata: {
      name: executionSecretName(metadata.name!), namespace: metadata.namespace,
      labels: { ...metadata.labels }, annotations: { ...metadata.annotations }
    },
    data: {
      serverKey: Buffer.from(tls.serverKey).toString("base64"),
      serverCert: Buffer.from(tls.serverCert).toString("base64"),
      clientCert: Buffer.from(tls.clientCert).toString("base64")
    }
  };
}
