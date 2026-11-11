# Test quality

Use this guide to design or review tests for changed behavior. [Root quality requirements](../AGENTS.md#mcp-server-quality-validation) and [BEST_PRACTICES](../BEST_PRACTICES.md#test-cases) own the coverage requirements. Preserve stricter package thresholds: Recovery currently enforces 100%, while the minimum for Python server quality is 90%. Passing coverage is a floor; assertions must still detect meaningful failures.

## Review criteria

| Behavior under review | Useful evidence |
| --- | --- |
| New behavior or regression | Inputs and expected observable results that distinguish the intended behavior from the defect. A regression case should fail for the original defect, rather than any incidental exception. |
| Validation/error handling | Boundaries, invalid values and the expected error category/message or MCP error result. “Some exception occurred” is insufficient when several failures are possible. |
| SDK conversion | Real conversion/result shaping with a fake service response containing representative fields; the converter itself is not mocked out. |
| Authentication | Every supported credential path, exact derived user agent, caller-specific clients and refusal of invalid or missing caller context where required. |
| Collections | First/middle/final and empty pages, caps, continuation, truncation and failure after partial results; see [pagination](pagination.md#review-checklist). |
| Mutations | Rejection before the service call when a safeguard fails, authorized execution and truthful partial/unknown outcomes; see [tool safety](tool-safety.md). |
| Isolation | Fixtures restore environment, monkeypatches, caches and shared state; test order does not affect outcomes. |

Mock external services at their boundary. Exercise production validation, conversion and serialization when those are the changed behavior. If a mock supplies the exact final value that the test later asserts, the test may establish wiring but not the transformation being reviewed. Assert the arguments that matter to the contract; asserting every internal helper call couples tests to implementation without improving confidence.

Use small realistic records, including missing/optional fields and distinctions such as unauthorized versus not-found. Parameterize cases that share one behavior; keep distinct failure reasons identifiable. Avoid timing sleeps, current-time dependencies and network access in the normal unit suite; use controllable clocks and deterministic fixtures where needed.

### Passwords and secrets in test data

Use clearly synthetic values for passwords and secrets in unit-test fixtures and examples. Suggested values are:

- `this-is-not-the-secret`
- `example-password`
- `DB_PASSWORD`
- `<redacted>`

Choose a value that fits the assertion, such as `<redacted>` for sanitized output. Never use real passwords, tokens or other credentials in test data.

## Function and protocol tests

Direct tests are useful for logic and service-boundary behavior. Add an in-memory MCP client test when registration, generated schemas, argument coercion, result serialization or error handling could fail independently of a direct call. Select the client/test APIs for the actual library and lock version; see [FastMCP testing](fastmcp.md#testing).

For example, Cloud's [model coercion tests](../src/oci-cloud-mcp-server/oracle/oci_cloud_mcp_server/tests/test_model_coercion.py) pass JSON-like arguments through `Client(mcp)` while faking the OCI client. Common's [authentication tests](../src/common/oracle_mcp_common/tests/test_auth.py) provide native credential-boundary examples. These are source definitions, not passing runs certified by this document.

## Validation and evidence

Use the [validation map](agent-development.md#validation-map) and native manifest for command, directory, prerequisites and coverage enforcement. Shared behavior needs consumer review and broader checks; one library's passing suite does not cover every integration. Preserve local thresholds and identify unsupported enforcement in excluded/non-Python packages rather than treating a successful build as coverage.

Live OCI/database and end-to-end tests have separate credentials, cost and mutation prerequisites. Keep them explicit and separately gated; normal tests should be offline and reliable. Record command, source state, discovered tests, coverage scope and result. Use passed, failed, blocked or not run accurately; a test definition or previously cached report is not a current successful execution.
