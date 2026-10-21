#!/usr/bin/env -S node --no-node-snapshot --experimental-strip-types
/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";

const groups = [
  ["apps", "v1"],
  ["rbac.authorization.k8s.io", "v1"],
  ["networking.k8s.io", "v1"],
  ["node.k8s.io", "v1"],
  ["admissionregistration.k8s.io", "v1"]
] as const;

const resources: Record<string, Array<{ name: string; kind: string; namespaced: boolean }>> = {
  v1: [
    { name: "namespaces", kind: "Namespace", namespaced: false },
    { name: "serviceaccounts", kind: "ServiceAccount", namespaced: true },
    { name: "resourcequotas", kind: "ResourceQuota", namespaced: true },
    { name: "limitranges", kind: "LimitRange", namespaced: true }
  ],
  "apps/v1": [{ name: "deployments", kind: "Deployment", namespaced: true }],
  "rbac.authorization.k8s.io/v1": [
    { name: "roles", kind: "Role", namespaced: true },
    { name: "rolebindings", kind: "RoleBinding", namespaced: true },
    { name: "clusterroles", kind: "ClusterRole", namespaced: false },
    { name: "clusterrolebindings", kind: "ClusterRoleBinding", namespaced: false }
  ],
  "networking.k8s.io/v1": [{ name: "networkpolicies", kind: "NetworkPolicy", namespaced: true }],
  "node.k8s.io/v1": [{ name: "runtimeclasses", kind: "RuntimeClass", namespaced: false }],
  "admissionregistration.k8s.io/v1": [
    { name: "validatingadmissionpolicies", kind: "ValidatingAdmissionPolicy", namespaced: false },
    {
      name: "validatingadmissionpolicybindings",
      kind: "ValidatingAdmissionPolicyBinding",
      namespaced: false
    }
  ]
};

const server = createServer((request, response) => {
  const path = request.url?.split("?", 1)[0] ?? "/";
  if (path === "/api") {
    return json(response, 200, { apiVersion: "v1", kind: "APIVersions", versions: ["v1"] });
  }
  if (path === "/apis") {
    return json(response, 200, {
      apiVersion: "v1",
      kind: "APIGroupList",
      groups: groups.map(([name, version]) => ({
        name,
        versions: [{ groupVersion: `${name}/${version}`, version }],
        preferredVersion: { groupVersion: `${name}/${version}`, version }
      }))
    });
  }
  const groupVersion = discoveryGroupVersion(path);
  if (groupVersion && resources[groupVersion]) {
    return json(response, 200, {
      apiVersion: "v1",
      kind: "APIResourceList",
      groupVersion,
      resources: resources[groupVersion].map(resource => ({
        ...resource,
        singularName: "",
        verbs: ["create", "get", "list", "patch", "update"]
      }))
    });
  }
  return json(response, 404, {
    apiVersion: "v1",
    kind: "Status",
    status: "Failure",
    reason: "NotFound",
    code: 404
  });
});

await new Promise<void>(resolve => server.listen(0, "127.0.0.1", resolve));
const address = server.address();
if (!address || typeof address === "string") {
  throw new Error("failed to start offline Kubernetes discovery fixture");
}
const tempDirectory = await mkdtemp(join(tmpdir(), "oci-js-kubectl-"));
const kubeconfig = join(tempDirectory, "config");
await writeFile(kubeconfig, `apiVersion: v1
kind: Config
clusters:
  - name: offline
    cluster:
      server: http://127.0.0.1:${address.port}
contexts:
  - name: offline
    context:
      cluster: offline
      user: offline
current-context: offline
users:
  - name: offline
    user: {}
`, { mode: 0o600 });

try {
  await runKubectl(kubeconfig, "examples/kubernetes/v1/standard-in-cluster.yaml");
  await runKubectl(kubeconfig, "examples/kata-kubernetes/v1/");
} finally {
  await new Promise<void>(resolve => server.close(() => resolve()));
  await rm(tempDirectory, { recursive: true, force: true });
}

function discoveryGroupVersion(path: string): string | undefined {
  if (path === "/api/v1") {
    return "v1";
  }
  const match = /^\/apis\/([^/]+)\/([^/]+)$/.exec(path);
  return match ? `${match[1]}/${match[2]}` : undefined;
}

function json(
  response: import("node:http").ServerResponse,
  status: number,
  value: unknown
): void {
  response.writeHead(status, { "content-type": "application/json" });
  response.end(JSON.stringify(value));
}

function runKubectl(kubeconfig: string, directory: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn("kubectl", [
      "apply",
      "--dry-run=client",
      "--validate=false",
      "--kubeconfig",
      kubeconfig,
      "-f",
      directory
    ], { stdio: "inherit" });
    child.once("error", reject);
    child.once("close", code => code === 0
      ? resolve()
      : reject(new Error(`kubectl client dry-run exited with status ${String(code)}`)));
  });
}
