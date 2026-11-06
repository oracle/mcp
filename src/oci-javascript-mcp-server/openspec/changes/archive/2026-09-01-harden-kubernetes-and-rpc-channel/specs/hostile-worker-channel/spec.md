## Purpose

Define a bounded, phase-safe trusted-host channel for every untrusted isolation runner so valid hostile traffic cannot consume unbounded host resources or retain OCI bridge authority after completion.

## ADDED Requirements

### Requirement: Frame assembly is bounded and linear
The trusted host SHALL assemble length-prefixed frames without repeatedly copying the complete partial frame for each input fragment. Undecoded queued bytes MUST remain bounded by the four-byte header plus the configured per-frame limit, currently 2 MiB, and completed frames SHALL flow into bounded message handling without accumulating an unbounded decoded-message array.

#### Scenario: Legal frame arrives one byte at a time
- **WHEN** an untrusted runner fragments a legal maximum-sized frame across a high number of small channel reads
- **THEN** the host SHALL decode or reject it with work and allocation growth proportional to the frame size rather than the square of the fragment count
- **AND** the absolute execution deadline SHALL remain authoritative

#### Scenario: Frame cannot fit within the queue bound
- **WHEN** a frame length exceeds the configured 2 MiB limit or queued undecoded bytes would exceed the header-plus-frame bound
- **THEN** the host SHALL terminate the exchange with `result` set to `null`, `error.message` set to `sandbox protocol failed`, bounded `stdout` and `stderr`, `exit_code` set to `1`, and `timed_out` set to `false`

### Requirement: Channel traffic, results, and writes are bounded per execution
The trusted host SHALL apply finite, host-owned cumulative ingress-byte, accepted-message, log-byte, result-byte, and egress-byte budgets to each execution in addition to the existing per-frame, OCI request, OCI call, and OCI concurrency limits. The trusted host MUST enforce the configured result-byte limit over the sum of the encoded terminal `result` and `error` values when accepting a terminal result from the hostile channel, independently of any cooperative worker-side validation. It SHALL process message acceptance and protocol state transitions in order, pause channel input while bounded work is pending, serialize outbound writes, and honor writable-stream backpressure. Exhausting a channel budget SHALL fail closed, and waiting for backpressure MUST NOT extend the absolute execution deadline.

#### Scenario: Valid message flood
- **WHEN** a compromised runner sends sustained schema-valid RPC, rejected-RPC, or log frames without exceeding any individual frame limit
- **THEN** the host SHALL stop the execution at a finite cumulative budget without unbounded heap, queued writes, or asynchronous handler growth
- **AND** no channel budget rejection SHALL invoke an additional OCI operation

#### Scenario: Runner stops reading host responses
- **WHEN** the worker-side consumer stalls and a trusted-host write reports backpressure
- **THEN** the host SHALL wait for drain before issuing the next write while channel input remains paused
- **AND** failure to drain before the remaining deadline SHALL produce the authoritative timeout result and bounded teardown

#### Scenario: Log cap has already been reached
- **WHEN** later valid log frames arrive after `stdout` or `stderr` has reached its 1 MiB retained-output cap
- **THEN** the host SHALL discard or reject the excess without repeatedly concatenating, rescanning, or copying the retained 1 MiB value
- **AND** the cumulative channel log budget SHALL still advance

#### Scenario: Combined raw terminal values exceed the configured result limit
- **WHEN** a compromised runner sends a schema-valid terminal message whose encoded `result` and `error` values are each within the host-owned configured result-byte limit but their encoded sizes sum to more than that limit while the complete frame remains below the per-frame limit
- **THEN** the trusted host SHALL reject the message before accepting or publishing the terminal result
- **AND** it SHALL return the sanitized protocol-failure result and begin bounded provider teardown without relying on worker-side result validation

#### Scenario: Concurrent executions experience pressure
- **WHEN** one execution exhausts channel budgets or stalls on backpressure while another execution exchanges valid messages
- **THEN** each execution SHALL retain independent channel state, budgets, cancellation, OCI call/concurrency accounting, result fields, and teardown

### Requirement: Worker protocol phases and RPC identifiers are strict
The trusted host SHALL enforce exactly one ordered `WAIT_HEALTH -> RUNNING -> TERMINAL` lifecycle. `WAIT_HEALTH` SHALL accept only one valid ready health message; `RUNNING` SHALL accept only valid log, RPC, result, and protocol-error messages; entering `TERMINAL` SHALL synchronously revoke further bridge acceptance before resolving the terminal result. RPC identifiers MUST be positive safe integers and MUST NOT be reused within an execution, including after their responses complete.

#### Scenario: Message arrives before health
- **WHEN** a runner sends log, RPC, result, protocol-error, or duplicate health traffic before completing the single health transition
- **THEN** the host SHALL return the sanitized protocol-failure result
- **AND** it SHALL invoke no OCI operation from the invalid sequence

#### Scenario: Duplicate or unsafe RPC identifier
- **WHEN** a runner sends a non-positive, non-safe-integer, in-flight duplicate, or previously completed RPC identifier
- **THEN** the host SHALL terminate the exchange as a protocol failure
- **AND** the duplicate or unsafe request SHALL not reach the OCI broker

#### Scenario: Terminal result and later work share one read
- **WHEN** a valid terminal result is followed in the same channel read by an RPC, malformed frame, duplicate result, or any other message
- **THEN** the host SHALL synchronously reject all post-terminal bridge work and stop the channel
- **AND** no post-terminal frame SHALL invoke OCI, alter captured output, or replace the single authoritative result

### Requirement: Existing hostile-input and isolation controls remain authoritative
The bounded channel SHALL preserve exact message schemas, strict UTF-8 and JSON decoding, protocol-version checks, dangerous-key and recursive-structure limits, host-owned OCI request validation, credential and Node-global isolation, unsupported-client-option rejection, public-error sanitization, and cancellation cleanup across Podman and all Kubernetes profiles.

#### Scenario: Malformed raw channel attempt
- **WHEN** a compromised runner sends malformed JSON, an unknown version or field, an oversized or truncated frame, invalid UTF-8, a dangerous key, or excessive recursive structure
- **THEN** the host SHALL return the sanitized protocol-failure result without invoking OCI from that frame
- **AND** provider teardown SHALL remain bounded and authoritative

#### Scenario: Raw authority escalation attempt
- **WHEN** a compromised runner uses the raw channel to request credentials, Node globals, an endpoint, signer, retry configuration, unsupported client option, or unsupported OCI operation
- **THEN** the trusted host SHALL reject the request under the existing broker and isolation policy
- **AND** channel possession SHALL grant no additional OCI, Kubernetes, filesystem, network, or host authority
