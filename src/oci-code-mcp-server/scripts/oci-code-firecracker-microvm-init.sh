#!/usr/bin/env bash
set -euo pipefail

DATA_MOUNT="/mnt/oci-code-data"
RESULT_PATH="${DATA_MOUNT}/stage/result.json"
MANIFEST_PATH="${DATA_MOUNT}/stage/request.json"

log() {
  echo "[oci-code-init] $*" > /dev/console
}

cmdline_value() {
  local key="$1"
  local value
  value="$(tr ' ' '\n' </proc/cmdline | awk -F= -v key="${key}" '$1 == key { print substr($0, index($0, "=") + 1); exit }')"
  printf '%s' "${value}"
}

first_non_loopback_iface() {
  local iface
  for iface in /sys/class/net/*; do
    iface="$(basename "${iface}")"
    if [ "${iface}" != "lo" ]; then
      printf '%s' "${iface}"
      return 0
    fi
  done
  return 1
}

write_failure_payload() {
  local message="$1"
  mkdir -p "$(dirname "${RESULT_PATH}")"
  python3 - "${MANIFEST_PATH}" "${RESULT_PATH}" "${message}" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
result_path = Path(sys.argv[2])
message = sys.argv[3]

request_id = "unknown-request"
vm_id = None
resume_snapshot = True
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
    request_id = manifest.get("request_id", request_id)
    vm_id = manifest.get("vm_id")
    resume_snapshot = bool(manifest.get("resume_snapshot", True))

payload = {
    "ok": False,
    "request_id": request_id,
    "error": {"type": "MicroVMInitError", "message": message},
    "vm_id": vm_id,
    "resumed_from_snapshot": resume_snapshot,
}
result_path.write_text(json.dumps(payload))
PY
}

cleanup_and_exit() {
  sync || true
  reboot -f || poweroff -f || /sbin/reboot -f || true
  sleep 2
  echo b >/proc/sysrq-trigger || true
  exit "${1:-0}"
}

mount -t proc proc /proc || true
mount -t sysfs sysfs /sys || true
mount -t devtmpfs devtmpfs /dev || true
mount -t tmpfs tmpfs /run || true
mount -t tmpfs tmpfs /tmp || true

mkdir -p "${DATA_MOUNT}"
if ! mount /dev/vdb "${DATA_MOUNT}"; then
  log "failed to mount /dev/vdb"
  write_failure_payload "Failed to mount the staged request disk"
  cleanup_and_exit 1
fi

GUEST_IP="$(cmdline_value oci.guest_ip)"
HOST_IP="$(cmdline_value oci.host_ip)"
DNS_IP="$(cmdline_value oci.dns)"
IFACE="$(first_non_loopback_iface || true)"

if [ -n "${IFACE}" ] && [ -n "${GUEST_IP}" ] && [ -n "${HOST_IP}" ]; then
  ip link set "${IFACE}" up || true
  ip addr flush dev "${IFACE}" || true
  ip addr add "${GUEST_IP}/30" dev "${IFACE}" || true
  ip route replace default via "${HOST_IP}" dev "${IFACE}" || true
fi

if [ -n "${DNS_IP}" ]; then
  printf 'nameserver %s\n' "${DNS_IP}" > /etc/resolv.conf
fi

if [ ! -f "${MANIFEST_PATH}" ]; then
  log "manifest missing at ${MANIFEST_PATH}"
  write_failure_payload "Manifest is missing from the staged request disk"
  cleanup_and_exit 1
fi

if [ ! -d "${DATA_MOUNT}/project/oracle/oci_code_mcp_server" ]; then
  log "project checkout missing on staged request disk"
  write_failure_payload "Project checkout is missing from the staged request disk"
  cleanup_and_exit 1
fi

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="${DATA_MOUNT}/project${PYTHONPATH:+:${PYTHONPATH}}"
export TMPDIR="${DATA_MOUNT}/tmp"
mkdir -p "${TMPDIR}"
PYTHON_BIN="/opt/oci-code-venv/bin/python"
[ -x "${PYTHON_BIN}" ] || PYTHON_BIN="$(command -v python3)"

if ! "${PYTHON_BIN}" -m oracle.oci_code_mcp_server.guest_runner --manifest "${MANIFEST_PATH}"; then
  log "guest runner exited non-zero"
fi

[ -f "${RESULT_PATH}" ] || write_failure_payload "Guest runner completed without writing a result payload"
sync || true
cleanup_and_exit 0
