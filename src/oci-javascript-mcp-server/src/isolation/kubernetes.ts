/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { randomUUID } from "node:crypto";
import { isIP } from "node:net";
import { createGrpcTlsBootstrap } from "../grpc-tls-host.ts";
import { MAX_RESULT_BYTES } from "../sandbox-common.ts";
import type { IsolationExecution, IsolationProvider, SandboxResult } from "../types.ts";
import { requiredExecutionPermissions, type KubernetesApi } from "./kubernetes-api.ts";
import type { KubernetesConfig } from "./kubernetes-config.ts";
import {
  diagnosticEvent,
  stderrKubernetesDiagnosticSink,
  type KubernetesDiagnosticSink,
  type KubernetesPhase,
  type KubernetesReason
} from "./kubernetes-diagnostics.ts";
import { buildExecutionPod } from "./kubernetes-pod.ts";
import { buildExecutionSecret, executionSecretName } from "./kubernetes-secret.ts";
import {
  runtimePolicyFor,
  type KubernetesRuntimePolicy
} from "./kubernetes-runtime-policy.ts";
import { startGrpcExecution } from "./grpc-execution.ts";
import { reconcileExpiredExecutions, startExpiryReconciliation } from "./kubernetes-reconciler.ts";
import type {
  KubernetesGrpcTunnel,
  KubernetesRunnerHandle
} from "./kubernetes-grpc.ts";

const POD_NAME_PREFIX = "oci-javascript-k8s-";
export class KubernetesIsolationProvider implements IsolationProvider {
  readonly #config: KubernetesConfig;
  readonly #policy: KubernetesRuntimePolicy;
  readonly #api: KubernetesApi;
  readonly #diagnostics: KubernetesDiagnosticSink;
  #stopReconciliation: (() => void) | undefined;
  #ready = false;

  constructor(
    config: KubernetesConfig,
    api: KubernetesApi,
    diagnostics: KubernetesDiagnosticSink = stderrKubernetesDiagnosticSink
  ) {
    this.#config = config;
    this.#policy = runtimePolicyFor(config);
    this.#api = api;
    this.#diagnostics = diagnostics;
  }

  async preflight(options: { startReconciliation?: boolean } = {}): Promise<void> {
    this.#ready = false;
    const started = Date.now();
    const correlationId = randomUUID();
    this.#emit(correlationId, "preflight", "started", "none", started);
    try {
      await this.#api.readNamespace(this.#config.namespace);
      for (const permission of requiredExecutionPermissions(this.#config.profile)) {
        const name = permission.resource === "namespaces" ? this.#config.namespace : undefined;
        const allowed = await this.#api.selfCan({
          group: permission.group,
          name,
          namespace: permission.namespaced ? this.#config.namespace : undefined,
          resource: permission.resource,
          subresource: "subresource" in permission ? permission.subresource : undefined,
          verb: permission.verb
        });
        if (!allowed) {
          throw new PreflightError("authorization");
        }
      }
      const reconciliation = await reconcileExpiredExecutions(
        this.#api,
        this.#config.namespace,
        this.#config.profile
      );
      if (reconciliation.failureCount > 0) {
        throw new PreflightError("cleanup");
      }
      if (options.startReconciliation !== false) {
        this.#stopReconciliation ??= startExpiryReconciliation(
          this.#api,
          this.#config.namespace,
          this.#config.profile,
          this.#config.reconcileIntervalMs,
          summary => {
            const failed = !summary || summary.failureCount > 0;
            this.#emit(
              randomUUID(),
              "reconciling",
              failed ? "failed" : "succeeded",
              failed ? "cleanup" : "none",
              Date.now(),
              summary
                ? {
                    successCount: summary.deletedPodNames.length + summary.deletedSecretNames.length,
                    failureCount: summary.failureCount
                  }
                : { successCount: 0, failureCount: 1 }
            );
          }
        );
      }
      this.#emit(correlationId, "preflight", "succeeded", "none", started);
      this.#ready = true;
    } catch (error) {
      const reason = error instanceof PreflightError ? error.reason : "api";
      this.#emit(correlationId, "preflight", "failed", reason, started);
      throw new Error(`Kubernetes provider preflight failed (${reason})`);
    }
  }

  stopReconciliation(): void {
    this.#stopReconciliation?.();
    this.#stopReconciliation = undefined;
  }

  run(code: string, options: Parameters<IsolationProvider["run"]>[1]): IsolationExecution {
    if (!this.#ready) {
      throw new Error("Kubernetes provider was not preflighted");
    }
    const name = `${POD_NAME_PREFIX}${randomUUID()}`;
    const correlationId = randomUUID();
    const started = Date.now();
    const localAbort = new AbortController();
    const abort = () => localAbort.abort();
    options.signal.addEventListener("abort", abort, { once: true });
    let runner: KubernetesRunnerHandle | undefined;
    let runnerPromise: Promise<KubernetesRunnerHandle> | undefined;
    let tunnel: KubernetesGrpcTunnel | undefined;
    let tunnelPromise: Promise<KubernetesGrpcTunnel> | undefined;
    let grpcExecution: IsolationExecution | undefined;
    let grpcCompleted = false;
    let createSettled: Promise<string> | undefined;
    const direct = this.#config.profile !== "local-development";
    const secretName = executionSecretName(name);
    let terminating = false;
    let cleanup: Promise<void> | undefined;
    let terminationDeadlineMs: number | undefined;
    let runnerStopping: Promise<void> | undefined;
    let tunnelStopping: Promise<void> | undefined;
    let prematureRunner: Promise<never> | undefined;
    let prematureTunnel: Promise<never> | undefined;
    let channelFailed = false;
    let postCleanupDeletionRequired = false;
    let primaryCleanupFinished = false;
    let lateDeletion: Promise<void> | undefined;
    let postCleanupSecretDeletionRequired = false;
    let lateSecretDeletion: Promise<void> | undefined;

    const watchClosure = <T>(closed: Promise<T>, message: string) => {
      const premature = closed.then(() => {
        if (!grpcCompleted) {
          channelFailed = true;
          throw new Error(message);
        }
        return new Promise<never>(() => {});
      }, error => {
        if (!grpcCompleted) {
          channelFailed = true;
          throw error;
        }
        return new Promise<never>(() => {});
      });
      // Startup may still be awaiting another resource when this rejects.
      void premature.catch(() => undefined);
      return premature;
    };
    const stopRunner = (handle: KubernetesRunnerHandle) => runnerStopping ??=
      Promise.resolve().then(() => handle.stop(terminationDeadlineMs!));
    const stopTunnel = (handle: KubernetesGrpcTunnel) => tunnelStopping ??=
      Promise.resolve().then(() => handle.stop(terminationDeadlineMs!));

    const phase = (value: KubernetesPhase) => {
      this.#emit(correlationId, value, "started", "none", started);
    };

    const deleteKnownPod = async (cleanupDeadlineMs: number, emitSuccess: boolean) => {
      phase("deleting");
      await deletePodByDeadline(
        this.#api,
        this.#config.namespace,
        name,
        cleanupDeadlineMs
      );
      phase("deleted");
      if (emitSuccess) {
        this.#emit(correlationId, "deleted", "succeeded", "none", started);
      }
    };

    const startLateDeletionIfRequired = () => {
      if (!primaryCleanupFinished) return;
      if (!lateDeletion && postCleanupDeletionRequired) {
        lateDeletion = deleteKnownPod(Date.now() + this.#config.cleanupTimeoutMs, false);
        void lateDeletion.catch(() => undefined);
      }
      if (!lateSecretDeletion && postCleanupSecretDeletionRequired) {
        lateSecretDeletion = deleteResourceByDeadline(this.#api, this.#config.namespace,
          secretName, Date.now() + this.#config.cleanupTimeoutMs, "secret");
        void lateSecretDeletion.catch(() => undefined);
      }
    };

    const result = (async (): Promise<SandboxResult> => {
      try {
        phase("creating");
        const pod = buildExecutionPod(
          this.#config,
          this.#policy,
          name,
          correlationId,
          options.deadlineMs
        );
        const tls = createGrpcTlsBootstrap();
        assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
        if (direct) {
          const creation = this.#api.createSecret(this.#config.namespace,
            buildExecutionSecret(pod, tls.runner), options.deadlineMs, localAbort.signal);
          const settled = () => {
            if (terminating) {
              postCleanupSecretDeletionRequired = true;
              startLateDeletionIfRequired();
            }
          };
          void creation.then(settled, settled);
          await raceExecutionStage(creation, options.deadlineMs, localAbort.signal);
          assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
        }
        createSettled = this.#api.createPod(
          this.#config.namespace,
          pod,
          options.deadlineMs,
          localAbort.signal
        );
        const creationSettled = () => {
          if (terminating) {
            postCleanupDeletionRequired = true;
            startLateDeletionIfRequired();
          }
        };
        void createSettled.then(creationSettled, creationSettled);
        const uid = await raceExecutionStage(createSettled, options.deadlineMs, localAbort.signal);
        assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
        phase("pending");
        let address: string;
        if (direct) {
          const endpoint = await raceExecutionStage(this.#api.waitForPodEndpoint(
            this.#config.namespace, name, uid, options.deadlineMs, localAbort.signal
          ), options.deadlineMs, localAbort.signal);
          assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
          if (endpoint.uid !== uid) throw new Error("Kubernetes pod identity changed");
          address = podGrpcAddress(endpoint.ip);
          phase("running");
          phase("connecting");
        } else {
          await this.#api.waitForPodRunning(
            this.#config.namespace,
            name,
            options.deadlineMs,
            localAbort.signal
          );
          assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
          phase("running");
          phase("connecting");
          runnerPromise = this.#api.startRunner(
            this.#config.namespace,
            name,
            tls.runner,
            options.deadlineMs,
            localAbort.signal
          ).then(handle => {
            runner = handle;
            prematureRunner = watchClosure(handle.closed,
              "Kubernetes runner exited before final gRPC status");
            if (terminating) void stopRunner(handle).catch(() => undefined);
            return handle;
          });
          runner = await raceExecutionStage(runnerPromise, options.deadlineMs, localAbort.signal);
          assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
          if (channelFailed) throw new Error("Kubernetes runner failed");
          tunnelPromise = this.#api.openTunnel(
            this.#config.namespace,
            name,
            50051,
            options.deadlineMs,
            localAbort.signal
          ).then(handle => {
            tunnel = handle;
            prematureTunnel = watchClosure(handle.closed,
              "Kubernetes port-forward closed before final gRPC status");
            if (terminating) void stopTunnel(handle).catch(() => undefined);
            return handle;
          });
          tunnel = await raceExecutionStage(Promise.race([tunnelPromise, prematureRunner!]),
            options.deadlineMs, localAbort.signal);
          assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
          if (channelFailed) throw new Error("Kubernetes execution channel failed");
          address = tunnel.address;
        }
        phase("executing");
        grpcExecution = startGrpcExecution(
          address,
          tls.credentials,
          code,
          {
            ...options,
            signal: localAbort.signal,
            memoryLimitMb: this.#config.isolateMemoryMb,
            maxResultBytes: MAX_RESULT_BYTES
          }
        );
        const grpcResult = grpcExecution.result.then(value => {
          grpcCompleted = true;
          return value;
        });
        const workerResult = direct ? await grpcResult
          : await Promise.race([grpcResult, prematureRunner!, prematureTunnel!]);
        this.#emit(correlationId, "executing", "succeeded", "none", started);
        return workerResult;
      } catch (error) {
        const timedOut = error instanceof ExecutionStageTimeoutError
          || localAbort.signal.aborted
          || Date.now() >= options.deadlineMs;
        const connected = runner !== undefined || tunnel !== undefined || grpcExecution !== undefined;
        this.#emit(
          correlationId,
          phaseForFailure(connected),
          timedOut ? "timed_out" : "failed",
          timedOut ? "deadline" : (connected ? "channel" : "api"),
          started
        );
        return timedOut ? timeoutResult() : providerFailureResult();
      }
    })();
    const deadlineTimer = setTimeout(
      () => localAbort.abort(),
      Math.max(1, options.deadlineMs - Date.now())
    );
    void result.finally(() => clearTimeout(deadlineTimer));

    const terminate = (requestedCleanupDeadlineMs?: number) => cleanup ??= (async () => {
      terminating = true;
      localAbort.abort();
      phase("closing");
      const cleanupDeadlineMs = terminationDeadlineMs = requestedCleanupDeadlineMs
        ?? Date.now() + this.#config.cleanupTimeoutMs;
      const resolvePending = async <T>(active: T | undefined, pending: Promise<T> | undefined) => {
        if (active) return active;
        if (!pending) return undefined;
        return await pending.then(value => value, () => undefined);
      };
      try {
        const outcomes = await Promise.allSettled([
          withCleanupDeadline(Promise.resolve().then(() => grpcExecution?.terminate(cleanupDeadlineMs)),
            cleanupDeadlineMs),
          withCleanupDeadline((async () => {
            const handle = await resolvePending(tunnel, tunnelPromise);
            if (handle) await stopTunnel(handle);
          })(), cleanupDeadlineMs),
          withCleanupDeadline((async () => {
            const handle = await resolvePending(runner, runnerPromise);
            if (handle) await stopRunner(handle);
          })(), cleanupDeadlineMs),
          deleteKnownPod(cleanupDeadlineMs, false),
          ...(direct ? [deleteResourceByDeadline(this.#api, this.#config.namespace,
            secretName, cleanupDeadlineMs, "secret")] : [])
        ]);
        if (outcomes.some(outcome => outcome.status === "rejected")) {
          throw new Error("Kubernetes execution cleanup failed");
        }
        this.#emit(correlationId, "deleted", "succeeded", "none", started);
      } finally {
        primaryCleanupFinished = true;
        startLateDeletionIfRequired();
        options.signal.removeEventListener("abort", abort);
      }
    })();

    return { result, terminate, terminationTimeoutMs: this.#config.cleanupTimeoutMs };
  }

  #emit(
    correlationId: string,
    phase: KubernetesPhase,
    outcome: "started" | "succeeded" | "failed" | "cancelled" | "timed_out",
    reason: KubernetesReason,
    started: number,
    reconciliation?: { successCount: number; failureCount: number }
  ): void {
    this.#diagnostics(diagnosticEvent(
      this.#config.profile,
      correlationId,
      phase,
      outcome,
      reason,
      started,
      Date.now(),
      reconciliation
    ));
  }
}

function withCleanupDeadline<T>(promise: Promise<T>, cleanupDeadlineMs: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(
      () => reject(new Error("Kubernetes execution cleanup failed")),
      Math.max(1, cleanupDeadlineMs - Date.now())
    );
    promise.then(resolve, reject).finally(() => clearTimeout(timeout));
  });
}

function raceExecutionStage<T>(
  promise: Promise<T>,
  deadlineMs: number,
  signal: AbortSignal
): Promise<T> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (callback: () => void) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      signal.removeEventListener("abort", aborted);
      callback();
    };
    const aborted = () => finish(() => reject(new ExecutionStageTimeoutError()));
    const timeout = setTimeout(aborted, Math.max(1, deadlineMs - Date.now()));
    signal.addEventListener("abort", aborted, { once: true });
    promise.then(
      value => finish(() => resolve(value)),
      error => finish(() => reject(error))
    );
    if (signal.aborted || Date.now() >= deadlineMs) aborted();
  });
}

class ExecutionStageTimeoutError extends Error {}

async function deletePodByDeadline(
  api: KubernetesApi,
  namespace: string,
  name: string,
  cleanupDeadlineMs: number
): Promise<void> {
  return deleteResourceByDeadline(api, namespace, name, cleanupDeadlineMs, "pod");
}

async function deleteResourceByDeadline(
  api: KubernetesApi, namespace: string, name: string, cleanupDeadlineMs: number,
  kind: "pod" | "secret"
): Promise<void> {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    Math.max(1, cleanupDeadlineMs - Date.now())
  );
  try {
    await withCleanupDeadline(
      kind === "pod" ? api.deletePod(namespace, name, controller.signal)
        : api.deleteSecret(namespace, name, controller.signal),
      cleanupDeadlineMs
    );
    const deleted = await withCleanupDeadline(
      kind === "pod" ? api.waitForPodDeleted(namespace, name, cleanupDeadlineMs, controller.signal)
        : api.waitForSecretDeleted(namespace, name, cleanupDeadlineMs, controller.signal),
      cleanupDeadlineMs
    );
    if (!deleted) {
      throw new Error("Kubernetes execution pod deletion was not confirmed");
    }
  } finally {
    clearTimeout(timeout);
    controller.abort();
  }
}

export function podGrpcAddress(ip: string): string {
  const family = isIP(ip);
  if (!family) throw new Error("Kubernetes pod endpoint is invalid");
  return family === 6 ? `[${ip}]:50051` : `${ip}:50051`;
}

class PreflightError extends Error {
  readonly reason: KubernetesReason;

  constructor(reason: KubernetesReason) {
    super(reason);
    this.reason = reason;
  }
}

function assertExecutionActive(deadlineMs: number, signal: AbortSignal, terminating: boolean): void {
  if (signal.aborted || terminating || Date.now() >= deadlineMs) {
    throw new Error("sandbox run deadline exceeded");
  }
}

function phaseForFailure(connected: boolean): KubernetesPhase {
  return connected ? "executing" : "pending";
}

function providerFailureResult(): SandboxResult {
  return {
    result: null,
    error: { message: "isolation provider failed" },
    stdout: "",
    stderr: "",
    exitCode: 1,
    timedOut: false
  };
}

function timeoutResult(): SandboxResult {
  return {
    result: null,
    error: { message: "sandbox run deadline exceeded" },
    stdout: "",
    stderr: "",
    exitCode: -1,
    timedOut: true
  };
}
