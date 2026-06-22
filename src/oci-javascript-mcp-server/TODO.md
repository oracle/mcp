# TODO

## Pagination Ergonomics

- Add SDK-native async iterator names by translating them to normal list calls with page tokens; do not add a separate pagination helper.

## Final Expression Correctness

- Consider Acorn for isolate-side final-expression parsing if the current best-effort heuristic causes real agent failures; avoid adding the parser dependency unless correctness issues justify the extra bootstrap surface.

## Host Metadata Performance

- Memoize filtered SDK operation names per service/client to avoid repeated request-shape filesystem probes on heavy multi-call scripts.

## HTTP Support

- Keep stdio as the default local transport.
- Add HTTP only as an opt-in mode, following the IDCS-gated pattern from `oracle/mcp#204`.
- Require a configured HTTPS public origin for non-local deployments.
- Enforce IDCS issuer, audience, and scope checks before accepting MCP requests.
- Preserve per-call sandbox isolation; document whether OCI credentials are shared by deployment or mapped per user.
