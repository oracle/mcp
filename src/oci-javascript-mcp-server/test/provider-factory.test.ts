/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import assert from "node:assert/strict";
import { registerHooks } from "node:module";
import test from "node:test";

test("provider factory loads only the selected provider's dependencies", async t => {
  let selected: "podman" | "kubernetes" | undefined;
  const hooks = registerHooks({
    resolve(specifier, context, nextResolve) {
      const resolved = nextResolve(specifier, context);
      if ((selected !== "kubernetes" && (specifier === "@kubernetes/client-node"
        || /\/kubernetes(?:-api)?\.ts$/.test(resolved.url)))
        || (selected !== "podman" && /\/podman\.ts$/.test(resolved.url))) {
        throw new Error(`Must not load an unselected provider dependency: ${specifier}`);
      }
      return resolved;
    }
  });
  t.after(() => hooks.deregister());

  const { createIsolationProvider } = await import("../src/isolation/provider-factory.ts");
  selected = "podman";
  for (const environment of [{}, { OCI_JAVASCRIPT_ISOLATION_PROVIDER: "podman" }]) {
    const provider = await createIsolationProvider(environment);
    const { PodmanIsolationProvider } = await import("../src/isolation/podman.ts");
    assert.ok(provider instanceof PodmanIsolationProvider);
  }

  selected = "kubernetes";
  const { validKataEnvironment } = await import("./kata-fixtures.ts");
  const { StartupKubernetesApi } = await import("./kubernetes-startup-fixture.ts");
  const provider = await createIsolationProvider(validKataEnvironment(), {
    kubernetesApi: new StartupKubernetesApi(),
    kubernetesDiagnostics: () => undefined,
    startReconciliation: false
  });
  const { KubernetesIsolationProvider } = await import("../src/isolation/kubernetes.ts");
  assert.ok(provider instanceof KubernetesIsolationProvider);
});
