#!/usr/bin/env bash
set -euo pipefail

# Dev install for MCP Atlassian server:
# Installs this package in editable mode with dev extras (pytest).
# Also ensures the MCP SDK dependency is installed via pyproject.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[dev_install] Installing editable with dev extras from: ${ROOT_DIR}"
python3 -m pip install -U pip
python3 -m pip install -e "${ROOT_DIR}[dev]"
echo "[dev_install] Done. You can now run tests with: pytest -q"
