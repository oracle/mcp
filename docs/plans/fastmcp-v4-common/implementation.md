# FastMCP 4 support for Common

Common 0.3.0 requires `fastmcp>=4.0.0,<5.0.0` and retains its public
credential builders, input precedence and caller isolation. Servers retain
request-context retrieval, service-client construction and lifecycle ownership.
The OCI SDK minimum remains `>=2.185.0`; the README now states that minimum.

## Common implementation

- Regenerate Common's lock through uv, targeting FastMCP 4.1.6 and MCP SDK 2.3.0.
- Use the public `enable_cimd` constructor parameter, verified in FastMCP 4.0.0
  and 4.1.6, instead of clearing a private manager after provider construction.
- Exercise FastMCP's real provider with mocked OIDC discovery and signer
  construction. Verify scope qualification, bare verification scopes, CIMD
  manager construction and advertised metadata, PKCE/callback behavior, distinct
  caller contexts and safe public failure messages. Retain existing credential
  mode, precedence and input-validation coverage.
- Build and clean-install the wheel in disposable environments through
  `moon run common:compatibility-test` (the existing matrix script). Keep this
  task uncached and separate from normal locked tests. Test both endpoints with
  exact OCI SDK 2.185.0 and with the current resolvable OCI SDK. Check installed package
  versions, public dependency metadata and dependency compatibility.

## Independent consumer development and releases

The six consumers now resolve published Common 0.2.x within their existing
manifest bounds. Their Common workspace source and `../common` membership were
removed, and their locks regenerated against registry Common 0.2.0. All locked
package names and versions are identical to the pre-decoupling versions; only
dependency source/workspace metadata changed. Consumer runtime code, tests,
server versions, FastMCP/OCI/CLI pins and denylists are unchanged.

Normal consumer CI validates its declared, published dependency combination.
It does not implicitly substitute the checkout's Common 0.3.0. Moon's Cloud
project inspection now reports no local project dependency, consistent with
removing the workspace edge. Shared Common compatibility checks are explicit
rather than inferred from the consumer's ordinary test run.

The earlier six-consumer FastMCP 4 runtime migration, including API CLI/denylist
coordination and the full combined validation record, remains preserved in its
Git stash. It was not restored for this update. Consumers can adopt Common 0.3.0
and FastMCP 4 later through explicit bounds, lock and compatibility updates.

Individual release jobs now publish only the selected package: select `common`
to release Common. They no longer upload/download or automatically publish an
unrelated checkout version of Common with every Python server release. Bulk
`all-python` publishing retains Common-first publishing and the index-visibility
wait. Publish a required Common version before releasing consumers that adopt
it. No package was published during this work.

## Opt-in local integration

`python3 scripts/check-common-consumer.py <consumer>` builds Common and the
consumer as wheels, installs them together in a disposable environment through
normal dependency resolution, checks installed dependencies and package
locations/versions, then runs the original consumer suite against the installed
artifacts with branch coverage and its native coverage threshold. It leaves
manifests, locks and ordinary project environments unchanged. Coverage is
temporary, and Recovery log/state paths are redirected into the disposable
directory. API and Cloud retain their legacy `/tmp/audit.log` behavior. The helper is a dependency/test
environment rather than a filesystem sandbox. Inherited Python/test and
dependency-override settings cannot silently bypass the check.

The helper accepts `--common-source` for a compatible local checkout. It pins
the installed consumer's runtime import path before loading tests; a tests-only
namespace supports source test fixtures without adding runtime source imports.
Its five focused unit tests run in CI through the new `root:test` task.

Current consumers require Common `>=0.2.0,<0.3.0`, so the default helper run
against local Common 0.3.0 intentionally fails dependency resolution. A real
Cloud check confirmed that rejection and temporary-output cleanup. A second
set of real checks used Common 0.2.0 archived from commit `b407596`. All six
consumer suites passed against the built wheels with the counts and coverage
listed below, without changing consumer bounds or applying the stashed migration.
Those checks use normal wheel dependency resolution rather than overriding it
with the consumer lock; compatible transitive versions may differ from the
ordinary locked environment.

The Common development guide also documents `uv run --locked --with-editable
../common pytest` for quick experiments. uv overlays may conflict with declared
project dependencies; that exploratory route is not release compatibility
proof. Use the wheel check for dependency-validating integration evidence.

## Validation evidence

The original Common suite passed 69 tests at 96.03% coverage before implementation.
The disabled-CIMD regression failed against the old implementation at both
FastMCP endpoints because it constructed a manager before discarding it.

Common 0.3.0 passed these complete clean-wheel suites on 2026-11-18. Each run
included branch coverage, dependency checks and wheel metadata/version checks,
without workspace source overrides:

| FastMCP | OCI SDK | MCP SDK | Tests | Coverage with branches |
| --- | --- | --- | ---: | ---: |
| 4.0.0 | 2.185.0 | 2.3.0 | 75 | 96.32% |
| 4.0.0 | 2.192.0 | 2.3.0 | 75 | 96.32% |
| 4.1.6 | 2.185.0 | 2.3.0 | 75 | 96.32% |
| 4.1.6 | 2.192.0 | 2.3.0 | 75 | 96.32% |

On 2026-11-19, `moon run common:compatibility-test` passed the same four
environments with 75 tests and 96.32% coverage each. Moon resolved the task
with caching disabled and no dependency from the standard `common:test` task.

On 2026-11-19, the original consumer suites passed against registry Common
0.2.0 and FastMCP 3.4.10 / MCP SDK 1.30.0:

| Consumer | Tests | Coverage with branches | OCI SDK |
| --- | ---: | ---: | --- |
| API | 121 | 96.89% | 2.185.1 |
| Cloud | 302 | 94.26% | 2.185.1 |
| Database | 169 | 93.41% | 2.185.1 |
| DB Observability | 67 | 92.94% | 2.185.1 |
| Document Understanding | 52 | 93.99% | 2.185.0 |
| Recovery | 215 | 100.00% | 2.185.1 |

All six lock checks, wheel/sdist builds and installed dependency checks passed.
Recovery's sandbox run used a writable temporary `ORACLE_MCP_LOG_DIR` so its
normal file-logging startup branch could execute; no test or gate was changed.
Locked synchronization removed leftover environment packages from the earlier
stashed migration before final dependency and suite checks.

The helper's five unit tests, root lint and the real compatible/incompatible
integration cases passed. Moon and publishing YAML parsed, and source review
confirmed that individual release guards no longer invoke Common publishing;
bulk Common-first behavior remains. No release workflow was executed.

| Shared check | Result |
| --- | --- |
| `moon run :test --force` | Passed: 33 tasks; 3,313 pytest cases across 30 Python packages, five helper unittest cases, 167 JavaScript tests |
| `moon run :lock-check --force` | Passed: all 30 Python project locks |
| Common + six consumer `install-check` targets | Passed: 21 test/build/install tasks through the actual CI install route |
| `moon run root:combine-coverage` | Passed: aggregate Python coverage 94%, above the 90% gate |
| Final `moon run root:test root:lint --force` | Passed after the helper isolation fix; five unit tests and repository lint |
| Documentation targets, YAML parsing and `git diff --check` | Passed |

Independent review confirmed unchanged consumer runtime versions/source/tests,
registry Common sourcing, explicit release guards and installed-artifact test
isolation. It found that an inherited Recovery log-file override could bypass
the temporary directory; the helper now removes file overrides and forces
log/state directories under its temporary root. Hostile-path assertions failed
before the fix and pass after it. Recovery's real wheel check passed all 215
tests at 100% again after the fix. The final source review has no remaining
findings. The stashed runtime migration remains unchanged.

Earlier repository-wide results from the stashed runtime migration apply only
to that snapshot. The Common production implementation and tests are unchanged
by this decoupling work. Endpoint checks cover tested versions rather than every
future 4.x release; mocked boundaries do not establish live OCI/IDCS behavior.
