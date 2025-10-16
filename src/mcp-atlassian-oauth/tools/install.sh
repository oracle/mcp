#!/usr/bin/env bash
set -euo pipefail

# Installer for MCP Atlassian OAuth server (Python)
# Tries pipx first (recommended), then falls back to pip in the current environment.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if command -v pipx >/dev/null 2>&1; then
  echo "[install] Using pipx to install package from: ${ROOT_DIR}"
  pipx install "${ROOT_DIR}"
  echo "[install] Done. Try running: mcp-atlassian"
  exit 0
fi

echo "[install] pipx not found. Falling back to pip install in current environment."
echo "[install] Installing package from: ${ROOT_DIR}"
python3 -m pip install "${ROOT_DIR}"
echo "[install] Done. Try running: mcp-atlassian"
