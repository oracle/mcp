"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Optional

from pydantic import BaseModel, Field

from oracle.python_mcp_server.sandbox import SandboxResult as RawSandboxResult


class SandboxResult(BaseModel):
    """Result of executing Python code in the WASM sandbox."""

    stdout: Optional[str] = Field(None, description="Standard output from the executed code.")
    stderr: Optional[str] = Field(None, description="Standard error from the executed code.")
    exit_code: Optional[int] = Field(None, description="Process exit code (0 = success).")
    timed_out: Optional[bool] = Field(None, description="Whether the execution exceeded the fuel/time budget.")


def map_sandbox_result(raw: RawSandboxResult) -> SandboxResult:
    """Convert a raw SandboxResult dataclass to the Pydantic model."""
    return SandboxResult(
        stdout=raw.stdout,
        stderr=raw.stderr,
        exit_code=raw.exit_code,
        timed_out=raw.timed_out,
    )
