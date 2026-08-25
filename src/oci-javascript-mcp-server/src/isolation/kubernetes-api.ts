/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { PassThrough, Writable } from "node:stream";
import {
  AuthorizationV1Api,
  CoreV1Api,
  Exec,
  KubeConfig,
  NodeV1Api,
  Watch,
  type V1Pod,
  type V1SelfSubjectAccessReview,
  type V1Status
} from "@kubernetes/client-node";
import type { WorkerChannel, WorkerChannelStatus } from "./worker-channel.ts";
import type { KubernetesProfile } from "./kubernetes-config.ts";

export type KubernetesPod = V1Pod;

export type ResourceAttributes = {
  group?: string;
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
  createPod(namespace: string, pod: KubernetesPod): Promise<void>;
  waitForPodRunning(
    namespace: string,
    name: string,
    deadlineMs: number,
    signal: AbortSignal
  ): Promise<void>;
  openExecChannel(namespace: string, name: string): Promise<WorkerChannel>;
  deletePod(namespace: string, name: string): Promise<void>;
  podExists(namespace: string, name: string): Promise<boolean>;
  waitForPodDeleted(namespace: string, name: string, deadlineMs: number): Promise<boolean>;
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
    new Exec(config)
  );
}

export class ClientNodeKubernetesApi implements KubernetesApi {
  readonly #core: CoreV1Api;
  readonly #node: NodeV1Api;
  readonly #authorization: AuthorizationV1Api;
  readonly #watch: Watch;
  readonly #exec: Exec;

  constructor(
    core: CoreV1Api,
    node: NodeV1Api,
    authorization: AuthorizationV1Api,
    watch: Watch,
    exec: Exec
  ) {
    this.#core = core;
    this.#node = node;
    this.#authorization = authorization;
    this.#watch = watch;
    this.#exec = exec;
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

  async createPod(namespace: string, pod: KubernetesPod): Promise<void> {
    await this.#core.createNamespacedPod({ namespace, body: pod });
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

  async openExecChannel(namespace: string, name: string): Promise<WorkerChannel> {
    const output = new PassThrough();
    const input = new PassThrough();
    const stderr = new BoundedDiscardStream(64 * 1024);
    let statusResolve!: (status: WorkerChannelStatus) => void;
    let statusReject!: (error: Error) => void;
    let settled = false;
    const closed = new Promise<WorkerChannelStatus>((resolve, reject) => {
      statusResolve = resolve;
      statusReject = reject;
    });
    const finish = (status: WorkerChannelStatus) => {
      if (!settled) {
        settled = true;
        statusResolve(status);
      }
    };
    const webSocket = await this.#exec.exec(
      namespace,
      name,
      "runner",
      ["node", "--no-node-snapshot", "--experimental-strip-types", "/app/src/sandbox-worker.ts"],
      output,
      stderr,
      input,
      false,
      (status: V1Status) => finish({ exitCode: statusCode(status), signal: null })
    );
    webSocket.once("close", () => finish({ exitCode: null, signal: null }));
    webSocket.once("error", () => {
      if (!settled) {
        settled = true;
        statusReject(new Error("Kubernetes exec channel failed"));
      }
    });
    let stopped: Promise<void> | undefined;
    return {
      output,
      input,
      closed,
      stop() {
        return stopped ??= (async () => {
          input.end();
          output.destroy();
          stderr.destroy();
          if (webSocket.readyState < webSocket.CLOSING) {
            webSocket.close();
          }
          await closed.catch(() => undefined);
        })();
      }
    };
  }

  async deletePod(namespace: string, name: string): Promise<void> {
    try {
      await this.#core.deleteNamespacedPod({ name, namespace, gracePeriodSeconds: 0 });
    } catch (error) {
      if (!isNotFound(error)) {
        throw error;
      }
    }
  }

  async podExists(namespace: string, name: string): Promise<boolean> {
    try {
      await this.#core.readNamespacedPod({ name, namespace });
      return true;
    } catch (error) {
      if (isNotFound(error)) {
        return false;
      }
      throw error;
    }
  }

  async waitForPodDeleted(namespace: string, name: string, deadlineMs: number): Promise<boolean> {
    if (!await this.podExists(namespace, name)) {
      return true;
    }
    return await new Promise((resolve, reject) => {
      let settled = false;
      let request: AbortController | undefined;
      const finish = (deleted: boolean, error?: Error) => {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timeout);
        request?.abort();
        error ? reject(error) : resolve(deleted);
      };
      const timeout = setTimeout(() => finish(false), Math.max(1, deadlineMs - Date.now()));
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
            void this.podExists(namespace, name).then(exists => finish(!exists)).catch(
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

class BoundedDiscardStream extends Writable {
  readonly #limit: number;
  #bytes = 0;

  constructor(limit: number) {
    super();
    this.#limit = limit;
  }

  override _write(
    chunk: Buffer | string,
    _encoding: BufferEncoding,
    callback: (error?: Error | null) => void
  ): void {
    this.#bytes = Math.min(this.#limit, this.#bytes + Buffer.byteLength(chunk));
    callback();
  }
}

function statusCode(status: V1Status): number | null {
  const cause = status.details?.causes?.find(item => item.reason === "ExitCode");
  const value = cause?.message === undefined ? NaN : Number(cause.message);
  return Number.isSafeInteger(value) ? value : null;
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
