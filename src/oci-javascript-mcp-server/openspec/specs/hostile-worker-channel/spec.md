# Hostile Worker Channel Specification

## Purpose

Define a bounded, phase-safe protobuf gRPC channel for every untrusted isolation
runner so hostile traffic cannot consume unbounded host resources or retain OCI
bridge authority after completion.

## Requirements

### Requirement: Protobuf gRPC messages are bounded and validated
The trusted host SHALL use the versioned protobuf v4 bidirectional Session
service for runner traffic. It SHALL configure finite send and receive limits,
validate that every envelope contains exactly one known message body, decode
opaque JSON fields with strict UTF-8, dangerous-key, depth, node, string, array,
object-key, and byte limits, and preserve JavaScript source and log code units
through bounded UTF-16LE fields. Unknown protobuf fields MUST NOT become
application fields.

#### Scenario: Oversized or malformed runner message
- **WHEN** a compromised runner sends an oversized protobuf message, a malformed
  envelope, invalid bounded text, invalid JSON, or excessive recursive structure
- **THEN** the host SHALL fail the gRPC session with a sanitized protocol result
- **AND** it SHALL invoke no OCI operation from the rejected message

### Requirement: Traffic and results are bounded per execution
The trusted host SHALL apply host-owned message, OCI request, OCI call,
concurrency, log, and terminal-result limits. The terminal result limit SHALL
cover the encoded result and error values and SHALL be enforced independently
of worker-side validation. Waiting on OCI work, transport backpressure, or final
gRPC status MUST NOT extend the absolute execution deadline.

#### Scenario: Valid RPC flood
- **WHEN** a compromised runner sends sustained schema-valid RPC messages
- **THEN** the host SHALL stop the execution at a finite call, concurrency,
  request, message, or deadline budget
- **AND** rejecting one message SHALL invoke no additional OCI operation

### Requirement: Protocol phases revoke authority
The host SHALL accept exactly one execution request and one terminal result.
Only positive, unique RPC identifiers for accepted in-flight requests SHALL
receive replies. Accepting a terminal result SHALL synchronously revoke queued
and future OCI replies, and success SHALL require the final successful gRPC
status rather than receipt of result bytes alone.

#### Scenario: Runner exits after sending result bytes
- **WHEN** result bytes arrive but the gRPC session finishes with a failure status
- **THEN** the host SHALL reject the execution as a sanitized protocol failure
- **AND** provider cleanup SHALL remain authoritative

#### Scenario: RPC arrives after terminal acceptance
- **WHEN** a runner sends or queues an OCI request after its terminal result
- **THEN** the host SHALL not invoke OCI for that request
- **AND** no reply SHALL be written after terminal acceptance

### Requirement: OCI authority remains in the trusted host
The gRPC channel SHALL carry only the narrow validated OCI broker contract.
Channel possession SHALL grant no credential, signer, endpoint, raw SDK client,
Kubernetes, filesystem, process, or network authority.

#### Scenario: Raw authority escalation attempt
- **WHEN** a compromised runner requests credentials, Node globals, an endpoint,
  signer, retry configuration, unsupported client option, or unsupported OCI operation
- **THEN** the trusted host SHALL reject the request under the existing broker policy
- **AND** provider teardown SHALL remain bounded and authoritative

### Requirement: Execution-scoped mutual TLS
Every execution SHALL use fresh server and client identities. The worker SHALL
receive its server private key, certificate, and the host public certificate over
its provider-owned bootstrap stream; it SHALL never receive the host private key.
Podman SHALL expose the runner only on host loopback. Kubernetes SHALL start the
runner with pods/exec, keep the bootstrap stream open, wait for an explicit
readiness line after gRPC bind succeeds, and carry exactly one loopback host
connection through pods/portforward. No legacy framed transport or fallback MAY
be used.

#### Scenario: Bootstrap or readiness is invalid
- **WHEN** TLS bootstrap input is empty, malformed, oversized, incomplete, or has
  unknown fields, or runner readiness is partial, duplicated, oversized, or unexpected
- **THEN** startup SHALL fail without opening an application session
- **AND** all provider resources SHALL still be cleaned up

#### Scenario: Kubernetes gRPC connection
- **WHEN** a Kubernetes runner becomes ready
- **THEN** the trusted host SHALL open one loopback-only port-forward to runner port 50051
- **AND** no Service, host port, host networking, declared container port, or
  non-loopback host listener SHALL be created
