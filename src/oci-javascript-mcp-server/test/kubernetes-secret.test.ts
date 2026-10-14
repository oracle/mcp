/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */
import assert from "node:assert/strict";
import test from "node:test";
import { createGrpcTlsBootstrap } from "../src/grpc-tls-host.ts";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import { buildExecutionPod } from "../src/isolation/kubernetes-pod.ts";
import { buildExecutionSecret, executionSecretName } from "../src/isolation/kubernetes-secret.ts";
import { runtimePolicyFor } from "../src/isolation/kubernetes-runtime-policy.ts";
import { validInClusterEnvironment } from "./kata-fixtures.ts";

test("execution Secret contains only runner TLS and copied execution metadata", () => {
  const config = parseKubernetesConfig(validInClusterEnvironment());
  const pod = buildExecutionPod(config, runtimePolicyFor(config), "execution-123", "correlation", Date.now() + 30_000);
  const tls = createGrpcTlsBootstrap().runner;
  const secret = buildExecutionSecret(pod, tls);
  assert.equal(secret.immutable, true);
  assert.equal(secret.type, "Opaque");
  assert.equal(secret.metadata?.name, executionSecretName("execution-123"));
  assert.equal(secret.metadata?.namespace, config.namespace);
  assert.deepEqual(secret.metadata?.labels, pod.metadata?.labels);
  assert.deepEqual(secret.metadata?.annotations, pod.metadata?.annotations);
  assert.equal(secret.metadata?.ownerReferences, undefined);
  assert.deepEqual(Object.keys(secret.data!).sort(), ["clientCert", "serverCert", "serverKey"]);
  for (const key of ["serverKey", "serverCert", "clientCert"] as const) {
    assert.equal(Buffer.from(secret.data![key]!, "base64").toString(), tls[key]);
  }
  assert.deepEqual(pod.spec!.volumes![1], {
    name: "runner-tls", secret: { secretName: "execution-123-tls", defaultMode: 0o440,
      items: ["serverKey", "serverCert", "clientCert"].map(key => ({ key, path: key })) }
  });
  assert.deepEqual(pod.spec!.containers[0]!.volumeMounts![1], {
    name: "runner-tls", mountPath: "/run/oci-javascript/tls", readOnly: true
  });
  assert.deepEqual(pod.spec!.containers[0]!.command, [
    "node", "--no-node-snapshot", "--experimental-strip-types", "/app/src/sandbox-worker.ts", "--tls-files"
  ]);
});
