#!/usr/bin/env bash
set -euo pipefail

# Run the Atlassian MCP server locally using uv and a .env file.
# No shell exports required — the app loads .env via python-dotenv.

# Move to project root (this script is in tools/)
cd "$(dirname "$0")/.."

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Copy examples/.env.example or create .env with your values."
  exit 1
fi

# Sync dependencies from pyproject.toml and run the server
uv sync
uv run -m mcp_atlassian_oauth
