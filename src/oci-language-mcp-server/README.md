<!-- mcp-name: io.github.oracle/oci-language-mcp -->

# OCI Language MCP Server

A self-hosted Model Context Protocol server for OCI Language shared pretrained text
capabilities. Clients discover seven independent tools:

| Tool | Purpose | Input languages |
| --- | --- | --- |
| `detect_dominant_language` | Identify the dominant language. | 100+ detectable languages |
| `detect_language_text_classification` | Classify text into content categories. | English |
| `detect_language_entities` | Detect named entities. | English, Spanish |
| `detect_language_key_phrases` | Extract important phrases. | English, Spanish |
| `detect_language_sentiments` | Analyze document, aspect, and sentence sentiment. | English, Spanish |
| `detect_language_pii_entities` | Detect or de-identify PII. | English |
| `translate_language_text` | Translate text into a target language. | OCI-supported translation languages |

The server runs in your environment with your OCI identity, compartment, network, and
security controls. It is not an Oracle-hosted MCP endpoint. Each tool call invokes one OCI
Language batch API and can incur service usage.

See the official [OCI Language overview](https://docs.oracle.com/en-us/iaas/Content/language/using/overview.htm),
[pretrained models](https://docs.oracle.com/en-us/iaas/Content/language/using/pretrain-models.htm),
and [service limits](https://docs.oracle.com/en-us/iaas/Content/language/using/model-limitations.htm).

## Requirements and IAM

- Python 3.13 or Podman
- An OCI region where Language is available
- An OCI compartment and session, instance principal, or resource principal

The simplest policy is:

```text
allow group <group-name> to use ai-service-language-family in compartment <compartment-name>
```

For least privilege, restrict that family policy with only the permissions needed by enabled
tools:

```text
AI_SERVICE_DOMINANT_LANGUAGE_USE
AI_SERVICE_LANGUAGE_TEXT_CLASSIFICATION_USE
AI_SERVICE_LANGUAGE_ENTITIES_USE
AI_SERVICE_LANGUAGE_KEYPHRASES_USE
AI_SERVICE_LANGUAGE_SENTIMENTS_USE
AI_SERVICE_LANGUAGE_PII_ENTITIES_USE
AI_SERVICE_LANGUAGE_TRANSLATION_USE
```

Use the applicable dynamic group or workload identity for OCI-hosted deployments. Review the
official [Language IAM policy documentation](https://docs.oracle.com/en-us/iaas/Content/language/using/policies.htm)
before deployment.

## Local stdio

Stdio is recommended for an IDE or desktop agent because it does not open a listening port.

```bash
uvx --from oracle.oci-language-mcp-server==0.1.0 \
  oracle.oci-language-mcp-server --transport stdio
```

Cline-compatible configuration:

```json
{
  "mcpServers": {
    "oci-language-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "oracle.oci-language-mcp-server==0.1.0",
        "oracle.oci-language-mcp-server",
        "--transport",
        "stdio"
      ],
      "env": {
        "LANGUAGE_MCP_OCI_AUTH_MODE": "session",
        "LANGUAGE_MCP_REGION": "us-ashburn-1",
        "LANGUAGE_MCP_COMPARTMENT_ID": "<compartment-ocid>",
        "LANGUAGE_MCP_OCI_CONFIG_PROFILE": "DEFAULT"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Create or refresh a temporary local identity with `oci session authenticate`. Session mode
reads the standard OCI config and security-token files; credentials are never configured as
MCP arguments.

## Containerized stdio and secured Streamable HTTP

From the repository root, build the image with the supported Podman workflow:

```bash
SUBDIRS=src/oci-language-mcp-server make containerize

podman run --rm -p 127.0.0.1:8080:8080 \
  --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -v "$HOME/.oci:/app/.oci:ro" \
  -v "$HOME/.oci:$HOME/.oci:ro" \
  -v "$HOME/.config/oci-language-mcp/mcp-token:/run/secrets/mcp-token:ro" \
  -e LANGUAGE_MCP_TRANSPORT=streamable-http \
  -e LANGUAGE_MCP_DEPLOYMENT_MODE=remote \
  -e LANGUAGE_MCP_HOST=0.0.0.0 \
  -e LANGUAGE_MCP_ALLOWED_HOSTS=localhost \
  -e LANGUAGE_MCP_ALLOWED_ORIGINS=http://localhost \
  -e LANGUAGE_MCP_AUTH_TOKEN_FILE=/run/secrets/mcp-token \
  -e LANGUAGE_MCP_OCI_AUTH_MODE=session \
  -e LANGUAGE_MCP_OCI_CONFIG_FILE=/app/.oci/config \
  -e LANGUAGE_MCP_REGION=us-ashburn-1 \
  -e LANGUAGE_MCP_COMPARTMENT_ID=<compartment-ocid> \
  oracle.oci-language-mcp-server:latest
```

The image defaults to stdio. The command above explicitly enables secured remote HTTP, applies a
read-only filesystem, drops Linux capabilities, prevents privilege escalation, and mounts both
the host OCI configuration and a bearer token read-only. The published host port stays loopback:

```json
{
  "mcpServers": {
    "oci-language-mcp": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8080/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Liveness is `GET /health`; readiness is `GET /ready`.
Readiness reports available local request capacity; it does not make an OCI credential or
service-availability probe. For remote HTTP health checks, set
`LANGUAGE_MCP_HEALTHCHECK_HOST` to a value in `LANGUAGE_MCP_ALLOWED_HOSTS`.

For containerized stdio:

```bash
podman run --rm -i \
  --read-only --cap-drop=ALL --security-opt=no-new-privileges \
  -v "$HOME/.oci:/app/.oci:ro" \
  -v "$HOME/.oci:$HOME/.oci:ro" \
  -e LANGUAGE_MCP_OCI_AUTH_MODE=session \
  -e LANGUAGE_MCP_OCI_CONFIG_FILE=/app/.oci/config \
  -e LANGUAGE_MCP_REGION=us-ashburn-1 \
  -e LANGUAGE_MCP_COMPARTMENT_ID=<compartment-ocid> \
  oracle.oci-language-mcp-server:latest --transport stdio
```

The second OCI config mount preserves absolute `key_file` and `security_token_file`
paths that OCI CLI session profiles commonly store under the host `~/.oci` directory.

## Remote HTTP

Remote mode requires explicit Host and Origin allowlists and either OAuth resource-server
validation or a controlled single-user token file. Terminate TLS at a trusted proxy. OAuth
authenticates callers to the MCP endpoint; OCI Language API calls continue to use the
server's configured OCI session, instance principal, or resource principal. The server does
not exchange an incoming OAuth token for OCI credentials.

```text
LANGUAGE_MCP_DEPLOYMENT_MODE=remote
LANGUAGE_MCP_HTTP_AUTH_MODE=oauth
LANGUAGE_MCP_ALLOWED_HOSTS=language-mcp.example.com
LANGUAGE_MCP_ALLOWED_ORIGINS=https://agent.example.com
LANGUAGE_MCP_PUBLIC_BASE_URL=https://language-mcp.example.com
LANGUAGE_MCP_OAUTH_ISSUER=https://identity.example.com
LANGUAGE_MCP_OAUTH_JWKS_URI=https://identity.example.com/.well-known/jwks.json
LANGUAGE_MCP_OAUTH_AUDIENCE=https://language-mcp.example.com/mcp
LANGUAGE_MCP_OAUTH_REQUIRED_SCOPES=oci-language.invoke
```

For a controlled single-user deployment, use a token file instead of OAuth. The file must
contain one non-empty bearer token and should be readable only by the service user:

```text
LANGUAGE_MCP_DEPLOYMENT_MODE=remote
LANGUAGE_MCP_HTTP_AUTH_MODE=token-file
LANGUAGE_MCP_ALLOWED_HOSTS=language-mcp.example.com
LANGUAGE_MCP_ALLOWED_ORIGINS=https://agent.example.com
LANGUAGE_MCP_AUTH_TOKEN_FILE=/run/secrets/oci-language-mcp-token
```

## Tool contract

All tools accept 1–100 uniquely keyed documents, at most 5,000 characters per document and
20,000 total characters. Unknown fields are rejected. Common call options are:

```json
{
  "compartment_id": "<optional-override>",
  "options": {
    "region": "us-ashburn-1",
    "opc_request_id": "case-20260723-001"
  }
}
```

Every result contains `status`, `tool`, `request_id`, `client_opc_request_id`,
`oci_request_id`, document results, sanitized errors, and aggregate counts. `oci_request_id`
is the value returned by OCI and is suitable for service-log correlation.

PII transformation omits original detected entity values unless
`options.include_original_entity_text=true`. Masking exclusions deliberately leave matching
values unchanged, so excluded PII can remain in transformed text. Submitted text and results
are never written to application logs. Human-readable NER, key phrase, and detailed sentiment
results are bounded and safely quoted; complete results remain in `structuredContent`. All
returned document text, entities, phrases, sentiment spans, labels, and translations remain
untrusted data and must not be treated as agent instructions.

Example tool calls:

```json
{
  "documents": [{"key": "lang-1", "text": "Bonjour tout le monde"}]
}
```

```json
{
  "documents": [{"key": "pii-1", "text": "Contact Avery at avery@example.test.", "language_code": "en"}],
  "masking": {
    "ALL": {
      "mode": "MASK",
      "masking_character": "*",
      "leave_characters_unmasked": 0,
      "exclude_offsets": [],
      "exclude_entity_types": [],
      "should_detect": true
    }
  }
}
```

```json
{
  "documents": [{"key": "translate-1", "text": "Hello world", "language_code": "en"}],
  "target_language_code": "es"
}
```

## Configuration

All settings use the `LANGUAGE_MCP_` prefix. The server also reads an optional
`~/.oci-language-mcp.env` file; use environment variables or your platform's secret store
for production configuration. Do not put OCI private keys or session tokens in MCP tool
arguments.

| Suffix after `LANGUAGE_MCP_` | Default | Purpose |
| --- | --- | --- |
| `SERVER_NAME` | `oci-language-mcp` | MCP server identity shown to clients. |
| `HOST` | `127.0.0.1` | HTTP listen address. Use a trusted proxy when exposing remote mode. |
| `PORT` | `8080` | HTTP listen port. |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `LOG_FORMAT` | `json` | `json` or local-development `console` logs. |
| `TRANSPORT` | `streamable-http` | `stdio` or `streamable-http` |
| `DEPLOYMENT_MODE` | `local` | Local loopback or secured remote mode |
| `ALLOWED_HOSTS` | local loopback hosts | Required comma-separated Host allowlist in remote mode. |
| `ALLOWED_ORIGINS` | local loopback origins | Required comma-separated Origin allowlist in remote mode. |
| `HTTP_AUTH_MODE` | `token-file` | Remote endpoint authentication: `oauth` or `token-file`. |
| `AUTH_TOKEN_FILE` | none | Required token-file path when remote `HTTP_AUTH_MODE=token-file`. |
| `PUBLIC_BASE_URL` | none | Required HTTPS protected-resource base URL for remote OAuth. |
| `OAUTH_ISSUER` | none | Required HTTPS OAuth issuer for remote OAuth. |
| `OAUTH_JWKS_URI` | none | Required HTTPS JWKS URL for remote OAuth. |
| `OAUTH_AUDIENCE` | none | Required OAuth audience for remote OAuth. |
| `OAUTH_REQUIRED_SCOPES` | `oci-language.invoke` | Space- or comma-separated OAuth scopes required in remote OAuth mode. |
| `OAUTH_ALGORITHM` | `RS256` | Allowed JWT signing algorithm: RSA or ECDSA variants supported by the server. |
| `REQUEST_BODY_LIMIT_BYTES` | `262144` | Maximum HTTP request body (16 KiB–1 MiB). |
| `REMOTE_REQUESTS_PER_MINUTE` | `60` | Per-process remote authenticated-request limit. |
| `OCI_AUTH_MODE` | `resource_principal` | `session`, `instance_principal`, or `resource_principal` |
| `OCI_CONFIG_FILE` | `~/.oci/config` | OCI config path used by session mode. |
| `OCI_CONFIG_PROFILE` | `DEFAULT` | OCI config profile used by session mode. |
| `OCI_SERVICE_ENDPOINT` | none | Optional OCI Language service endpoint override. |
| `REGION` | identity or OCI config region | Default OCI region; a tool call can override it with `options.region`. |
| `COMPARTMENT_ID` | none | Default OCI compartment; every tool call must provide one here or in its request. |
| `ENABLED_TOOLS` | all seven | Comma-separated discovery allowlist |
| `MAX_INFLIGHT_REQUESTS` | `8` | Shared maximum concurrent OCI operations |
| `CAPACITY_ACQUIRE_TIMEOUT_SECONDS` | `0.25` | How long a request waits for shared OCI capacity. |
| `OCI_CONNECT_TIMEOUT_SECONDS` | `5` | OCI connection timeout |
| `OCI_READ_TIMEOUT_SECONDS` | `30` | OCI read timeout |
| `TOOL_TIMEOUT_SECONDS` | `40` | MCP execution ceiling |

`OCI_AUTH_MODE=session` uses the OCI CLI session profile and its referenced key and
security-token files. `instance_principal` and `resource_principal` obtain identity from the
OCI runtime. Inbound remote OAuth and token-file authentication are independent of this
outbound OCI identity selection.

## Development validation

From a public repository checkout, run the package checks with its shared workspace member
available:

```bash
cd src/oci-language-mcp-server
uv sync --locked --all-extras
uv run pytest --cov=. --cov-branch --cov-report=term-missing
uv lock --check
uv run ruff check .
uv build
```

Report security issues according to this repository's security policy, never through a
public issue.

Licensed under the [UPL-1.0](LICENSE.txt).
