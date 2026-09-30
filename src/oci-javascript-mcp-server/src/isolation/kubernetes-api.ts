/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import {
  AuthorizationV1Api,
  CoreV1Api,
  Exec,
  KubeConfig,
  NodeV1Api,
  Observable,
  PortForward,
  Watch,
  type ConfigurationOptions,
  type RequestContext,
  type ResponseContext,
  type V1Pod,
  type V1SelfSubjectAccessReview,
  type V1Status
} from "@kubernetes/client-node";
import type { RunnerTlsBootstrap } from "../grpc-tls.ts";
import {
  ClientNodeKubernetesGrpcTransport,
  type KubernetesGrpcTransport,
  type KubernetesGrpcTunnel,
  type KubernetesRunnerHandle
} from "./kubernetes-grpc.ts";
import type { KubernetesProfile } from "./kubernetes-config.ts";

export type KubernetesPod = V1Pod;

export type ResourceAttributes = {
  group?: string;
  name?: string;
  namespace?: string;
  resource: string;
  subresource?: string;
  verb: string;
};

export interface KubernetesApi {
  readNamespace(name: string): Promise<void>;
  readRuntimeClass(name: string): Promise<{ handler: string }>;
  selfCan(attributes: ResourceAttributes): Promise<boolean>;
  dryRunCreatePod(namespace: string, pod: KubernetesPod): Promise<boolean>;
  createPod(
    namespace: string,
    pod: KubernetesPod,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<void>;
  waitForPodRunning(
    namespace: string,
    name: string,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<void>;
  startRunner(
    namespace: string,
    name: string,
    bootstrap: RunnerTlsBootstrap,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<KubernetesRunnerHandle>;
  openTunnel(
    namespace: string,
    name: string,
    targetPort: number,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<KubernetesGrpcTunnel>;
  deletePod(namespace: string, name: string, signal?: AbortSignal): Promise<void>;
  podExists(namespace: string, name: string, signal?: AbortSignal): Promise<boolean>;
  waitForPodDeleted(
    namespace: string,
    name: string,
    deadlineMs: number,
    signal?: AbortSignal
  ): Promise<boolean>;
  listManagedPods(namespace: string, profile: KubernetesProfile): Promise<KubernetesPod[]>;
}

export function createInClusterKubernetesApi(): KubernetesApi {
  const config = new KubeConfig();
  config.loadFromCluster();
  return createClientNodeKubernetesApi(config);
}

export function createKubeconfigKubernetesApi(path: string, context: string): KubernetesApi {
  const config = new KubeConfig();
  config.loadFromFile(path);
  if (config.getContextObject(context) === null) {
    throw new Error("configured Kubernetes context does not exist");
  }
  config.setCurrentContext(context);
  return createClientNodeKubernetesApi(config);
}

function createClientNodeKubernetesApi(config: KubeConfig): KubernetesApi {
  return new ClientNodeKubernetesApi(
    config.makeApiClient(CoreV1Api),
    config.makeApiClient(NodeV1Api),
    config.makeApiClient(AuthorizationV1Api),
    new Watch(config),
    new ClientNodeKubernetesGrpcTransport(
      (deadlineMs, signal) => new Exec(deadlineKubeConfig(config, deadlineMs, signal)),
      (deadlineMs, signal) => new PortForward(deadlineKubeConfig(config, deadlineMs, signal))
    )
  );
}

export class ClientNodeKubernetesApi implements KubernetesApi {
  readonly #core: CoreV1Api;
  readonly #node: NodeV1Api;
  readonly #authorization: AuthorizationV1Api;
  readonly #watch: Watch;
  readonly #grpcTransport: KubernetesGrpcTransport;

  constructor(
    core: CoreV1Api,
    node: NodeV1Api,
    authorization: AuthorizationV1Api,
    watch: Watch,
    grpcTransport: KubernetesGrpcTransport
  ) {
    this.#core = core;
    this.#node = node;
    this.#authorization = authorization;
    this.#watch = watch;
    this.#grpcTransport = grpcTransport;
  }

  async readNamespace(name: string): Promise<void> {
    await this.#core.readNamespace({ name });
  }

  async readRuntimeClass(name: string): Promise<{ handler: string }> {
    const value = await this.#node.readRuntimeClass({ name });
    return { handler: value.handler };
  }

  async selfCan(attributes: ResourceAttributes): Promise<boolean> {
    const review: V1SelfSubjectAccessReview = {
      apiVersion: "authorization.k8s.io/v1",
      kind: "SelfSubjectAccessReview",
      spec: {
        resourceAttributes: {
          group: attributes.group ?? "",
          name: attributes.name,
          namespace: attributes.namespace,
          resource: attributes.resource,
          subresource: attributes.subresource,
          verb: attributes.verb
        }
      }
    };
    const response = await this.#authorization.createSelfSubjectAccessReview({ body: review });
    return response.status?.allowed === true;
  }

  async dryRunCreatePod(namespace: string, pod: KubernetesPod): Promise<boolean> {
    try {
      await this.#core.createNamespacedPod({ namespace, body: pod, dryRun: "All" });
      return true;
    } catch (error) {
      if (isAdmissionRejection(error)) {
        return false;
      }
      throw error;
    }
  }

  async createPod(
    namespace: string,
    pod: KubernetesPod,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<void> {
    if (signal.aborted || Date.now() >= deadlineMs) {
      throw new Error("sandbox run deadline exceeded");
    }
    const request = deadlineRequestSignal(deadlineMs, signal);
    try {
      await this.#core.createNamespacedPod(
        { namespace, body: pod },
        requestSignalOptions(request.signal)
      );
    } finally {
      request.dispose();
    }
  }

  async waitForPodRunning(
    namespace: string,
    name: string,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<void> {
    const current = await this.#core.readNamespacedPod({ name, namespace });
    if (current.status?.phase === "Running") {
      return;
    }
    if (podFailed(current)) {
      throw new Error("Kubernetes execution pod failed before running");
    }
    return await new Promise((resolve, reject) => {
      let settled = false;
      let request: AbortController | undefined;
      let timeout: NodeJS.Timeout | undefined;
      const finish = (error?: Error) => {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timeout);
        signal.removeEventListener("abort", aborted);
        request?.abort();
        error ? reject(error) : resolve();
      };
      const aborted = () => finish(new Error("sandbox run deadline exceeded"));
      signal.addEventListener("abort", aborted, { once: true });
      if (signal.aborted) {
        aborted();
        return;
      }
      timeout = setTimeout(aborted, Math.max(1, deadlineMs - Date.now()));
      timeout.unref();
      void this.#watch.watch(
        `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
        { fieldSelector: `metadata.name=${name}` },
        (_event, pod: KubernetesPod) => {
          if (pod.status?.phase === "Running") {
            finish();
            return;
          }
          if (podFailed(pod)) {
            finish(new Error("Kubernetes execution pod failed before running"));
          }
        },
        error => finish(error ? new Error("Kubernetes pod watch failed") : undefined)
      ).then(value => {
        request = value;
        if (settled) {
          request.abort();
        }
      }).catch(() => finish(new Error("Kubernetes pod watch failed")));
    });
  }

  startRunner(
    namespace: string,
    name: string,
    bootstrap: RunnerTlsBootstrap,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<KubernetesRunnerHandle> {
    return this.#grpcTransport.startRunner(namespace, name, bootstrap, deadlineMs, signal);
  }

  openTunnel(
    namespace: string,
    name: string,
    targetPort: number,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<KubernetesGrpcTunnel> {
    return this.#grpcTransport.openTunnel(namespace, name, targetPort, deadlineMs, signal);
  }

  async deletePod(namespace: string, name: string, signal?: AbortSignal): Promise<void> {
    try {
      await this.#core.deleteNamespacedPod(
        { name, namespace, gracePeriodSeconds: 0 },
        requestSignalOptions(signal)
      );
    } catch (error) {
      if (!isNotFound(error)) {
        throw error;
      }
    }
  }

  async podExists(namespace: string, name: string, signal?: AbortSignal): Promise<boolean> {
    try {
      await this.#core.readNamespacedPod({ name, namespace }, requestSignalOptions(signal));
      return true;
    } catch (error) {
      if (isNotFound(error)) {
        return false;
      }
      throw error;
    }
  }

  async waitForPodDeleted(
    namespace: string,
    name: string,
    deadlineMs: number,
    signal?: AbortSignal
  ): Promise<boolean> {
    if (signal?.aborted) {
      throw new Error("Kubernetes deletion confirmation cancelled");
    }
    if (!await this.podExists(namespace, name, signal)) {
      return true;
    }
    return await new Promise((resolve, reject) => {
      let settled = false;
      let request: AbortController | undefined;
      let timeout: NodeJS.Timeout | undefined;
      const finish = (deleted: boolean, error?: Error) => {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timeout);
        signal?.removeEventListener("abort", cancelled);
        request?.abort();
        error ? reject(error) : resolve(deleted);
      };
      const cancelled = () => finish(
        false,
        new Error("Kubernetes deletion confirmation cancelled")
      );
      signal?.addEventListener("abort", cancelled, { once: true });
      if (signal?.aborted) {
        cancelled();
        return;
      }
      timeout = setTimeout(() => finish(false), Math.max(1, deadlineMs - Date.now()));
      timeout.unref();
      void this.#watch.watch(
        `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods`,
        { fieldSelector: `metadata.name=${name}` },
        (event, pod: KubernetesPod) => {
          if (event === "DELETED" && pod.metadata?.name === name) {
            finish(true);
          }
        },
        error => {
          if (isNotFound(error)) {
            finish(true);
          } else if (error) {
            finish(false, new Error("Kubernetes deletion watch failed"));
          } else {
            void this.podExists(namespace, name, signal).then(exists => finish(!exists)).catch(
              () => finish(false, new Error("Kubernetes deletion confirmation failed"))
            );
          }
        }
      ).then(value => {
        request = value;
        if (settled) {
          request.abort();
        }
      }).catch(() => finish(false, new Error("Kubernetes deletion watch failed")));
    });
  }

  async listManagedPods(
    namespace: string,
    profile: KubernetesProfile
  ): Promise<KubernetesPod[]> {
    const response = await this.#core.listNamespacedPod({
      namespace,
      labelSelector: (
        "app.kubernetes.io/managed-by=oci-javascript-mcp,"
        + "oci.oracle.com/isolation-provider=kubernetes,"
        + `oci.oracle.com/kubernetes-profile=${profile}`
      )
    });
    return response.items;
  }
}

function requestSignalOptions(signal?: AbortSignal): ConfigurationOptions | undefined {
  if (!signal) {
    return undefined;
  }
  return {
    middlewareMergeStrategy: "append",
    middleware: [{
      pre(context: RequestContext) {
        context.setSignal(signal);
        return new Observable(Promise.resolve(context));
      },
      post(context: ResponseContext) {
        return new Observable(Promise.resolve(context));
      }
    }]
  };
}

function deadlineRequestSignal(
  deadlineMs: number,
  parent: AbortSignal
): { signal: AbortSignal; dispose(): void } {
  const controller = new AbortController();
  const abort = () => controller.abort();
  const timeout = setTimeout(abort, Math.max(1, deadlineMs - Date.now()));
  parent.addEventListener("abort", abort, { once: true });
  if (parent.aborted || Date.now() >= deadlineMs) {
    abort();
  }
  return {
    signal: controller.signal,
    dispose() {
      clearTimeout(timeout);
      parent.removeEventListener("abort", abort);
    }
  };
}

function deadlineKubeConfig(
  config: KubeConfig,
  deadlineMs: number,
  signal: AbortSignal
): KubeConfig {
  return {
    getCurrentCluster: () => config.getCurrentCluster(),
    async applyToHTTPSOptions(
      options: Parameters<KubeConfig["applyToHTTPSOptions"]>[0]
    ) {
      await config.applyToHTTPSOptions(options);
      Object.assign(options, {
        handshakeTimeout: Math.max(1, deadlineMs - Date.now()),
        signal
      });
    }
  } as KubeConfig;
}

export function isNotFound(error: unknown): boolean {
  if (!error || typeof error !== "object") {
    return false;
  }
  const record = error as Record<string, unknown>;
  return record.statusCode === 404
    || record.code === 404
    || (record.response as { statusCode?: unknown } | undefined)?.statusCode === 404;
}

function isAdmissionRejection(error: unknown): boolean {
  const status = errorStatus(error);
  return status === 400 || status === 403 || status === 422;
}

function errorStatus(error: unknown): unknown {
  if (!error || typeof error !== "object") {
    return undefined;
  }
  const record = error as Record<string, unknown>;
  return record.statusCode
    ?? record.code
    ?? (record.response as { statusCode?: unknown } | undefined)?.statusCode;
}

function podFailed(pod: KubernetesPod): boolean {
  const reason = pod.status?.containerStatuses?.[0]?.state?.waiting?.reason;
  return pod.status?.phase === "Failed"
    || reason === "ImagePullBackOff"
    || reason === "ErrImagePull"
    || reason === "CreateContainerConfigError";
}
