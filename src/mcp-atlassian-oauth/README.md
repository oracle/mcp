# MCP Atlassian OAuth (Python)

Model Context Protocol (MCP) server exposing Atlassian Jira and Confluence tools with OAuth/Token support. This package mirrors the structure and developer experience of the official MCP servers, providing a clean src/tests/tools/examples layout and marketplace metadata.

- Language: Python (>= 3.10)
- License: UPL-1.0
- Entry point: python -m mcp_atlassian_oauth
- Marketplace metadata: mcp.json (id: oracle.atlassian.oauth)

## Features

Provided MCP tools:
- Jira
  - jira_get_myself — GET /rest/api/latest/myself
  - jira_search_issues — Search by JQL
  - jira_get_issue — Get issue by key
  - jira_add_comment — Add comment to issue
  - jira_find_similar — Heuristic search for related issues (phrase + token passes; optional semantic re-ranking)
- Confluence
  - conf_get_server_info — GET /rest/api/latest/settings/systemInfo (fallback to “/”)
  - conf_get_page — Get page by ID
  - conf_search_cql — CQL search

TLS/SSL handling:
- Corporate/self-signed support via env:
  - MCP_SSL_VERIFY — "false"/"0"/"no"/"off" to disable verification (default: verify enabled)
  - MCP_CA_BUNDLE — absolute path to a PEM CA bundle

## Resource URIs

This server exposes first-class MCP Resources so you can browse and read Jira/Confluence content via URIs.

Supported schemes:
- Jira
  - jira://{project_key}
  - jira://{project_key}/issues
  - jira://{project_key}/issues/{issue_key}
- Confluence
  - confluence://{space_key}
  - confluence://{space_key}/pages
  - confluence://{space_key}/pages/{title} (title must be URL-encoded)

Query params:
- format
  - Jira: markdown (default) | json
  - Confluence page: markdown (default) | storage | json
- limit: paging size for project/space summaries

Examples:
- confluence://DOCS/pages/Getting%20Started?format=markdown
- jira://ENG/issues/ENG-12345?format=json

See examples/uri_examples.md for more.

## Defaults and set_defaults

Runtime defaults to simplify usage:
- preferred user: MCP_PREFERRED_USER
- default Jira project key: JIRA_DEFAULT_PROJECT
- default Confluence space key: CONF_DEFAULT_SPACE
- default output format: MCP_DEFAULT_OUTPUT_FORMAT (markdown|json|storage)

You can also change these at runtime using the MCP tool:
- set_defaults
  - inputs: { preferredUser?, jiraProject?, confSpace?, outputFormat?, show? }
  - behavior: when show=true, returns current defaults without changing them

### Preferred user substitution (JQL/CQL)
- When MCP_PREFERRED_USER is set (or set via the set_defaults tool as preferredUser), any occurrence of currentUser() in:
  - Jira JQL (jira_search_issues), or
  - Confluence CQL (conf_search_cql)
  is replaced at runtime with the quoted preferred user string.  
- If MCP_PREFERRED_USER is not set, queries are left unchanged and currentUser() resolves to the authenticated token’s user (default behavior).

Examples:
- JQL: assignee = currentUser() ORDER BY updated DESC
  → assignee = "divakar.sureka@oracle.com" ORDER BY updated DESC
- CQL: creator = currentUser() ORDER BY modified DESC
  → creator = "divakar.sureka@oracle.com" ORDER BY modified DESC

Notes:
- Provide the value that your Jira/Confluence instance expects (e.g., email, username, or accountId).
- The substitution is a simple textual replacement of currentUser() (case-insensitive). Avoid quoting currentUser() inside string literals. Future versions may add smarter parsing if needed.


### Default project/space injection (JQL/CQL)

- When JIRA_DEFAULT_PROJECT is set (or set via the set_defaults tool as jiraProject), jira_search_issues will add a project constraint if your JQL does not already specify one.  
  • Behavior: If no project clause is present, injects project = "<KEY>" before any ORDER BY.  
  • Example:  
    - Input JQL: assignee = currentUser() ORDER BY updated DESC  
    - With JIRA_DEFAULT_PROJECT=UNIFIER → assignee = currentUser() AND project = "UNIFIER" ORDER BY updated DESC  
  • If your JQL already contains project = … or project in (…), it is left unchanged.

- When CONF_DEFAULT_SPACE is set (or set via the set_defaults tool as confSpace), conf_search_cql will add a space constraint if your CQL does not already specify one.  
  • Behavior: If no space clause is present, injects space = "<KEY>" before any ORDER BY.  
  • Example:  
    - Input CQL: creator = currentUser() ORDER BY modified DESC  
    - With CONF_DEFAULT_SPACE=DOCS → creator = currentUser() AND space = "DOCS" ORDER BY modified DESC  
  • If your CQL already contains space = … or space in (…), it is left unchanged.

### Default output format for resource URIs

- When MCP_DEFAULT_OUTPUT_FORMAT is set (or set via set_defaults as outputFormat), resource reads without an explicit format=… will default to this value.  
  • Supported: markdown (default) | json | storage (Confluence page XHTML)  
  • Applies to:  
    - confluence://… (space and page reads)  
    - jira://… (project/issue summaries)  
  • You can still override per-call using the URI query param, e.g., jira://UNIFIER?format=json

## Semantic Search (optional)

jira_find_similar supports a semantic re-ranking mode behind an optional extra.
- Install the extra in your venv: pip install ".[semantic]"
- Modes:
  - heuristic (default): phrase + token passes with ranking
  - semantic: re-rank by embeddings (if model available), fallback to heuristic otherwise
  - hybrid: apply heuristic then re-rank with embeddings when available

Default model: sentence-transformers/all-MiniLM-L6-v2

## Remote (URL) deployment

To run this server as a remote endpoint consumable by Cline’s “Remote MCP”:

- Install ops extra (WebSocket + .env):
  - pip install ".[ops]"
  - or pip install -r requirements-ops.txt
- Set environment (example):
  - MCP_TRANSPORT=ws
  - MCP_HOST=0.0.0.0
  - MCP_PORT=8765
- Keep org-wide credentials on the server (e.g., an .env file in the working directory). Users set personal defaults via the set_defaults tool from their client.
- Start the server:
  - python -m mcp_atlassian_oauth
- Expose wss:// via a TLS reverse proxy (e.g., NGINX/IIS/ARR) and add the URL in Cline’s “Remote MCP” tab.

Full Linux and Windows setup instructions: see [REMOTE_SERVER_SETUP.md](./REMOTE_SERVER_SETUP.md)

## Single Setup Approach (Repo-local venv)

We standardize on a dedicated virtual environment inside this project. Your MCP host must launch THIS venv’s python with -m mcp_atlassian_oauth.

1) Create and activate the venv

- macOS/Linux
  cd /absolute/path/to/mcp-atlassian-oauth
  python3 -m venv .venv
  source .venv/bin/activate

2) Install the package into the venv (installs MCP SDK dependency “mcp”)

  python -m pip install -U pip
  pip install .

  # Optional: enable semantic search
  # pip install ".[semantic]"

3) Quick sanity check (should print the venv’s python path and versions)

  python -c "import sys, inspect, mcp, mcp_atlassian_oauth as s; print('python =', sys.executable); print('mcp =', getattr(mcp, '__version__', 'OK')); print('server =', inspect.getfile(s))"

4) Manual run (for a quick smoke test)

  # Set the minimum required env first (replace with real values)
  export JIRA_BASE_URL='https://your-domain.atlassian.net'
  export CONF_BASE_URL='https://your-domain.atlassian.net/wiki'

  # Then start the server
  python -m mcp_atlassian_oauth

If you see the server start without ModuleNotFoundError for mcp, your venv is correct.

## Configure in Cline (or your MCP host)

Point to the venv’s python and invoke the module. Adjust the schema to match your host (some use “servers”, others “mcpServers”):

{
  "mcpServers": {
    "oracle.atlassian.oauth": {
      "command": "/absolute/path/to/mcp-atlassian-oauth/.venv/bin/python",
      "args": ["-m", "mcp_atlassian_oauth"],
      "env": {
        "JIRA_BASE_URL": "https://your-domain.atlassian.net",
        "JIRA_ACCESS_TOKEN": "",
        "JIRA_CLIENT_ID": "",
        "JIRA_CLIENT_SECRET": "",
        "JIRA_REFRESH_TOKEN": "",
        "CONF_BASE_URL": "https://your-domain.atlassian.net/wiki",
        "CONF_ACCESS_TOKEN": "",
        "CONF_CLIENT_ID": "",
        "CONF_CLIENT_SECRET": "",
        "CONF_REFRESH_TOKEN": "",
        "MCP_SSL_VERIFY": "true",
        "MCP_CA_BUNDLE": "",
        "MCP_PREFERRED_USER": "automation.bot",
        "JIRA_DEFAULT_PROJECT": "ENG",
        "CONF_DEFAULT_SPACE": "DOCS",
        "MCP_DEFAULT_OUTPUT_FORMAT": "markdown"
      },
      "disabled": false
    }
  }
}

Why this is reliable:
- It guarantees your MCP host launches the exact interpreter where this package and its dependencies (mcp) are installed.
- It avoids ambiguity with system/global Python installs.

## Environment Variables

Set the following for Jira:
- JIRA_BASE_URL — e.g., https://your-domain.atlassian.net
- JIRA_ACCESS_TOKEN — OAuth access token (optional if using refresh)
- JIRA_CLIENT_ID — OAuth client id (optional; used for refresh)
- JIRA_CLIENT_SECRET — OAuth client secret (optional; used for refresh)
- JIRA_REFRESH_TOKEN — OAuth refresh token (optional)

Confluence:
- CONF_BASE_URL — e.g., https://your-domain.atlassian.net/wiki
- CONF_ACCESS_TOKEN — OAuth access token (optional if using refresh)
- CONF_CLIENT_ID — OAuth client id (optional; used for refresh)
- CONF_CLIENT_SECRET — OAuth client secret (optional; used for refresh)
- CONF_REFRESH_TOKEN — OAuth refresh token (optional)

TLS/SSL (optional):
- MCP_SSL_VERIFY, MCP_CA_BUNDLE — see TLS section above

## Tests (optional)

Within the venv:

  pip install -e ".[dev]"
  pytest -q

## Troubleshooting

- ImportError: No module named 'mcp'
  - Your MCP host is not launching the venv’s python. Ensure "command" points to …/mcp-atlassian-oauth/.venv/bin/python.
  - Or you installed this package into a different interpreter. Re-run the “Single Setup Approach”.

- Clearing global Python installs (to avoid conflicts)
  - To remove previously installed copies from a system interpreter (example for /usr/local/bin/python3):

    /usr/local/bin/python3 -m pip uninstall -y mcp-atlassian-oauth mcp || true
    /usr/local/bin/python3 -c 'import importlib; print("mcp:", importlib.util.find_spec("mcp")); print("server:", importlib.util.find_spec("mcp_atlassian_oauth"))'

  - After clearing, rely exclusively on the repo-local venv as described above.

## Project Layout

mcp-atlassian-oauth/
  LICENSE
  README.md
  pyproject.toml
  mcp.json
  src/
    mcp_atlassian_oauth/
      __init__.py
      __main__.py
      server.py
  tests/
    test_smoke.py
    test_resources.py
  tools/
    dev_install.sh
    install.sh
    run_local.sh
  examples/
    cline_mcp_settings.json
    .env.example
    python_client.py

## Security Notes

- Prefer OAuth refresh flow where available; long-lived access tokens are discouraged.
- When disabling SSL verification (MCP_SSL_VERIFY=false), do so only in trusted environments.
- Do not commit secrets. Use .env or your MCP host’s environment injection.

## License

UPL-1.0. See LICENSE.
