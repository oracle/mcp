/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { randomUUID } from "node:crypto";
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
import { startChannelExecution } from "./pipe-execution.ts";
import { reconcileExpiredPods, startExpiryReconciliation } from "./kubernetes-reconciler.ts";
import type { WorkerChannel } from "./worker-channel.ts";

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
  { resource: "pods", subresource: "exec", verb: "get", namespaced: true }
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
        const allowed = await this.#api.selfCan({
          group: permission.group,
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
        if (await this.#api.dryRunCreatePod(this.#config.namespace, variant)) {
          if (this.#config.profile !== "local-development") {
            throw new PreflightError("admission");
          }
          admissionEnforced = false;
        }
      }
      await reconcileExpiredPods(this.#api, this.#config.namespace, this.#config.profile);
      this.#descriptor = providerDescriptor(this.#config, this.#policy, admissionEnforced);
      if (options.startReconciliation !== false) {
        this.#stopReconciliation ??= startExpiryReconciliation(
          this.#api,
          this.#config.namespace,
          this.#config.profile,
          this.#config.reconcileIntervalMs,
          () => this.#emit(randomUUID(), "reconciling", "failed", "cleanup", Date.now())
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
    let channel: WorkerChannel | undefined;
    let createSettled: Promise<void> = Promise.resolve();
    let terminating = false;
    let cleanup: Promise<void> | undefined;

    const phase = (value: KubernetesPhase) => {
      this.#emit(correlationId, value, "started", "none", started);
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
        createSettled = this.#api.createPod(this.#config.namespace, pod);
        await createSettled;
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
        channel = await this.#api.openExecChannel(this.#config.namespace, name);
        assertExecutionActive(options.deadlineMs, localAbort.signal, terminating);
        phase("executing");
        const execution = startChannelExecution(channel, code, {
          ...options,
          signal: localAbort.signal,
          memoryLimitMb: this.#config.isolateMemoryMb,
          maxResultBytes: this.#config.maxResultBytes,
          terminationTimeoutMs: this.#config.cleanupTimeoutMs
        });
        const workerResult = mapKubernetesChannelResult(await execution.result as SandboxResult);
        this.#emit(correlationId, "executing", "succeeded", "none", started);
        return workerResult;
      } catch {
        const timedOut = localAbort.signal.aborted || Date.now() >= options.deadlineMs;
        this.#emit(
          correlationId,
          phaseForFailure(channel),
          timedOut ? "timed_out" : "failed",
          timedOut ? "deadline" : (channel ? "channel" : "api"),
          started
        );
        return timedOut ? timeoutResult() : providerFailureResult();
      }
    })();

    const terminate = () => cleanup ??= (async () => {
      terminating = true;
      localAbort.abort();
      phase("closing");
      await channel?.stop().catch(() => undefined);
      await createSettled.catch(() => undefined);
      phase("deleting");
      await this.#api.deletePod(this.#config.namespace, name);
      if (!await this.#api.waitForPodDeleted(
        this.#config.namespace,
        name,
        Date.now() + this.#config.cleanupTimeoutMs
      )) {
        throw new Error("Kubernetes execution pod deletion was not confirmed");
      }
      phase("deleted");
      this.#emit(correlationId, "deleted", "succeeded", "none", started);
      options.signal.removeEventListener("abort", abort);
    })();

    return { result, terminate, terminationTimeoutMs: this.#config.cleanupTimeoutMs };
  }

  #emit(
    correlationId: string,
    phase: KubernetesPhase,
    outcome: "started" | "succeeded" | "failed" | "cancelled" | "timed_out",
    reason: KubernetesReason,
    started: number
  ): void {
    this.#diagnostics(diagnosticEvent(
      this.#config.profile,
      correlationId,
      phase,
      outcome,
      reason,
      started
    ));
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

function phaseForFailure(channel: WorkerChannel | undefined): KubernetesPhase {
  return channel ? "executing" : "pending";
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

function mapKubernetesChannelResult(result: SandboxResult): SandboxResult {
  const message = result.error?.message;
  return message === "sandbox runner failed" || message?.startsWith("sandbox runner exited")
    ? providerFailureResult()
    : result;
}
