# Setup Guide (uv-only)

This project now uses uv exclusively for environment management and running. requirements.txt files and pip/venv instructions are no longer used.

- Transports
  - stdio (default): editor spawns the server with `python -m mcp_atlassian_oauth` (env via .env or editor settings)
  - HTTP (streamable): POST `/mcp` using JSON/NDJSON streaming. Clients connect by URL.

- Requirements
  - Python 3.10+
  - Network access to Atlassian endpoints
  - uv installed

- Where credentials live
  - Local stdio (dev): `.env` in the project root (loaded automatically)
  - Remote HTTP: `.env` on the server/VM

---

## 0) Place the code

Copy or extract this repository to your desired location, for example:

- macOS/Linux: `/absolute/path/to/mcp-atlassian-oauth`
- Windows: `\absolute\path\to\mcp-atlassian-oauth`

---

## 1) Install uv

- macOS (Homebrew)
  ```bash
  brew install astral-sh/uv/uv
  ```

- macOS/Linux (Official Installer)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Restart your shell so "uv" is on PATH
  ```

- Windows (PowerShell)
  ```powershell
  iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex
  ```

- Fallbacks
  ```bash
  pipx install uv
  # or
  pip install uv
  ```

---

## 2) Prepare .env

Create a `.env` at the project root. A template is provided:

```bash
cd /absolute/path/to/mcp-atlassian-oauth
cp examples/.env.example .env
# Edit .env with your Jira/Confluence OAuth values and any transport settings
```

The app auto-loads `.env` (python-dotenv). No `export` required.

---

## 3) Local development (stdio)

For editor integration, configure Cline to spawn the server and inject environment variables.
Do NOT rely on `.env` in this mode — Cline passes env from its settings.

Cline settings (Map form: `mcpServers`)
```json
{
  "mcpServers": {
    "atlassian.oauth (stdio)": {
      "command": "uv",
      "args": ["run", "-m", "mcp_atlassian_oauth"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "JIRA_BASE_URL": "https://your-jira.example.com",
        "JIRA_CLIENT_ID": "",
        "JIRA_CLIENT_SECRET": "",
        "JIRA_REFRESH_TOKEN": "",
        "JIRA_ACCESS_TOKEN": "",
        "CONF_BASE_URL": "https://your-confluence.example.com/wiki",
        "CONF_CLIENT_ID": "",
        "CONF_CLIENT_SECRET": "",
        "CONF_REFRESH_TOKEN": "",
        "CONF_ACCESS_TOKEN": "",
        "MCP_SSL_VERIFY": "true",
        "MCP_CA_BUNDLE": "",
        "MCP_PREFERRED_USER": "automation.bot",
        "JIRA_DEFAULT_PROJECT": "ENG",
        "CONF_DEFAULT_SPACE": "DOCS",
        "MCP_DEFAULT_OUTPUT_FORMAT": "markdown"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Cline settings (Array form: `servers`)
```json
{
  "servers": [
    {
      "name": "atlassian.oauth (stdio)",
      "command": "uv",
      "args": ["run", "-m", "mcp_atlassian_oauth"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "JIRA_BASE_URL": "https://your-jira.example.com",
        "JIRA_CLIENT_ID": "",
        "JIRA_CLIENT_SECRET": "",
        "JIRA_REFRESH_TOKEN": "",
        "JIRA_ACCESS_TOKEN": "",
        "CONF_BASE_URL": "https://your-confluence.example.com/wiki",
        "CONF_CLIENT_ID": "",
        "CONF_CLIENT_SECRET": "",
        "CONF_REFRESH_TOKEN": "",
        "CONF_ACCESS_TOKEN": "",
        "MCP_SSL_VERIFY": "true",
        "MCP_CA_BUNDLE": "",
        "MCP_PREFERRED_USER": "automation.bot",
        "JIRA_DEFAULT_PROJECT": "ENG",
        "CONF_DEFAULT_SPACE": "DOCS",
        "MCP_DEFAULT_OUTPUT_FORMAT": "markdown"
      },
      "disabled": false,
      "autoApprove": []
    }
  ]
}
```

Note:
- Prefer `command: "uv"` so it runs in the project’s uv-managed environment.
- Alternatively, you can use the project-local interpreter:
  - macOS/Linux: `/absolute/path/to/mcp-atlassian-oauth/.venv/bin/python`
  - Windows: `\\absolute\\path\\to\\mcp-atlassian-oauth\\.venv\\Scripts\\python.exe`

---

## 4) Remote URL (HTTP stream)

On the server/VM, put the `.env` with at least:
```env
MCP_TRANSPORT=http
MCP_HOST=0.0.0.0
MCP_PORT=8765
MCP_PATH=/mcp
LOG_LEVEL=info
# plus Jira/Confluence OAuth values
```

Start:
```bash
./tools/run_local.sh
# Logs: "Uvicorn running on http://0.0.0.0:8765"
```

Connect clients by URL:
- Development: `http://<server-ip>:8765/mcp`
- Production: front with TLS reverse proxy (`https://your-host.example.com/mcp`)

Cline (streamableHttp):
```json
{
  "mcpServers": {
    "oracle-atlassian-oauth": {
      "type": "streamableHttp",
      "url": "http://<server-ip>:8765/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

## 5) Reverse proxy (Streaming-friendly)

### NGINX
```nginx
server {
  listen 443 ssl;
  server_name your-host.example.com;

  ssl_certificate     /etc/ssl/your.crt;
  ssl_certificate_key /etc/ssl/your.key;

  location /mcp {
    proxy_http_version 1.1;
    proxy_set_header Host $host;

    proxy_request_buffering off;
    proxy_buffering off;

    proxy_pass http://127.0.0.1:8765;
  }
}
```

### Caddy
```caddy
your-host.example.com {
  route /mcp* {
    reverse_proxy 127.0.0.1:8765 {
      transport http {
        versions h2c 1.1
        read_buffer 0
        write_buffer 0
      }
      flush_interval -1
    }
  }
}
```

---

## 6) Troubleshooting

- Missing credentials
  - Ensure `.env` contains required Jira/Confluence OAuth values.
  - The server returns clear errors when tools requiring auth are invoked without creds.

- Port already in use
  - Set `MCP_PORT` in `.env` to an alternate port (e.g., 8787) and re-run `./tools/run_local.sh`.

- uv not found
  - Install uv using one of the methods in Step 1.

- Streaming timeouts
  - Ensure clients use `application/json` (single JSON request) or `application/x-ndjson` for NDJSON streaming.
  - If behind a proxy, disable request/response buffering (see reverse proxy section).

---

## 7) Notes on legacy artifacts

- requirements.txt / requirements-ops.txt are no longer used; uv reads dependencies from `pyproject.toml`.
- All setup is based on uv (`uv sync`, `uv run`).
