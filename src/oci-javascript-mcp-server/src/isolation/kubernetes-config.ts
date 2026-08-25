/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { isAbsolute } from "node:path";

export const ISOLATION_PROVIDER_ENV = "OCI_JAVASCRIPT_ISOLATION_PROVIDER";
export const KUBERNETES_PROFILE_ENV = "OCI_JAVASCRIPT_KUBERNETES_PROFILE";

export type IsolationProviderName = "podman" | "kubernetes";
export type KubernetesProfile = "local-development" | "in-cluster" | "kata-in-cluster";
export type KubernetesImagePullPolicy = "IfNotPresent" | "Never";

type SharedKubernetesConfig = {
  namespace: string;
  image: string;
  imagePullPolicy: KubernetesImagePullPolicy;
  imageDigestPinned: boolean;
  runnerServiceAccount: string;
  cpuMillicores: number;
  memoryMb: number;
  ephemeralStorageMb: number;
  tmpMb: number;
  isolateMemoryMb: number;
  maxResultBytes: number;
  cleanupTimeoutMs: number;
  reconcileIntervalMs: number;
};

export type LocalDevelopmentConfig = SharedKubernetesConfig & {
  profile: "local-development";
  credentialMode: "explicit-kubeconfig";
  kubeconfigPath: string;
  kubeconfigContext: string;
};

export type InClusterConfig = SharedKubernetesConfig & {
  profile: "in-cluster";
  credentialMode: "in-cluster";
  trustedHostNamespace: string;
  trustedHostPodName: string;
  trustedHostPodUid: string;
};

export type KataInClusterConfig = SharedKubernetesConfig & {
  profile: "kata-in-cluster";
  credentialMode: "in-cluster";
  trustedHostNamespace: string;
  trustedHostPodName: string;
  trustedHostPodUid: string;
  runtimeClass: string;
  runtimeHandler: string;
};

export type KubernetesConfig = LocalDevelopmentConfig | InClusterConfig | KataInClusterConfig;

export type KubernetesReconcilerConfig = {
  profile: "in-cluster" | "kata-in-cluster";
  namespace: string;
  reconcileIntervalMs: number;
};

const DNS_LABEL = /^[a-z0-9](?:[-a-z0-9]{0,61}[a-z0-9])?$/;
const DNS_SUBDOMAIN = /^[a-z0-9](?:[-a-z0-9.]{0,251}[a-z0-9])?$/;
const KUBERNETES_UID = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const DIGEST_IMAGE = /^[A-Za-z0-9](?:[A-Za-z0-9._:/-]{0,254})@sha256:[a-f0-9]{64}$/;
const LOCAL_IMAGE = /^[a-z0-9](?:[a-z0-9._:/-]{0,254})$/;

const LOCAL_ONLY_ENV = [
  "OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG",
  "OCI_JAVASCRIPT_KUBERNETES_CONTEXT",
  "OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE"
] as const;
const HOST_IDENTITY_ENV = [
  "OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE",
  "OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME",
  "OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID"
] as const;
const KATA_ONLY_ENV = [
  "OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS",
  "OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER"
] as const;

export function parseIsolationProviderName(
  environment: NodeJS.ProcessEnv = process.env
): IsolationProviderName {
  const value = environment[ISOLATION_PROVIDER_ENV];
  if (value === undefined) {
    if (environment[KUBERNETES_PROFILE_ENV] !== undefined) {
      throw new Error(`${KUBERNETES_PROFILE_ENV} requires ${ISOLATION_PROVIDER_ENV}='kubernetes'`);
    }
    return "podman";
  }
  if (value === "podman") {
    if (environment[KUBERNETES_PROFILE_ENV] !== undefined) {
      throw new Error(`${KUBERNETES_PROFILE_ENV} is incompatible with the podman provider`);
    }
    return value;
  }
  if (value === "kubernetes") {
    return value;
  }
  throw new Error(`${ISOLATION_PROVIDER_ENV} must be 'podman' or 'kubernetes'`);
}

export function parseKubernetesConfig(
  environment: NodeJS.ProcessEnv = process.env
): KubernetesConfig {
  const profile = requiredProfile(environment);
  const namespace = requiredDnsLabel(environment, "OCI_JAVASCRIPT_KUBERNETES_NAMESPACE");
  const image = required(environment, "OCI_JAVASCRIPT_KUBERNETES_IMAGE");
  const digestPinned = DIGEST_IMAGE.test(image);
  const shared = {
    namespace,
    image,
    imagePullPolicy: "IfNotPresent" as KubernetesImagePullPolicy,
    imageDigestPinned: digestPinned,
    runnerServiceAccount: requiredDnsLabel(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT"
    ),
    cpuMillicores: boundedInteger(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_CPU_MILLICORES",
      100,
      100,
      4000
    ),
    memoryMb: boundedInteger(environment, "OCI_JAVASCRIPT_KUBERNETES_MEMORY_MB", 512, 128, 2048),
    ephemeralStorageMb: boundedInteger(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_EPHEMERAL_STORAGE_MB",
      64,
      16,
      1024
    ),
    tmpMb: boundedInteger(environment, "OCI_JAVASCRIPT_KUBERNETES_TMP_MB", 16, 1, 64),
    isolateMemoryMb: boundedInteger(
      environment,
      "OCI_JAVASCRIPT_ISOLATE_MEMORY_MB",
      128,
      16,
      1024
    ),
    maxResultBytes: boundedInteger(
      environment,
      "OCI_JAVASCRIPT_MAX_RESULT_BYTES",
      1024 * 1024,
      1,
      (2 * 1024 * 1024) - (64 * 1024)
    ),
    cleanupTimeoutMs: boundedInteger(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_CLEANUP_TIMEOUT_SECONDS",
      30,
      1,
      60
    ) * 1000,
    reconcileIntervalMs: boundedInteger(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_RECONCILE_INTERVAL_SECONDS",
      30,
      5,
      300
    ) * 1000
  };

  if (profile === "local-development") {
    assertUnset(environment, [...HOST_IDENTITY_ENV, ...KATA_ONLY_ENV], profile);
    const kubeconfigPath = required(environment, "OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG");
    if (!isAbsolute(kubeconfigPath)) {
      throw new Error("OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG must be an absolute path");
    }
    const kubeconfigContext = required(environment, "OCI_JAVASCRIPT_KUBERNETES_CONTEXT");
    if (digestPinned) {
      return {
        ...shared,
        profile,
        credentialMode: "explicit-kubeconfig",
        kubeconfigPath,
        kubeconfigContext
      };
    }
    if (
      environment.OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE !== "true"
      || !isSafeLocalTaggedImage(image)
    ) {
      throw new Error(
        "local-development images must use @sha256 or an explicitly allowed safe local tag"
      );
    }
    return {
      ...shared,
      imagePullPolicy: "Never",
      profile,
      credentialMode: "explicit-kubeconfig",
      kubeconfigPath,
      kubeconfigContext
    };
  }

  assertUnset(environment, LOCAL_ONLY_ENV, profile);
  if (!digestPinned) {
    throw new Error("in-cluster Kubernetes images must use an immutable @sha256 digest");
  }
  const trustedHostNamespace = requiredDnsLabel(
    environment,
    "OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE"
  );
  if (namespace === trustedHostNamespace) {
    throw new Error("Kubernetes execution and trusted-host namespaces must be different");
  }
  const inCluster = {
    ...shared,
    credentialMode: "in-cluster" as const,
    trustedHostNamespace,
    trustedHostPodName: requiredDnsSubdomain(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME"
    ),
    trustedHostPodUid: requiredUid(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID"
    )
  };
  if (profile === "in-cluster") {
    assertUnset(environment, KATA_ONLY_ENV, profile);
    return { ...inCluster, profile };
  }
  return {
    ...inCluster,
    profile,
    runtimeClass: requiredDnsLabel(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS"
    ),
    runtimeHandler: requiredDnsLabel(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER"
    )
  };
}

export function parseKubernetesReconcilerConfig(
  environment: NodeJS.ProcessEnv = process.env
): KubernetesReconcilerConfig {
  const profile = requiredProfile(environment);
  if (profile === "local-development") {
    throw new Error("the cleanup-only reconciler supports only in-cluster profiles");
  }
  return {
    profile,
    namespace: requiredDnsLabel(environment, "OCI_JAVASCRIPT_KUBERNETES_NAMESPACE"),
    reconcileIntervalMs: boundedInteger(
      environment,
      "OCI_JAVASCRIPT_KUBERNETES_RECONCILE_INTERVAL_SECONDS",
      30,
      5,
      300
    ) * 1000
  };
}

function requiredProfile(environment: NodeJS.ProcessEnv): KubernetesProfile {
  const value = required(environment, KUBERNETES_PROFILE_ENV);
  if (value === "local-development" || value === "in-cluster" || value === "kata-in-cluster") {
    return value;
  }
  throw new Error(
    `${KUBERNETES_PROFILE_ENV} must be 'local-development', 'in-cluster', or 'kata-in-cluster'`
  );
}

function required(environment: NodeJS.ProcessEnv, name: string): string {
  const value = environment[name];
  if (value === undefined || value === "") {
    throw new Error(`${name} is required for the selected Kubernetes profile`);
  }
  if (value.includes("\0") || value.trim() !== value || value.length > 4096) {
    throw new Error(`${name} is invalid`);
  }
  return value;
}

function requiredDnsLabel(environment: NodeJS.ProcessEnv, name: string): string {
  const value = required(environment, name);
  if (!DNS_LABEL.test(value)) {
    throw new Error(`${name} must be a DNS-safe Kubernetes label`);
  }
  return value;
}

function requiredDnsSubdomain(environment: NodeJS.ProcessEnv, name: string): string {
  const value = required(environment, name);
  if (!DNS_SUBDOMAIN.test(value) || value.split(".").some(part => !DNS_LABEL.test(part))) {
    throw new Error(`${name} must be a DNS-safe Kubernetes name`);
  }
  return value;
}

function requiredUid(environment: NodeJS.ProcessEnv, name: string): string {
  const value = required(environment, name);
  if (!KUBERNETES_UID.test(value)) {
    throw new Error(`${name} must be a Kubernetes pod UID`);
  }
  return value;
}

function boundedInteger(
  environment: NodeJS.ProcessEnv,
  name: string,
  fallback: number,
  minimum: number,
  maximum: number
): number {
  const raw = environment[name];
  if (raw === undefined) {
    return fallback;
  }
  if (!/^(?:0|[1-9][0-9]*)$/.test(raw)) {
    throw new Error(`${name} must be an integer from ${minimum} through ${maximum}`);
  }
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new Error(`${name} must be an integer from ${minimum} through ${maximum}`);
  }
  return value;
}

function assertUnset(
  environment: NodeJS.ProcessEnv,
  names: readonly string[],
  profile: KubernetesProfile
): void {
  const incompatible = names.find(name => environment[name] !== undefined);
  if (incompatible) {
    throw new Error(`${incompatible} is incompatible with the ${profile} profile`);
  }
}

function isSafeLocalTaggedImage(value: string): boolean {
  if (!LOCAL_IMAGE.test(value) || value.includes("@")) {
    return false;
  }
  const finalSlash = value.lastIndexOf("/");
  const finalColon = value.lastIndexOf(":");
  return finalColon > finalSlash
    && finalColon < value.length - 1
    && /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$/.test(value.slice(finalColon + 1));
}
