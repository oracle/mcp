#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
INSTALLER_SCRIPT="$SCRIPT_DIR/install_oci_recovery_mcp.py"

if [ ! -f "$INSTALLER_SCRIPT" ]; then
  echo "The Python installer must be beside this launcher: $INSTALLER_SCRIPT" >&2
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Git is required. Install Git for your operating system, then run this installer again." >&2
  exit 1
fi

UV_COMMAND="$(command -v uv || true)"
if [ -z "$UV_COMMAND" ]; then
  echo "uv was not found; installing uv for your user account."
  UV_INSTALLER="$(mktemp "${TMPDIR:-/tmp}/uv-install.XXXXXX.sh")"
  trap 'rm -f "$UV_INSTALLER"' EXIT HUP INT TERM
  if command -v curl >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh -o "$UV_INSTALLER"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$UV_INSTALLER" https://astral.sh/uv/install.sh
  else
    echo "curl or wget is required to install uv." >&2
    exit 1
  fi
  sh "$UV_INSTALLER"
  rm -f "$UV_INSTALLER"
  trap - EXIT HUP INT TERM

  if [ -x "$HOME/.local/bin/uv" ]; then
    UV_COMMAND="$HOME/.local/bin/uv"
  elif [ -x "$HOME/.cargo/bin/uv" ]; then
    UV_COMMAND="$HOME/.cargo/bin/uv"
  else
    UV_COMMAND="$(command -v uv || true)"
  fi
fi

if [ -z "$UV_COMMAND" ]; then
  echo "uv installation finished, but its executable was not found. Open a new terminal and rerun this script." >&2
  exit 1
fi

export OCI_RECOVERY_UV="$UV_COMMAND"
if [ -r /dev/tty ]; then
  "$UV_COMMAND" run --python 3.13 --no-project --no-sync "$INSTALLER_SCRIPT" "$@" < /dev/tty
else
  "$UV_COMMAND" run --python 3.13 --no-project --no-sync "$INSTALLER_SCRIPT" "$@"
fi
