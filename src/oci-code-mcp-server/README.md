# OCI Code MCP Server

## Overview

`oracle.oci-code-mcp-server` is a host-side MCP server for running OCI Python SDK snippets inside an ephemeral Firecracker microVM instead of executing arbitrary Python in-process.

The host server:

- accepts Python code over MCP
- validates it with AST guardrails as defense in depth
- serializes only the minimum OCI auth material needed for the guest
- hands execution to a Firecracker runner command
- expects the runner to resume a snapshot, enforce strict limits, allow only OCI egress, and destroy the VM after the request
- returns only the JSON-serializable result plus minimal sandbox metadata

This package intentionally separates the MCP interface from the Linux-only Firecracker wiring. The repo does not yet include the actual Firecracker launcher, jailer setup, TAP networking, or nftables rules; those are expected to be provided by the external runner command configured for this server.
For macOS local development, the repo does include a Lima-based nested Firecracker path that provisions those pieces inside a Linux guest.

## Security model

The safety boundary is the microVM, not the Python AST filter.

- The AST policy blocks obviously dangerous imports and reflective escape hatches.
- The guest runner strips dangerous builtins as another layer.
- The real enforcement point is the Firecracker runtime plus host network policy.

If the external runner is not configured, the server refuses execution rather than falling back to in-process Python.

## Running the server

### STDIO transport mode

```sh
OCI_CODE_FIRECRACKER_RUNNER_CMD=/usr/local/bin/oci-code-firecracker-runner uvx oracle.oci-code-mcp-server
```

### HTTP streaming transport mode

```sh
ORACLE_MCP_HOST=<hostname/IP address> ORACLE_MCP_PORT=<port number> OCI_CODE_FIRECRACKER_RUNNER_CMD=/usr/local/bin/oci-code-firecracker-runner uvx oracle.oci-code-mcp-server
```

For repo-local development, this package now ships a helper wrapper at `scripts/oci-code-firecracker-runner`. A typical local setup looks like:

```sh
export OCI_CODE_FIRECRACKER_RUNNER_CMD="/path/to/repo/src/oci-code-mcp-server/scripts/oci-code-firecracker-runner"
```

## macOS Local Dev With Lima Nested Virtualization

The `lima` backend is the recommended local-dev path on macOS. It uses Lima to boot or reuse a Linux guest with nested virtualization enabled, stages the manifest and project into that guest, and then runs a guest-side helper that will:

- provision a guest-local Firecracker runtime inside the Lima VM
- invoke a real nested Firecracker microVM inside that guest for every request

This is the practical macOS path for testing "Linux guest runs Firecracker" without depending on a separately signed host helper with Apple virtualization entitlements.

Prerequisites on macOS:

- Lima installed and `limactl` available on the host
- a Lima instance started with `--vm-type=vz --nested-virt`
- a Linux guest that exposes `/dev/kvm` when nested virtualization is working
- enough host permissions to let the Lima guest create TAP devices and access `/dev/kvm`

Typical instance bring-up:

```sh
limactl start --vm-type=vz --nested-virt --name firecracker-dev template:default
limactl shell firecracker-dev -- sh -lc 'test -c /dev/kvm && echo kvm-present || echo no-kvm'
```

## Required environment

| Variable | Description |
| --- | --- |
| `OCI_CODE_FIRECRACKER_RUNNER_CMD` | Required. External command that resumes a Firecracker snapshot, runs the guest bootstrap, and writes a JSON result payload. |
| `OCI_CODE_RUNNER_BACKEND` | Optional. `delegate` for a real Linux-side Firecracker orchestrator, `lima` for macOS Lima-based nested-virt bring-up, or `emulator` for unsafe host-local testing. Default: `delegate`. |
| `OCI_CODE_FIRECRACKER_DELEGATE_CMD` | Required when `OCI_CODE_RUNNER_BACKEND=delegate`. The real orchestrator command invoked by the wrapper. |
| `OCI_CODE_LIMACTL_BIN` | Optional `limactl` binary path. Default: `limactl`. |
| `OCI_CODE_LIMA_INSTANCE` | Optional Lima instance name. Default: `firecracker-dev`. |
| `OCI_CODE_LIMA_START_TEMPLATE` | Optional Lima template used if the instance does not already exist. Default: `template:default`. |
| `OCI_CODE_LIMA_VM_TYPE` | Optional Lima VM type used during first boot. Default: `vz`. |
| `OCI_CODE_LIMA_START_TIMEOUT` | Optional `limactl start --timeout` value. Default: `10m`. |
| `OCI_CODE_LIMA_ENABLE_NESTED_VIRT` | Optional. When true, add `--nested-virt` when creating a new instance. Default: `true`. |
| `OCI_CODE_LIMA_COPY_BACKEND` | Optional Lima copy backend: `auto`, `scp`, or `rsync`. Default: `auto`. |
| `OCI_CODE_LIMA_GUEST_ROOT` | Optional base directory inside the Lima guest where staged requests are copied. Default: `/tmp/oci-code-mcp`. |
| `OCI_CODE_LIMA_GUEST_FIRECRACKER_CMD` | Optional guest-local command that launches the Firecracker microVM and consumes `--manifest ...`. Default inside the Lima guest: `~/.local/bin/oci-code-lima-firecracker-orchestrator`. |
| `OCI_CODE_LIMA_GUEST_VENV_ROOT` | Optional guest-side venv cache root used by `oci-code-lima-guest-runner.sh`. |
| `OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC` | Optional OCI SDK pip spec installed in the Lima guest venv. Default: `oci==2.160.0`. |
| `OCI_CODE_LIMA_KEEP_GUEST_BUNDLE` | Optional. When true, keep the staged request bundle in the Lima guest after execution for debugging. Default: `false`. |
| `OCI_CODE_LIMA_FIRECRACKER_FORCE_REBUILD` | Optional. When true, rebuild the inner Firecracker rootfs instead of reusing matching cached guest assets. The setup script also accepts `--force`. |
| `OCI_CODE_SNAPSHOT_NAME` | Optional. Snapshot label to request from the runner. Default: `oci-python-sdk-default`. |
| `OCI_CODE_ALLOWED_EGRESS` | Optional comma-separated domain suffix allowlist passed to the runner. Default: `*.oraclecloud.com`. |
| `OCI_CONFIG_FILE` | Optional OCI config path used to source auth material on the host. |
| `OCI_CONFIG_PROFILE` | Optional default OCI profile if the tool call does not specify one. |

## Tool

| Tool Name | Description |
| --- | --- |
| `execute_oci_python` | Execute restricted Python inside an ephemeral Firecracker-backed OCI sandbox. |

### `execute_oci_python`

The code contract is intentionally small:

- define `main(input_data)` and return a JSON-serializable value, or
- assign a top-level `result`

The guest runtime also injects these helpers:

- `INPUT`: the `input_data` object passed to the tool
- `load_oci_config()`: load the guest OCI config file
- `build_oci_signer()`: build a signer from the injected auth material
- `create_oci_client(SomeSdkClient)`: instantiate an OCI SDK client with the guest config and signer

Example:

```python
from oci.identity import IdentityClient


def main(input_data):
    client = create_oci_client(IdentityClient)
    response = client.list_regions()
    return [region.name for region in response.data]
```

Example MCP payload:

```json
{
  "code": "from oci.identity import IdentityClient\n\ndef main(input_data):\n    client = create_oci_client(IdentityClient)\n    response = client.list_regions()\n    return [region.name for region in response.data]\n",
  "input_data": {},
  "timeout_seconds": 30,
  "memory_limit_mib": 512
}
```

Example response shape:

```json
{
  "request_id": "95d13e4f6c234636a77424eb5bd45543",
  "result": ["us-ashburn-1", "us-phoenix-1"],
  "sandbox": {
    "executor": "firecracker-command",
    "snapshot": "oci-python-sdk-default",
    "resumed_from_snapshot": true,
    "vm_id": "oci-code-95d13e4f6c234636a77424eb5bd45543",
    "execution_time_ms": 812
  }
}
```

## Firecracker runner contract

The configured runner command is invoked with:

```text
<runner> --manifest /tmp/.../request.json
```

This package now includes a stable wrapper command named `oci-code-firecracker-runner`. It supports these modes:

- `delegate`: production shape. Validate the manifest and forward it to `OCI_CODE_FIRECRACKER_DELEGATE_CMD --manifest ...`.
- `lima`: macOS local-dev path. Start or reuse a Lima guest, stage the manifest and project into Linux, and run a guest-side helper that launches a nested Firecracker microVM inside that VM.
- `emulator`: unsafe local mode. Execute the guest runner directly on the host for testing only.

Recommended usage:

```sh
export OCI_CODE_FIRECRACKER_RUNNER_CMD="/usr/local/bin/oci-code-firecracker-runner"
export OCI_CODE_RUNNER_BACKEND="delegate"
export OCI_CODE_FIRECRACKER_DELEGATE_CMD="/usr/local/bin/real-firecracker-orchestrator"
```

Unsafe host-local bring-up only:

```sh
export OCI_CODE_FIRECRACKER_RUNNER_CMD="/path/to/repo/src/oci-code-mcp-server/scripts/oci-code-firecracker-runner"
export OCI_CODE_RUNNER_BACKEND="emulator"
```

Lima-backed local development on macOS:

```sh
limactl start --vm-type=vz --nested-virt --name firecracker-dev template:default

export OCI_CODE_FIRECRACKER_RUNNER_CMD="$PWD/scripts/oci-code-firecracker-runner"
export OCI_CODE_RUNNER_BACKEND="lima"
export OCI_CODE_LIMA_INSTANCE="firecracker-dev"
```

The repo ships these local-dev helpers:

- `scripts/oci-code-lima-guest-runner.sh`: guest-side helper copied into the Lima VM for every request
- `scripts/oci-code-lima-setup-firecracker.sh`: host-side installer that provisions Firecracker, its kernel/rootfs, and the guest-local orchestrator inside the Lima VM
- `scripts/oci-code-lima-firecracker-smoke-test.sh`: host-side smoke test that exercises the nested Firecracker path end-to-end

### Smoke test the `lima` backend

Real Firecracker path inside the Lima guest:

```sh
cd /path/to/repo/src/oci-code-mcp-server
./scripts/oci-code-lima-setup-firecracker.sh
./scripts/oci-code-lima-firecracker-smoke-test.sh
```

The setup step is incremental. If the guest already has matching Firecracker assets, rerunning it reuses them. Use `./scripts/oci-code-lima-setup-firecracker.sh --force` to rebuild the inner rootfs explicitly.

For a real OCI SDK request after the echo smoke test passes:

```sh
./scripts/oci-code-lima-firecracker-smoke-test.sh --oci-regions
```

The Lima helper runs the package runner in `delegate` mode inside Linux. The reproducible local-dev path in this repo installs that delegate as `~/.local/bin/oci-code-lima-firecracker-orchestrator` inside the Lima guest, and the guest helper uses that path automatically unless you override `OCI_CODE_LIMA_GUEST_FIRECRACKER_CMD`.

The manifest contains:

- request id
- snapshot name
- code
- JSON input payload
- timeout and memory limits
- requested OCI-only egress policy
- serialized OCI auth bundle
- result file path

The runner is expected to:

1. resume or launch a microVM from the requested snapshot
2. inject the manifest into the guest
3. run `python -m oracle.oci_code_mcp_server.guest_runner --manifest <path-inside-guest>`
4. enforce timeout, memory, and OCI-only egress
5. destroy the VM after the request
6. write a JSON result payload to the host-visible result path

When using the included wrapper in `delegate` mode, the low-level Firecracker orchestration still lives behind `OCI_CODE_FIRECRACKER_DELEGATE_CMD`. That lets the MCP server and manifest contract stay stable while the Linux-specific implementation evolves independently.

## Limitations

- The production security story depends on Linux Firecracker infrastructure that is not bundled in this repo yet.
- The `lima` backend depends on a Lima guest that actually exposes `/dev/kvm`; a running Lima VM alone is not enough.
- The `lima` backend assumes the guest can create TAP devices, enable IPv4 forwarding, and access `/dev/kvm`; those operations may still require local host approval depending on your Lima setup.
- The included `emulator` backend is intentionally unsafe and should only be used for local testing.
- The egress policy is passed symbolically as domain suffixes; the external runner must translate that into concrete network controls.
- The AST filter is intentionally conservative and may reject some metaprogramming-heavy snippets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment, Firecracker runner hardening, OCI credential safety, and network policy enforcement.
