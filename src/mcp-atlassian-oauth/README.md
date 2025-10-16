# MCP Atlassian OAuth (Python)

An Atlassian MCP server that exposes secure, OAuth‑enabled tools and resource access for Jira and Confluence. Designed for local editor integration (stdio) as well as remote connections (HTTP) while keeping organization credentials and per‑user defaults clearly separated.

- Language: Python (>= 3.10)
- License: UPL-1.0
- Entry point: python -m mcp_atlassian_oauth
- Marketplace metadata: mcp.json (id: oracle.atlassian.oauth)
- Transports supported:
  - stdio (default) for local/editor spawn
  - HTTP (streamable) via POST /mcp (NDJSON/JSON streaming)

## Getting started

This README intentionally avoids setup instructions. See the dedicated setup guide for complete, copy‑pasteable steps for both supported modes:
- Local (stdio) — env injection via Cline settings JSON
- Remote (streamable HTTP) — .env on the server/VM

Refer to: [SETUP.md](./SETUP.md)

## What it does

- Surfaces Jira and Confluence operations as structured MCP tools for AI systems and editors.
- Supports first‑class MCP resources for Jira/Confluence to browse and read content via URIs.
- Honors enterprise TLS/CA requirements (MCP_SSL_VERIFY, MCP_CA_BUNDLE) for outbound HTTPS.
- Lets users define sensible defaults (preferred user, project, space, output format) to simplify everyday workflows.

---

### Key capabilities

- Transports
  - stdio (default) for editor/agent spawn
  - HTTP (streamable) via POST /mcp (JSON/NDJSON in/out)
- OAuth/Token support
  - OAuth refresh flow (client id/secret + refresh token)
  - Direct access tokens (optional)
- Defaults (env or tool)
  - MCP_PREFERRED_USER, JIRA_DEFAULT_PROJECT, CONF_DEFAULT_SPACE, MCP_DEFAULT_OUTPUT_FORMAT
- Security & TLS
  - MCP_SSL_VERIFY, MCP_CA_BUNDLE for outbound HTTPS customization
  - MCP_HTTP_TRUST_ENV controls proxy env usage (set to false to ignore HTTP(S)_PROXY/NO_PROXY); set NO_PROXY for intranet hosts

---

### Use cases

- Developer productivity: search, triage, and comment on Jira issues directly from your editor.
- Knowledge and context: pull Confluence pages/summaries into AI workflows and code reviews.
- Team workflows: standardize project/space defaults and identities through MCP.

---

### Tools (representative)

- Jira
  - jira_get_myself — GET /rest/api/latest/myself
  - jira_search_issues — Search by JQL
  - jira_get_issue — Get issue by key
  - jira_add_comment — Add a comment to an issue
  - jira_find_similar — Heuristic related‑issue search (optional semantic re‑ranking)
- Confluence
  - conf_get_server_info — Server info (fallback to “/”)
  - conf_get_page — Fetch page by ID
  - conf_search_cql — Search using CQL
- Utility
  - set_defaults — preferred user, default Jira project, default Confluence space, default output format

---

### Resource URIs

- Jira
  - jira://{project_key}
  - jira://{project_key}/issues
  - jira://{project_key}/issues/{issue_key}
- Confluence
  - confluence://{space_key}
  - confluence://{space_key}/pages
  - confluence://{space_key}/pages/{title} (URL‑encoded)
- Output formats
  - markdown (default), json, storage (Confluence)

---

## Setup and operations

See [SETUP.md](./SETUP.md) for:
- Installing uv
- Local/editor usage (stdio) via Cline settings JSON (env injection by Cline)
- Remote/URL usage (HTTP) via `.env` on the VM and uv run
- Reverse proxy guidance and troubleshooting

### Security notes

- Keep organization credentials on the server for HTTP mode; do not place org secrets in client configs.
- Prefer OAuth refresh flow over long‑lived access tokens.
- Use MCP_SSL_VERIFY=true and MCP_CA_BUNDLE to trust corporate CAs.

### License

UPL‑1.0. See LICENSE.
