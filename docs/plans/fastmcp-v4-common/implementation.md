# FastMCP 4 support for Common

Common 0.3.0 requires `fastmcp>=4.0.0,<5.0.0` and retains its public
credential builders, input precedence and caller isolation. Servers retain
request-context retrieval, service-client construction and lifecycle ownership.
The OCI SDK minimum remains `>=2.185.0`; the README now states that minimum.

## Implementation

- Regenerate Common's lock through uv, targeting FastMCP 4.1.6 and MCP SDK 2.3.0.
- Use the public `enable_cimd` constructor parameter, verified in FastMCP 4.0.0
  and 4.1.6, instead of clearing a private manager after provider construction.
- Exercise FastMCP's real provider with mocked OIDC discovery and signer
  construction. Verify scope qualification, bare verification scopes, CIMD
  manager construction and advertised metadata, PKCE/callback behavior, distinct
  caller contexts and safe public failure messages. Retain existing credential
  mode, precedence and input-validation coverage.
- Build and clean-install the wheel in disposable environments through
  `bash scripts/check-common-fastmcp.sh`. Test both FastMCP endpoints with exact
  OCI SDK 2.185.0 and with the current resolvable OCI SDK. Check installed package
  versions, public dependency metadata and dependency compatibility.

## Delivery boundary

This commit contains Common and its directly supporting checks/documentation.
The six-consumer migration and API CLI/denylist updates were separated into a
Git stash at the user's request. The full consumer investigation and validation
record is preserved in that stash rather than represented as current code here.

The unchanged API, Cloud, Database, DB Observability and Recovery manifests pin
FastMCP 3.4.10; Document Understanding requires `>=3.4.5,<4.0.0`. All six require
Common `>=0.2.0,<0.3.0` through local uv workspace sources. Their current bounds
conflict with Common 0.3.0, so this Common-only change is not independently
merge-ready for the repository-wide checks.

Before landing the coupled migration, update all six consumers to Common
`>=0.3.0,<0.4.0`, select compatible FastMCP bounds, regenerate locks and validate
any framework adaptations. API also needs CLI dependency coordination: its
current CLI's certificate constraint conflicts with FastMCP 4.1.6. The stashed
work contains a tested CLI 3.96.0 migration and associated denylist preservation.
Publish Common 0.3.0 before dependent servers. Older published server artifacts
retain their 0.2.x Common range and a compatible published Common 0.2.0 candidate,
as confirmed by the earlier isolated dependency-resolution check.

## Validation evidence

The original suite passed 69 tests at 96.03% coverage before implementation.
The disabled-CIMD regression failed against the old implementation at both
FastMCP endpoints because it constructed a manager before discarding it.

The complete Common 0.3.0 suite passed the following clean-wheel environments on
2026-11-18. Each run included branch coverage, dependency checks and wheel
metadata/version checks, without workspace source overrides:

| FastMCP | OCI SDK | MCP SDK | Tests | Coverage with branches |
| --- | --- | --- | ---: | ---: |
| 4.0.0 | 2.185.0 | 2.3.0 | 75 | 96.32% |
| 4.0.0 | 2.192.0 | 2.3.0 | 75 | 96.32% |
| 4.1.6 | 2.185.0 | 2.3.0 | 75 | 96.32% |
| 4.1.6 | 2.192.0 | 2.3.0 | 75 | 96.32% |

After the scope split on 2026-11-19, the forced Common lock check, full suite
(75 tests, 96.32% coverage with branches), wheel/sdist build and root lint all
passed. Documentation target, shell syntax and diff checks also passed.
Repository-wide test, lock, install and aggregate-coverage results from the
combined consumer migration belong to the stashed snapshot. They do not
establish a passing Common-only workspace with unchanged consumer bounds.

Independent review of the earlier combined snapshot found no source findings,
including Common's provider integration and endpoint test route. The Common
production implementation and tests are unchanged by the scope split. Endpoint
checks cover the tested versions rather than every future 4.x release; mocked
external boundaries do not establish live OCI/IDCS authentication.
