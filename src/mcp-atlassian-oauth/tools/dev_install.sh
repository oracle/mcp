#!/usr/bin/env bash
set -euo pipefail

# Dev install for MCP Atlassian server using uv (preferred):
# - Creates/uses a project-local virtualenv
# - Installs dependencies from pyproject.toml
# - Includes dev extras for pytest, httpx, etc.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[dev_install] Using uv to create venv and install deps from: ${ROOT_DIR}"

if ! command -v uv >/dev/null 2>&1; then
  echo "[dev_install] 'uv' is not installed. See https://docs.astral.sh/uv/getting-started/ to install uv."
  exit 1
fi

cd "${ROOT_DIR}"
uv sync --locked || uv sync
echo "[dev_install] Done. You can now run tests with: uv run -m pytest -q"
