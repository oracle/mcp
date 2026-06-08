# Repository Agent Instructions

## Scope

These instructions apply to the entire repository. More specific instructions in a nested `AGENTS.md` file override this file for that subtree.

## Repository Layout

- `src/<server-name>/` contains individual MCP server implementations.
- `tests/` contains repository-level tests and end-to-end test assets.
- `BEST_PRACTICES.md` defines expected quality standards for MCP servers in this repository.
- `README.md` contains repository setup, authentication, and client configuration guidance.

## Validation

- For Python MCP servers with `pyproject.toml` that are not listed in `EXCLUDED_PROJECTS`, run `make test project=<server-name>` to test one server, for example `make test project=oci-compute-mcp-server`.
- Some servers are excluded from common Makefile targets through `EXCLUDED_PROJECTS`. For any excluded server, do not rely on `make build`, `make install`, `make test`, or related repository-level targets; follow that server's `README.md` for validation and report a gap if the README does not document validation commands.
- Run `make lint` after Python source changes.
- Run `make test` when a change affects shared behavior across multiple non-excluded servers.
- For non-Python servers, read the server's `README.md` and run its documented test command.
- Do not mark validation complete until the relevant commands pass.

## Editing Rules

- Keep each MCP server self-contained under `src/<server-name>/` unless shared repository tooling must change.
- Do not add secrets, tenancy-specific values, credentials, or local absolute paths to examples, configs, docs, or tests.
- Do not edit generated or local output artifacts such as `htmlcov/`, `.coverage*`, `.ruff_cache/`, `.pytest_cache/`, `__pycache__/`, `dist/`, `src/logs`, or `.venv/`.
- Keep diffs focused on the requested change; avoid unrelated formatting, import reordering, or refactors.

## MCP Server Quality Validation

When validating the quality of any MCP server under `src/`:

- Read `BEST_PRACTICES.md` first and use it as the validation checklist.
- Use `src/oci-compute-mcp-server/` as the reference example for expected structure, packaging, models, server entry point, tool parameter style, and tests.
- If changes are scoped to a specific server, validate only that server for best-practice patterns and 90% coverage. Do not audit or require unrelated servers to meet those standards unless the change touches shared tooling or the user explicitly asks for a broader review.
- Confirm the server includes unit tests for the MCP server code.
- For Python MCP servers, require unit tests to enforce at least 90% coverage through `[tool.coverage.report] fail_under = 90` in `pyproject.toml`. Do not mark validation complete if the coverage threshold is lower than 90% or if coverage fails.
- For non-Python or Makefile-excluded servers, follow the server's `README.md` to identify the test and coverage commands. Report a gap if the README does not document how to enforce 90% unit-test coverage.
- Treat end-to-end tests under `tests/e2e/` as optional unless they can run without making the normal test suite slower or less reliable.
