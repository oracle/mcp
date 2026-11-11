# Apply context-authoring conventions: scope and reuse

## Approved increment

The user authorized adding repository context conventions to the existing `dustin-sale/mcp` pilot on `codex/monorepo-agent-context-clean`, adding local context conventions and a root authoring/maintenance route, using Common/Compute authentication as the first focused topic, validating documentation and committing locally. This bundle records that increment separately from the [original engineering-guide adoption](../adopt-monorepo-agent-context/adoption-summary.md).

Scope: repository context conventions, root/shared/component discovery, and the authentication relationship between Common and Compute. Preserve the broad nine-area guides for all 34 servers and Common, native engineering documentation and application requirements. No application source, manifests, commands, generated files, skills or harness are changed; no auth migration, other-server topic audit or live/effectiveness evaluation is included.

## Source assessment

Sources were inspected before creating the new explanations, against the MCP baseline below.

| Existing source | What it answers / material gap | Decision |
| --- | --- | --- |
| [Root guide](../../../AGENTS.md) and [shared engineering map](../../agent-development.md) | Broad engineering orientation, scope/validation and existing routes; no explicit repository authoring method | Preserve orientation/policy; add a specific authoring route to new [agent-context.md](../../agent-context.md), whose explanation covers real local location, authority, mapping and maintenance choices |
| [Common guide](../../../src/common/AGENTS.md), [README authentication module](../../../src/common/README.md#authentication-module), [profile contract](../../../src/common/README.md#profile-backed-authentication), [HTTP contract](../../../src/common/README.md#http-idcs-authentication) | Adequate shared API, ownership, precedence and security explanation; no Common topic document needed | Reuse native contract sections directly; add a scoped comparison route to Compute's explanation without copying the shared contract into a new Common document |
| [Root quality rules](../../../AGENTS.md#mcp-server-quality-validation) and [BEST_PRACTICES auth guidance](../../../BEST_PRACTICES.md#oci-sdk-authentication) | Existing requirements for Common adoption and caller-specific HTTP handling | Reuse in place; preserve shared requirements rather than treating Compute's current behavior as new policy |
| [Compute guide](../../../src/oci-compute-mcp-server/AGENTS.md) and [native README](../../../src/oci-compute-mcp-server/README.md) | Broad engineering guide and startup/callback instructions; legacy gap mentioned briefly. No substantial explanation relates local credential/transport branches to Common's profile and HTTP contract | Add one focused [Compute authentication explanation](../../../src/oci-compute-mcp-server/docs/authentication.md), update auth routes and add a native README cross-link; retain native startup procedure and all broad guide areas |
| [Common source](../../../src/common/oracle_mcp_common/auth.py), [exports](../../../src/common/oracle_mcp_common/__init__.py), [tests](../../../src/common/oracle_mcp_common/tests/test_auth.py), [manifest](../../../src/common/pyproject.toml) | Builder ownership, direct-profile classification, explicit HTTP context, available check definitions and install requirements | Reuse as supporting sources; no code or dependency remediation. Existing README/manifest version discrepancy remains explicit |
| [Compute source](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py), [tool tests](../../../src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/tests/test_compute_tools.py), [manifest](../../../src/oci-compute-mcp-server/pyproject.toml) | Security-token profile path, host/port-gated local HTTP path, local provider/client creation and absent Common dependency; tests differ in assertion strength | Relate these sources in the local topic document; label observations and unrun definitions separately from shared requirements and results |
| [Original adoption summary](../adopt-monorepo-agent-context/adoption-summary.md) | Prior scoped documentation and ten-case evaluation record | Preserve unchanged as history; record current checks in this bundle rather than extending the old evaluation's claim |

## Sequential application

1. Inspect the applicable pilot instructions/native sources; assess reuse/update/creation.
2. Add local conventions and the root authoring route. Keep engineering guidance and its substantive policy intact.
3. Add only the justified Compute topic explanation; map relevant Common shared prerequisites and local evidence from root, Common and Compute. Link authoring conventions from the shared engineering entry.
4. Validate selected root/component walkthroughs, relative targets/anchors, source claims, coverage preservation, documentation-only diff and evidence distinctions. Record actual outcomes separately.
5. Review the completed documentation increment and commit locally on the existing pilot branch.

## Source identities

MCP inspected baseline: `019fec4392667e99e97fac7baa69a08440835675` on `codex/monorepo-agent-context-clean`. This increment leaves application sources and test/manifest definitions unchanged.

| Baseline source | Git blob at the inspected MCP commit |
| --- | --- |
| Root AGENTS.md | `7a5a5f1bc6dbe734c636f0a55e8b826c4763b34f` |
| BEST_PRACTICES.md | `541a3d43ee72f113fd97280a29bfe9e303aea18f` |
| Common README.md | `8866f59c393c8e5ccf3df795d3f1466af4a67320` |
| Common auth.py | `4de730a85377d43acc6c19b169988efce22f9682` |
| Common test_auth.py | `09bea9b5d4c7f15679cde9925192b47bbc8191b3` |
| Common pyproject.toml | `dfbb789a60ebc72b291ff2d494aa154a298a1d28` |
| Compute README.md | `134dc106762c14bb926f642a82acc233ac9cdafa` (only a topic cross-link added in this increment) |
| Compute server.py | `47c23122c12c4247fd4cd0323400f53a70a25167` |
| Compute test_compute_tools.py | `4eae783c9e1d5e04c9015d3023525ca7c4351fe2` |
| Compute pyproject.toml | `f3390398fde70f3d4cae08912cbe1d2fac713f53` |

## Review criteria

Root and relevant component starts must reach applicable instructions, the shared prerequisites, the owning local explanation and supporting sources. Common-only authentication work must still reach its adequate native contract directly. Creation must supply interpretation beyond an adequate single link. Every guide retains broad orientation; no new requirement or exception is inferred from implementation. Relative links/anchors resolve, source names and claims match the inspected definitions, and historical evaluations/test definitions are not described as new passing results. See the [outcome](outcome.md) for executed documentation checks and limitations.
