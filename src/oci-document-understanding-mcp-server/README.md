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

For real OCI calls, the server uses `oracle-mcp-common` to resolve OCI SDK
authentication. Set `OCI_MCP_AUTH_TYPE` when you need a specific mode:

- `security_token`
- `api_key`
- `instance_principal`
- `resource_principal`
- `instance_principal_delegation`
- `resource_principal_delegation`
- `oke_workload_identity`
- `identity_domain_upst`

When `OCI_MCP_AUTH_TYPE` is unset, the common library's `auto` mode uses a
security token only when the selected OCI profile directly declares
`security_token_file`; otherwise it uses API-key authentication. Principal
authentication modes must be selected explicitly.

`DOCUMENT_MCP_MODE` selects the provider, not the authentication mode:

| `DOCUMENT_MCP_MODE` | Description |
| --- | --- |
| `oci` (default) | Real OCI Document Understanding SDK provider. |
| `stub` | Deterministic fake provider for local MCP flow testing. |

For local session-token authentication, run:

```sh
oci session authenticate --profile-name DEFAULT --region us-phoenix-1
```

The selected OCI config profile must contain `security_token_file` and the
matching session `key_file`.

## Configuration

| Environment Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DOCUMENT_MCP_MODE` | No | `oci` | Provider mode: `oci` or `stub`. |
| `OCI_MCP_AUTH_TYPE` | No | `auto` | OCI authentication type, resolved by `oracle-mcp-common`. |
| `OCI_REGION` | Depends on auth type | Profile or signer region | OCI region, resolved by `oracle-mcp-common`. |
| `OCI_COMPARTMENT_ID` | Yes for non-stub OCI calls | None | Default compartment OCID for Document Understanding requests. |
| `OCI_CONFIG_PROFILE` | No | `DEFAULT` | OCI config profile, resolved by `oracle-mcp-common`. |
| `OCI_CONFIG_FILE` | No | OCI SDK default | OCI config file, resolved by `oracle-mcp-common`. |

`OCI_REGION`, when set, takes precedence over the region in an OCI config
profile. Otherwise, profile authentication uses the profile region and
principal authentication uses the signer region. The OCI SDK derives the
official Document Understanding endpoint from that resolved region.

Session-token authentication with the default OCI profile:

```sh
OCI_MCP_AUTH_TYPE=security_token \
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..example \
uv run oracle.oci-document-understanding-mcp-server
```

Instance-principal authentication:

```sh
OCI_MCP_AUTH_TYPE=instance_principal \
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..example \
uv run oracle.oci-document-understanding-mcp-server
```

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

Set `include_confidence` to `false` to omit confidence fields from extraction
results.

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
DOCUMENT_MCP_MODE=stub uv run oracle.oci-document-understanding-mcp-server
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
