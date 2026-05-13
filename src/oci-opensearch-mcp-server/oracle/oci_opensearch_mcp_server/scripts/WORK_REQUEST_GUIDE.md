# OCI OpenSearch Work Request Guide

Use the work-request tools whenever a mutation tool returns `opc_work_request_id`, but do not
poll continuously by default. Long-running OpenSearch workflows can remain non-terminal for a
while, so report the work request ID to the user and ask before repeated status checks.

## When to call each tool

- `get_work_request`: check one known work request once for a current status snapshot
- `list_work_requests`: correlate recent operations in a compartment or find the latest related request

`list_work_requests` returns an object with `items` and `count`. If no matching work requests exist, the tool returns `{"items": [], "count": 0}` so an empty result is explicit.

## Typical status progression

- accepted
- in progress
- succeeded, failed, or canceled

## Agent status-check policy

After an async mutation returns `opc_work_request_id`:

1. Report the mutation acceptance status and work request ID to the user.
2. If useful, call `get_work_request` once for an immediate status snapshot.
3. If the work request is not terminal, do not keep polling automatically.
4. Ask the user whether they want another status check later or repeated polling.
5. Avoid submitting another conflicting mutation until the earlier work request is terminal.

## Failure triage

1. Confirm you are checking the correct work request identifier.
2. Re-read the original mutation payload for missing required fields or stale `if_match` usage.
3. For shape-related create or vertical resize failures, confirm that shape strings came from `list_opensearch_cluster_shapes`.
4. Check for shape and capacity causes such as an invalid shape string, an OCPU or memory value that is incompatible with the chosen shape, service-limit exhaustion, regional or availability-domain capacity shortfall, or another mutation already in progress.
5. Refresh the cluster state with `get_opensearch_cluster` before retrying another mutation.
6. Avoid submitting another conflicting mutation until the earlier work request is terminal.

If `list_work_requests` cannot complete, it returns the normalized OCI service error fields: `status`, `code`, `message`, and `opc_request_id` when OCI provides one.