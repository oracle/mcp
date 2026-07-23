# OCI Document Understanding MCP Server

## Overview

This FastMCP-based server provides MCP tools for OCI Document Understanding
extraction and classification workflows.

It supports stdio transport only. It does not expose HTTP, streamable HTTP,
OAuth, IDCS bearer-token validation, `/mcp`, or `/.well-known/*` endpoints.

## Running the Server

### STDIO Transport Mode

```sh
uvx oracle.oci-document-understanding-mcp-server
```

For local source testing:

```sh
uv run oracle.oci-document-understanding-mcp-server
```

For local wheel testing:

```sh
uvx \
  --python 3.13 \
  --no-python-downloads \
  --from ./dist/oracle_oci_document_understanding_mcp_server-0.1.0-py3-none-any.whl \
  oracle.oci-document-understanding-mcp-server
```

## Authentication

The server supports OCI SDK authentication modes through `OCI_AUTH_MODE`.

Supported values:

- `session-token`
- `api-key`
- `instance-principal`
- `none`

`none` is only for `DOCUMENT_MCP_MODE=stub`, which uses a deterministic fake
provider and does not call OCI.

`DOCUMENT_MCP_MODE` controls the default auth mode:

| `DOCUMENT_MCP_MODE` | Default `OCI_AUTH_MODE` | Description |
| --- | --- | --- |
| `stub` | `none` | Local MCP flow testing without OCI calls. |
| `local` | `session-token` | Local OCI config profile with session-token auth. |
| `prod` | `instance-principal` | OCI Compute instance principal auth. |

For local session-token authentication, run:

```sh
oci session authenticate --profile-name DEFAULT --region us-phoenix-1
```

The selected OCI config profile must contain `security_token_file` and the
matching session `key_file`.

## Configuration

| Environment Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DOCUMENT_MCP_MODE` | No | `local` | Runtime mode: `stub`, `local`, or `prod`. |
| `OCI_AUTH_MODE` | No | Derived from `DOCUMENT_MCP_MODE` | OCI auth mode: `session-token`, `api-key`, `instance-principal`, or `none`. |
| `OCI_REGION` | No | `us-ashburn-1` | OCI region used for Document Understanding requests. |
| `OCI_COMPARTMENT_ID` | Yes for non-stub OCI calls | None | Default compartment OCID for Document Understanding requests. |
| `OCI_CONFIG_PROFILE` | No | `DEFAULT` | OCI config profile name. |
| `OCI_CONFIG_FILE` | No | OCI SDK default | OCI config file path. |
| `OCI_DOCUMENT_ENDPOINT` | No | None | Optional Document Understanding endpoint override. |

## Tools

| Tool Name | Description |
| --- | --- |
| `document_extract` | Extract text, key-value pairs, tables, and document elements from an inline base64 or Object Storage document. |
| `document_classify` | Classify an inline base64 or Object Storage document and return candidate document classes. |

## Input Sources

Inline base64 input:

```json
{
  "document": "<base64-document>",
  "mime_type": "application/pdf",
  "features": ["TEXT", "KEY_VALUE"],
  "options": {
    "language": "en",
    "include_confidence": true
  }
}
```

Object Storage input:

```json
{
  "document_source": {
    "source_type": "OBJECT_STORAGE",
    "namespace_name": "my_namespace",
    "bucket_name": "my_bucket",
    "object_name": "documents/invoice.pdf"
  },
  "features": ["TEXT", "KEY_VALUE", "TABLE"],
  "options": {
    "language": "en",
    "include_confidence": true
  }
}
```

Classification input:

```json
{
  "document": "<base64-document>",
  "mime_type": "application/pdf",
  "document_type_hint": "invoice",
  "options": {
    "language": "en",
    "confidence_threshold": 0.2
  }
}
```

## Local Stub Mode

Stub mode validates MCP flow without OCI credentials:

```sh
DOCUMENT_MCP_MODE=stub \
OCI_AUTH_MODE=none \
uv run oracle.oci-document-understanding-mcp-server
```

Use the development test command below for local validation. MCP clients can run
the server with the package entry point shown in the running examples above.

## Project Layout

```text
oci-document-understanding-mcp-server/
├── LICENSE.txt
├── CHANGELOG.md
├── README.md
├── pyproject.toml
├── uv.lock
└── oracle/
    ├── __init__.py
    └── oci_document_understanding_mcp_server/
        ├── __init__.py
        ├── server.py
        ├── handlers/
        ├── oci/
        ├── parsers/
        ├── response.py
        └── tests/
```

## Development

```sh
uv sync --locked --all-extras --dev
uv run pytest --cov=. --cov-branch --cov-report=term-missing
uv build
```

The package entry point is:

```toml
[project.scripts]
"oracle.oci-document-understanding-mcp-server" = "oracle.oci_document_understanding_mcp_server.server:main"
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
