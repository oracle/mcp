#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import {
  createInClusterKubernetesApi,
  type KubernetesApi
} from "./isolation/kubernetes-api.ts";
import {
  parseKubernetesReconcilerConfig,
  type KubernetesReconcilerConfig
} from "./isolation/kubernetes-config.ts";
import {
  diagnosticEvent,
  stderrKubernetesDiagnosticSink,
  type KubernetesDiagnosticSink
} from "./isolation/kubernetes-diagnostics.ts";
import { reconcileExpiredPods } from "./isolation/kubernetes-reconciler.ts";

export async function runCleanupReconciler(
  api: KubernetesApi,
  config: KubernetesReconcilerConfig,
  signal: AbortSignal,
  diagnostics: KubernetesDiagnosticSink = stderrKubernetesDiagnosticSink
): Promise<void> {
  while (!signal.aborted) {
    const started = Date.now();
    const correlationId = randomUUID();
    try {
      const summary = await reconcileExpiredPods(api, config.namespace, config.profile);
      const failed = summary.failureCount > 0;
      diagnostics(diagnosticEvent(
        config.profile,
        correlationId,
        "reconciling",
        failed ? "failed" : "succeeded",
        failed ? "cleanup" : "none",
        started,
        Date.now(),
        {
          successCount: summary.deletedNames.length,
          failureCount: summary.failureCount
        }
      ));
    } catch {
      diagnostics(diagnosticEvent(
        config.profile,
        correlationId,
        "reconciling",
        "failed",
        "cleanup",
        started,
        Date.now(),
        { successCount: 0, failureCount: 1 }
      ));
    }
    await waitForNextRun(config.reconcileIntervalMs, signal);
  }
}

export async function main(
  environment: NodeJS.ProcessEnv = process.env,
  options: {
    api?: KubernetesApi;
    signal?: AbortSignal;
    diagnostics?: KubernetesDiagnosticSink;
  } = {}
): Promise<void> {
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (!options.signal) {
    process.once("SIGINT", abort);
    process.once("SIGTERM", abort);
  }
  try {
    await runCleanupReconciler(
      options.api ?? createInClusterKubernetesApi(),
      parseKubernetesReconcilerConfig(environment),
      options.signal ?? controller.signal,
      options.diagnostics
    );
  } finally {
    process.removeListener("SIGINT", abort);
    process.removeListener("SIGTERM", abort);
  }
}

function waitForNextRun(milliseconds: number, signal: AbortSignal): Promise<void> {
  if (signal.aborted) {
    return Promise.resolve();
  }
  return new Promise(resolve => {
    const done = () => {
      clearTimeout(timer);
      signal.removeEventListener("abort", done);
      resolve();
    };
    const timer = setTimeout(done, milliseconds);
    signal.addEventListener("abort", done, { once: true });
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  await main();
}
