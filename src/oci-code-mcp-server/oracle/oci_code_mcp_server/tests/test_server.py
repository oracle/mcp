"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from oracle.oci_code_mcp_server.executor import (
    ExecutionLimits,
    ExecutionRequest,
    ExecutionResult,
    FirecrackerCommandExecutor,
    SandboxExecutionError,
    _load_result_payload,
)
from oracle.oci_code_mcp_server.guest_runner import execute_user_code, run_manifest
from oracle.oci_code_mcp_server.policy import CodePolicyError, make_restricted_builtins, validate_user_code
from oracle.oci_code_mcp_server.server import main, mcp


class FakeExecutor:
    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        assert request.snapshot_name == "snapshot-a"
        return ExecutionResult(
            request_id=request.request_id,
            result={"regions": ["us-ashburn-1"]},
            snapshot_name=request.snapshot_name,
            resumed_from_snapshot=True,
            vm_id="vm-123",
            execution_time_ms=17,
            executor_name="firecracker-command",
        )


class TestPolicy:
    def test_rejects_disallowed_import(self):
        with pytest.raises(CodePolicyError):
            validate_user_code("import os\n\nresult = 1\n")

    def test_restricted_builtins_strip_eval(self):
        safe_builtins = make_restricted_builtins()
        assert "eval" not in safe_builtins
        assert "len" in safe_builtins


class TestGuestRunner:
    def test_execute_user_code_uses_main(self):
        result = execute_user_code(
            """
def main(input_data):
    return {"value": input_data["value"] + 1}
""",
            {"value": 4},
        )

        assert result["result"] == {"value": 5}

    def test_run_manifest_returns_error_payload(self):
        payload = run_manifest(
            {
                "request_id": "req-1",
                "code": "import os\n\nresult = 1\n",
                "input": {},
            }
        )

        assert payload["ok"] is False
        assert payload["error"]["type"] == "CodePolicyError"


class TestExecutorHelpers:
    def test_load_result_payload_prefers_file(self, tmp_path: Path):
        result_path = tmp_path / "result.json"
        result_path.write_text(json.dumps({"ok": True, "result": {"x": 1}}))

        payload = _load_result_payload(result_path, "")

        assert payload["result"] == {"x": 1}

    def test_execute_raises_when_runner_missing(self):
        executor = FirecrackerCommandExecutor(runner_command="")
        request = ExecutionRequest(
            request_id="req-2",
            code="result = 1",
            input_data=None,
            profile_name="DEFAULT",
            snapshot_name="oci-python-sdk-default",
            auth_bundle={},
            allowed_egress=["*.oraclecloud.com"],
            limits=ExecutionLimits(),
        )

        with pytest.raises(SandboxExecutionError):
            executor.execute(request)


class TestServerTools:
    @pytest.mark.asyncio
    async def test_execute_oci_python_success(self):
        request = ExecutionRequest(
            request_id="req-3",
            code="def main(input_data):\n    return input_data\n",
            input_data={"hello": "world"},
            profile_name="DEFAULT",
            snapshot_name="snapshot-a",
            auth_bundle={},
            allowed_egress=["*.oraclecloud.com"],
            limits=ExecutionLimits(timeout_seconds=20, memory_limit_mib=256),
        )

        with (
            patch("oracle.oci_code_mcp_server.server.build_execution_request", return_value=request),
            patch("oracle.oci_code_mcp_server.server.get_executor", return_value=FakeExecutor()),
        ):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "execute_oci_python",
                        {
                            "code": "def main(input_data):\n    return input_data\n",
                            "input_data": {"hello": "world"},
                            "snapshot_name": "snapshot-a",
                        },
                    )
                ).data

        assert result["result"] == {"regions": ["us-ashburn-1"]}
        assert result["sandbox"]["vm_id"] == "vm-123"

    @pytest.mark.asyncio
    async def test_execute_oci_python_rejects_policy_violation(self):
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "execute_oci_python",
                    {
                        "code": "import os\n\nresult = 1\n",
                    },
                )

    @pytest.mark.asyncio
    async def test_execute_oci_python_surfaces_sandbox_error(self):
        request = ExecutionRequest(
            request_id="req-4",
            code="result = 1",
            input_data=None,
            profile_name="DEFAULT",
            snapshot_name="snapshot-a",
            auth_bundle={},
            allowed_egress=["*.oraclecloud.com"],
            limits=ExecutionLimits(),
        )

        failing_executor = type(
            "FailingExecutor",
            (),
            {"execute": lambda self, request: (_ for _ in ()).throw(SandboxExecutionError("boom"))},
        )()

        with (
            patch("oracle.oci_code_mcp_server.server.build_execution_request", return_value=request),
            patch("oracle.oci_code_mcp_server.server.get_executor", return_value=failing_executor),
        ):
            async with Client(mcp) as client:
                with pytest.raises(ToolError):
                    await client.call_tool("execute_oci_python", {"code": "result = 1"})


class TestMain:
    @patch("oracle.oci_code_mcp_server.server.mcp.run")
    def test_main_with_host_and_port(self, mock_mcp_run):
        with patch.dict(
            "os.environ",
            {
                "ORACLE_MCP_HOST": "127.0.0.1",
                "ORACLE_MCP_PORT": "9000",
            },
            clear=False,
        ):
            main()

        mock_mcp_run.assert_called_once_with(transport="http", host="127.0.0.1", port=9000)

    @patch("oracle.oci_code_mcp_server.server.mcp.run")
    def test_main_without_host_and_port(self, mock_mcp_run):
        with patch.dict("os.environ", {}, clear=True):
            main()

        mock_mcp_run.assert_called_once_with()
