# OCI Full Stack Disaster Recovery MCP Server

An MCP server that exposes Oracle Cloud Infrastructure (OCI) Full Stack Disaster Recovery
(FSDR) operations as tools for MCP-aware clients.

FSDR uses two regions (primary and standby). This server supports both via named OCI config
profiles — `FSDR_REGION1` and `FSDR_REGION2` by default. Every tool accepts a `profile`
parameter to target the desired region.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) installed (`brew install uv` on macOS)
- OCI config at `~/.oci/config` with profiles `[FSDR_REGION1]` and `[FSDR_REGION2]`

### OCI Config Example (`~/.oci/config`)

```ini
[FSDR_REGION1]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:...
tenancy=ocid1.tenancy.oc1..xxxxxx
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem

[FSDR_REGION2]
user=ocid1.user.oc1..xxxxxx
fingerprint=xx:xx:xx:...
tenancy=ocid1.tenancy.oc1..xxxxxx
region=us-phoenix-1
key_file=~/.oci/oci_api_key.pem
```

## Installation & Running

### Using uvx (recommended)

```bash
uvx --from /path/to/oci-fsdr-mcp oracle.oci-fsdr-mcp-server
```

### Using uv (development)

```bash
cd oci-fsdr-mcp
uv sync
uv run oracle.oci-fsdr-mcp-server
```

### Using pip (legacy)

```bash
pip install -e .
oracle.oci-fsdr-mcp-server
```

The legacy `oci-fsdr-mcp` console command remains available for existing local
client configurations, but new configurations should use
`oracle.oci-fsdr-mcp-server`.

## MCP Client Configuration

Use the following server configuration in any MCP-aware client that supports
stdio servers:

```json
{
  "mcpServers": {
    "oci-fsdr": {
      "command": "uvx",
      "args": ["--from", "/path/to/oci-fsdr-mcp", "oracle.oci-fsdr-mcp-server"],
      "env": {
        "FSDR_PROFILE_1": "FSDR_REGION1",
        "FSDR_PROFILE_2": "FSDR_REGION2"
      }
    }
  }
}
```

> **Note:** Replace `/path/to/oci-fsdr-mcp` with the absolute path to your local clone,
> e.g. `/Users/yourname/Documents/oci-fsdr-mcp`.

This server uses MCP over stdio. Run it from an MCP client for normal use.
If you start it directly in a terminal, it waits for JSON-RPC messages on stdin;
arbitrary keystrokes or blank lines will be reported as invalid JSON.

### Environment Variables

| Variable          | Default        | Description                                      |
|-------------------|----------------|--------------------------------------------------|
| `OCI_CONFIG_FILE` | `~/.oci/config`| Path to OCI config file                          |
| `FSDR_PROFILE_1`  | `FSDR_REGION1` | OCI config profile for region 1 (primary)        |
| `FSDR_PROFILE_2`  | `FSDR_REGION2` | OCI config profile for region 2 (standby)        |

To use custom profile names:

```bash
FSDR_PROFILE_1=MY_PRIMARY FSDR_PROFILE_2=MY_STANDBY uvx --from . oracle.oci-fsdr-mcp-server
```

OCI profiles are validated when the server first creates a client for the
requested profile. A missing or misconfigured profile causes that tool call to
fail with the OCI SDK configuration error.

---

## Tools

All tools accept an optional `profile` parameter (default: `FSDR_REGION1`).
Pass `profile="FSDR_REGION2"` to target the standby region.

### Read Operations

| Tool | Description |
|------|-------------|
| `list_dr_protection_groups` | List DRPGs in a compartment. Requires `compartment_id`. |
| `list_dr_plans_for_protection_group` | List DR Plans for a DRPG. Requires `dr_protection_group_id`. |
| `list_dr_plan_executions_for_protection_group` | List DR Plan Executions for a DRPG. Requires `dr_protection_group_id`. |
| `get_dr_protection_group` | Get details of a DRPG. Requires `dr_protection_group_id`. |
| `get_dr_plan` | Get details of a DR Plan. Requires `dr_plan_id`. |
| `get_dr_plan_execution` | Get details of a DR Plan Execution. Requires `dr_plan_execution_id`. |
| `get_work_request` | Get details of a Work Request. Requires `work_request_id`. |

### Write Operations

All mutations go through a single generic tool:

| Tool | Description |
|------|-------------|
| `fsdr_raw_call` | Invoke any `DisasterRecoveryClient` method by name. Accepts `operation`, `parameters`, and `profile`. |

This keeps the server schema-agnostic — new member types, plan execution
types, or FSDR APIs never require server changes. Callers describe
polymorphic payloads with a `_type` discriminator naming the exact OCI SDK
model class; see the tool docstring and the guided prompts for examples.

### Important: `fsdr_raw_call` behavior and precautions

`fsdr_raw_call` is the server's generic **write / mutation** interface.
It can call any OCI Python SDK `DisasterRecoveryClient` operation by exact
method name, including operations such as:

- `create_dr_protection_group`
- `associate_dr_protection_group`
- `update_dr_protection_group`
- `create_dr_plan`
- `create_dr_plan_execution`

`fsdr_raw_call` executes immediately — there is **no built-in preview mode,
dry run, or confirmation prompt inside the MCP server**.

If you see a confirmation dialog before the call runs, that comes from your
MCP client, **not** from this server.

Before invoking `fsdr_raw_call`, users should:

1. **Confirm the target region/profile**
   - `FSDR_REGION1` and `FSDR_REGION2` can point to different OCI regions.
   - A valid payload sent to the wrong profile can modify the wrong region.

2. **Verify the exact OCI operation name**
   - `operation` must be the exact `DisasterRecoveryClient` SDK method name.
   - Double-check whether the call creates, updates, associates, disassociates,
     deletes, or executes a DR workflow.

3. **Review the full payload before execution**
   - Validate OCIDs, display names, peer IDs, peer region values, plan type,
     and execution options.
   - For polymorphic payloads, ensure `_type` matches the exact OCI SDK model
     class name.

4. **Check existing state first using read tools**
   - Prefer reading first with:
     - `list_dr_protection_groups`
     - `get_dr_protection_group`
     - `list_dr_plans_for_protection_group`
     - `get_dr_plan`
     - `list_dr_plan_executions_for_protection_group`
     - `get_dr_plan_execution`
     - `get_work_request`

5. **Be careful with member updates**
   - `update_dr_protection_group` member updates typically replace the full
     members list.
   - Fetch current members first and merge intentionally, otherwise existing
     members may be removed unintentionally.

6. **Treat plan execution as a live action**
   - Creating a DR plan execution can start a switchover, failover, or drill.
   - These are operational changes, not informational queries.

7. **Track work requests after write operations**
   - Many OCI write operations are asynchronous.
   - Use `get_work_request` and the DR plan/drill execution read tools to
     confirm the final result.

The bundled prompts (`setup_drpg_pair`, `run_switchover`, `run_failover`,
`run_drill`, `plan_refresh_workflow`, `add_members`) are intended to guide
clients and users through safer, confirmation-oriented workflows before they
invoke `fsdr_raw_call`.

---

## Project Layout

```text
oci-fsdr-mcp/
├── LICENSE.txt
├── CONTRIBUTING.md
├── pyproject.toml
├── README.md
├── uv.lock
└── oracle/
    └── oci_fsdr_mcp_server/
        ├── auth.py
        ├── consts.py
        ├── models.py
        ├── server.py
        └── data/
```

The server entry point is `oracle/oci_fsdr_mcp_server/server.py`, exposed as
the `oracle.oci-fsdr-mcp-server` console script.

## Development

```bash
uv sync --extra dev
uv run pytest
```

Contributions must follow the Oracle Contributor Agreement process described
in [CONTRIBUTING.md](CONTRIBUTING.md). Source files include the UPL header, and
tool parameters use Pydantic `Field` metadata so MCP clients receive clear
schemas.

---

## Typical Two-Region Workflow

```
# 1. Create PRIMARY DRPG in region 1
fsdr_raw_call(
  operation="create_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={
    "create_dr_protection_group_details": {
      "compartment_id": "<ocid>",
      "display_name": "Primary DRPG",
      "log_location": {
        "_type": "CreateObjectStorageLogLocationDetails",
        "bucket": "<bucket>",
        "namespace": "<ns>"
      }
    }
  }
)

# 2. Create STANDBY DRPG in region 2 (same shape, profile="FSDR_REGION2")

# 3. Associate them (call from the primary region)
fsdr_raw_call(
  operation="associate_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={
    "dr_protection_group_id": "<region1-ocid>",
    "associate_dr_protection_group_details": {
      "peer_id": "<region2-ocid>",
      "peer_region": "us-phoenix-1",
      "role": "PRIMARY"
    }
  }
)

# 4. Add members (replaces full member list — fetch current, merge, then update)
fsdr_raw_call(
  operation="update_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={
    "dr_protection_group_id": "<region1-ocid>",
    "update_dr_protection_group_details": {
      "members": [
        {"_type": "UpdateDrProtectionGroupMemberDatabaseDetails",
         "member_id": "ocid1.dbsystem..."}
      ]
    }
  }
)

# 5. Create a switchover plan on the PRIMARY DRPG
fsdr_raw_call(
  operation="create_dr_plan",
  profile="FSDR_REGION1",
  parameters={
    "create_dr_plan_details": {
      "dr_protection_group_id": "<region1-ocid>",
      "display_name": "Switchover Plan",
      "type": "SWITCHOVER"
    }
  }
)

# 6. Execute the plan
fsdr_raw_call(
  operation="create_dr_plan_execution",
  profile="FSDR_REGION1",
  parameters={
    "create_dr_plan_execution_details": {
      "plan_id": "<plan-ocid>",
      "display_name": "Switchover Run 1",
      "execution_options": {
        "_type": "SwitchoverExecutionOptionDetails",
        "are_prechecks_enabled": true,
        "are_warnings_ignored": false
      }
    }
  }
)
```
