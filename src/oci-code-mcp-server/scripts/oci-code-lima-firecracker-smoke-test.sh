#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTANCE="${OCI_CODE_LIMA_INSTANCE:-firecracker-dev}"
SMOKE_MODE="echo"

usage() {
  cat <<'EOF'
Usage: oci-code-lima-firecracker-smoke-test.sh [--oci-regions]

Run a host-side smoke test that exercises:
host MCP server -> Lima guest -> nested Firecracker microVM -> guest OCI Python runner

Options:
  --oci-regions  Run a real OCI SDK request (list regions) instead of the default echo test
EOF
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

if [ "${1:-}" = "--oci-regions" ]; then
  SMOKE_MODE="oci-regions"
  shift
fi

[ "$#" -eq 0 ] || {
  echo "Unexpected arguments: $*" >&2
  usage >&2
  exit 1
}

export OCI_CODE_FIRECRACKER_RUNNER_CMD="${OCI_CODE_FIRECRACKER_RUNNER_CMD:-${SCRIPT_DIR}/oci-code-firecracker-runner}"
export OCI_CODE_RUNNER_BACKEND="lima"
export OCI_CODE_LIMA_INSTANCE="${INSTANCE}"
export OCI_CODE_SMOKE_TEST_MODE="${SMOKE_MODE}"

uv run --project "${PROJECT_DIR}" python - <<'PY'
import asyncio
import os

from fastmcp import Client

from oracle.oci_code_mcp_server.server import mcp

MODE = os.environ.get("OCI_CODE_SMOKE_TEST_MODE", "echo")
if MODE == "oci-regions":
    CODE = """from oci.identity import IdentityClient

def main(input_data):
    client = create_oci_client(IdentityClient)
    response = client.list_regions()
    return [region.name for region in response.data]
"""
    INPUT = {}
else:
    CODE = """def main(input_data):
    return {"echo": input_data["value"] + 1}
"""
    INPUT = {"value": 41}


async def main() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_oci_python",
            {
                "code": CODE,
                "input_data": INPUT,
            },
        )
        print(result.data)


asyncio.run(main())
PY
