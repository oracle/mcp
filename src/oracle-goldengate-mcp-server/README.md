# Oracle GoldenGate MCP Server

## Overview

This server provides tools to interact with Oracle GoldenGate deployments through the GoldenGate Administration REST APIs.
It includes tools for administration, process lifecycle management, and operational monitoring.

## Running the server

### 1) Obtain the code

1. Download ZIP
2. Extract ZIP and open `oracle-goldengate-mcp-server`.

If you are using Git (recommended to get updates and pull additional required files), you can clone/pull instead of relying only on ZIP downloads.

Clone:

```sh
git clone https://github.com/julientestut/mcp.git
cd mcp/src/oracle-goldengate-mcp-server
```

If you already cloned the repository, pull latest changes (including any newly added required files):

```sh
git pull --ff-only
```

To pull only this server folder from the repo root:

```sh
git sparse-checkout init --cone
git sparse-checkout set src/oracle-goldengate-mcp-server
git pull --ff-only
```

### 2) Install Python prerequisites with uv (Windows/Linux/macOS)

Install `uv` using Astral's installation guide:

- https://docs.astral.sh/uv/getting-started/installation/

Then install Python and create a virtual environment.

This repository includes a committed `uv.lock` file for reproducible dependency resolution.

Linux/macOS:

```sh
# Install a supported Python version (project requires >=3.10)
uv python install 3.12

# From the oracle-goldengate-mcp-server directory
uv venv --python 3.12
source .venv/bin/activate

# Install the package and dependencies
uv pip install -e .

# (Optional, recommended) Sync exactly to lockfile versions
uv sync --frozen
```

Windows (PowerShell):

```powershell
# Install a supported Python version (project requires >=3.10)
uv python install 3.12

# From the oracle-goldengate-mcp-server directory
uv venv --python 3.12
.\.venv\Scripts\Activate.ps1

# Install the package and dependencies
uv pip install -e .

# (Optional, recommended) Sync exactly to lockfile versions
uv sync --frozen
```

You can use `3.13` as well, but `3.12` is generally a safer default for compatibility.

### Dependency lockfile (`uv.lock`)

- `uv.lock` is committed and should be kept under version control.
- To refresh it after changing dependencies in `pyproject.toml`, run:

```sh
python -m uv lock
```

### 3) Configure env file

Copy template and fill values:

- `oracle-goldengate-mcp-server.env.example` → `oracle-goldengate-mcp-server.env`

### 4) Run the server

The MCP server entry point is:

- `oracle.oracle-goldengate-mcp-server`

Before starting, make sure your environment variables are loaded from:

- `oracle-goldengate-mcp-server.env`

using this template:

- `oracle-goldengate-mcp-server.env.example`

#### Windows (PowerShell)

```powershell
# From oracle-goldengate-mcp-server
.\.venv\Scripts\Activate.ps1
Get-Content .\oracle-goldengate-mcp-server.env | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -match '^\s*$') { return }
  $name, $value = $_ -split '=', 2
  [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
}
uv run oracle.oracle-goldengate-mcp-server
```

#### Windows (cmd.exe)

```bat
:: From oracle-goldengate-mcp-server
call .venv\Scripts\activate.bat
for /f "usebackq tokens=* delims=" %i in ("oracle-goldengate-mcp-server.env") do @echo %i| findstr /r "^[ ]*# ^[ ]*$" >nul || set %i
uv run oracle.oracle-goldengate-mcp-server
```

#### Linux / macOS (bash/zsh)

```sh
# From oracle-goldengate-mcp-server
source .venv/bin/activate
set -a
source ./oracle-goldengate-mcp-server.env
set +a
uv run oracle.oracle-goldengate-mcp-server
```

Notes:
- Transport is `stdio`.
- For troubleshooting, set `OGG_MCP_DEBUG=true`.

### Environment configuration

Copy `oracle-goldengate-mcp-server.env.example` to `oracle-goldengate-mcp-server.env` and set:

- `OGG_BASE_URL` (required)
- `OGG_USERNAME` (required for basic authentication)
- `OGG_MCP_DEBUG` (false by default, true to get more verbose logging)
- One password source (recommended order):
  1. `OGG_PASSWORD_SECRET_OCID`
  2. `OGG_PASSWORD_FILE`
  3. `OGG_PASSWORD`

If multiple password sources are provided, the server resolves them in the same order above.

Optional variables are also supported:
- `OCI_TENANCY_OCID` (required when using `OGG_PASSWORD_SECRET_OCID`)
- `OCI_USER_OCID` (required when using `OGG_PASSWORD_SECRET_OCID`)
- `OCI_KEY_FINGERPRINT` (required when using `OGG_PASSWORD_SECRET_OCID`)
- `OCI_PRIVATE_KEY_FILE` (required when using `OGG_PASSWORD_SECRET_OCID`)
- `OCI_PRIVATE_KEY_PASSPHRASE` (optional when using `OCI_PRIVATE_KEY_FILE`)
- `OCI_REGION` (required when using `OGG_PASSWORD_SECRET_OCID`)

## Tools

| Tool Name | Description |
| --- | --- |
| list_domains | Return the list of GoldenGate domains available in OCI GoldenGate deployment. |
| list_connections | Return the list of connections in a GoldenGate domain. |
| list_checkpoint_tables | Return checkpoint tables for a given domain/connection. |
| list_extracts | Return the list of Extract processes. |
| list_replicats | Return the list of Replicat processes. |
| list_distribution_paths | Return the list of Distribution Paths. |
| list_trails | Return the list of trails. |
| get_extract_status | Return the status of an Extract. |
| get_replicat_status | Return the status of a Replicat. |
| create_connection | Create a credential store alias/connection. |
| add_trandata_schema | Add TRANDATA at schema level for a given connection. |
| add_trandata_table | Add TRANDATA at table level for a given connection. |
| create_extract | Create an Extract. |
| update_extract | Update an Extract. |
| create_replicat | Create a Replicat. |
| update_replicat | Update a Replicat. |
| create_distribution_path | Create a Distribution Path. |
| create_data_stream | Create a GoldenGate Data Stream. |
| start | Start a GoldenGate process. |
| stop | Stop a GoldenGate process. |
| start_distribution_path | Start a Distribution Path. |
| stop_distribution_path | Stop a Distribution Path. |
| get_extract_lag | Retrieve Extract lag metrics. |
| get_replicat_lag | Retrieve Replicat lag metrics. |
| get_extract_report | Retrieve an Extract report. |
| get_replicat_report | Retrieve a Replicat report. |
| get_extract_stats | Retrieve Extract statistics. |
| get_replicat_stats | Retrieve Replicat statistics. |
| get_extract_details | Retrieve Extract details. |
| get_replicat_details | Retrieve Replicat details. |
| get_data_stream_info | Retrieve Data Stream metadata. |
| get_data_stream_yaml | Retrieve Data Stream AsyncAPI YAML definition. |

⚠️ **NOTE**: All actions are performed with the permissions of the configured credentials. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
