#!/usr/bin/env bash
set -euo pipefail

REQUEST_ROOT="${1:?usage: oci-code-lima-guest-runner.sh <request-root>}"
OCI_PIP_SPEC="${OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC:-oci==2.160.0}"

STAGE_DIR="${REQUEST_ROOT}/stage"
PROJECT_PATH="${REQUEST_ROOT}/project"
MANIFEST_PATH="${STAGE_DIR}/request.json"
RESULT_PATH="${STAGE_DIR}/result.json"
VENV_ROOT="${OCI_CODE_LIMA_GUEST_VENV_ROOT:-/var/tmp/oci-code-mcp/venvs}"
SPEC_SLUG="$(printf '%s' "${OCI_PIP_SPEC}" | tr '/:=' '___')"
VENV_PATH="${VENV_ROOT}/${SPEC_SLUG}"

python_minor_version() {
  python3 - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
}

ensure_python_present() {
  if command -v python3 >/dev/null 2>&1 && python3 -m pip --version >/dev/null 2>&1; then
    return 0
  fi

  if command -v apt-get >/dev/null 2>&1; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip python3-venv
    return 0
  fi

  if command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-pip
    return 0
  fi

  if command -v yum >/dev/null 2>&1; then
    sudo yum install -y python3 python3-pip
    return 0
  fi

  echo "Unable to install python3/python3-pip automatically inside the Lima guest" >&2
  exit 1
}

ensure_venv_support() {
  if python3 - <<'PY' >/dev/null 2>&1
import ensurepip
print(ensurepip.version())
PY
  then
    return 0
  fi

  if command -v apt-get >/dev/null 2>&1; then
    PYTHON_MM="$(python_minor_version)"
    sudo DEBIAN_FRONTEND=noninteractive apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "python${PYTHON_MM}-venv" python3-venv >/dev/null || \
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "python${PYTHON_MM}-venv" >/dev/null || \
      sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv >/dev/null
    return 0
  fi

  echo "python3 is present but ensurepip/venv support is unavailable inside the Lima guest" >&2
  exit 1
}

venv_python_usable() {
  [ -x "${VENV_PATH}/bin/python" ] || return 1
  "${VENV_PATH}/bin/python" -c 'import sys; print(sys.executable)' >/dev/null 2>&1 || return 1
  "${VENV_PATH}/bin/python" -m pip --version >/dev/null 2>&1
}

oci_installed_in_venv() {
  "${VENV_PATH}/bin/python" - "${OCI_PIP_SPEC}" <<'PY' >/dev/null 2>&1
import importlib.metadata
import sys

expected = sys.argv[1]
try:
    installed = importlib.metadata.version("oci")
except importlib.metadata.PackageNotFoundError:
    raise SystemExit(1)
raise SystemExit(0 if installed == expected else 1)
PY
}

ensure_venv_with_oci() {
  mkdir -p "${VENV_ROOT}"

  if ! venv_python_usable; then
    rm -rf "${VENV_PATH}"
    python3 -m venv "${VENV_PATH}"
  fi

  if oci_installed_in_venv; then
    return 0
  fi

  PIP_DISABLE_PIP_VERSION_CHECK=1 "${VENV_PATH}/bin/python" -m pip install --upgrade pip >/dev/null
  PIP_DISABLE_PIP_VERSION_CHECK=1 "${VENV_PATH}/bin/python" -m pip install "${OCI_PIP_SPEC}"
}

ensure_manifest_present() {
  [ -f "${MANIFEST_PATH}" ] || {
    echo "Expected manifest at ${MANIFEST_PATH}" >&2
    exit 1
  }
}

ensure_project_present() {
  [ -d "${PROJECT_PATH}/oracle/oci_code_mcp_server" ] || {
    echo "Expected staged project checkout at ${PROJECT_PATH}" >&2
    exit 1
  }
}

run_firecracker_backend() {
  local firecracker_cmd
  firecracker_cmd="${OCI_CODE_LIMA_GUEST_FIRECRACKER_CMD:-${HOME}/.local/bin/oci-code-lima-firecracker-orchestrator}"

  [ -c /dev/kvm ] || {
    echo "/dev/kvm is not available inside the Lima guest" >&2
    exit 1
  }

  [ -x "${firecracker_cmd}" ] || {
    echo "Nested Firecracker delegate not found or not executable: ${firecracker_cmd}" >&2
    exit 1
  }

  export PYTHONPATH="${PROJECT_PATH}${PYTHONPATH:+:${PYTHONPATH}}"
  export OCI_CODE_FIRECRACKER_DELEGATE_CMD="${firecracker_cmd}"
  "${VENV_PATH}/bin/python" -m oracle.oci_code_mcp_server.runner --backend delegate --manifest "${MANIFEST_PATH}"
}

ensure_python_present
ensure_venv_support
ensure_manifest_present
ensure_project_present
ensure_venv_with_oci
run_firecracker_backend

[ -f "${RESULT_PATH}" ] || {
  echo "Guest runner completed without writing ${RESULT_PATH}" >&2
  exit 1
}
