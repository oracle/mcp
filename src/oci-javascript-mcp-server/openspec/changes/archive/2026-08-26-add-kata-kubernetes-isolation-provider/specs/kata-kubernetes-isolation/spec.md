## Purpose

Defines hardened per-execution Kubernetes pod isolation shared by local, standard in-cluster, and Kata in-cluster profiles, while keeping their credential sources and assurance claims explicit.

## ADDED Requirements

### Requirement: Fresh Kubernetes boundary per execution
Every Kubernetes-backed `run_javascript` call SHALL create a uniquely named pod, worker process, framed channel, temporary filesystem, deadline, resource budget, and cleanup lifecycle. Pods and mutable runner state MUST NOT be reused across executions.

#### Scenario: Successful fresh execution
- **WHEN** a Kubernetes-backed tool call begins
- **THEN** the provider SHALL create one new execution pod using the selected profile's reviewed pod shape and image policy
- **AND** the pod SHALL be distinct from every earlier or concurrent execution

#### Scenario: Concurrent executions
- **WHEN** multiple Kubernetes-backed calls execute concurrently
- **THEN** each call SHALL have an independent pod, channel, state, cancellation path, and cleanup lifecycle
- **AND** no runner SHALL access another execution's channel or mutable state

### Requirement: Monotonic runtime profiles
All Kubernetes profiles SHALL use one hardened base pod contract. A runtime profile MAY add a RuntimeClass, stricter admission checks, scheduling constraints, or assurance evidence, but MUST NOT weaken or override the base credential, namespace, host-access, security-context, resource, protocol, deadline, or cleanup controls.

#### Scenario: Standard runtime policy
- **WHEN** `local-development` or `in-cluster` builds an execution pod
- **THEN** it SHALL use the cluster's standard runtime without claiming Kata or VM-backed execution
- **AND** it SHALL retain every shared hardened pod control

#### Scenario: Kata runtime policy
- **WHEN** `kata-in-cluster` builds an execution pod
- **THEN** it SHALL add the exact configured and preflighted RuntimeClass and reviewed Kata scheduling constraints
- **AND** it SHALL NOT alter or remove any shared hardened pod control

### Requirement: Profile-specific Kubernetes credentials and topology
`local-development` SHALL use only an explicitly configured kubeconfig path and context from the trusted workstation. `in-cluster` and `kata-in-cluster` SHALL use only the trusted host pod's service account and SHALL require trusted-host and execution namespaces to differ. No Kubernetes or OCI credential SHALL enter an execution pod.

#### Scenario: Local workstation host
- **WHEN** `local-development` starts on a workstation
- **THEN** it SHALL use only the configured kubeconfig file and context to manage pods in the configured execution namespace
- **AND** it SHALL not require or fabricate a downward-API pod identity

#### Scenario: Separate in-cluster namespaces
- **WHEN** either in-cluster profile starts
- **THEN** the trusted host's cross-namespace grants SHALL authorize only required execution-namespace operations
- **AND** those grants SHALL NOT authorize pod or `pods/exec` access in the trusted-host namespace

#### Scenario: Runner inspects credentials
- **WHEN** a compromised runner inspects its environment and filesystem
- **THEN** it SHALL find no kubeconfig, service-account token, OCI configuration, OCI credential, signer, or trusted-host secret
- **AND** Kubernetes and OCI authority SHALL remain in the trusted host

### Requirement: Profile-specific image policy
Both in-cluster profiles SHALL require a lowercase SHA-256 digest-pinned runner image. `local-development` MAY use either a digest-pinned image or an explicitly configured locally loaded tag only when pull policy is fixed to `Never`. A mutable local tag MUST remain a development-only posture and MUST NOT be accepted by either in-cluster profile.

#### Scenario: Local loaded image
- **WHEN** `local-development` explicitly selects a locally loaded tagged runner image
- **THEN** the pod SHALL use `imagePullPolicy: Never`
- **AND** the descriptor SHALL report unverified image provenance and development-only status

#### Scenario: Mutable in-cluster image
- **WHEN** either in-cluster profile is configured with a tag-only runner image
- **THEN** startup SHALL fail before accepting MCP requests
- **AND** no execution pod SHALL be created

### Requirement: Hardened credential-free execution pod
Every execution pod SHALL run as a fixed non-root identity with privilege escalation disabled, all Linux capabilities dropped, a read-only root filesystem, bounded CPU, memory and temporary storage, and runtime-default seccomp. It SHALL disable service-account token mounting and service-link injection and SHALL use no host network, host PID, host IPC, host path, privileged device, runtime socket, persistent volume, unreviewed sidecar, arbitrary command, or arbitrary environment entry.

#### Scenario: Runner attempts host access
- **WHEN** a compromised runner attempts root, capabilities, host namespaces, host mounts, runtime sockets, privileged devices, or unexpected writable storage
- **THEN** the pod and runtime controls SHALL deny or omit that authority
- **AND** the attempt SHALL NOT broaden the framed OCI broker authority

#### Scenario: Temporary storage
- **WHEN** a runner writes temporary data
- **THEN** the only writable filesystem SHALL be an execution-scoped, size-limited memory-backed temporary volume
- **AND** deletion of the pod SHALL remove that state

### Requirement: Profile-aware startup preflight
Every profile SHALL verify access to its execution namespace and the pod lifecycle and exec operations it requires. Both in-cluster profiles SHALL additionally require separate-namespace identity, cross-namespace self-access checks, acceptance of the conforming pod shape, and rejection of shared unsafe variants. `kata-in-cluster` SHALL additionally verify the exact RuntimeClass handler and rejection of a wrong-RuntimeClass variant. Local development SHALL report admission enforcement as unverified when a local cluster does not provide the reviewed production admission policy rather than claiming equivalent enforcement.

#### Scenario: Standard in-cluster admission
- **WHEN** `in-cluster` preflights admission
- **THEN** the conforming standard-runtime pod SHALL be accepted and unsafe shared variants SHALL be rejected
- **AND** startup SHALL fail if the effective admission path permits a weakened base pod

#### Scenario: Kata admission
- **WHEN** `kata-in-cluster` preflights admission
- **THEN** the conforming Kata pod SHALL be accepted and shared plus wrong-RuntimeClass variants SHALL be rejected
- **AND** a missing or mismatched RuntimeClass handler SHALL fail startup

#### Scenario: Local cluster lacks production admission
- **WHEN** `local-development` can perform the required pod lifecycle but cannot prove the production admission policy
- **THEN** the profile MAY run for development with that gap recorded in its descriptor
- **AND** it SHALL remain ineligible for in-cluster or production assurance claims

### Requirement: Restricted network posture
Execution pods SHALL have no application Service or guest-reachable broker listener. In-cluster deployments SHALL use a dedicated execution namespace with reviewed default-deny ingress and egress controls. A profile MUST NOT claim effective network isolation solely from a NetworkPolicy object, and local development SHALL treat local-cluster CNI enforcement as unverified unless separately proven.

#### Scenario: Direct network attempt
- **WHEN** a compromised runner attempts direct network access
- **THEN** an admitted deployment's reviewed controls SHALL block prohibited cluster, metadata, node, private, link-local, DNS, and public destinations
- **AND** OCI access SHALL remain available only through the framed host channel

#### Scenario: Network enforcement unverified
- **WHEN** effective CNI and node controls have not been demonstrated
- **THEN** the descriptor and documentation SHALL identify the missing evidence
- **AND** the profile SHALL NOT be represented as production network isolation

### Requirement: Execution-scoped hostile framed channel
The trusted host SHALL communicate with each Kubernetes runner through one execution-scoped, non-TTY, bidirectional standard-stream channel. The channel SHALL retain the existing four-byte length prefix, protocol version, exact message schemas, sequencing, strict UTF-8 and JSON validation, dangerous-key rejection, and recursive decode limits. It SHALL expose no guest-reachable listener or bearer broker credential.

#### Scenario: Normal worker exchange
- **WHEN** the runner reports readiness
- **THEN** the host SHALL send exactly one bounded execute message containing code, remaining deadline, reflection metadata, isolate memory limit, and result limit
- **AND** logs, OCI RPC, RPC results, cancellation, and final results SHALL retain the existing contract

#### Scenario: Malformed, invalid UTF-8, or truncated frame
- **WHEN** the runner sends malformed JSON, invalid UTF-8, or closes with an incomplete frame
- **THEN** the host SHALL reject the exchange without exposing raw control-plane details
- **AND** the execution pod SHALL be deleted

#### Scenario: Unknown version, message, or field
- **WHEN** the runner sends an unknown protocol version, unsupported message type, missing required field, or unknown field
- **THEN** the host SHALL reject it without invoking the OCI SDK
- **AND** the execution pod SHALL be deleted

#### Scenario: Oversized or structurally unsafe frame
- **WHEN** the runner sends an oversized frame, excessive structure, non-finite number, or dangerous key such as `__proto__`, `prototype`, or `constructor`
- **THEN** the host SHALL reject it within configured limits
- **AND** the execution pod SHALL be deleted

#### Scenario: Raw channel use after compromise
- **WHEN** a compromised runner bypasses the facade and writes frames directly
- **THEN** the host SHALL independently validate message sequence, OCI operation and request shape, deadline, call and concurrency budgets, response size, and public errors
- **AND** channel possession SHALL NOT grant OCI or Kubernetes authorization

### Requirement: End-to-end deadline and deterministic cleanup
The existing execution deadline SHALL include pod creation, scheduling, image availability, exec connection, worker execution, RPC, and result delivery. Abort and timeout SHALL remain authoritative in every phase. Termination SHALL close the channel, request zero-grace deletion, and confirm the pod is absent within a host-clamped cleanup budget; cleanup failure SHALL override an otherwise valid or timed-out result.

#### Scenario: Timeout before worker connection
- **WHEN** scheduling or connection consumes the remaining deadline
- **THEN** the result SHALL set `result` to null, `error` to `sandbox run deadline exceeded`, `stdout` and `stderr` to bounded accumulated values, `exit_code` to -1, and `timed_out` to true
- **AND** cleanup SHALL still delete and confirm the pod

#### Scenario: Successful execution cleanup
- **WHEN** the worker returns a valid result
- **THEN** the caller SHALL receive success only after termination confirms pod deletion
- **AND** unconfirmed deletion SHALL instead return `isolation provider cleanup failed`

#### Scenario: Cancellation race
- **WHEN** cancellation races with create, watch, exec, result, or deletion
- **THEN** late completions SHALL NOT resume execution or replace the authoritative outcome
- **AND** termination SHALL remain idempotent

### Requirement: Profile-aware orphan reconciliation
The trusted host SHALL reconcile expired managed pods for every Kubernetes profile while it is running. Both in-cluster profiles SHALL support an independently deployed cleanup-only reconciler with get, list, watch, and delete authority but no create or `pods/exec` authority. Reconciliation SHALL delete only expired pods matching trusted managed labels and profile metadata and SHALL preserve unrelated, malformed, and non-expired pods.

#### Scenario: Expired local development pod
- **WHEN** the local host starts or reaches its reconciliation interval and finds an expired pod it manages
- **THEN** it SHALL delete and confirm that pod
- **AND** it SHALL preserve unrelated or non-expired pods

#### Scenario: All in-cluster hosts unavailable
- **WHEN** all trusted host replicas are down and an in-cluster managed pod expires
- **THEN** the independent reconciler SHALL delete and confirm the expired pod
- **AND** it SHALL not gain create or exec authority

### Requirement: Runtime-specific assurance boundaries
Standard-runtime profiles SHALL be described only as container isolation plus the nested `isolated-vm` boundary. Kata RuntimeClass selection SHALL be CRI-neutral and SHALL not itself prove a VM boundary. Production admission of `kata-in-cluster` SHALL require real-node evidence for the RuntimeClass-to-CRI-to-Kata mapping, guest kernel, node runtime, hypervisor, scheduling, CNI, PID limits, overhead, image provenance, deletion, reconciliation, and concurrent isolation.

#### Scenario: Standard in-cluster deployment
- **WHEN** `in-cluster` runs successfully with the default runtime
- **THEN** it SHALL provide the shared Kubernetes lifecycle and pod hardening
- **AND** it SHALL not claim a per-execution guest kernel or Kata protection

#### Scenario: Kata RuntimeClass object exists
- **WHEN** `kata-in-cluster` reads a matching RuntimeClass but real-node evidence is absent
- **THEN** the implementation SHALL remain a functionally tested POC rather than production-approved
- **AND** no provider self-description SHALL be accepted as proof of the VM boundary

#### Scenario: Approved Kata deployment
- **WHEN** a real deployment demonstrates the complete reviewed runtime, guest-kernel, network, resource, cleanup, and operational evidence
- **THEN** the exact recorded profile MAY proceed to a separate production security decision
- **AND** changes to that evidence SHALL require revalidation
