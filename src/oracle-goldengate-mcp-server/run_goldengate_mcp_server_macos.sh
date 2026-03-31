#!/usr/bin/env bash
set -euo pipefail
umask 077

# Launch script for Python GoldenGate MCP Server (macOS)
# Usage: ./run_goldengate_mcp_server_macos.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/oracle-goldengate-mcp-server.env"
LOG_DIR="${SCRIPT_DIR}/logs"
RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_DIR}/run_goldengate_mcp_server_macos_${RUN_TS}.log"
LOG_PATTERN="run_goldengate_mcp_server_macos_*.log"

mkdir -p "${LOG_DIR}"

log_line() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" >> "${LOG_FILE}"
}

on_error() {
  local exit_code="$1"
  local line_no="$2"
  log_line "[ERROR] Launcher failed at line ${line_no} with exit code ${exit_code}"
  exit "${exit_code}"
}
trap 'on_error $? $LINENO' ERR

require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    log_line "[ERROR] Required command not found: ${cmd}"
    exit 1
  fi
}

prune_old_logs() {
  local count
  count="$(find "${LOG_DIR}" -maxdepth 1 -type f -name "${LOG_PATTERN}" | wc -l | tr -d '[:space:]')"
  [[ -z "${count}" ]] && count=0
  (( count <= 10 )) && return 0

  # Keep the 10 newest files by mtime (macOS/BSD stat uses %m for epoch mtime).
  find "${LOG_DIR}" -maxdepth 1 -type f -name "${LOG_PATTERN}" -print \
    | while IFS= read -r file; do
        stat -f '%m %N' "${file}"
      done \
    | sort -nr \
    | awk 'NR>10 { sub(/^[0-9]+ /, "", $0); print }' \
    | while IFS= read -r old_file; do
        [[ -n "${old_file}" ]] && rm -f -- "${old_file}"
      done
}

# Keep only the 10 most recent macOS launcher logs
prune_old_logs

run_and_log() {
  log_line "[INFO] Running command: $*"
  "$@" >> "${LOG_FILE}" 2>&1
}

normalize_crlf_in_place() {
  local file_path="$1"
  if [[ -f "${file_path}" ]] && grep -q $'\r' "${file_path}"; then
    log_line "[WARN] Detected CRLF line endings in ${file_path}; normalizing to LF"
    sed -i '' $'s/\r$//' "${file_path}"
  fi
}

if [[ -f "${ENV_FILE}" ]]; then
  normalize_crlf_in_place "${ENV_FILE}"
  if [[ ! -r "${ENV_FILE}" ]]; then
    log_line "[ERROR] Environment file is not readable: ${ENV_FILE}"
    exit 1
  fi
  log_line "[INFO] Loading environment file: ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
else
  log_line "[ERROR] Environment file not found: ${ENV_FILE}"
  log_line "[ERROR] Aborting startup. Create the env file from oracle-goldengate-mcp-server.env.empty and set required values."
  exit 1
fi

require_command python3

if [[ ! -x "${SCRIPT_DIR}/.venv/bin/python" ]]; then
  run_and_log python3 -m venv "${SCRIPT_DIR}/.venv"
fi

VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"

python_is_supported() {
  "${VENV_PYTHON}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'
}

ensure_supported_python() {
  if [[ ! -x "${VENV_PYTHON}" ]]; then
    log_line "[ERROR] Virtual environment Python not found: ${VENV_PYTHON}"
    exit 1
  fi

  if python_is_supported; then
    return 0
  fi

  current_version="$("${VENV_PYTHON}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo unknown)"
  log_line "[WARN] Virtual environment uses unsupported Python ${current_version}; project requires >=3.10"
  rm -rf "${SCRIPT_DIR}/.venv"

  for py_cmd in python3.12 python3.11 python3.10 python3; do
    if command -v "${py_cmd}" >/dev/null 2>&1; then
      run_and_log "${py_cmd}" -m venv "${SCRIPT_DIR}/.venv"
      VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"
      if [[ -x "${VENV_PYTHON}" ]] && python_is_supported; then
        fixed_version="$("${VENV_PYTHON}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
        log_line "[INFO] Recreated virtual environment with supported Python ${fixed_version} using ${py_cmd}"
        return 0
      fi
      rm -rf "${SCRIPT_DIR}/.venv"
    fi
  done

  log_line "[ERROR] Could not find a supported Python interpreter (>=3.10) on PATH."
  log_line "[ERROR] Install Python 3.10+ (or uv-managed Python) and rerun this launcher."
  exit 1
}

ensure_supported_python

ensure_venv_pip() {
  if "${VENV_PYTHON}" -m pip --version >/dev/null 2>&1; then
    if ! run_and_log "${VENV_PYTHON}" -m pip install --upgrade pip setuptools wheel; then
      log_line "[WARN] pip exists but tooling upgrade failed; continuing with current pip"
    fi
    return 0
  fi

  log_line "[WARN] pip is missing in virtual environment; attempting bootstrap via ensurepip"
  if "${VENV_PYTHON}" -m ensurepip --upgrade >> "${LOG_FILE}" 2>&1; then
    run_and_log "${VENV_PYTHON}" -m pip install --upgrade pip setuptools wheel
    return 0
  fi

  log_line "[WARN] Could not bootstrap pip in virtual environment via ensurepip."
  log_line "[WARN] Attempting virtual environment repair to restore pip availability"

  rm -rf "${SCRIPT_DIR}/.venv"
  run_and_log python3 -m venv "${SCRIPT_DIR}/.venv"
  VENV_PYTHON="${SCRIPT_DIR}/.venv/bin/python"

  if "${VENV_PYTHON}" -m pip --version >/dev/null 2>&1; then
    log_line "[INFO] pip restored after recreating virtual environment"
    return 0
  fi

  log_line "[WARN] Virtual environment repair did not restore pip."
  log_line "[WARN] Will continue without pip and attempt uv fallback if dependency installation is required."
  return 1
}

HAS_VENV_PIP=0
if ensure_venv_pip; then
  HAS_VENV_PIP=1
fi

if "${VENV_PYTHON}" -c "import oracle.oracle_goldengate_mcp_server.server" >/dev/null 2>&1; then
  log_line "[INFO] Package import check passed, skipping pip install"
else
  if [[ "${HAS_VENV_PIP}" -eq 1 ]]; then
    log_line "[INFO] Package import check failed, running pip install -e"
    run_and_log "${VENV_PYTHON}" -m pip install -e "${SCRIPT_DIR}"
  else
    if ! command -v uv >/dev/null 2>&1; then
      log_line "[WARN] pip is unavailable in virtual environment and uv is not installed."
      log_line "[WARN] Continuing without dependency auto-install; server startup may fail if dependencies are missing."
      goto_after_install=1
    else
      log_line "[WARN] pip unavailable; using uv to install project dependencies into the virtual environment"
      if ! run_and_log uv pip install --python "${VENV_PYTHON}" -e "${SCRIPT_DIR}"; then
        log_line "[WARN] uv pip install failed; continuing without dependency auto-install"
      fi
    fi
    if [[ "${goto_after_install:-0}" -eq 1 ]]; then
      :
    fi
  fi
fi

export MCP_TRANSPORT=stdio
export PYTHONUNBUFFERED=1
# Do not set GG_MCP_LOG_FILE here: startup logs are already captured from stderr
# into ${LOG_FILE}. Setting GG_MCP_LOG_FILE duplicates startup log entries.
log_line "Starting GoldenGate MCP server (transport=stdio)"
"${VENV_PYTHON}" -m oracle.oracle_goldengate_mcp_server.server \
  2>> "${LOG_FILE}"
