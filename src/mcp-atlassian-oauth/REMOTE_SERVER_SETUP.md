# Remote URL Deployment (Linux and Windows)

Goal: Run this MCP server centrally and expose it over a URL that clients (e.g., Cline “Remote MCP”) can connect to. Keep organization-wide credentials on the server; users only set their personal defaults client-side.

This server supports two transport modes:
- stdio (default) — for local usage: python -m mcp_atlassian_oauth
- WebSocket (remote URL) — for remote usage: serve ws:// (behind TLS/wss via a reverse proxy)

Transport is selected by the MCP_TRANSPORT environment variable.

## 1) Which settings are org-wide vs user-specific?

Org-wide secrets (server-side only):
- Jira:
  - JIRA_BASE_URL (e.g., https://your-domain.atlassian.net)
  - JIRA_CLIENT_ID (optional, required for refresh flow)
  - JIRA_CLIENT_SECRET (optional, required for refresh flow)
  - JIRA_ACCESS_TOKEN (optional)
  - JIRA_REFRESH_TOKEN (optional)
- Confluence:
  - CONF_BASE_URL (e.g., https://your-domain.atlassian.net/wiki)
  - CONF_CLIENT_ID (optional, required for refresh flow)
  - CONF_CLIENT_SECRET (optional, required for refresh flow)
  - CONF_ACCESS_TOKEN (optional)
  - CONF_REFRESH_TOKEN (optional)
- TLS:
  - MCP_SSL_VERIFY ("true" or "false")
  - MCP_CA_BUNDLE (absolute path to PEM bundle, optional)

User-specific (set in client or via tool call after connect):
- MCP_PREFERRED_USER (e.g., user email/ID for query substitution)
- JIRA_DEFAULT_PROJECT
- CONF_DEFAULT_SPACE
- MCP_DEFAULT_OUTPUT_FORMAT ("markdown" | "json" | "storage")

Note on TOKEN_URL variables:
- JIRA_TOKEN_URL and CONF_TOKEN_URL are not used. The server derives the token endpoint as {BASE_URL}/rest/oauth2/latest/token.

## 2) Prerequisites

- Python 3.10+ on the server
- This repository or a packaged install of mcp-atlassian-oauth
- For WebSocket mode:
  - websockets (installed via optional extra [ops])
  - Recommended: TLS reverse proxy (NGINX, Caddy, IIS/ARR) to provide wss://

## 3) Install the server

Create a directory and Python virtual environment on the server.

### Linux

```bash
# As root or a privileged user
useradd -r -m -d /opt/mcp-atlassian-oauth -s /usr/sbin/nologin mcp || true
install -d -o mcp -g mcp -m 0755 /opt/mcp-atlassian-oauth
# Copy repo contents or release artifacts to /opt/mcp-atlassian-oauth
# e.g., rsync -a ./ /opt/mcp-atlassian-oauth/

cd /opt/mcp-atlassian-oauth
python3 -m venv .venv
source .venv/bin/activate
# Install package with ops extras (dotenv + websockets)
pip install -U pip
pip install ".[ops]"
# Optional: semantic search extra
# pip install ".[semantic]"
```

Create a .env containing ORG-WIDE secrets:
```bash
cat >/opt/mcp-atlassian-oauth/.env <<'EOF'
JIRA_BASE_URL=https://your-jira
JIRA_CLIENT_ID=...
JIRA_CLIENT_SECRET=...
JIRA_ACCESS_TOKEN=
JIRA_REFRESH_TOKEN=

CONF_BASE_URL=https://your-confluence
CONF_CLIENT_ID=...
CONF_CLIENT_SECRET=...
CONF_ACCESS_TOKEN=
CONF_REFRESH_TOKEN=

MCP_SSL_VERIFY=true
MCP_CA_BUNDLE=
# WebSocket listener settings (default host/port shown)
MCP_TRANSPORT=ws
MCP_HOST=0.0.0.0
MCP_PORT=8765
EOF
chown mcp:mcp /opt/mcp-atlassian-oauth/.env
chmod 600 /opt/mcp-atlassian-oauth/.env
```

Test run (foreground):
```bash
cd /opt/mcp-atlassian-oauth
source .venv/bin/activate
python -m mcp_atlassian_oauth
```

You should now have a WebSocket listener on ws://0.0.0.0:8765.

Systemd unit (optional, recommended):
```ini
# /etc/systemd/system/mcp-atlassian-oauth.service
[Unit]
Description=MCP Atlassian OAuth Server (WebSocket)
After=network.target

[Service]
Type=simple
User=mcp
Group=mcp
WorkingDirectory=/opt/mcp-atlassian-oauth
ExecStart=/opt/mcp-atlassian-oauth/.venv/bin/python -m mcp_atlassian_oauth
Restart=on-failure
# If you prefer not to use .env auto-loading, comment it out in code and use:
# EnvironmentFile=/opt/mcp-atlassian-oauth/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable --now mcp-atlassian-oauth
systemctl status mcp-atlassian-oauth -n 50
```

TLS termination via reverse proxy (example NGINX):
```nginx
server {
    listen 443 ssl;
    server_name your-host.example.com;

    ssl_certificate     /etc/ssl/your.crt;
    ssl_certificate_key /etc/ssl/your.key;

    location /mcp {
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_pass http://127.0.0.1:8765;
    }
}
```
Connect clients to wss://your-host.example.com/mcp.

### Windows

Open PowerShell as Administrator:

```powershell
# Choose an installation directory
New-Item -ItemType Directory -Force -Path "C:\mcp-atlassian-oauth" | Out-Null
# Copy repository contents or package to C:\mcp-atlassian-oauth

cd C:\mcp-atlassian-oauth
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install ".[ops]"
# Optional: semantic extra
# pip install ".[semantic]"
```

Create a .env (UTF-8, CRLF or LF is fine) in C:\mcp-atlassian-oauth\.env:

```
JIRA_BASE_URL=https://your-jira
JIRA_CLIENT_ID=...
JIRA_CLIENT_SECRET=...
JIRA_ACCESS_TOKEN=
JIRA_REFRESH_TOKEN=

CONF_BASE_URL=https://your-confluence
CONF_CLIENT_ID=...
CONF_CLIENT_SECRET=...
CONF_ACCESS_TOKEN=
CONF_REFRESH_TOKEN=

MCP_SSL_VERIFY=true
MCP_CA_BUNDLE=
MCP_TRANSPORT=ws
MCP_HOST=0.0.0.0
MCP_PORT=8765
```

Test run (foreground):
```powershell
cd C:\mcp-atlassian-oauth
.\.venv\Scripts\Activate.ps1
python -m mcp_atlassian_oauth
```

Run as a Windows Service (NSSM):
1) Install NSSM (https://nssm.cc/).
2) Create service:
   - Application: C:\mcp-atlassian-oauth\.venv\Scripts\python.exe
   - Arguments: -m mcp_atlassian_oauth
   - AppDirectory: C:\mcp-atlassian-oauth
   - Use “AppEnvironmentExtra” to paste key=value pairs only if you do NOT want to use .env.
   - Otherwise rely on .env automatic loading (recommended).
3) Start the service via Services.msc or:
```powershell
nssm install "MCP Atlassian OAuth"
nssm start "MCP Atlassian OAuth"
```

TLS termination on Windows:
- Use IIS/ARR or NGINX for Windows to terminate TLS and reverse proxy to ws://127.0.0.1:8765.
- Ensure “WebSocket Protocol” feature is installed in IIS for ARR.

## 4) Client setup (Cline “Remote MCP”)

In Cline:
- Remote MCP tab → “Add a remote MCP server”
- Name: oracle.atlassian.oauth (or your org name)
- URL endpoint: 
  - wss://your-host.example.com/mcp (recommended, behind TLS)
  - or ws://your-host:8765 (development)

Do NOT configure org secrets on clients. After connect, each user should set personal defaults using the provided tool:
- set_defaults
  - Inputs: preferredUser?, jiraProject?, confSpace?, outputFormat?, show?
  - Example usage flows:
    - Set only preferred user: { "preferredUser": "divakar@example.com" }
    - Set project and space: { "jiraProject": "ENG", "confSpace": "DOCS" }
    - Show current defaults: { "show": true }

### Client configuration JSON examples (Cline)

Depending on your Cline build, you may configure remote MCP by URL using either an object map (mcpServers) or an array (servers). A minimal single-entry fragment is also shown.

- Map form (mcpServers):
```json
{
  "mcpServers": {
    "oracle.atlassian.oauth": {
      "url": "wss://your-host.example.com/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

- Array form (servers):
```json
{
  "servers": [
    {
      "name": "oracle.atlassian.oauth",
      "url": "wss://your-host.example.com/mcp",
      "disabled": false,
      "autoApprove": []
    }
  ]
}
```

Notes:
- Do not include org-wide secrets for remote URL mode; those live only on the server.
- Per-user defaults are not part of the client config for URL transport. After connecting, invoke the set_defaults tool with payloads like:
  - `{ "preferredUser": "alice@example.com" }`
  - `{ "jiraProject": "ENG", "confSpace": "DOCS", "outputFormat": "markdown" }`

### Per-user defaults: exact calls in Cline

After connecting to the remote server in Cline:

- Via UI (Tools panel):
  1) Open the MCP Servers panel and select the server (e.g., oracle.atlassian.oauth)
  2) Choose tool: set_defaults
  3) Paste one of the following JSON payloads and run

- Set preferred user only:
```json
{ "preferredUser": "alice@example.com" }
```

- Set default project/space and output format:
```json
{ "jiraProject": "ENG", "confSpace": "DOCS", "outputFormat": "markdown" }
```

- Show current defaults (no changes):
```json
{ "show": true }
```

- Advanced (JSON-RPC shape seen by some clients):
```json
{
  "method": "tools/call",
  "params": {
    "name": "set_defaults",
    "arguments": {
      "preferredUser": "alice@example.com"
    }
  }
}
```

## 5) Local (stdio) vs Remote (ws) recap

- Local (stdio): 
  - Activate venv, set minimum env (JIRA_BASE_URL, CONF_BASE_URL, tokens if any), then:
    python -m mcp_atlassian_oauth
- Remote (ws):
  - Ensure MCP_TRANSPORT=ws in the environment (or .env), then:
    python -m mcp_atlassian_oauth
  - Expose over wss:// via a reverse proxy.

## 6) Security notes

- Treat CLIENT_ID/CLIENT_SECRET/ACCESS/REFRESH tokens as secrets; rotate if leaked.
- Keep MCP_SSL_VERIFY=true; use MCP_CA_BUNDLE to trust corporate CA bundles.
- Restrict inbound access via firewall and only expose TLS (wss) externally.
- Prefer service accounts if operating in a shared-identity model.

## 7) Troubleshooting

- 401 Unauthorized:
  - Ensure ACCESS_TOKEN is valid or provide REFRESH_TOKEN + CLIENT_ID/CLIENT_SECRET so refresh can occur.
- websockets not found:
  - Install ops extra: pip install ".[ops]"
- .env not loaded:
  - Ensure the file is in the working directory (where you run python -m mcp_atlassian_oauth) and readable.
  - Or inject env via systemd EnvironmentFile/NSSM AppEnvironmentExtra instead.
- Port in use:
  - Change MCP_PORT or stop the conflicting service.
