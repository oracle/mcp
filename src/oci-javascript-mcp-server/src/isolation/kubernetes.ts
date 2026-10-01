/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { randomUUID } from "node:crypto";
import { createGrpcTlsBootstrap } from "../grpc-tls-host.ts";
import { MAX_RESULT_BYTES } from "../sandbox-common.ts";
import type { IsolationExecution, IsolationProvider, SandboxResult } from "../types.ts";
import type { KubernetesApi, ResourceAttributes } from "./kubernetes-api.ts";
import type { KubernetesConfig } from "./kubernetes-config.ts";
import {
  diagnosticEvent,
  providerDescriptor,
  stderrKubernetesDiagnosticSink,
  type KubernetesDiagnosticSink,
  type KubernetesPhase,
  type KubernetesProviderDescriptor,
  type KubernetesReason
} from "./kubernetes-diagnostics.ts";
import {
  buildExecutionPod,
  runtimeAdmissionVariants,
  unsafeAdmissionVariants
} from "./kubernetes-pod.ts";
import {
  runtimePolicyFor,
  type KubernetesRuntimePolicy
} from "./kubernetes-runtime-policy.ts";
import { startGrpcExecution } from "./grpc-execution.ts";
import { reconcileExpiredPods, startExpiryReconciliation } from "./kubernetes-reconciler.ts";
import type {
  KubernetesGrpcTunnel,
  KubernetesRunnerHandle
} from "./kubernetes-grpc.ts";

const POD_NAME_PREFIX = "oci-javascript-k8s-";
const SHARED_ACCESS: ReadonlyArray<Omit<ResourceAttributes, "namespace"> & {
  namespaced: boolean;
}> = [
  { resource: "namespaces", verb: "get", namespaced: false },
  { resource: "pods", verb: "create", namespaced: true },
  { resource: "pods", verb: "get", namespaced: true },
  { resource: "pods", verb: "list", namespaced: true },
  { resource: "pods", verb: "watch", namespaced: true },
  { resource: "pods", verb: "delete", namespaced: true },
  { resource: "pods", subresource: "exec", verb: "create", namespaced: true },
  { resource: "pods", subresource: "exec", verb: "get", namespaced: true },
  { resource: "pods", subresource: "portforward", verb: "create", namespaced: true },
  { resource: "pods", subresource: "portforward", verb: "get", namespaced: true }
];
const RUNTIME_CLASS_ACCESS = {
  group: "node.k8s.io",
  resource: "runtimeclasses",
  verb: "get",
  namespaced: false
} as const;

export class KubernetesIsolationProvider implements IsolationProvider {
  readonly #config: KubernetesConfig;
  readonly #policy: KubernetesRuntimePolicy;
  readonly #api: KubernetesApi;
  readonly #diagnostics: KubernetesDiagnosticSink;
  #stopReconciliation: (() => void) | undefined;
  #descriptor: KubernetesProviderDescriptor | undefined;

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

  get descriptor(): KubernetesProviderDescriptor | undefined {
    return this.#descriptor;
  }

  async preflight(options: { startReconciliation?: boolean } = {}): Promise<void> {
    const started = Date.now();
    const correlationId = randomUUID();
    this.#emit(correlationId, "preflight", "started", "none", started);
    try {
      await this.#api.readNamespace(this.#config.namespace);
      if (this.#policy.kind === "kata") {
        const runtimeClass = await this.#api.readRuntimeClass(this.#policy.runtimeClassName);
        if (runtimeClass.handler !== this.#policy.runtimeHandler) {
          throw new PreflightError("runtime_class");
        }
      }
      const permissions = this.#policy.kind === "kata"
        ? [...SHARED_ACCESS, RUNTIME_CLASS_ACCESS]
        : SHARED_ACCESS;
      for (const permission of permissions) {
        const name = permission.resource === "namespaces"
          ? this.#config.namespace
          : permission.resource === "runtimeclasses" && this.#policy.kind === "kata"
            ? this.#policy.runtimeClassName
            : undefined;
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
      const probe = buildExecutionPod(
        this.#config,
        this.#policy,
        `${POD_NAME_PREFIX}preflight`,
        correlationId,
        Date.now() + 30_000
      );
      if (!await this.#api.dryRunCreatePod(this.#config.namespace, probe)) {
        throw new PreflightError("admission");
      }
      let admissionEnforced = true;
      const unsafe = [
        ...unsafeAdmissionVariants(probe),
        ...runtimeAdmissionVariants(probe, this.#policy)
      ];
      for (const variant of unsafe) {
        if (await this.#api.dryRunCreatePod(this.#config.namespace, variant.pod)) {
          if (this.#config.profile !== "local-development") {
            throw new PreflightError("admission");
          }
          admissionEnforced = false;
        }
      }
      const reconciliation = await reconcileExpiredPods(
        this.#api,
        this.#config.namespace,
        this.#config.profile
      );
      if (reconciliation.failureCount > 0) {
        throw new PreflightError("cleanup");
      }
      this.#descriptor = providerDescriptor(this.#config, this.#policy, admissionEnforced);
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
                    successCount: summary.deletedNames.length,
                    failureCount: summary.failureCount
                  }
                : { successCount: 0, failureCount: 1 }
            );
          }
        );
      }
      this.#emit(correlationId, "preflight", "succeeded", "none", started);
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
    if (!this.#descriptor) {
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
    let createSettled: Promise<void> | undefined;
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
      if (lateDeletion || !postCleanupDeletionRequired || !primaryCleanupFinished) return;
      lateDeletion = deleteKnownPod(Date.now() + this.#config.cleanupTimeoutMs, false);
      void lateDeletion.catch(() => undefined);
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
        await raceExecutionStage(createSettled, options.deadlineMs, localAbort.signal);
        assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
        phase("pending");
        await this.#api.waitForPodRunning(
          this.#config.namespace,
          name,
          options.deadlineMs,
          localAbort.signal
        );
        assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
        phase("running");
        phase("connecting");
        const tls = createGrpcTlsBootstrap();
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
        phase("executing");
        grpcExecution = startGrpcExecution(
          tunnel.address,
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
        const workerResult = await Promise.race([grpcResult, prematureRunner!, prematureTunnel!]);
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
          deleteKnownPod(cleanupDeadlineMs, true)
        ]);
        if (outcomes.some(outcome => outcome.status === "rejected")) {
          throw new Error("Kubernetes execution cleanup failed");
        }
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
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    Math.max(1, cleanupDeadlineMs - Date.now())
  );
  try {
    await withCleanupDeadline(
      api.deletePod(namespace, name, controller.signal),
      cleanupDeadlineMs
    );
    const deleted = await withCleanupDeadline(
      api.waitForPodDeleted(namespace, name, cleanupDeadlineMs, controller.signal),
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
