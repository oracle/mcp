/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { V1Pod } from "@kubernetes/client-node";
import type { KubernetesConfig } from "./kubernetes-config.ts";
import {
  runtimeClassName,
  type KubernetesRuntimePolicy
} from "./kubernetes-runtime-policy.ts";

export const MANAGED_BY_LABEL = "app.kubernetes.io/managed-by";
export const PROVIDER_LABEL = "oci.oracle.com/isolation-provider";
export const PROFILE_LABEL = "oci.oracle.com/kubernetes-profile";
export const CORRELATION_ANNOTATION = "oci.oracle.com/execution-correlation";
export const EXPIRY_ANNOTATION = "oci.oracle.com/expires-at";
export const HOST_NAMESPACE_ANNOTATION = "oci.oracle.com/trusted-host-namespace";
export const HOST_NAME_ANNOTATION = "oci.oracle.com/trusted-host-name";
export const HOST_UID_ANNOTATION = "oci.oracle.com/trusted-host-uid";
export const RUNNER_CONTAINER_NAME = "runner";

const WAIT_COMMAND = [
  "node",
  "--no-node-snapshot",
  "--experimental-strip-types",
  "-e",
  "setInterval(() => {}, 2147483647)"
];

export type PodTiming = {
  activeDeadlineSeconds: number;
  expiresAt: string;
};

export function derivePodTiming(deadlineMs: number, cleanupTimeoutMs: number, nowMs: number): PodTiming {
  if (
    !Number.isSafeInteger(deadlineMs)
    || !Number.isSafeInteger(cleanupTimeoutMs)
    || !Number.isSafeInteger(nowMs)
    || cleanupTimeoutMs < 1
  ) {
    throw new Error("Kubernetes pod deadline is invalid");
  }
  const remainingMs = deadlineMs - nowMs;
  if (remainingMs <= 0) {
    throw new Error("sandbox run deadline exceeded");
  }
  const activeDeadlineSeconds = Math.ceil(remainingMs / 1000);
  if (activeDeadlineSeconds < 1 || activeDeadlineSeconds > 120) {
    throw new Error("Kubernetes pod deadline is outside the supported execution range");
  }
  const expiryMs = deadlineMs + cleanupTimeoutMs;
  if (!Number.isSafeInteger(expiryMs)) {
    throw new Error("Kubernetes pod expiry is invalid");
  }
  return { activeDeadlineSeconds, expiresAt: new Date(expiryMs).toISOString() };
}

export function buildExecutionPod(
  config: KubernetesConfig,
  policy: KubernetesRuntimePolicy,
  name: string,
  correlationId: string,
  deadlineMs: number,
  nowMs = Date.now()
): V1Pod {
  if (config.profile !== policy.profile) {
    throw new Error("Kubernetes runtime policy does not match the selected profile");
  }
  const timing = derivePodTiming(deadlineMs, config.cleanupTimeoutMs, nowMs);
  const hostAnnotations: Record<string, string> = config.credentialMode === "in-cluster" ? {
    [HOST_NAMESPACE_ANNOTATION]: config.trustedHostNamespace,
    [HOST_NAME_ANNOTATION]: config.trustedHostPodName,
    [HOST_UID_ANNOTATION]: config.trustedHostPodUid
  } : {};
  const selectedRuntimeClass = runtimeClassName(policy);
  return {
    apiVersion: "v1",
    kind: "Pod",
    metadata: {
      name,
      namespace: config.namespace,
      labels: {
        [MANAGED_BY_LABEL]: "oci-javascript-mcp",
        [PROVIDER_LABEL]: "kubernetes",
        [PROFILE_LABEL]: config.profile
      },
      annotations: {
        [CORRELATION_ANNOTATION]: correlationId,
        [EXPIRY_ANNOTATION]: timing.expiresAt,
        ...hostAnnotations
      }
    },
    spec: {
      ...(selectedRuntimeClass === undefined ? {} : { runtimeClassName: selectedRuntimeClass }),
      restartPolicy: "Never",
      activeDeadlineSeconds: timing.activeDeadlineSeconds,
      serviceAccountName: config.runnerServiceAccount,
      automountServiceAccountToken: false,
      enableServiceLinks: false,
      hostNetwork: false,
      hostPID: false,
      hostIPC: false,
      securityContext: {
        runAsNonRoot: true,
        runAsUser: 65532,
        runAsGroup: 65532,
        fsGroup: 65532,
        seccompProfile: { type: "RuntimeDefault" }
      },
      containers: [{
        name: RUNNER_CONTAINER_NAME,
        image: config.image,
        imagePullPolicy: config.imagePullPolicy,
        command: WAIT_COMMAND,
        securityContext: {
          runAsNonRoot: true,
          runAsUser: 65532,
          runAsGroup: 65532,
          allowPrivilegeEscalation: false,
          privileged: false,
          readOnlyRootFilesystem: true,
          capabilities: { drop: ["ALL"] },
          seccompProfile: { type: "RuntimeDefault" }
        },
        resources: {
          requests: {
            cpu: `${config.cpuMillicores}m`,
            memory: `${config.memoryMb}Mi`,
            "ephemeral-storage": `${config.ephemeralStorageMb}Mi`
          },
          limits: {
            cpu: `${config.cpuMillicores}m`,
            memory: `${config.memoryMb}Mi`,
            "ephemeral-storage": `${config.ephemeralStorageMb}Mi`
          }
        },
        volumeMounts: [{ name: "tmp", mountPath: "/tmp", readOnly: false }]
      }],
      volumes: [{
        name: "tmp",
        emptyDir: { medium: "Memory", sizeLimit: `${config.tmpMb}Mi` }
      }]
    }
  };
}

export function unsafeAdmissionVariants(pod: V1Pod): V1Pod[] {
  return [
    mutate(pod, value => { value.spec!.containers[0]!.image = "runner:mutable"; }),
    mutate(pod, value => { value.spec!.serviceAccountName = "wrong-runner"; }),
    mutate(pod, value => { value.spec!.automountServiceAccountToken = true; }),
    mutate(pod, value => { value.spec!.containers[0]!.command = ["sh"]; }),
    mutate(pod, value => { value.spec!.containers[0]!.env = [{ name: "UNSAFE", value: "1" }]; }),
    mutate(pod, value => { value.spec!.hostNetwork = true; }),
    mutate(pod, value => { value.spec!.volumes!.push({ name: "extra", emptyDir: {} }); }),
    mutate(pod, value => {
      value.spec!.containers[0]!.securityContext!.allowPrivilegeEscalation = true;
    })
  ];
}

export function runtimeAdmissionVariants(
  pod: V1Pod,
  policy: KubernetesRuntimePolicy
): V1Pod[] {
  return policy.kind === "kata"
    ? [mutate(pod, value => { value.spec!.runtimeClassName = "wrong-runtime"; })]
    : [];
}

function mutate(pod: V1Pod, callback: (value: V1Pod) => void): V1Pod {
  const value = structuredClone(pod);
  callback(value);
  return value;
}
