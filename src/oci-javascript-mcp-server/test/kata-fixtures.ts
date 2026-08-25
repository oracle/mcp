/*
 * Copyright (c) 2026, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at
 * https://oss.oracle.com/licenses/upl.
 */

export function validKataEnvironment(): NodeJS.ProcessEnv {
  return {
    ...validInClusterEnvironment(),
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "kata-in-cluster",
    OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_CLASS: "kata-qemu-runtime-rs",
    OCI_JAVASCRIPT_KUBERNETES_KATA_RUNTIME_HANDLER: "kata-qemu-runtime-rs"
  };
}

export function validInClusterEnvironment(): NodeJS.ProcessEnv {
  return {
    OCI_JAVASCRIPT_ISOLATION_PROVIDER: "kubernetes",
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "in-cluster",
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: "oci-js-execution",
    OCI_JAVASCRIPT_KUBERNETES_IMAGE: `registry.example/runner@sha256:${"a".repeat(64)}`,
    OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT: "oci-js-runner",
    OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_NAMESPACE: "oci-js-host",
    OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_NAME: "oci-js-host-0",
    OCI_JAVASCRIPT_KUBERNETES_TRUSTED_HOST_POD_UID: "12345678-1234-1234-1234-123456789abc"
  };
}

export function validLocalEnvironment(): NodeJS.ProcessEnv {
  return {
    OCI_JAVASCRIPT_ISOLATION_PROVIDER: "kubernetes",
    OCI_JAVASCRIPT_KUBERNETES_PROFILE: "local-development",
    OCI_JAVASCRIPT_KUBERNETES_NAMESPACE: "oci-js-local",
    OCI_JAVASCRIPT_KUBERNETES_IMAGE: "oci-javascript-mcp-runner:dev",
    OCI_JAVASCRIPT_KUBERNETES_ALLOW_LOCAL_IMAGE: "true",
    OCI_JAVASCRIPT_KUBERNETES_RUNNER_SERVICE_ACCOUNT: "oci-js-runner",
    OCI_JAVASCRIPT_KUBERNETES_KUBECONFIG: "/tmp/oci-javascript-test-kubeconfig",
    OCI_JAVASCRIPT_KUBERNETES_CONTEXT: "oci-js-local"
  };
}
