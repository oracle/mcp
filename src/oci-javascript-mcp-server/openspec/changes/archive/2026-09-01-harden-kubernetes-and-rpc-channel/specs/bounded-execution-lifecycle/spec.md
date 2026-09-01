## MODIFIED Requirements

### Requirement: Execution result delivery has a bounded lifecycle
The trusted host SHALL apply one absolute execution deadline to provider startup, Kubernetes pod creation and exec establishment, runner execution, host OCI RPC acceptance, channel egress, and result delivery. Kubernetes pod creation SHALL receive that deadline and its abort signal, and the trusted host MUST stop awaiting an unresolved creation request when the deadline or cleanup bound wins. After the execution deadline, the host SHALL allow no more than one provider-specific, host-clamped cleanup tail before returning the structured MCP tool result. Provider cleanup, bounded channel shutdown, execution-resource destruction, and outstanding host-RPC draining MUST consume that one tail concurrently rather than serially.

#### Scenario: OCI request does not settle after cancellation
- **WHEN** an execution reaches its deadline while a host OCI RPC remains unresolved after its abort signal fires
- **THEN** the server SHALL return no later than the execution deadline plus its configured cleanup tail with `result` set to `null`, `error.message` set to `sandbox run deadline exceeded`, bounded `stdout` and `stderr`, `exit_code` set to `-1`, and `timed_out` set to `true`

#### Scenario: Provider cleanup consumes most of the tail
- **WHEN** a provider needs nearly its full host-clamped cleanup tail to close its channel and destroy its execution resource while an OCI RPC also remains unresolved
- **THEN** the server SHALL not add a second RPC-drain wait after provider cleanup completes

#### Scenario: Kubernetes exec establishment never settles
- **WHEN** Kubernetes exec setup stalls past cancellation or the absolute execution deadline
- **THEN** the server SHALL stop waiting for the connection, return the authoritative timeout shape within the single cleanup tail, and attempt zero-grace pod deletion
- **AND** a channel that completes late SHALL be closed without starting worker execution or restoring bridge authority

#### Scenario: Kubernetes pod creation never settles
- **WHEN** Kubernetes pod creation remains unresolved through cancellation, the absolute execution deadline, and the cleanup bound
- **THEN** the server SHALL abort and stop awaiting the creation request, attempt zero-grace deletion for the known execution pod identity, and return within the single cleanup tail
- **AND** the unresolved request SHALL not postpone result delivery or restore execution authority

### Requirement: Cleanup failures remain visible and authoritative
The trusted host SHALL retain provider cleanup as the authority for releasing runner resources. Pod-creation cancellation, channel shutdown, and execution-resource destruction SHALL be independently bounded cleanup activities, and creation or channel failure or delay MUST NOT postpone or suppress a zero-grace Kubernetes pod-deletion attempt for the known execution pod identity. If termination begins while creation is pending and that request later resolves or rejects, the provider SHALL treat the outcome as ambiguous and start a new bounded zero-grace deletion and absence-confirmation attempt after primary cleanup without opening an exec channel, starting worker execution, restoring bridge authority, or changing the returned result. If the provider cannot close its channel or confirm execution-resource destruction within the host-clamped cleanup tail, the server SHALL return a sanitized cleanup failure rather than report a successful or timed-out execution as complete.

#### Scenario: Provider deletion is unconfirmed
- **WHEN** a provider cannot confirm destruction of its execution resource within its cleanup tail
- **THEN** the server SHALL return `result` as `null`, `error.message` as `isolation provider cleanup failed`, bounded empty-or-captured `stdout` and `stderr`, a nonzero `exit_code`, and `timed_out` as `false`

#### Scenario: Kubernetes channel never closes
- **WHEN** an established Kubernetes exec channel ignores close while the execution is terminating
- **THEN** the provider SHALL attempt and confirm zero-grace pod deletion without waiting indefinitely for the channel
- **AND** any unconfirmed channel shutdown SHALL remain a sanitized cleanup failure within the single cleanup tail

#### Scenario: Kubernetes pod creation succeeds late
- **WHEN** a cancelled or deadline-expired creation request reports success after the primary deletion attempt observed absence or cleanup already returned
- **THEN** the provider SHALL trigger a bounded zero-grace deletion and absence-confirmation attempt for that execution pod
- **AND** the late success SHALL not start exec, run guest code, restore bridge authority, or replace the authoritative MCP result

#### Scenario: Kubernetes pod is created but the client observes failure
- **WHEN** termination begins while pod creation is pending, the API server persists the pod, and the client request later rejects because cancellation or transport failure lost the successful response
- **THEN** the provider SHALL treat the rejection as an ambiguous creation outcome and trigger a fresh bounded zero-grace deletion and absence-confirmation attempt after primary cleanup
- **AND** the rejected client outcome SHALL not suppress deletion, start exec, run guest code, restore bridge authority, or replace the authoritative MCP result
