"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import os
from logging import Logger
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from . import __project__
from .executor import FirecrackerCommandExecutor, SandboxExecutionError, build_execution_request
from .policy import CodePolicyError, validate_user_code

logger = Logger(__name__, level="INFO")

mcp = FastMCP(
    name=__project__,
    instructions="""
        This server executes OCI Python SDK snippets inside an ephemeral Firecracker-backed sandbox.
        Use execute_oci_python for code that must call the OCI Python SDK.
        The code must define main(input_data) or assign a top-level result.
        The host never executes arbitrary user code in-process.
    """,
)


@mcp.resource("resource://oci-code-execution-contract")
def code_execution_contract() -> str:
    return """
OCI code execution contract:
- Define main(input_data) and return a JSON-serializable value, or assign a top-level result.
- INPUT is injected as a convenience alias for input_data.
- Guest helpers: load_oci_config(), build_oci_signer(), create_oci_client(SomeClient)
- Only a narrow stdlib import allowlist is accepted; os/subprocess/socket/importlib and reflective dunder access are blocked.
- The runner must execute inside a Firecracker microVM and destroy the VM after the request.
""".strip()


def get_executor() -> FirecrackerCommandExecutor:
    return FirecrackerCommandExecutor()


@mcp.tool(
    description="Execute restricted Python against the OCI Python SDK inside an ephemeral Firecracker sandbox"
)
def execute_oci_python(
    code: str = Field(
        ...,
        description=(
            "Python source code. Define main(input_data) or assign a top-level result. "
            "The guest also provides INPUT, load_oci_config(), build_oci_signer(), "
            "and create_oci_client(SomeClient)."
        ),
    ),
    input_data: dict[str, Any] | None = Field(
        None,
        description="Optional JSON object passed to main(input_data) and exposed as INPUT.",
    ),
    timeout_seconds: int = Field(
        30,
        ge=1,
        le=120,
        description="Maximum guest runtime in seconds.",
    ),
    memory_limit_mib: int = Field(
        512,
        ge=128,
        le=8192,
        description="Maximum guest memory in MiB.",
    ),
    snapshot_name: str | None = Field(
        None,
        description="Optional Firecracker snapshot label. Defaults to OCI_CODE_SNAPSHOT_NAME.",
    ),
    profile_name: str | None = Field(
        None,
        description="Optional OCI config profile to serialize into the guest.",
    ),
) -> dict[str, Any]:
    try:
        validate_user_code(code)
        request = build_execution_request(
            code=code,
            input_data=input_data,
            profile_name=profile_name,
            snapshot_name=snapshot_name,
            timeout_seconds=timeout_seconds,
            memory_limit_mib=memory_limit_mib,
        )
        result = get_executor().execute(request)
        return result.to_response()
    except CodePolicyError as exc:
        logger.error("Code policy rejected execution: %s", exc)
        raise ToolError(f"Code policy rejected execution: {exc}") from exc
    except SandboxExecutionError as exc:
        logger.error("Sandbox execution failed: %s", exc)
        raise ToolError(f"Sandbox execution failed: {exc}") from exc


def main() -> None:
    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
