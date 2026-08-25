/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import type { IsolationProvider } from "../types.ts";
import {
  createInClusterKubernetesApi,
  createKubeconfigKubernetesApi,
  type KubernetesApi
} from "./kubernetes-api.ts";
import {
  parseIsolationProviderName,
  parseKubernetesConfig,
  type LocalDevelopmentConfig
} from "./kubernetes-config.ts";
import type { KubernetesDiagnosticSink } from "./kubernetes-diagnostics.ts";
import { KubernetesIsolationProvider } from "./kubernetes.ts";
import { PodmanIsolationProvider } from "./podman.ts";

export type ProviderFactoryDependencies = {
  kubernetesApi?: KubernetesApi;
  kubernetesDiagnostics?: KubernetesDiagnosticSink;
  createKubeconfigApi?: (config: LocalDevelopmentConfig) => KubernetesApi;
  createInClusterApi?: () => KubernetesApi;
  startReconciliation?: boolean;
  createPodman?: (options: { cliPath?: string; image?: string }) => IsolationProvider;
};

export async function createIsolationProvider(
  environment: NodeJS.ProcessEnv = process.env,
  dependencies: ProviderFactoryDependencies = {}
): Promise<IsolationProvider> {
  const selected = parseIsolationProviderName(environment);
  if (selected === "podman") {
    const createPodman = dependencies.createPodman
      ?? (options => new PodmanIsolationProvider(options));
    return createPodman({
      cliPath: environment.OCI_JAVASCRIPT_PODMAN_CLI,
      image: environment.OCI_JAVASCRIPT_PODMAN_IMAGE
    });
  }

  const config = parseKubernetesConfig(environment);
  const api = dependencies.kubernetesApi ?? (config.credentialMode === "explicit-kubeconfig"
    ? (dependencies.createKubeconfigApi ?? (value => createKubeconfigKubernetesApi(
      value.kubeconfigPath,
      value.kubeconfigContext
    )))(config)
    : (dependencies.createInClusterApi ?? createInClusterKubernetesApi)());
  const provider = new KubernetesIsolationProvider(
    config,
    api,
    dependencies.kubernetesDiagnostics
  );
  await provider.preflight({ startReconciliation: dependencies.startReconciliation });
  return provider;
}
