"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Optional

from fastmcp import FastMCP
from oracle.python_mcp_server.models import SandboxResult, map_sandbox_result
from oracle.python_mcp_server.sandbox import run_python as _run_python
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


@mcp.tool(description="Execute Python code in a WASM sandbox with no filesystem or network access")
def run_python(
    code: str = Field(..., description="Python source code to execute"),
    timeout: Optional[float] = Field(
        30.0,
        description="Maximum wall-clock seconds allowed for execution",
        ge=1,
        le=120,
    ),
) -> SandboxResult:
    try:
        logger.info("Executing Python code in sandbox")
        result = _run_python(code, stdin_data=None, timeout_seconds=timeout or 30.0)
        return map_sandbox_result(result)

    except Exception as e:
        logger.error(f"Error in run_python tool: {str(e)}")
        raise e


@mcp.tool(description="Execute Python code with stdin data in a WASM sandbox with no filesystem or network access")
def run_python_with_input(
    code: str = Field(..., description="Python source code to execute"),
    stdin: str = Field(..., description="Data to feed to the process's stdin"),
    timeout: Optional[float] = Field(
        30.0,
        description="Maximum wall-clock seconds allowed for execution",
        ge=1,
        le=120,
    ),
) -> SandboxResult:
    try:
        logger.info("Executing Python code in sandbox with stdin")
        result = _run_python(code, stdin_data=stdin, timeout_seconds=timeout or 30.0)
        return map_sandbox_result(result)

    except Exception as e:
        logger.error(f"Error in run_python_with_input tool: {str(e)}")
        raise e


def main() -> None:

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
