#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCH="$(uname -m)"

INSTALL_ROOT="${OCI_CODE_LIMA_FIRECRACKER_HOME:-${HOME}/.local/share/oci-code-firecracker}"
BIN_DIR="${OCI_CODE_LIMA_FIRECRACKER_BIN_DIR:-${HOME}/.local/bin}"
CACHE_DIR="${INSTALL_ROOT}/downloads"
BUILD_DIR="${INSTALL_ROOT}/build"
ROOTFS_DIR="${BUILD_DIR}/rootfs"
ROOTFS_IMAGE="${INSTALL_ROOT}/rootfs.ext4"
KERNEL_IMAGE="${INSTALL_ROOT}/vmlinux"
METADATA_PATH="${INSTALL_ROOT}/build-metadata.json"
OCI_PIP_SPEC="${OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC:-oci==2.160.0}"
DNS_SERVER="${OCI_CODE_LIMA_FIRECRACKER_DNS:-1.1.1.1}"
ROOTFS_VENV_DIR="/opt/oci-code-venv"
FORCE_REBUILD="${OCI_CODE_LIMA_FIRECRACKER_FORCE_REBUILD:-false}"

usage() {
  cat <<'EOF'
Usage: oci-code-lima-install-firecracker-guest.sh [--force]

Install or refresh the nested Firecracker runtime inside the current Lima guest.

Options:
  --force  Rebuild the inner Firecracker rootfs even if cached assets already match
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --force)
      FORCE_REBUILD="true"
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

mkdir -p "${INSTALL_ROOT}" "${BIN_DIR}" "${CACHE_DIR}" "${BUILD_DIR}"

require_tool() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Required tool not found: $1" >&2
    exit 1
  }
}

require_tool curl
require_tool python3
require_tool sha256sum
require_tool sudo
require_tool tar

print_summary() {
  local status_line="$1"

  cat <<EOF
${status_line}

Binaries:
  ${BIN_DIR}/firecracker
  ${BIN_DIR}/oci-code-lima-firecracker-orchestrator

Assets:
  ${KERNEL_IMAGE}
  ${ROOTFS_IMAGE}

Guest-side exports for the host runner:
  export OCI_CODE_LIMA_GUEST_FIRECRACKER_CMD="${BIN_DIR}/oci-code-lima-firecracker-orchestrator"
EOF
}

metadata_matches() {
  local init_sha="$1"
  local latest_kernel_key="$2"
  local latest_rootfs_key="$3"

  [ -f "${METADATA_PATH}" ] || return 1
  [ -x "${BIN_DIR}/firecracker" ] || return 1
  [ -f "${KERNEL_IMAGE}" ] || return 1
  [ -f "${ROOTFS_IMAGE}" ] || return 1

  python3 - "${METADATA_PATH}" "${ARCH}" "${latest_version}" "${ci_version}" "${latest_kernel_key}" "${latest_rootfs_key}" "${OCI_PIP_SPEC}" "${DNS_SERVER}" "${init_sha}" <<'PY'
import json
import sys
from pathlib import Path

metadata = json.loads(Path(sys.argv[1]).read_text())
expected = {
    "arch": sys.argv[2],
    "firecracker_version": sys.argv[3],
    "ci_version": sys.argv[4],
    "kernel_key": sys.argv[5],
    "rootfs_key": sys.argv[6],
    "oci_pip_spec": sys.argv[7],
    "dns_server": sys.argv[8],
    "microvm_init_sha256": sys.argv[9],
}
raise SystemExit(0 if metadata == expected else 1)
PY
}

write_metadata() {
  local init_sha="$1"
  local latest_kernel_key="$2"
  local latest_rootfs_key="$3"

  python3 - "${METADATA_PATH}" "${ARCH}" "${latest_version}" "${ci_version}" "${latest_kernel_key}" "${latest_rootfs_key}" "${OCI_PIP_SPEC}" "${DNS_SERVER}" "${init_sha}" <<'PY'
import json
import sys
from pathlib import Path

payload = {
    "arch": sys.argv[2],
    "firecracker_version": sys.argv[3],
    "ci_version": sys.argv[4],
    "kernel_key": sys.argv[5],
    "rootfs_key": sys.argv[6],
    "oci_pip_spec": sys.argv[7],
    "dns_server": sys.argv[8],
    "microvm_init_sha256": sys.argv[9],
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2, sort_keys=True))
PY
}

release_url="https://github.com/firecracker-microvm/firecracker/releases"
latest_version="${OCI_CODE_LIMA_FIRECRACKER_VERSION:-$(basename "$(curl -fsSLI -o /dev/null -w '%{url_effective}' "${release_url}/latest")")}"
ci_version="${OCI_CODE_LIMA_FIRECRACKER_CI_VERSION:-${latest_version%.*}}"

firecracker_tarball="${CACHE_DIR}/firecracker-${latest_version}-${ARCH}.tgz"
release_dir="${CACHE_DIR}/release-${latest_version}-${ARCH}"

latest_kernel_key="$(
  curl -fsSL "https://s3.amazonaws.com/spec.ccfc.min/?prefix=firecracker-ci/${ci_version}/${ARCH}/vmlinux-&list-type=2" \
    | grep -oP "(?<=<Key>)(firecracker-ci/${ci_version}/${ARCH}/vmlinux-[0-9]+\.[0-9]+\.[0-9]{1,3})(?=</Key>)" \
    | sort -V | tail -1
)"
latest_rootfs_key="$(
  curl -fsSL "https://s3.amazonaws.com/spec.ccfc.min/?prefix=firecracker-ci/${ci_version}/${ARCH}/ubuntu-&list-type=2" \
    | grep -oP "(?<=<Key>)(firecracker-ci/${ci_version}/${ARCH}/ubuntu-[0-9]+\.[0-9]+\.squashfs)(?=</Key>)" \
    | sort -V | tail -1
)"

[ -n "${latest_kernel_key}" ] || {
  echo "Unable to resolve a Firecracker CI kernel for ${ci_version}/${ARCH}" >&2
  exit 1
}
[ -n "${latest_rootfs_key}" ] || {
  echo "Unable to resolve a Firecracker CI Ubuntu rootfs for ${ci_version}/${ARCH}" >&2
  exit 1
}

current_init_sha="$(sha256sum "${SCRIPT_DIR}/oci-code-firecracker-microvm-init.sh" | awk '{print $1}')"

if [ "${FORCE_REBUILD}" != "true" ] && metadata_matches "${current_init_sha}" "${latest_kernel_key}" "${latest_rootfs_key}"; then
  install -m 0755 "${SCRIPT_DIR}/oci-code-lima-firecracker-orchestrator.sh" "${BIN_DIR}/oci-code-lima-firecracker-orchestrator"
  sudo setfacl -m "u:${USER}:rw" /dev/kvm >/dev/null 2>&1 || true
  print_summary "Reusing existing nested Firecracker assets inside the Lima guest."
  exit 0
fi

if command -v apt-get >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    acl \
    ca-certificates \
    curl \
    e2fsprogs \
    iproute2 \
    iptables \
    jq \
    python3 \
    python3-pip \
    python3-venv \
    rsync \
    squashfs-tools \
    util-linux
fi

if [ ! -f "${firecracker_tarball}" ]; then
  curl -fL "${release_url}/download/${latest_version}/firecracker-${latest_version}-${ARCH}.tgz" -o "${firecracker_tarball}"
fi
rm -rf "${release_dir}"
tar -xzf "${firecracker_tarball}" -C "${CACHE_DIR}"

install -m 0755 "${release_dir}/firecracker-${latest_version}-${ARCH}" "${BIN_DIR}/firecracker"
if [ -f "${release_dir}/jailer-${latest_version}-${ARCH}" ]; then
  install -m 0755 "${release_dir}/jailer-${latest_version}-${ARCH}" "${BIN_DIR}/jailer"
fi

kernel_download="${CACHE_DIR}/$(basename "${latest_kernel_key}")"
rootfs_squashfs="${CACHE_DIR}/$(basename "${latest_rootfs_key}")"

[ -f "${kernel_download}" ] || curl -fL "https://s3.amazonaws.com/spec.ccfc.min/${latest_kernel_key}" -o "${kernel_download}"
[ -f "${rootfs_squashfs}" ] || curl -fL "https://s3.amazonaws.com/spec.ccfc.min/${latest_rootfs_key}" -o "${rootfs_squashfs}"

sudo rm -rf "${ROOTFS_DIR}"
unsquashfs -f -d "${ROOTFS_DIR}" "${rootfs_squashfs}" >/dev/null

sudo cp "${SCRIPT_DIR}/oci-code-firecracker-microvm-init.sh" "${ROOTFS_DIR}/oci-init"
sudo chmod 0755 "${ROOTFS_DIR}/oci-init"
sudo mkdir -p "${ROOTFS_DIR}/tmp"
sudo chmod 1777 "${ROOTFS_DIR}/tmp"
sudo mkdir -p "${ROOTFS_DIR}/var/cache/apt/archives/partial" "${ROOTFS_DIR}/var/lib/apt/lists/partial"
sudo mkdir -p "${ROOTFS_DIR}/var/log/apt"
printf 'nameserver %s\n' "${DNS_SERVER}" | sudo tee "${ROOTFS_DIR}/etc/resolv.conf" >/dev/null

cleanup_chroot_mounts() {
  set +e
  for dir in dev sys proc; do
    if mountpoint -q "${ROOTFS_DIR}/${dir}"; then
      sudo umount "${ROOTFS_DIR}/${dir}" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup_chroot_mounts EXIT

sudo mount --bind /dev "${ROOTFS_DIR}/dev"
sudo mount --bind /sys "${ROOTFS_DIR}/sys"
sudo mount --bind /proc "${ROOTFS_DIR}/proc"

sudo chroot "${ROOTFS_DIR}" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get update
sudo chroot "${ROOTFS_DIR}" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y \
  ca-certificates \
  iproute2 \
  python3 \
  python3-venv
sudo chroot "${ROOTFS_DIR}" rm -rf "${ROOTFS_VENV_DIR}"
sudo chroot "${ROOTFS_DIR}" python3 -m venv "${ROOTFS_VENV_DIR}"
sudo chroot "${ROOTFS_DIR}" "${ROOTFS_VENV_DIR}/bin/python" -m pip install --upgrade pip
sudo chroot "${ROOTFS_DIR}" "${ROOTFS_VENV_DIR}/bin/python" -m pip install "${OCI_PIP_SPEC}"
sudo chroot "${ROOTFS_DIR}" /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get clean

cleanup_chroot_mounts
trap - EXIT

sudo chown -R root:root "${ROOTFS_DIR}"

rootfs_size_mb="$(( $(sudo du -sm "${ROOTFS_DIR}" | awk '{print $1}') + 1024 ))"
[ "${rootfs_size_mb}" -ge 1536 ] || rootfs_size_mb=1536
truncate -s "${rootfs_size_mb}M" "${ROOTFS_IMAGE}"
sudo mkfs.ext4 -q -F -d "${ROOTFS_DIR}" "${ROOTFS_IMAGE}"

install -m 0644 "${kernel_download}" "${KERNEL_IMAGE}"
install -m 0755 "${SCRIPT_DIR}/oci-code-lima-firecracker-orchestrator.sh" "${BIN_DIR}/oci-code-lima-firecracker-orchestrator"
write_metadata "${current_init_sha}" "${latest_kernel_key}" "${latest_rootfs_key}"

sudo setfacl -m "u:${USER}:rw" /dev/kvm >/dev/null 2>&1 || true

print_summary "Installed nested Firecracker assets inside the Lima guest."
