#!/usr/bin/env bash
set -euo pipefail

# Run the MCP Atlassian OAuth server locally via Python module.
# Loads environment variables from ./examples/.env if present.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/examples/.env"

if [[ -f "${ENV_FILE}" ]]; then
  echo "[run] Loading env from ${ENV_FILE}"
  # shellcheck disable=SC2046
  export $(grep -v '^[[:space:]]*#' "${ENV_FILE}" | grep -v '^[[:space:]]*$' | xargs -I{} echo {})
fi

echo "[run] Starting server: python -m mcp_atlassian_oauth"
exec /usr/bin/env python3 -m mcp_atlassian_oauth
