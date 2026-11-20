# End-to-End Tests for OCI MCP Servers

These optional [Behave](https://behave.readthedocs.io/en/latest/) scenarios run real MCP server processes against mock OCI services. Codex CLI supplies the model interaction and MCP client loop. They require inference access, but do not require an OCI tenancy, Ollama, `ollama-mcp-bridge`, or the Python Codex SDK.

This is the CLI alternative for [oracle/mcp#570](https://github.com/oracle/mcp/issues/570). The SDK alternative will be evaluated independently from the same base; this implementation has no backend selector.

## Setup

1. Install `uv` and [proto](https://moonrepo.dev/docs/proto/install), then run `proto install` from the repository root.
2. Install [Codex CLI](https://developers.openai.com/codex/cli/) and authenticate with `codex login`, or supply `CODEX_API_KEY` securely in your environment. This runner was tested with **codex-cli 0.170.0** and **gpt-6.1-sol**. It requires that version's `--json`, `--ephemeral`, `--strict-config`, `--no-daemon`, MCP approval settings, and feature controls. An incompatible executable fails setup or configuration validation.
3. Run `uv sync --project tests --locked`. Each enabled `uv` server in the host inventory is also synchronized with `uv sync --project <project> --locked --no-dev` at suite startup, using the driver's normal network settings before mock proxy injection. No server code or lockfile is upgraded.

The runner supports macOS and Linux/POSIX process groups and `/usr/bin/env`. A headless OCI machine needs Python 3.13+, the repository tools, the Codex executable, and an existing supported OpenAI authentication/inference path with network access. It does not provision OCI infrastructure or use OCI Generative AI inference.

Authentication comes from `CODEX_API_KEY` or a private, temporary copy of `$CODEX_HOME/auth.json` (default source: `~/.codex/auth.json`). Keyring-only login is not copied; use file-backed `codex login` or `CODEX_API_KEY`. Personal Codex configuration, MCP servers, plugins, skills, and sessions are not copied. Temporary authentication and session directories are deleted after each scenario. The runner does not change global Codex configuration.

## Run scenarios

From the repository root:

```bash
moon run root:e2e-tests
moon run root:e2e-tests -- -n "List the compute instances"
```

Run the three representative smoke scenarios:

```bash
moon run root:e2e-tests -- -n '^(List the compute instances|Get compute instance details|Get the namespace)$' --no-capture
```

The equivalent direct invocation is:

```bash
uv run --project tests --locked --no-dev behave tests/e2e/features
```

Keep execution serial. Mock state is shared within a suite run. The trusted driver assigns temporary loopback ports, generates dummy OCI credentials and a proxy certificate, and owns their cleanup. No local service needs to be stopped to free port 5000.

## Configuration

Optionally copy `tests/e2e/features/.env.template` to `.env` in the same directory. Existing environment variables take precedence. Keep authentication secrets outside that file.

| Variable | Default | Purpose |
| --- | --- | --- |
| `MCP_HOST_FILE` | Adjacent `mcphost.json` | Existing MCP server inventory; relative overrides resolve from the invocation directory. |
| `CODEX_E2E_EXECUTABLE` | `codex` on `PATH` | CLI executable. |
| `CODEX_E2E_MODEL` | `gpt-6.1-sol` | Model supported by your Codex account. |
| `CODEX_E2E_TIMEOUT` | `180` | Positive, finite deadline in seconds per Codex invocation. |

The old bridge `URL` and Ollama `MODEL` settings are no longer used. Model reasoning settings use the CLI's defaults.

`mcphost.json` remains the single server inventory. The runner translates enabled stdio entries into disposable Codex TOML. It supports `command`, string-array `args`, string-valued `env`, `cwd`, `type="stdio"`, `disabled`, and positive finite `timeout` (default 60 seconds for startup and each tool call). Unknown settings, transports, and environment substitutions are rejected. Disabled entries never launch. Server working directories, relative arguments and relative `PYTHONPATH` entries resolve from the host file's directory, or its explicit `cwd`.

Only `${env:OCI_CONFIG_FILE}` and `${env:MOCK_OCI_PROXY}` are substituted, with values supplied by the trusted test driver. Put proxy and certificate overrides in each MCP entry's `env`; they apply to the server processes. MCP children receive an empty inherited environment plus explicitly configured test values, isolated `HOME`, `PATH`, and dependency-cache/runtime settings. They do not inherit provider keys or real OCI credential variables. Custom launcher commands must already have their dependencies installed; automatic preparation recognizes the inventory's `uv run --project <path> --locked --no-dev <entrypoint>` form.

Every scenario exposes all enabled inventory entries, preserving cross-service requests such as listing Compute instances before querying instance-agent executions.

## Execution and evidence

Each independent scenario uses a fresh `codex exec --json` session in an empty temporary directory. Prompts travel through stdin and launch commands use argument arrays. The agent has a read-only sandbox with shell, web search, image-file inspection, browser/computer use, JavaScript/code execution, apps, plugins, memories and subagents disabled. It cannot read repository fixtures through a shell. MCP servers retain the mock endpoint patches in `mocks/sitecustomize.py`.

Only the disposable test MCP entries receive `default_tools_approval_mode="approve"`, allowing the suite's mock operations to run without interactive prompts. The configured global policy remains `on-request`; enterprise requirements still apply. No sandbox or approval bypass flags are used. CLI 0.170.0 internally defaults exec approvals to `never`; a managed policy can replace that with `on-request` and emit a startup warning. Those pre-turn warnings are reported separately. Required MCP initialization failures and failed turns fail the scenario. Failed tool attempts remain available as diagnostics; the agent may recover through a successful retry or another operation that fulfills the request.

The runner records native final text, successful MCP calls with arguments/results, failed attempts, thread ID, token usage and invocation duration. It does not synthesize bridge HTTP responses. Every active operation outcome explicitly requires its corresponding successful MCP tool call or an explicitly accepted equivalent, followed by the existing response-content assertions. Compute's chained lookup must also use an exact ID returned by a successful listing and include it in the final answer. Failed attempts, resource reads and unrelated successful lookups cannot satisfy the requested-operation checks. Add a `require_call` or `require_chain` check when adding an operation outcome assertion.

Inventory scenarios validate the required live startup/catalog and the existing tool-name assertions; the general inventory also checks all enabled server names. They do not require executing an operation merely to list capabilities.

Codex's built-in MCP resource discovery and reads are recorded separately, including the synthetic `codex` server used for aggregate discovery. They can access only the configured catalog and cannot satisfy operation-call assertions. This supports server-provided guidance such as Monitoring's required MQL resource.

## Offline checks and diagnostics

Normal offline tests need neither Codex nor inference authentication:

```bash
uv run --project tests --locked pytest tests/unit -q \
  --cov=codex_runner --cov-branch --cov-report=term-missing --cov-fail-under=90
uv lock --project tests --check
uv sync --project tests --locked --all-groups
moon run root:lint
```

`--no-capture --format pretty` shows per-scenario runtime/model identity, duration, usage, startup warnings, MCP operation names, and assertion failures. On failure:

- **Executable or authentication setup:** check `codex --version`, `codex login status`, and the documented authentication source. Do not paste credentials into logs.
- **Dependency preparation or required MCP startup:** check the enabled host entry, its project lock, executable, relative paths and mock environment. All selected servers are required; an unavailable one cannot silently disappear from the catalog.
- **Nonzero exit:** check CLI compatibility, account/model access and MCP startup. Raw process stderr is withheld because it may contain provider credentials.
- **Failed attempt or missing evidence:** failed attempts are logged separately and retained in `CodexResult.failed_calls`. A recovered attempt can pass only when the requested operation succeeds and its response assertions pass. A plausible answer, unrelated successful lookup or successful process exit alone cannot pass an operation scenario.
- **Invalid/truncated events or missing final text:** the scenario fails instead of accepting partial output. Shell/file/web/collaboration execution events and calls to foreign servers are rejected.
- **Timeout or excessive output:** the invocation fails after its deadline or 8 MiB of combined stdout/stderr. Owned Codex/MCP process groups are terminated and killed if necessary, including descendants of an exited leader. Ctrl-C and SIGTERM also unwind the driver and run cleanup. Mock processes and temporary certificates/credentials are removed on normal completion and setup failures.

Authenticated local results and OCI execution results are separate evidence. Local mock-backed success does not establish a live OCI integration or an OCI-hosted run.

----
<small>Copyright (c) 2025, 2026, Oracle and/or its affiliates. Licensed under the [Universal Permissive License v1.0](https://oss.oracle.com/licenses/upl).</small>
