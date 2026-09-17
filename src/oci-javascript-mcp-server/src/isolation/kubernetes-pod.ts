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

export type AdmissionVariant = {
  readonly id: string;
  readonly pod: V1Pod;
};

export function unsafeAdmissionVariants(pod: V1Pod): AdmissionVariant[] {
  // LimitRange may default omitted resource fields before ValidatingAdmissionPolicy
  // evaluation, so only value changes that remain observable at that point belong here.
  return [
    variant("metadata-owner-reference", pod, value => {
      value.metadata!.ownerReferences = [{
        apiVersion: "v1",
        kind: "Pod",
        name: "unsafe-owner",
        uid: "00000000-0000-0000-0000-000000000000"
      }];
    }),
    variant("metadata-managed-by-label", pod, value => {
      value.metadata!.labels![MANAGED_BY_LABEL] = "unsafe";
    }),
    variant("metadata-provider-label", pod, value => {
      value.metadata!.labels![PROVIDER_LABEL] = "unsafe";
    }),
    variant("metadata-profile-label", pod, value => {
      value.metadata!.labels![PROFILE_LABEL] = "unsafe";
    }),
    variant("image", pod, value => {
      value.spec!.containers[0]!.image = "runner:mutable";
    }),
    variant("image-pull-policy", pod, value => {
      value.spec!.containers[0]!.imagePullPolicy = "Always";
    }),
    variant("service-account", pod, value => {
      value.spec!.serviceAccountName = "wrong-runner";
    }),
    variant("service-account-token", pod, value => {
      value.spec!.automountServiceAccountToken = true;
    }),
    variant("service-links", pod, value => {
      value.spec!.enableServiceLinks = true;
    }),
    variant("restart-policy", pod, value => {
      value.spec!.restartPolicy = "Always";
    }),
    variant("host-network", pod, value => {
      value.spec!.hostNetwork = true;
    }),
    variant("host-pid", pod, value => {
      value.spec!.hostPID = true;
    }),
    variant("host-ipc", pod, value => {
      value.spec!.hostIPC = true;
    }),
    variant("command", pod, value => {
      value.spec!.containers[0]!.command = ["sh"];
    }),
    variant("environment", pod, value => {
      value.spec!.containers[0]!.env = [{ name: "UNSAFE", value: "1" }];
    }),
    variant("container-count", pod, value => {
      value.spec!.containers.push({ ...structuredClone(value.spec!.containers[0]!), name: "extra" });
    }),
    variant("container-name", pod, value => {
      value.spec!.containers[0]!.name = "unsafe";
    }),
    variant("init-container", pod, value => {
      value.spec!.initContainers = [{ ...structuredClone(value.spec!.containers[0]!), name: "init" }];
    }),
    variant("ephemeral-container", pod, value => {
      value.spec!.ephemeralContainers = [{
        ...structuredClone(value.spec!.containers[0]!),
        name: "debug"
      }];
    }),
    variant("pod-run-as-non-root", pod, value => {
      value.spec!.securityContext!.runAsNonRoot = false;
    }),
    variant("pod-run-as-user", pod, value => {
      value.spec!.securityContext!.runAsUser = 0;
    }),
    variant("pod-run-as-group", pod, value => {
      value.spec!.securityContext!.runAsGroup = 0;
    }),
    variant("pod-fs-group", pod, value => {
      value.spec!.securityContext!.fsGroup = 0;
    }),
    variant("container-run-as-non-root", pod, value => {
      value.spec!.containers[0]!.securityContext!.runAsNonRoot = false;
    }),
    variant("container-run-as-user", pod, value => {
      value.spec!.containers[0]!.securityContext!.runAsUser = 0;
    }),
    variant("container-run-as-group", pod, value => {
      value.spec!.containers[0]!.securityContext!.runAsGroup = 0;
    }),
    variant("privilege-escalation", pod, value => {
      value.spec!.containers[0]!.securityContext!.allowPrivilegeEscalation = true;
    }),
    variant("privileged", pod, value => {
      value.spec!.containers[0]!.securityContext!.privileged = true;
    }),
    variant("read-only-root-filesystem", pod, value => {
      value.spec!.containers[0]!.securityContext!.readOnlyRootFilesystem = false;
    }),
    variant("pod-seccomp", pod, value => {
      value.spec!.securityContext!.seccompProfile = { type: "Unconfined" };
    }),
    variant("container-seccomp", pod, value => {
      value.spec!.containers[0]!.securityContext!.seccompProfile = { type: "Unconfined" };
    }),
    variant("capabilities-drop", pod, value => {
      value.spec!.containers[0]!.securityContext!.capabilities!.drop = [];
    }),
    variant("capabilities-add", pod, value => {
      value.spec!.containers[0]!.securityContext!.capabilities!.add = ["NET_ADMIN"];
    }),
    variant("ports", pod, value => {
      value.spec!.containers[0]!.ports = [{ containerPort: 8080 }];
    }),
    variant("volume-devices", pod, value => {
      value.spec!.containers[0]!.volumeDevices = [{ name: "unsafe", devicePath: "/dev/unsafe" }];
    }),
    variant("liveness-probe", pod, value => {
      value.spec!.containers[0]!.livenessProbe = { exec: { command: ["true"] } };
    }),
    variant("readiness-probe", pod, value => {
      value.spec!.containers[0]!.readinessProbe = { exec: { command: ["true"] } };
    }),
    variant("startup-probe", pod, value => {
      value.spec!.containers[0]!.startupProbe = { exec: { command: ["true"] } };
    }),
    variant("lifecycle-hook", pod, value => {
      value.spec!.containers[0]!.lifecycle = { postStart: { exec: { command: ["true"] } } };
    }),
    variant("cpu-resources", pod, value => {
      value.spec!.containers[0]!.resources!.requests!.cpu = "1m";
      value.spec!.containers[0]!.resources!.limits!.cpu = "1m";
    }),
    variant("cpu-resources-unequal", pod, value => {
      value.spec!.containers[0]!.resources!.limits!.cpu = "200m";
    }),
    variant("cpu-resources-malformed", pod, value => {
      value.spec!.containers[0]!.resources!.requests!.cpu = "invalid";
      value.spec!.containers[0]!.resources!.limits!.cpu = "invalid";
    }),
    variant("memory-resources", pod, value => {
      value.spec!.containers[0]!.resources!.requests!.memory = "1Mi";
      value.spec!.containers[0]!.resources!.limits!.memory = "1Mi";
    }),
    variant("memory-resources-unequal", pod, value => {
      value.spec!.containers[0]!.resources!.limits!.memory = "768Mi";
    }),
    variant("memory-resources-malformed", pod, value => {
      value.spec!.containers[0]!.resources!.requests!.memory = "invalid";
      value.spec!.containers[0]!.resources!.limits!.memory = "invalid";
    }),
    variant("ephemeral-storage-resources", pod, value => {
      value.spec!.containers[0]!.resources!.requests!["ephemeral-storage"] = "1Mi";
      value.spec!.containers[0]!.resources!.limits!["ephemeral-storage"] = "1Mi";
    }),
    variant("ephemeral-storage-resources-unequal", pod, value => {
      value.spec!.containers[0]!.resources!.limits!["ephemeral-storage"] = "128Mi";
    }),
    variant("ephemeral-storage-resources-malformed", pod, value => {
      value.spec!.containers[0]!.resources!.requests!["ephemeral-storage"] = "invalid";
      value.spec!.containers[0]!.resources!.limits!["ephemeral-storage"] = "invalid";
    }),
    variant("active-deadline", pod, value => {
      value.spec!.activeDeadlineSeconds = 121;
    }),
    variant("extra-volume", pod, value => {
      value.spec!.volumes!.push({ name: "extra", emptyDir: {} });
    }),
    variant("tmp-volume-source", pod, value => {
      value.spec!.volumes![0]!.emptyDir = undefined;
      value.spec!.volumes![0]!.configMap = { name: "unsafe" };
    }),
    variant("tmp-volume-name", pod, value => {
      value.spec!.volumes![0]!.name = "unsafe";
    }),
    variant("tmp-medium", pod, value => {
      value.spec!.volumes![0]!.emptyDir!.medium = "";
    }),
    variant("tmp-size-limit", pod, value => {
      value.spec!.volumes![0]!.emptyDir!.sizeLimit = "65Mi";
    }),
    variant("tmp-size-limit-malformed", pod, value => {
      value.spec!.volumes![0]!.emptyDir!.sizeLimit = "invalid";
    }),
    variant("tmp-size-limit-missing", pod, value => {
      delete value.spec!.volumes![0]!.emptyDir!.sizeLimit;
    }),
    variant("extra-volume-mount", pod, value => {
      value.spec!.containers[0]!.volumeMounts!.push({ name: "extra", mountPath: "/extra" });
    }),
    variant("tmp-mount-name", pod, value => {
      value.spec!.containers[0]!.volumeMounts![0]!.name = "unsafe";
    }),
    variant("tmp-mount-path", pod, value => {
      value.spec!.containers[0]!.volumeMounts![0]!.mountPath = "/unsafe";
    }),
    variant("tmp-mount-read-only", pod, value => {
      value.spec!.containers[0]!.volumeMounts![0]!.readOnly = true;
    })
  ];
}

export function runtimeAdmissionVariants(
  pod: V1Pod,
  policy: KubernetesRuntimePolicy
): AdmissionVariant[] {
  return policy.kind === "kata"
    ? [variant("runtime-class", pod, value => { value.spec!.runtimeClassName = "wrong-runtime"; })]
    : [];
}

function variant(id: string, pod: V1Pod, callback: (value: V1Pod) => void): AdmissionVariant {
  const variantPod = structuredClone(pod);
  callback(variantPod);
  return { id, pod: variantPod };
}
