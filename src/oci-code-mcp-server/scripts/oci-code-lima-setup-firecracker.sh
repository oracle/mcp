#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTANCE="${OCI_CODE_LIMA_INSTANCE:-firecracker-dev}"
LIMACTL_BIN="${OCI_CODE_LIMACTL_BIN:-limactl}"
GUEST_TMP_ROOT="${OCI_CODE_LIMA_SETUP_TMP_ROOT:-/tmp/oci-code-firecracker-setup}"
GUEST_TMP_DIR="${GUEST_TMP_ROOT}/$(date +%s)"
FORCE_REBUILD=false

usage() {
  cat <<'EOF'
Usage: oci-code-lima-setup-firecracker.sh [--force]

Prepare the current Lima guest to run a nested Firecracker microVM by:
- ensuring the Lima instance is running with nested virtualization
- copying the guest install/orchestrator scripts into the VM
- installing Firecracker, its kernel/rootfs assets, and the guest-local delegate command

Environment:
  OCI_CODE_LIMA_INSTANCE     Lima instance name (default: firecracker-dev)
  OCI_CODE_LIMACTL_BIN       limactl binary path (default: limactl)
  OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC
  OCI_CODE_LIMA_FIRECRACKER_VERSION
  OCI_CODE_LIMA_FIRECRACKER_CI_VERSION
  OCI_CODE_LIMA_FIRECRACKER_DNS
  OCI_CODE_LIMA_FIRECRACKER_HOME
  OCI_CODE_LIMA_FIRECRACKER_BIN_DIR
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --force)
      FORCE_REBUILD=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Required tool not found: $1" >&2
    exit 1
  }
}

append_guest_export() {
  local name="$1"
  local value="${!name:-}"
  [ -n "${value}" ] || return 0
  GUEST_EXPORTS="${GUEST_EXPORTS}export ${name}=$(printf '%q' "${value}") && "
}

require_tool "${LIMACTL_BIN}"

"${LIMACTL_BIN}" start -y --timeout 10m "${INSTANCE}" >/dev/null

"${LIMACTL_BIN}" shell "${INSTANCE}" -- sh -lc "rm -rf '${GUEST_TMP_DIR}' && mkdir -p '${GUEST_TMP_DIR}'"
"${LIMACTL_BIN}" copy --backend auto \
  "${SCRIPT_DIR}/oci-code-lima-install-firecracker-guest.sh" \
  "${SCRIPT_DIR}/oci-code-lima-firecracker-orchestrator.sh" \
  "${SCRIPT_DIR}/oci-code-firecracker-microvm-init.sh" \
  "${INSTANCE}:${GUEST_TMP_DIR}/"

GUEST_EXPORTS=""
append_guest_export "OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC"
append_guest_export "OCI_CODE_LIMA_FIRECRACKER_VERSION"
append_guest_export "OCI_CODE_LIMA_FIRECRACKER_CI_VERSION"
append_guest_export "OCI_CODE_LIMA_FIRECRACKER_DNS"
append_guest_export "OCI_CODE_LIMA_FIRECRACKER_HOME"
append_guest_export "OCI_CODE_LIMA_FIRECRACKER_BIN_DIR"
if [ "${FORCE_REBUILD}" = "true" ]; then
  GUEST_EXPORTS="${GUEST_EXPORTS}export OCI_CODE_LIMA_FIRECRACKER_FORCE_REBUILD=true && "
fi
INSTALL_ARGS=""
if [ "${FORCE_REBUILD}" = "true" ]; then
  INSTALL_ARGS=" --force"
fi

"${LIMACTL_BIN}" shell "${INSTANCE}" -- sh -lc \
  "${GUEST_EXPORTS}chmod +x '${GUEST_TMP_DIR}/oci-code-lima-install-firecracker-guest.sh' '${GUEST_TMP_DIR}/oci-code-lima-firecracker-orchestrator.sh' '${GUEST_TMP_DIR}/oci-code-firecracker-microvm-init.sh' && '${GUEST_TMP_DIR}/oci-code-lima-install-firecracker-guest.sh'${INSTALL_ARGS}"

cat <<EOF
Nested Firecracker guest setup completed for Lima instance ${INSTANCE}.

Use these host-side exports:
  export OCI_CODE_FIRECRACKER_RUNNER_CMD="${SCRIPT_DIR}/oci-code-firecracker-runner"
  export OCI_CODE_RUNNER_BACKEND="lima"
  export OCI_CODE_LIMA_INSTANCE="${INSTANCE}"

Repro steps:
  ${SCRIPT_DIR}/oci-code-lima-firecracker-smoke-test.sh
  ${SCRIPT_DIR}/oci-code-lima-firecracker-smoke-test.sh --oci-regions

Guest default delegate path:
  ~/.local/bin/oci-code-lima-firecracker-orchestrator

Rerun behavior:
  Subsequent setup runs reuse the guest Firecracker assets when the cached build inputs still match.
  Use --force to rebuild the inner rootfs explicitly.
EOF
