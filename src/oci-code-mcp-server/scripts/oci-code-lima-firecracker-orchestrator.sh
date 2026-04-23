#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: oci-code-lima-firecracker-orchestrator.sh --manifest /path/to/request.json

Run a nested Firecracker microVM inside the current Lima guest. The script:
- rewrites the staged manifest for the nested microVM
- builds a request data disk containing stage/ and project/
- creates a tap/NAT network for OCI egress
- launches Firecracker with a prepared kernel and rootfs template
- copies the result payload back to the original manifest.result_path
EOF
}

MANIFEST_PATH=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --manifest)
      MANIFEST_PATH="$2"
      shift 2
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

[ -n "${MANIFEST_PATH}" ] || {
  usage >&2
  exit 1
}
[ -f "${MANIFEST_PATH}" ] || {
  echo "Manifest not found: ${MANIFEST_PATH}" >&2
  exit 1
}

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Required tool not found: $1" >&2
    exit 1
  }
}

require_tool python3
require_tool jq
require_tool sudo
require_tool truncate
require_tool mkfs.ext4
require_tool ip
require_tool iptables
require_tool mount
require_tool umount
require_tool setfacl
require_tool timeout

FIRECRACKER_BIN="${OCI_CODE_LIMA_FIRECRACKER_BIN:-${HOME}/.local/bin/firecracker}"
KERNEL_PATH="${OCI_CODE_LIMA_FIRECRACKER_KERNEL_PATH:-${HOME}/.local/share/oci-code-firecracker/vmlinux}"
ROOTFS_TEMPLATE="${OCI_CODE_LIMA_FIRECRACKER_ROOTFS_TEMPLATE:-${HOME}/.local/share/oci-code-firecracker/rootfs.ext4}"
RUN_ROOT="${OCI_CODE_LIMA_FIRECRACKER_RUN_ROOT:-/tmp/oci-code-firecracker}"
DNS_SERVER="${OCI_CODE_LIMA_FIRECRACKER_DNS:-1.1.1.1}"
KEEP_WORKDIR="${OCI_CODE_LIMA_FIRECRACKER_KEEP_WORKDIR:-false}"

[ -x "${FIRECRACKER_BIN}" ] || {
  echo "Firecracker binary not found or not executable: ${FIRECRACKER_BIN}" >&2
  exit 1
}
[ -f "${KERNEL_PATH}" ] || {
  echo "Kernel image not found: ${KERNEL_PATH}" >&2
  exit 1
}
[ -f "${ROOTFS_TEMPLATE}" ] || {
  echo "Rootfs template not found: ${ROOTFS_TEMPLATE}" >&2
  exit 1
}

REQUEST_ID="$(python3 - "${MANIFEST_PATH}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
print(manifest["request_id"])
PY
)"
HOST_RESULT_PATH="$(python3 - "${MANIFEST_PATH}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
print(manifest.get("result_path", ""))
PY
)"
TIMEOUT_SECONDS="$(python3 - "${MANIFEST_PATH}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
print(manifest.get("limits", {}).get("timeout_seconds", 30))
PY
)"
MEMORY_MIB="$(python3 - "${MANIFEST_PATH}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
print(max(manifest.get("limits", {}).get("memory_limit_mib", 512), 256))
PY
)"
VCPU_COUNT="$(python3 - "${MANIFEST_PATH}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
print(max(manifest.get("limits", {}).get("vcpu_count", 1), 1))
PY
)"

REQUEST_ROOT="$(cd "$(dirname "${MANIFEST_PATH}")/.." && pwd)"
PROJECT_SOURCE="${REQUEST_ROOT}/project"

[ -d "${PROJECT_SOURCE}/oracle/oci_code_mcp_server" ] || {
  echo "Expected staged project checkout at ${PROJECT_SOURCE}" >&2
  exit 1
}

WORKDIR="${RUN_ROOT}/${REQUEST_ID}"
BUNDLE_ROOT="${WORKDIR}/bundle"
DATA_IMAGE="${WORKDIR}/data.ext4"
ROOTFS_IMAGE="${WORKDIR}/rootfs.ext4"
FIRECRACKER_CONFIG="${WORKDIR}/firecracker.json"
API_SOCKET="${WORKDIR}/firecracker.sock"
FC_STDERR="${WORKDIR}/firecracker.stderr.log"
FC_STDOUT="${WORKDIR}/firecracker.stdout.log"
MOUNT_DIR="${WORKDIR}/mount"

mkdir -p "${WORKDIR}" "${BUNDLE_ROOT}/stage" "${BUNDLE_ROOT}/project" "${MOUNT_DIR}"

cleanup() {
  set +e
  if mountpoint -q "${MOUNT_DIR}"; then
    sudo umount "${MOUNT_DIR}" >/dev/null 2>&1 || true
  fi
  if [ -n "${TAP_DEV:-}" ]; then
    sudo iptables -D FORWARD -i "${TAP_DEV}" -j ACCEPT >/dev/null 2>&1 || true
    sudo iptables -D FORWARD -o "${TAP_DEV}" -m state --state RELATED,ESTABLISHED -j ACCEPT >/dev/null 2>&1 || true
    sudo iptables -t nat -D POSTROUTING -s "${GUEST_IP}/32" -o "${HOST_IFACE}" -j MASQUERADE >/dev/null 2>&1 || true
    sudo ip link del "${TAP_DEV}" >/dev/null 2>&1 || true
  fi
  if [ "${KEEP_WORKDIR}" != "true" ]; then
    rm -rf "${WORKDIR}"
  fi
}
trap cleanup EXIT

write_failure_payload() {
  local message="$1"
  python3 - "${MANIFEST_PATH}" "${HOST_RESULT_PATH}" "${message}" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
result_path = Path(sys.argv[2])
message = sys.argv[3]

payload = {
    "ok": False,
    "request_id": manifest.get("request_id", "unknown-request"),
    "error": {"type": "FirecrackerDelegateError", "message": message},
    "vm_id": manifest.get("vm_id"),
    "resumed_from_snapshot": bool(manifest.get("resume_snapshot", True)),
}
result_path.write_text(json.dumps(payload))
PY
}

python3 - "${MANIFEST_PATH}" "${BUNDLE_ROOT}/stage/request.json" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text())
manifest["result_path"] = "/mnt/oci-code-data/stage/result.json"
Path(sys.argv[2]).write_text(json.dumps(manifest, indent=2, sort_keys=True))
PY

cp -a "${PROJECT_SOURCE}/." "${BUNDLE_ROOT}/project/"
mkdir -p "${BUNDLE_ROOT}/tmp"

DATA_SIZE_MB="$(( $(du -sm "${BUNDLE_ROOT}" | awk '{print $1}') + 256 ))"
[ "${DATA_SIZE_MB}" -ge 512 ] || DATA_SIZE_MB=512
truncate -s "${DATA_SIZE_MB}M" "${DATA_IMAGE}"
mkfs.ext4 -q -F -d "${BUNDLE_ROOT}" "${DATA_IMAGE}"

if ! cp --reflink=auto "${ROOTFS_TEMPLATE}" "${ROOTFS_IMAGE}" 2>/dev/null; then
  cp "${ROOTFS_TEMPLATE}" "${ROOTFS_IMAGE}"
fi

sudo setfacl -m "u:${USER}:rw" /dev/kvm >/dev/null 2>&1 || true
[ -r /dev/kvm ] && [ -w /dev/kvm ] || {
  write_failure_payload "Current user cannot access /dev/kvm inside the Lima guest"
  exit 1
}

NET_OCTET="$(( (16#${REQUEST_ID:0:2} % 200) + 20 ))"
HOST_IP="172.30.${NET_OCTET}.1"
GUEST_IP="172.30.${NET_OCTET}.2"
HOST_IFACE="$(ip -j route list default | jq -r '.[0].dev')"
TAP_DEV="fc${REQUEST_ID:0:8}"
MAC_ADDR="06:00:${REQUEST_ID:0:2}:${REQUEST_ID:2:2}:${REQUEST_ID:4:2}:${REQUEST_ID:6:2}"

sudo ip link del "${TAP_DEV}" >/dev/null 2>&1 || true
sudo ip tuntap add dev "${TAP_DEV}" mode tap user "${USER}"
sudo ip addr add "${HOST_IP}/30" dev "${TAP_DEV}"
sudo ip link set dev "${TAP_DEV}" up
sudo sysctl -w net.ipv4.ip_forward=1 >/dev/null
sudo iptables -I FORWARD 1 -i "${TAP_DEV}" -j ACCEPT
sudo iptables -I FORWARD 1 -o "${TAP_DEV}" -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -s "${GUEST_IP}/32" -o "${HOST_IFACE}" -j MASQUERADE

KERNEL_ARGS="console=ttyS0 reboot=k panic=1 pci=off nomodules random.trust_cpu=on root=/dev/vda rw init=/oci-init oci.guest_ip=${GUEST_IP} oci.host_ip=${HOST_IP} oci.dns=${DNS_SERVER}"
if [ "$(uname -m)" = "aarch64" ]; then
  KERNEL_ARGS="keep_bootcon ${KERNEL_ARGS}"
fi

cat >"${FIRECRACKER_CONFIG}" <<EOF
{
  "boot-source": {
    "kernel_image_path": "${KERNEL_PATH}",
    "boot_args": "${KERNEL_ARGS}"
  },
  "drives": [
    {
      "drive_id": "rootfs",
      "path_on_host": "${ROOTFS_IMAGE}",
      "is_root_device": true,
      "is_read_only": false
    },
    {
      "drive_id": "data",
      "path_on_host": "${DATA_IMAGE}",
      "is_root_device": false,
      "is_read_only": false
    }
  ],
  "machine-config": {
    "vcpu_count": ${VCPU_COUNT},
    "mem_size_mib": ${MEMORY_MIB},
    "smt": false
  },
  "network-interfaces": [
    {
      "iface_id": "net1",
      "guest_mac": "${MAC_ADDR}",
      "host_dev_name": "${TAP_DEV}"
    }
  ]
}
EOF

set +e
timeout --signal=TERM "$(( TIMEOUT_SECONDS + 15 ))" \
  "${FIRECRACKER_BIN}" --api-sock "${API_SOCKET}" --config-file "${FIRECRACKER_CONFIG}" \
  >"${FC_STDOUT}" 2>"${FC_STDERR}"
FC_EXIT=$?
set -e

mountpoint -q "${MOUNT_DIR}" && sudo umount "${MOUNT_DIR}" >/dev/null 2>&1 || true
sudo mount -o loop,ro,noload "${DATA_IMAGE}" "${MOUNT_DIR}"

if [ -f "${MOUNT_DIR}/stage/result.json" ] && [ -n "${HOST_RESULT_PATH}" ]; then
  sudo cp "${MOUNT_DIR}/stage/result.json" "${HOST_RESULT_PATH}"
fi
sudo umount "${MOUNT_DIR}" >/dev/null

if [ -n "${HOST_RESULT_PATH}" ] && [ -f "${HOST_RESULT_PATH}" ]; then
  exit 0
fi

if [ "${FC_EXIT}" -eq 124 ]; then
  write_failure_payload "Nested Firecracker microVM timed out"
elif [ "${FC_EXIT}" -ne 0 ]; then
  write_failure_payload "Nested Firecracker exited with status ${FC_EXIT}. See ${FC_STDERR}"
else
  write_failure_payload "Nested Firecracker exited without producing a result payload"
fi

exit 1
