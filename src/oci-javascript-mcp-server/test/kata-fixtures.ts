/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { KubernetesPod } from "../src/isolation/kubernetes-api.ts";
import type { KubernetesProfile } from "../src/isolation/kubernetes-config.ts";
import {
  MANAGED_BY_LABEL,
  PROFILE_LABEL,
  PROVIDER_LABEL
} from "../src/isolation/kubernetes-pod.ts";

export function validKataEnvironment(): NodeJS.ProcessEnv {
  return {
    ...validInClusterEnvironment(),
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "kata-in-cluster",
    OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS: "kata-qemu-runtime-rs",
    OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER: "kata-qemu-runtime-rs"
  };
}

export function validInClusterEnvironment(): NodeJS.ProcessEnv {
  return {
    OCI_JAVASCRIPT_ISOLATION_PROVIDER: "kubernetes",
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "in-cluster",
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: "oci-js-execution",
    OCI_JAVASCRIPT_KUBERNETES_IMAGE: `registry.example/runner@sha256:${"a".repeat(64)}`,
    OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT: "oci-js-runner",
    OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE: "oci-js-host",
    OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME: "oci-js-host-0",
    OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID: "12345678-1234-1234-1234-123456789abc"
  };
}

export function validLocalEnvironment(): NodeJS.ProcessEnv {
  return {
    OCI_JAVASCRIPT_ISOLATION_PROVIDER: "kubernetes",
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "local-development",
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: "oci-js-local",
    OCI_JAVASCRIPT_KUBERNETES_IMAGE: "oci-javascript-mcp-runner:dev",
    OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE: "true",
    OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT: "oci-js-runner",
    OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG: "/tmp/oci-javascript-test-kubeconfig",
    OCI_JAVASCRIPT_KUBERNETES_CONTEXT: "oci-js-local"
  };
}

export function conformingPodAdmission(pod: KubernetesPod, profile: KubernetesProfile): boolean {
  const spec = pod.spec;
  const container = spec?.containers[0];
  const expectedImage = profile === "local-development"
    ? "oci-javascript-mcp-runner:dev"
    : `registry.example/runner@sha256:${"a".repeat(64)}`;
  const expectedPullPolicy = profile === "local-development" ? "Never" : "IfNotPresent";
  const expectedRuntimeClass = profile === "kata-in-cluster"
    ? "kata-qemu-runtime-rs"
    : undefined;
  return pod.metadata?.ownerReferences === undefined
    && pod.metadata?.labels?.[MANAGED_BY_LABEL] === "oci-javascript-mcp"
    && pod.metadata?.labels?.[PROVIDER_LABEL] === "kubernetes"
    && pod.metadata?.labels?.[PROFILE_LABEL] === profile
    && spec?.runtimeClassName === expectedRuntimeClass
    && spec?.serviceAccountName === "oci-js-runner"
    && spec?.automountServiceAccountToken === false
    && spec?.enableServiceLinks === false
    && spec?.restartPolicy === "Never"
    && spec?.hostNetwork === false
    && spec?.hostPID === false
    && spec?.hostIPC === false
    && spec?.containers.length === 1
    && spec.initContainers === undefined
    && spec.ephemeralContainers === undefined
    && container?.name === "runner"
    && container.image === expectedImage
    && container.imagePullPolicy === expectedPullPolicy
    && same(container.command, [
      "node",
      "--no-node-snapshot",
      "--experimental-strip-types",
      "-e",
      "setInterval(() => {}, 2147483647)"
    ])
    && container.env === undefined
    && spec.securityContext?.runAsNonRoot === true
    && spec.securityContext.runAsUser === 65532
    && spec.securityContext.runAsGroup === 65532
    && spec.securityContext.fsGroup === 65532
    && spec.securityContext.seccompProfile?.type === "RuntimeDefault"
    && container.securityContext?.runAsNonRoot === true
    && container.securityContext.runAsUser === 65532
    && container.securityContext.runAsGroup === 65532
    && container.securityContext.allowPrivilegeEscalation === false
    && container.securityContext.privileged === false
    && container.securityContext.readOnlyRootFilesystem === true
    && same(container.securityContext.capabilities?.drop, ["ALL"])
    && container.securityContext.capabilities?.add === undefined
    && container.securityContext.seccompProfile?.type === "RuntimeDefault"
    && container.ports === undefined
    && container.volumeDevices === undefined
    && container.livenessProbe === undefined
    && container.readinessProbe === undefined
    && container.startupProbe === undefined
    && container.lifecycle === undefined
    && equalBoundedQuantity(
      container.resources?.requests?.cpu,
      container.resources?.limits?.cpu,
      "m",
      100,
      4000
    )
    && equalBoundedQuantity(
      container.resources?.requests?.memory,
      container.resources?.limits?.memory,
      "Mi",
      128,
      2048
    )
    && equalBoundedQuantity(
      container.resources?.requests?.["ephemeral-storage"],
      container.resources?.limits?.["ephemeral-storage"],
      "Mi",
      16,
      1024
    )
    && Number.isInteger(spec.activeDeadlineSeconds)
    && spec.activeDeadlineSeconds! >= 1
    && spec.activeDeadlineSeconds! <= 120
    && spec.volumes?.length === 1
    && spec.volumes[0]?.name === "tmp"
    && spec.volumes[0].emptyDir?.medium === "Memory"
    && boundedQuantity(spec.volumes[0].emptyDir.sizeLimit, "Mi", 1, 64)
    && same(container.volumeMounts, [{ name: "tmp", mountPath: "/tmp", readOnly: false }]);
}

export const reviewedResourceSettings: ReadonlyArray<Readonly<Record<string, string>>> = [
  {},
  {
    OCI_JAVASCRIPT_KUBERNETES_CPU_MILLICORES: "250",
    OCI_JAVASCRIPT_KUBERNETES_MEMORY_MB: "768",
    OCI_JAVASCRIPT_KUBERNETES_EPHEMERAL_STORAGE_MB: "128",
    OCI_JAVASCRIPT_KUBERNETES_TMP_MB: "32"
  },
  {
    OCI_JAVASCRIPT_KUBERNETES_CPU_MILLICORES: "100",
    OCI_JAVASCRIPT_KUBERNETES_MEMORY_MB: "128",
    OCI_JAVASCRIPT_KUBERNETES_EPHEMERAL_STORAGE_MB: "16",
    OCI_JAVASCRIPT_KUBERNETES_TMP_MB: "1"
  },
  {
    OCI_JAVASCRIPT_KUBERNETES_CPU_MILLICORES: "4000",
    OCI_JAVASCRIPT_KUBERNETES_MEMORY_MB: "2048",
    OCI_JAVASCRIPT_KUBERNETES_EPHEMERAL_STORAGE_MB: "1024",
    OCI_JAVASCRIPT_KUBERNETES_TMP_MB: "64"
  }
];

function equalBoundedQuantity(
  request: string | number | undefined,
  limit: string | number | undefined,
  suffix: string,
  minimum: number,
  maximum: number
): boolean {
  return request === limit && boundedQuantity(request, suffix, minimum, maximum);
}

function boundedQuantity(
  value: string | number | undefined,
  suffix: string,
  minimum: number,
  maximum: number
): boolean {
  if (typeof value !== "string") {
    return false;
  }
  const match = new RegExp(`^(\\d+)${suffix}$`).exec(value);
  const amount = match ? Number(match[1]) : NaN;
  return Number.isSafeInteger(amount) && amount >= minimum && amount <= maximum;
}

function same(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}
