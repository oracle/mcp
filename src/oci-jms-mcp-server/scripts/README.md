# JMS Script Utilities

This folder contains temporary local utilities for manual JMS MCP testing.

## `test_jms_mcp_client.py`

This is a temporary manual validation client for the JMS MCP server.
It connects to an already-running HTTP MCP server and exercises the 9 JMS tools.

Remove this script and this README before committing if you do not want local-only test utilities in the final change set.

### Prerequisites

- The JMS MCP server must already be running over HTTP.
- Default target URL: `http://127.0.0.1:8888/mcp`
- The repo virtualenv should exist at `../../.venv` when run from `src/oci-jms-mcp-server`

### Run All 9 Tools

From the JMS package directory:

```sh
cd src/oci-jms-mcp-server
../../.venv/bin/python scripts/test_jms_mcp_client.py
```

### Run One Tool

```sh
../../.venv/bin/python scripts/test_jms_mcp_client.py --tool list_fleets
```

### Override Inputs

```sh
../../.venv/bin/python scripts/test_jms_mcp_client.py \
  --url http://127.0.0.1:8888/mcp \
  --compartment-id ocid1.compartment.oc1..aaaaaaaamfgnvfzwcbbhn7ktlulig2whera32rwrvvmfkkx3svic4geffgxq \
  --fleet-id ocid1.jmsfleet.oc1.iad.amaaaaaa6cijguiayfvn2rk5i3ue5cwd67ru4h3gnalej6dqievm233hytla \
  --limit 10 \
  --timeout 20
```

### Output

The script prints:

- discovered tool names
- `PASS` / `FAIL` / `TIMEOUT` / `SKIPPED` for each tool
- a final summary line with pass/fail counts

### Supported Options

- `--url`
- `--compartment-id`
- `--fleet-id`
- `--limit`
- `--timeout`
- `--tool`
