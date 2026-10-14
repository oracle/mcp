# Dependency and packaging review

Read this only when dependencies, locks, packaging or SDK/CLI surfaces change. Use [native validation](../../../../docs/agent-development.md#validation-map) and component instructions. The former Makefile workflow and mandatory generated `__init__.py` edits are not current procedures.

## Constraints and resolved environments

Record changed direct constraints/resolved versions, rationale and runtime minima. Check manifest/lock coherence with the actual lock check; Moon Python defines `moon run <project>:lock-check` from root. Select build/install checks when metadata, entry points or artifacts change. Do not require unrelated packages to share one SDK pin or silently regenerate locks with another toolchain.

Review containers, README/client configuration, examples and existing changelogs for user/operator effects. A lock-only diff needs a compatibility reason. Packaging success does not establish unit coverage or live compatibility.

## OCI SDK and Common

Map consumers through manifests, graph edges and actual call sites. Use the [authentication ledger](../../../../docs/authentication.md#adoption-ledger); declarations alone do not establish adoption. Review client constructors, methods/models/enums, pagination, errors, retries, signers and request/result compatibility.

Check metadata-derived user agents and required Common integration across affected credential paths. HTTP clients remain caller-specific. Common-only checks do not establish consumer compatibility; use root-required shared tests/coverage and native procedures for excluded packages. State mock/live evidence limits.

## OCI CLI / API server

For API `oci-cli` changes, inspect normalization, process environment, aliases/global options and denylist coverage. Keep the [generator](../../../../scripts/oci-api-denylist-generator.py), [inventory denylist](../../../../scripts/denylist) and [runtime copy](../../../../src/oci-api-mcp-server/oracle/oci_api_mcp_server/denylist) coherent with the exact reviewed CLI version.

If relevant command/options changed, inspect regeneration prerequisites and resulting differences. Verify the generator's executable/version before running; an unrelated global CLI is not evidence for the lock. If regeneration is unnecessary, record the checked old/new surface and concrete reason. Build success alone cannot establish denylist compatibility. Grade a demonstrated bypass or missing evidence proportionately and retain the root subprocess exception boundary.
