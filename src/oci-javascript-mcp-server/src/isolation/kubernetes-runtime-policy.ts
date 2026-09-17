/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { KubernetesConfig, KubernetesProfile } from "./kubernetes-config.ts";

export type StandardRuntimePolicy = {
  kind: "standard";
  profile: "local-development" | "in-cluster";
};

export type KataRuntimePolicy = {
  kind: "kata";
  profile: "kata-in-cluster";
  runtimeClassName: string;
  runtimeHandler: string;
};

/**
 * Deliberately exposes only typed additive runtime fields. It cannot alter the
 * base pod command, credentials, environment, storage, resources, or security.
 */
export type KubernetesRuntimePolicy = StandardRuntimePolicy | KataRuntimePolicy;

export function runtimePolicyFor(config: KubernetesConfig): KubernetesRuntimePolicy {
  if (config.profile === "kata-in-cluster") {
    return {
      kind: "kata",
      profile: config.profile,
      runtimeClassName: config.runtimeClass,
      runtimeHandler: config.runtimeHandler
    };
  }
  return { kind: "standard", profile: config.profile };
}

export function runtimeClassName(policy: KubernetesRuntimePolicy): string | undefined {
  return policy.kind === "kata" ? policy.runtimeClassName : undefined;
}

export function isInClusterProfile(
  profile: KubernetesProfile
): profile is "in-cluster" | "kata-in-cluster" {
  return profile === "in-cluster" || profile === "kata-in-cluster";
}
