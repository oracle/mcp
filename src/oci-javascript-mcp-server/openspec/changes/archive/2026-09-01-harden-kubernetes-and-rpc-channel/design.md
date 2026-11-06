## Context

See `proposal.md` for motivation. The active implementation has two in-server isolation providers: Podman and Kubernetes (`local-development`, `in-cluster`, and `kata-in-cluster`). Both run the same credential-free worker and share the trusted-host framed channel. The nested `isolated-vm` boundary, provider boundary, and OCI broker remain distinct controls; neither a standard container nor a RuntimeClass name alone establishes a VM-grade boundary.

The current channel decodes all complete messages from a read, starts message handlers without ordered acceptance, writes without honoring backpressure, and retains no terminal protocol phase or cumulative traffic budget. Kubernetes exec establishment does not receive cancellation/deadline state, channel stop can wait indefinitely, and pod deletion begins only after channel stop. Reconciliation stops on its first failed candidate, admission probes cover only a subset of the pod contract, and cluster-scoped access checks omit object names.

Review of the initial implementation found three remaining gaps within this change's stated guarantees: terminal result size is trusted to the cooperative worker until later coordinator validation, reconciliation timeouts stop awaiting but do not abort the underlying Kubernetes request, and the example admission policies hard-code default resource values even though the trusted configuration documents reviewed ranges. This revision closes those gaps without changing the wire format, public result shape, or configured limits.

Two additional reviews exposed narrower defects in that revision: pod creation itself remained unbounded and could succeed after cleanup returned, terminal acceptance applied the configured result limit independently to `result` and `error`, and the example CEL used unsupported relational operators for quantity values. The corrected design treats creation as deadline-owned work with late-success deletion, applies one budget to both encoded terminal values together, and uses the quantity library's inclusive `compareTo()` form.

A later review identified that late-success handling still treated client rejection as proof that the API server did not create the pod. Kubernetes create outcomes are ambiguous when cancellation or transport failure loses the response. The corrected lifecycle therefore treats either resolution or rejection after termination begins as requiring a fresh bounded deletion after primary cleanup.

The repository's OpenSpec configuration still describes the pre-Kubernetes provider state. For this change, the active provider-selection and Kubernetes specs plus the current code are the source of truth; this design introduces no third provider and no process fallback.

### Execution flow and authority boundary

```text
MCP run_javascript
        |
        v
trusted sandbox coordinator -- owns deadline, OCI call/concurrency limits
        |
        +--> Podman process/container ------+
        |                                   |
        +--> Kubernetes pod + exec channel -+--> hostile framed worker channel
                                                    |
                                      health -> execute -> worker -> isolated-vm
                                                    |
                                      RPC request <- SDK-shaped oci facade
                                                    |
                                      trusted OCI broker -> OCI SDK -> response
                                                    |
                                      logs/result -> TERMINAL
                                                    |
                          revoke RPC authority + bounded channel/provider cleanup
```

## Goals / Non-Goals

**Goals:**

- Make trusted-host memory, queued work, frame assembly, and channel writes finite per execution under valid hostile traffic.
- Enforce the configured result-payload limit over the combined encoded terminal `result` and `error` values at the hostile-channel trust boundary before terminal acceptance.
- Preserve concurrent OCI RPC support while ordering protocol acceptance and terminal authority changes.
- Make the absolute execution deadline govern backpressure, Kubernetes pod creation, and exec connection setup.
- Ensure stalled creation or exec closure cannot prevent or consume the entire opportunity for pod deletion, and repeat deletion after any creation request that settles after termination begins regardless of its client-visible outcome.
- Continue reconciliation after individual candidate failures, abort timed-out Kubernetes requests, and emit sanitized aggregate evidence.
- Make admission and cluster-read claims exactly match what startup preflight establishes while preserving every documented reviewed resource configuration.

**Non-Goals:**

- Changing the wire version, worker message schemas, MCP tool/result schemas, SDK-shaped facade, OCI operation exposure, or supported client options.
- Changing OCI call, concurrency, request, response, result, or per-frame limits except to derive additional cumulative channel bounds from them.
- Solving the separate review findings for OCI authorization, sensitive response policy, SDK retries, response pre-materialization, dependency publication, or wire-tag schemas.
- Claiming real-cluster admission, CNI, CRI, Kata guest-kernel, image provenance, or production evidence.
- Adding a provider, process fallback, guest credential, network listener, or application-level provider admission mechanism.

## Decisions

### 1. Use a segmented decoder and a single ordered channel pump

`FrameDecoder` will retain a queue of input segments, a head offset, total queued bytes, and the expected body length. It will copy a frame body once, only after the complete body is available. A lazy iterator/callback will yield one decoded message at a time so one input chunk containing many frames cannot create a large intermediate message array.

The trusted channel consumer will use one asynchronous pump. The pump will count raw ingress before decoding, consume yielded messages in order, and pause/resume the readable while it awaits bounded acceptance or writer backpressure. Undecoded storage is limited to four header bytes plus the current frame body; existing exact UTF-8, JSON, protocol-version, field, dangerous-key, recursive structure, and 2 MiB frame checks remain unchanged.

Alternative considered: periodically concatenate chunks into a larger buffer. This still makes fragmentation cost depend on copy frequency and leaves decoded batches unbounded.

### 2. Derive cumulative channel budgets from existing host limits

The sandbox coordinator will pass frozen host-owned channel limits with each provider run. The accepted-message budget is the configured OCI call budget plus the fixed health, two log, and terminal control-message allowance. Ingress and egress byte budgets are finite upper bounds derived from that message budget and the existing 2 MiB frame ceiling, rather than new operator-tunable environment variables. Raw log payload bytes have a separate cumulative allowance equal to the existing 1 MiB `stdout` plus 1 MiB `stderr` caps.

Every incoming frame consumes ingress and message budget before asynchronous broker work. Every encoded host frame consumes egress budget before it can enter the writer. Invalid input terminates immediately; budget exhaustion returns the existing sanitized protocol failure unless the absolute deadline has already won. This preserves the currently supported maximum OCI-call behavior while preventing unlimited rejected-message or error-response traffic.

Terminal result acceptance will encode `result` and `error` with the same JSON representation used for result-budget enforcement, sum those encoded byte lengths, and compare the sum once with the host-owned configured result limit before changing the protocol phase to `TERMINAL` or resolving the execution result. A compromised runner therefore cannot nearly double the configured allowance by populating both fields or bypass the configured result contract by omitting the cooperative worker check. The existing 2 MiB per-frame limit and structural decoder limits remain the allocation ceiling while the frame is decoded; the terminal check prevents an over-budget decoded payload from becoming authoritative or reaching the outer MCP result path.

Captured output will use a byte-tracking accumulator (`text`, retained bytes, capped state) instead of repeatedly measuring and rebuilding a 1 MiB string. Once a stream is full, later additions are O(1) apart from counting the incoming payload; traffic beyond the cumulative log allowance terminates the protocol.

Alternative considered: add four new environment variables. That increases configuration surface and permits unsafe operator values without improving the fixed worker contract.

### 3. Separate ordered acceptance from concurrent RPC completion

The host protocol state is:

```text
WAIT_HEALTH -- one ready health --> RUNNING -- result/protocol failure --> TERMINAL
     |                                  |                                  |
 other message: fail             health/unsafe id: fail             no work accepted
```

Acceptance is synchronous and ordered. A valid RPC must use a positive safe integer not present in a per-execution `seenRpcIds` set; IDs remain reserved after completion. Acceptance records the ID before launching `hostRpc`. OCI calls may then complete concurrently under the existing sandbox-owned in-flight limit. Their responses enter one outbound writer queue.

On a result, protocol error, budget failure, cancellation, or deadline, the host transitions to `TERMINAL` and disables bridge acceptance before resolving the execution result. Frames already decoded later in the same read and all later reads can stop the channel but cannot start OCI work, append output, or replace the single result. The existing test that accepts a result before health will be inverted.

Alternative considered: await every OCI RPC in the message pump. That simplifies ordering but removes the intentionally supported host RPC concurrency of four.

### 4. Serialize writes and make backpressure deadline-aware

All `execute`, `rpc_result`, and `cancel` frames use one writer. The writer encodes and accounts for a frame only when it reaches the head, calls `write`, and, when `write` returns false, pauses input and races `drain`, channel close/error, cancellation, and the absolute deadline. Only after drain may the next frame be written and input resumed. The queue is bounded by the accepted-message budget and existing RPC concurrency; no independent unbounded promise chain or encoded-buffer queue is allowed.

Deadline loss produces the standard timeout result and begins termination. Stream errors retain the existing sanitized runner/protocol failure mapping. The worker wire format remains version 1 because the bundled worker already follows the stricter legal sequence.

### 5. Make Kubernetes pod creation, exec connection, and close independently bounded

`createPod` will receive the execution abort signal and absolute deadline. The client-node adapter will apply the remaining-time bound and signal to the generated create request, while the provider will also race the returned promise against the same authority. Termination will stop awaiting creation at the cleanup bound and can issue deletion immediately using the already-known pod name rather than waiting for creation to settle.

Because an adapter or remote API may settle after cancellation or after an earlier deletion observed `NotFound`, and a rejected client promise does not prove the API server rejected the create, the provider will attach a settlement handler before racing creation. If termination began while creation was pending, either resolution or rejection requires a fresh bounded zero-grace deletion and absence confirmation after primary cleanup. Settlement cannot enter scheduling, watch, exec, or worker startup. This best-effort post-return cleanup does not delay or replace the already-authoritative MCP result, and reconciliation remains the final backstop if the request never settles or the follow-up deletion cannot be confirmed.

`openExecChannel` will receive the absolute execution deadline and abort signal. The production connector will create a per-call Kubernetes exec/WebSocket setup whose HTTPS/WebSocket options carry a remaining-time handshake timeout and the execution abort signal. The host will also race the SDK promise against that same deadline/signal and register a late-settlement handler that immediately closes any channel returned after authority has ended. Test seams will cover never-settling and late-settling connectors without real cluster access.

`WorkerChannel.stop` will accept an absolute cleanup deadline. Kubernetes stop destroys local streams, requests WebSocket close, and rejects with a sanitized internal failure if `closed` does not settle by that deadline. Podman continues to kill its child tree and perform named cleanup under its existing provider tail.

Alternative considered: react only to successful Kubernetes SDK create resolution. A transport failure or cancellation can reject after the API server persisted the pod, so success-only handling leaves an ambiguous creation resource after cleanup.

### 6. Run Kubernetes deletion independently from channel shutdown

Termination computes one cleanup deadline and starts its independent cleanup tasks without waiting unboundedly for pod creation to settle:

1. abort and stop awaiting pending creation or exec establishment;
2. stop an assigned or late-arriving exec channel within the cleanup deadline;
3. issue zero-grace pod deletion for the known pod name and confirm absence within the same cleanup deadline.

The tasks are awaited with all-settled semantics so creation or channel failure cannot skip deletion. A pending create or exec request is aborted by the signal; a late channel is closed by the connector, and any creation settlement after termination began is handled only by the bounded deletion path. Cleanup succeeds only when required channel closure and pod deletion are confirmed; otherwise the outer sandbox retains the existing `isolation provider cleanup failed` precedence. Primary cleanup consumes the existing single Kubernetes cleanup tail concurrently with host-RPC draining; a later creation settlement can trigger deletion after return but cannot extend result delivery.

Alternative considered: ignore channel-close failure after pod deletion. The active bounded-lifecycle specification requires both channel closure and execution-resource destruction to be authoritative, so the design preserves that stricter outcome.

### 7. Isolate reconciliation outcomes per candidate

Each expired managed pod receives its own five-second deadline and `AbortController`. The Kubernetes API seam carries that signal through delete, existence-read, and deletion-confirmation operations. The client-node adapter applies it to generated HTTP request contexts through per-request middleware and also aborts any deletion watch. At the candidate deadline, reconciliation aborts the controller before recording the failure and continuing, so a timed-out HTTP request or watch cannot remain active across later candidates or future passes. Delete/confirmation exceptions and timeouts are caught for that candidate, counted, and processing continues with later candidates. The pass returns an internal summary containing deleted names for deterministic tests plus a failure count; diagnostics expose only aggregate counts/outcome and never pod names or raw errors.

Startup preflight still fails closed if its initial reconciliation summary contains failures, but only after the entire candidate set has been attempted. Periodic host and cleanup-only loops emit one sanitized failed event when any candidate fails and continue on their next interval. Processing remains sequential to avoid a cleanup surge against the control plane; the namespace quota, per-candidate timeout, and request cancellation bound each pass. Tests use cancellation-aware never-settling fakes and assert that the prior candidate's signal is aborted before the next candidate begins and that repeated passes do not increase active request count.

Alternative considered: unbounded parallel deletion. It shortens a large pass but can amplify an already degraded Kubernetes API and complicates overlap with normal cleanup.

### 8. Generate one admission variant per reviewed invariant and narrow the claim

Admission variants will be identified, immutable mutations of the trusted pod builder output. The shared set covers metadata ownership/profile, image/pull policy, service account, token and service links, restart policy, host network/PID/IPC, command/environment, container/init/ephemeral cardinality, pod and container root identity, privilege escalation/privileged mode, read-only root, seccomp, capabilities, unexpected ports/devices/probes/hooks, bounded resources and active deadline, extra/wrong volumes, memory-backed `/tmp`, size limit, and mount semantics. Resource variants distinguish malformed or out-of-range values from unequal request/limit pairs. Kata adds the wrong RuntimeClass variant.

The example policies use inclusive Kubernetes CEL quantity comparisons of the form `quantity(value).compareTo(quantity(min)) >= 0 && quantity(value).compareTo(quantity(max)) <= 0` rather than unsupported relational operators between quantity values or hard-coded defaults. CPU must remain between `100m` and `4`, memory between `128Mi` and `2Gi`, ephemeral storage between `16Mi` and `1Gi`, and memory-backed `/tmp` between `1Mi` and `64Mi`; CPU, memory, and ephemeral-storage requests must equal their corresponding limits. These bounds match the configuration parser and operator documentation, so default, non-default, minimum, and maximum generated pods are conforming while values outside the reviewed ranges remain denied. The former `32Mi` `/tmp` negative variant is replaced by an out-of-range value because `32Mi` is documented as valid.

Tests will require the variant identifier set to match the reviewed pod/admission contract, and manifest admission fixtures must reject the same set. This makes omissions visible during review. When a real API server is configured, server-side validation must report no `status.typeChecking.expressionWarnings` for either policy before acceptance evidence is recorded; otherwise the environment-only check is explicitly skipped and no server-side CEL claim is made. The descriptor value changes from `enforced` to `reviewed-variants-rejected`; `unverified` remains for local development gaps. An external evidence flag records that the exact deployed admission policy revision is not proven by dry-run behavior alone.

Alternative considered: retain `enforced` after expanding probes. Dry-run rejections still cannot identify the enforcing policy revision or prove the complete cluster admission chain, so the broader label remains unsupportable.

### 9. Name only cluster objects that can be restricted

Kubernetes authorization attributes gain optional `name`. Namespace `get` uses the configured execution namespace; Kata RuntimeClass `get` uses the configured RuntimeClass. Standard and Kata ClusterRoles add matching `resourceNames`. Dynamic pod create/list/watch/delete and exec checks remain namespace-scoped because generated pod names and Kubernetes RBAC semantics do not support equivalent `resourceNames` restriction for the required operations.

The Kata guide will reference `npm run kubectl:dry-run:kubernetes`. A focused documentation test will extract the Kubernetes guide's `npm run` validation commands and assert that each script exists in `package.json`.

## Risks / Trade-offs

- **[Risk] Stricter phases reject a custom or stale runner that previously sent result/log/RPC before health.** → The bundled worker already sends health first and one terminal result; keep protocol version 1, add compatibility tests for the shipped worker, and document that nonconforming workers were never supported.
- **[Risk] Cumulative byte formulas permit a large but finite amount of work when the OCI call budget is configured high.** → Keep per-frame, request, call, concurrency, deadline, and provider resource limits; derive rather than independently expand budgets; document that increasing the call budget increases the cumulative channel ceiling.
- **[Risk] Pausing input during backpressure can contribute to a mutual stall.** → Race drain against close, cancellation, and the absolute deadline, then force provider cleanup.
- **[Risk] A Kubernetes exec promise may settle after pod deletion.** → Abort the request where supported, enforce handshake timeout, and retain a late-settlement close handler that cannot enter `RUNNING` or restore RPC authority.
- **[Risk] A Kubernetes create request may settle after deletion observed `NotFound` or cleanup returned, and rejection may still follow server-side creation.** → Abort the underlying request, race the trusted await, attach a handler for both settlement outcomes before racing, and route either post-termination outcome only to a fresh bounded zero-grace deletion while reconciliation remains the backstop.
- **[Risk] Sequential five-second reconciliation bounds can make a many-failure pass long.** → Continue after each bound, rely on namespace quota, emit aggregate failure, and keep limited concurrency as a future change only if real evidence requires it.
- **[Risk] A Kubernetes client path may ignore the candidate abort signal.** → Apply the signal at the generated request context and watch layers, test signal observation and active-request counts, and fail the candidate closed at the same deadline.
- **[Risk] Admission variants and example CEL policies drift apart.** → Give variants stable identifiers and test the exact shared/Kata identifier sets against both pod invariants and manifest fixtures.
- **[Risk] CEL quantity behavior differs across supported Kubernetes versions.** → Use the documented `compareTo()` API, validate both policies on the supported API server with no type-check warnings, retain fixture coverage for every boundary, and keep real-cluster admission evidence explicit rather than inferred from static parsing.
- **[Risk] `resourceNames` may be added to operations Kubernetes cannot restrict usefully.** → Limit it to exact Namespace and RuntimeClass `get`; retain namespace-scoped pod lifecycle rules.

## Migration Plan

1. Land the decoder, channel budgets, host-side result acceptance check, state machine, writer, and O(1) log accumulator with focused adversarial tests; verify both Podman and fake Kubernetes exchanges retain the MCP result contract.
2. Land deadline-aware Kubernetes create and exec setup plus concurrent stop/delete cleanup with never/late creation, never/late connection, and never-closing channel tests.
3. Change reconciliation summaries and both loops, propagate candidate cancellation through Kubernetes delete/read/watch operations, then verify a failed or never-settling first candidate does not block later deletion or remain active across passes.
4. Expand admission variants, align CEL `quantity().compareTo()` bounds with every documented resource range, update the descriptor and diagnostics, add exact named access checks, update standard/Kata RBAC and admission fixtures, and verify both policies produce no server-side type-check warnings when a configured API server is available.
5. Correct and validate documentation commands; update README or other operator documentation for the narrower admission evidence label.
6. Run focused tests, `npm test`, `npm run coverage`, `npm run check`, `npm run check:kubernetes-manifests`, `npm run kubectl:dry-run:kubernetes`, `npm run packcheck`, and `npm run ci`; run the opt-in local-cluster harness when a configured cluster is available and record a clear skip otherwise.

No persisted data migration or protocol-version rollout is required. Rollback is a code rollback before production admission; operators using Kubernetes must first confirm managed pods are deleted or recovered by the cleanup reconciler. Rollback must not select a different provider/profile automatically and must not claim the former `enforced` descriptor as stronger evidence.
