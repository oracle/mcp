# OCI Vision MCP Server

## Overview

This server provides MCP tools for OCI Vision image analysis and related Object
Storage image workflows.

It supports stdio transport only. It does not expose HTTP, streamable HTTP,
OAuth, IDCS bearer-token validation, `/mcp`, or `/.well-known/*` endpoints.

## Running the Server

### STDIO Transport Mode

```sh
uvx oracle.oci-vision-mcp-server
```

For local wheel testing:

```sh
uvx \
  --python 3.13 \
  --no-python-downloads \
  --from ./dist/oracle_oci_vision_mcp_server-0.1.0-py3-none-any.whl \
  oracle.oci-vision-mcp-server
```

## Authentication

The server uses OCI CLI-compatible session-token authentication. Run
`oci session authenticate` to create or refresh a session profile; that profile
contains both `security_token_file` and the matching session `key_file`. The
server requires those session-profile entries and does not support API-key-only
profiles, instance principals, resource principals, IDCS bearer tokens, or
OAuth.

Set the profile and region through environment variables:

```sh
OCI_CONFIG_PROFILE=DEFAULT
OCI_REGION=us-phoenix-1
OCI_VISION_DEFAULT_COMPARTMENT_ID=ocid1.compartment.oc1..example
```

If the session token is missing or expired, refresh it with:

```sh
oci session authenticate --profile-name DEFAULT --region us-phoenix-1
```

Automatic browser-based authentication is disabled by default. To opt in for
local interactive use, set `OCI_MCP_AUTO_AUTH=true`.

## Tools

| Tool Name | Description |
| --- | --- |
| `analyze_image` | Run one combined OCI Vision request with one or more image-analysis features. |
| `parallel_analyze_image` | Run multiple analyze-image calls concurrently and return ordered direct results. |
| `classify_image` | Backward-compatible Vision image analysis tool. Prefer `detect_objects` for new object-detection use cases. |
| `detect_objects` | Detect objects in an image and optionally include bounding boxes. |
| `detect_faces` | Detect faces in an image without identifying people. |
| `detect_text` | Run OCR on an image. |
| `create_image_job` | Create an async OCI Vision image job for Object Storage inputs. |
| `get_image_job` | Get lifecycle state and metadata for an OCI Vision image job. |
| `cancel_image_job` | Cancel an OCI Vision image job when explicitly confirmed. |
| `upload_image_to_object_storage` | Upload a local/base64 image to OCI Object Storage. |
| `list_object_storage_objects` | List Object Storage objects for batch or async Vision workflows. |
| `fetch_object_storage_object` | Download one or more Object Storage objects to local files. |
| `get_analysis_result` | Read a stored raw OCI result by MCP request id. |
| `get_config_status` | Return resolved runtime configuration status. |

## Configuration

| Environment Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `OCI_CONFIG_PROFILE` | No | `DEFAULT` | OCI config profile to use. |
| `OCI_REGION` | No | Profile region | OCI region override. |
| `OCI_VISION_DEFAULT_COMPARTMENT_ID` | Yes for Vision tools unless passed in the tool input | None | Default compartment OCID for Vision requests. |
| `MCP_IMAGE_BASE_DIR` | No | Current working directory | Base directory used to validate local `file_path` image inputs. |
| `OCI_VISION_RESULT_STORE_DIR` | No | `~/.oci-vision-mcp/results` | Directory for raw OCI result metadata. |
| `OCI_VISION_LOG_DIR` | No | `~/.oci-vision-mcp/logs` | Directory reserved for MCP diagnostic logs. |
| `OCI_MCP_AUTO_AUTH` | No | `false` | Opt-in browser-based session authentication. |
| `OCI_MCP_REFRESH_SESSION` | No | `true` | Retry once after refreshing an expired session token. |
| `OCI_SESSION_AUTH_COMMAND` | No | `oci` | Executable used for `oci session authenticate`. |
| `OCI_OBJECT_STORAGE_NAMESPACE` | No | None | Default namespace for Object Storage tools and image-job output. |
| `OCI_OBJECT_STORAGE_BUCKET` | No | None | Default bucket for Object Storage tools and image-job output. |
| `OCI_OBJECT_STORAGE_DOWNLOAD_DIR` | No | `~/.oci-vision-mcp/obj_results` | Local directory used by `fetch_object_storage_object`. |
| `OCI_VISION_ENABLE_URL_INPUTS` | No | `false` | Enables direct HTTPS image URL inputs when explicitly opted in. |
| `OCI_VISION_JOB_OUTPUT_NAMESPACE` | No | Object Storage namespace default | Default async image-job output namespace. |
| `OCI_VISION_JOB_OUTPUT_BUCKET` | No | Object Storage bucket default | Default async image-job output bucket. |

## Client Examples

Codex:

```toml
[mcp_servers.oci_vision_mcp]
command = "uvx"
args = [
  "--python", "3.13",
  "--no-python-downloads",
  "--from", "/absolute/path/to/oci-vision-mcp/dist/oracle_oci_vision_mcp_server-0.1.0-py3-none-any.whl",
  "oracle.oci-vision-mcp-server"
]
startup_timeout_sec = 300
tool_timeout_sec = 300
enabled = true

[mcp_servers.oci_vision_mcp.env]
OCI_CONFIG_PROFILE = "DEFAULT"
OCI_REGION = "us-phoenix-1"
OCI_VISION_DEFAULT_COMPARTMENT_ID = "ocid1.compartment.oc1..example"
MCP_IMAGE_BASE_DIR = "/absolute/path/to/oci-vision-mcp"
```

## Project Layout

```text
oci-vision-mcp-server/
├── LICENSE.txt
├── CHANGELOG.md
├── Containerfile
├── README.md
├── pyproject.toml
├── uv.lock
└── oracle/
    ├── __init__.py
    └── oci_vision_mcp_server/
        ├── __init__.py
        ├── server.py
        ├── authentication/
        ├── config/
        ├── io/
        ├── observability/
        ├── oci_clients/
        ├── oci_mapper/
        ├── prompts/
        ├── responses/
        ├── runtime/
        ├── tools/
        └── tests/
```

## Development

```sh
uv sync
uv run pytest --cov=. --cov-branch --cov-report=term-missing
uv build
```

The package entry point is:

```toml
[project.scripts]
"oracle.oci-vision-mcp-server" = "oracle.oci_vision_mcp_server.server:main"
```

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are
responsible for obtaining and providing all required licenses and copyright
notices for third-party code used in order to ensure compliance with their
respective open source licenses.

## Disclaimer

Users are responsible for their local environment, OCI permissions, and
credential safety. Different language model selections may yield different
results and performance.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
