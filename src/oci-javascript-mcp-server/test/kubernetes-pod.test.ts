/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import test from "node:test";
import { parseKubernetesConfig } from "../src/isolation/kubernetes-config.ts";
import {
  EXPIRY_ANNOTATION,
  HOST_UID_ANNOTATION,
  PROFILE_LABEL,
  buildExecutionPod,
  derivePodTiming,
  runtimeAdmissionVariants,
  unsafeAdmissionVariants
} from "../src/isolation/kubernetes-pod.ts";
import { runtimePolicyFor } from "../src/isolation/kubernetes-runtime-policy.ts";
import {
  validInClusterEnvironment,
  validKataEnvironment,
  validLocalEnvironment
} from "./kata-fixtures.ts";

test("all Kubernetes profiles share the exact hardened credential-free base pod", () => {
  const environments = [
    validLocalEnvironment(),
    validInClusterEnvironment(),
    validKataEnvironment()
  ];
  const now = 1_800_000_000_000;
  const pods = environments.map((environment, index) => {
    const config = parseKubernetesConfig(environment);
    return buildExecutionPod(
      config,
      runtimePolicyFor(config),
      `oci-javascript-k8s-${index}`,
      "correlation",
      now + 30_000,
      now
    );
  });

  for (const pod of pods) {
    assert.equal(pod.metadata?.ownerReferences, undefined);
    assert.equal(pod.metadata?.annotations?.[EXPIRY_ANNOTATION], new Date(now + 60_000).toISOString());
    assert.equal(pod.spec?.restartPolicy, "Never");
    assert.equal(pod.spec?.activeDeadlineSeconds, 30);
    assert.equal(pod.spec?.automountServiceAccountToken, false);
    assert.equal(pod.spec?.enableServiceLinks, false);
    assert.equal(pod.spec?.serviceAccountName, "oci-js-runner");
    assert.equal(pod.spec?.hostNetwork, false);
    assert.equal(pod.spec?.hostPID, false);
    assert.equal(pod.spec?.hostIPC, false);
    assert.deepEqual(pod.spec?.securityContext?.seccompProfile, { type: "RuntimeDefault" });
    assert.equal(pod.spec?.containers.length, 1);
    const runner = pod.spec?.containers[0];
    assert.deepEqual(runner?.env, undefined);
    assert.deepEqual(runner?.ports, undefined);
    assert.equal(runner?.securityContext?.runAsNonRoot, true);
    assert.equal(runner?.securityContext?.runAsUser, 65532);
    assert.equal(runner?.securityContext?.allowPrivilegeEscalation, false);
    assert.equal(runner?.securityContext?.readOnlyRootFilesystem, true);
    assert.deepEqual(runner?.securityContext?.capabilities?.drop, ["ALL"]);
    assert.equal(runner?.resources?.requests?.cpu, runner?.resources?.limits?.cpu);
    assert.equal(runner?.resources?.requests?.memory, runner?.resources?.limits?.memory);
    assert.equal(
      runner?.resources?.requests?.["ephemeral-storage"],
      runner?.resources?.limits?.["ephemeral-storage"]
    );
    assert.deepEqual(runner?.volumeMounts, [{ name: "tmp", mountPath: "/tmp", readOnly: false }]);
    assert.deepEqual(pod.spec?.volumes, [{
      name: "tmp",
      emptyDir: { medium: "Memory", sizeLimit: "16Mi" }
    }]);
  }

  assert.equal(pods[0]?.metadata?.labels?.[PROFILE_LABEL], "local-development");
  assert.equal(pods[0]?.spec?.containers[0]?.imagePullPolicy, "Never");
  assert.equal(pods[0]?.metadata?.annotations?.[HOST_UID_ANNOTATION], undefined);
  assert.equal(pods[0]?.spec?.runtimeClassName, undefined);
  assert.equal(pods[1]?.spec?.runtimeClassName, undefined);
  assert.equal(pods[2]?.spec?.runtimeClassName, "kata-qemu-runtime-rs");
  assert.equal(pods[2]?.metadata?.annotations?.[HOST_UID_ANNOTATION], "12345678-1234-1234-1234-123456789abc");
});

test("runtime policy is monotonic and cannot be applied across profiles", () => {
  const standard = parseKubernetesConfig(validInClusterEnvironment());
  const kata = parseKubernetesConfig(validKataEnvironment());
  assert.throws(() => buildExecutionPod(
    standard,
    runtimePolicyFor(kata),
    "mismatch",
    "correlation",
    Date.now() + 30_000
  ), /does not match/);
});

test("pod timing covers rounding, maximum, expiry, and invalid boundaries", () => {
  assert.deepEqual(derivePodTiming(1001, 1000, 1000), {
    activeDeadlineSeconds: 1,
    expiresAt: new Date(2001).toISOString()
  });
  assert.equal(derivePodTiming(120_000, 30_000, 0).activeDeadlineSeconds, 120);
  assert.throws(() => derivePodTiming(1000, 1000, 1000), /deadline exceeded/);
  assert.throws(() => derivePodTiming(120_001, 1000, 0), /outside/);
  assert.throws(() => derivePodTiming(NaN, 1000, 0), /invalid/);
  assert.throws(
    () => derivePodTiming(Number.MAX_SAFE_INTEGER, 1, Number.MAX_SAFE_INTEGER - 1),
    /expiry/
  );
});

test("shared and Kata-only admission variants are separate and immutable", () => {
  const config = parseKubernetesConfig(validKataEnvironment());
  const policy = runtimePolicyFor(config);
  const pod = buildExecutionPod(
    config,
    policy,
    "oci-javascript-k8s-test",
    "correlation",
    Date.now() + 30_000
  );
  const original = structuredClone(pod);
  const shared = unsafeAdmissionVariants(pod);
  const runtime = runtimeAdmissionVariants(pod, policy);
  assert.equal(shared.length, 8);
  assert.equal(runtime.length, 1);
  assert.deepEqual(pod, original);
  assert.equal(shared.some(value => !value.spec?.containers[0]?.image?.includes("@sha256:")), true);
  assert.equal(shared.some(value => value.spec?.automountServiceAccountToken === true), true);
  assert.equal(shared.some(value => value.spec?.hostNetwork === true), true);
  assert.equal(shared.some(value => value.spec?.volumes?.length === 2), true);
  assert.equal(runtime[0]?.spec?.runtimeClassName, "wrong-runtime");
});
