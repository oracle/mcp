## Purpose

Ensure timed-out sandbox executions return predictably while preserving trusted cleanup, OCI credential isolation, and hostile-protocol controls.

## ADDED Requirements

### Requirement: Execution result delivery has a bounded lifecycle
The trusted host SHALL apply one absolute execution deadline to provider startup, runner execution, host OCI RPC acceptance, and result delivery. After that deadline, it SHALL allow no more than one provider-specific, host-clamped cleanup tail before returning the structured MCP tool result. Provider cleanup and outstanding host-RPC draining MUST consume that one tail concurrently rather than serially.

#### Scenario: OCI request does not settle after cancellation
- **WHEN** an execution reaches its deadline while a host OCI RPC remains unresolved after its abort signal fires
- **THEN** the server SHALL return no later than the execution deadline plus its configured cleanup tail with `result` set to `null`, `error.message` set to `sandbox run deadline exceeded`, bounded `stdout` and `stderr`, `exit_code` set to `-1`, and `timed_out` set to `true`

#### Scenario: Provider cleanup consumes most of the tail
- **WHEN** a provider needs nearly its full host-clamped cleanup tail to close its channel and destroy its execution resource while an OCI RPC also remains unresolved
- **THEN** the server SHALL not add a second RPC-drain wait after provider cleanup completes

### Requirement: Cancellation remains authoritative for host OCI work
After an execution completes, is cancelled, or reaches its deadline, the trusted host SHALL reject further OCI bridge work for that execution, abort in-flight OCI requests, and prevent automatic OCI-SDK retries or the SDK default circuit breaker from extending or re-driving cancelled work. Late completion of a cancelled RPC MUST NOT alter the returned tool result or restore guest authority.

#### Scenario: Abort reaches an active OCI request
- **WHEN** the execution deadline expires during a supported OCI SDK operation
- **THEN** the host SHALL signal cancellation to that operation, SHALL not issue an automatic retry after cancellation, and SHALL disable the SDK default circuit breaker for that client

#### Scenario: Late RPC completion
- **WHEN** an OCI request settles after the bounded cleanup tail has elapsed and the timeout result was returned
- **THEN** the late completion SHALL not produce another MCP response, expose additional output, or permit another guest request

### Requirement: Cleanup failures remain visible and authoritative
The trusted host SHALL retain provider cleanup as the authority for releasing runner resources. If the provider cannot close its channel or confirm execution-resource destruction within the host-clamped cleanup tail, the server SHALL return a sanitized cleanup failure rather than report a successful or timed-out execution as complete.

#### Scenario: Provider deletion is unconfirmed
- **WHEN** a provider cannot confirm destruction of its execution resource within its cleanup tail
- **THEN** the server SHALL return `result` as `null`, `error.message` as `isolation provider cleanup failed`, bounded empty-or-captured `stdout` and `stderr`, a nonzero `exit_code`, and `timed_out` as `false`

### Requirement: Unawaited OCI work is reported without unbounded waiting
The server SHALL continue to reject a script that otherwise completes successfully while it has unawaited OCI work. That rejection SHALL occur within the bounded lifecycle and MUST NOT wait indefinitely for the abandoned RPC to settle.

#### Scenario: Script finishes before its OCI call
- **WHEN** a script returns a successful result while a permitted OCI RPC remains pending
- **THEN** the server SHALL abort the pending work and return a structured non-timeout error indicating unawaited OCI calls within the cleanup tail

### Requirement: Cancellation preserves protocol and isolation controls
Cancellation and bounded draining SHALL NOT relax framed-worker validation, request validation, credential isolation, client-option restrictions, byte limits, or public-error sanitization.

#### Scenario: Malformed frame arrives during cancellation
- **WHEN** a runner sends a malformed, unknown-version, unknown-field, oversized, invalid-UTF-8, dangerous-key, or truncated protocol frame while cancellation is in progress
- **THEN** the host SHALL reject the frame using the existing sanitized protocol-failure behavior and SHALL not invoke host OCI RPC from that frame

#### Scenario: Runner attempts raw OCI access after cancellation
- **WHEN** a compromised runner attempts a direct raw-channel request, credential access, Node-global access, or unsupported client option after cancellation begins
- **THEN** the host SHALL preserve credential and Node-global isolation, reject unsupported bridge input, and expose no raw provider or SDK diagnostic in the MCP result
