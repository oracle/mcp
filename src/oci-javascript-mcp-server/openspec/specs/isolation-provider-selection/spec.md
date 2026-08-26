# Isolation Provider Selection Specification

## Purpose

Defines trusted, explicit provider and Kubernetes-profile selection so untrusted executions cannot trigger an unintended credential source, container runtime, or weaker isolation posture.

## Requirements

### Requirement: Trusted provider and profile selection
The server SHALL select exactly one isolation provider at startup from trusted operator configuration. Supported providers SHALL be `podman` and `kubernetes`, with `podman` retained as the compatibility default when no provider is configured. Kubernetes selection SHALL require exactly one profile from `local-development`, `in-cluster`, or `kata-in-cluster`. Guest code and MCP input MUST NOT select or alter the provider, profile, connection mode, runtime policy, or image policy.

#### Scenario: Local Kubernetes development selection
- **WHEN** the operator selects `kubernetes` with the `local-development` profile and valid explicit kubeconfig configuration
- **THEN** every subsequent `run_javascript` execution SHALL use the shared Kubernetes engine with the standard runtime policy
- **AND** the server SHALL identify the profile as development-only container isolation

#### Scenario: Standard in-cluster selection
- **WHEN** the operator selects `kubernetes` with the `in-cluster` profile and valid in-cluster configuration
- **THEN** every subsequent execution SHALL use the trusted host service account and the cluster's standard runtime
- **AND** the server SHALL identify the profile as container-grade rather than VM-grade isolation

#### Scenario: Kata in-cluster selection
- **WHEN** the operator selects `kubernetes` with the `kata-in-cluster` profile and valid Kata configuration
- **THEN** every subsequent execution SHALL use the configured and preflighted Kata RuntimeClass
- **AND** the server SHALL NOT substitute the standard runtime or Podman

#### Scenario: Compatibility default
- **WHEN** no isolation provider is configured
- **THEN** the server SHALL select the existing Podman provider
- **AND** existing Podman configuration behavior SHALL remain compatible

### Requirement: Exact profile configuration
The server SHALL validate the selected provider, profile, credential source, image policy, and security-relevant configuration before accepting MCP requests. It MUST reject unknown providers or profiles, profile-incompatible values, implicit credential discovery, missing required values, unsafe identifiers, and out-of-range resource or cleanup limits.

#### Scenario: Kubernetes provider without profile
- **WHEN** the operator selects `kubernetes` without an exact supported profile
- **THEN** startup SHALL fail before connecting MCP stdio
- **AND** no execution pod SHALL be created

#### Scenario: Local profile without explicit kubeconfig
- **WHEN** `local-development` is selected without an explicit kubeconfig path and context
- **THEN** startup SHALL fail without trying in-cluster credentials or a default user kubeconfig
- **AND** the server SHALL NOT fall back to Podman

#### Scenario: In-cluster profile with external credentials
- **WHEN** either in-cluster profile is selected with kubeconfig or other external Kubernetes credentials
- **THEN** startup SHALL reject the incompatible credential source
- **AND** only service-account-backed in-cluster authentication SHALL be permitted

#### Scenario: Invalid in-cluster topology
- **WHEN** an in-cluster profile has missing downward-API host identity, equal trusted-host and execution namespaces, unavailable required RBAC, or a mutable runner image
- **THEN** startup SHALL fail closed before accepting MCP requests
- **AND** no execution pod SHALL be created

#### Scenario: Invalid Kata configuration
- **WHEN** `kata-in-cluster` has a missing or mismatched RuntimeClass name or handler
- **THEN** startup SHALL fail before any execution pod is created
- **AND** the standard in-cluster policy SHALL NOT be substituted

### Requirement: Explicit assurance posture
The trusted provider descriptor and operator diagnostics SHALL identify the active provider and profile, credential mode, runtime policy, image policy, namespace topology, completed preflights, and unverified external controls without disclosing credentials, endpoints, raw Kubernetes errors, guest data, or resource details. A standard-runtime profile MUST NOT claim a per-execution VM boundary, and a Kata profile MUST NOT claim production approval solely from RuntimeClass lookup or pod creation.

#### Scenario: Standard profile descriptor
- **WHEN** either standard-runtime profile starts successfully
- **THEN** its descriptor SHALL report container isolation and the nested `isolated-vm` boundary
- **AND** it SHALL explicitly report that a Kata guest-kernel boundary was not requested or verified

#### Scenario: Kata profile descriptor
- **WHEN** `kata-in-cluster` starts successfully after RuntimeClass and admission preflight
- **THEN** its descriptor SHALL record the selected RuntimeClass and handler
- **AND** it SHALL retain explicit unverified flags for real-node, guest-kernel, CRI, CNI, PID, overhead, and provenance evidence

### Requirement: Provider choice preserves host controls
Provider and profile selection SHALL NOT change the `run_javascript` contract, OCI facade, host credential ownership, supported client options, SDK request validation, execution deadline, OCI call and concurrency budgets, frame limits, result limits, or public-error sanitization.

#### Scenario: Equivalent successful result
- **WHEN** the same supported script completes successfully through Podman or any Kubernetes profile
- **THEN** the tool result SHALL contain compatible `result`, `error`, `stdout`, `stderr`, `exit_code`, and `timed_out` fields
- **AND** profile-specific control-plane details SHALL NOT appear in those fields

#### Scenario: Unsupported client authority
- **WHEN** guest code supplies an endpoint, credential provider, signer, retry configuration, or unsupported client option through any profile
- **THEN** the trusted host SHALL reject it before invoking the OCI SDK
- **AND** changing profiles SHALL NOT broaden guest authority

### Requirement: No automatic provider, profile, or credential fallback
The server SHALL treat startup, execution, protocol, scheduling, runtime, or cleanup failure as failure of the selected configuration. It MUST NOT retry guest code through a different provider, Kubernetes profile, credential source, or runtime.

#### Scenario: Selected profile fails
- **WHEN** an execution cannot be scheduled, started, connected, completed, or deleted through the selected profile
- **THEN** it SHALL fail or time out using the normal structured result contract
- **AND** the code SHALL NOT run through Podman, another Kubernetes profile, or another credential source
