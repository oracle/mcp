"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import oci

from . import __project__, __version__

DEFAULT_SNAPSHOT_NAME = "oci-python-sdk-default"
DEFAULT_ALLOWED_EGRESS = ("*.oraclecloud.com",)


class SandboxExecutionError(RuntimeError):
    """Raised when the external sandbox runner cannot complete a request."""


@dataclass(slots=True)
class ExecutionLimits:
    timeout_seconds: int = 30
    memory_limit_mib: int = 512
    vcpu_count: int = 1
    max_result_bytes: int = 262_144


@dataclass(slots=True)
class ExecutionRequest:
    request_id: str
    code: str
    input_data: dict[str, Any] | None
    profile_name: str
    snapshot_name: str
    auth_bundle: dict[str, Any]
    allowed_egress: list[str]
    limits: ExecutionLimits


@dataclass(slots=True)
class ExecutionResult:
    request_id: str
    result: Any
    snapshot_name: str
    resumed_from_snapshot: bool
    vm_id: str | None
    execution_time_ms: int
    executor_name: str

    def to_response(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "result": self.result,
            "sandbox": {
                "executor": self.executor_name,
                "snapshot": self.snapshot_name,
                "resumed_from_snapshot": self.resumed_from_snapshot,
                "vm_id": self.vm_id,
                "execution_time_ms": self.execution_time_ms,
            },
        }


def _user_agent() -> str:
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    return f"{user_agent_name}/{__version__}"


def _default_profile_name(profile_name: str | None) -> str:
    return profile_name or os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)


def _config_file_location() -> str:
    return os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION)


def collect_auth_bundle(profile_name: str | None = None) -> dict[str, Any]:
    resolved_profile = _default_profile_name(profile_name)
    config = oci.config.from_file(
        file_location=_config_file_location(),
        profile_name=resolved_profile,
    )
    config["additional_user_agent"] = _user_agent()

    filtered_config = {
        key: value
        for key, value in config.items()
        if key in {"additional_user_agent", "fingerprint", "pass_phrase", "region", "tenancy", "user"}
        and value not in (None, "")
    }

    key_pem = Path(os.path.expanduser(config["key_file"])).read_text()

    security_token = None
    token_file = os.path.expanduser(config.get("security_token_file", "") or "")
    if token_file and os.path.exists(token_file):
        security_token = Path(token_file).read_text()

    return {
        "profile_name": resolved_profile,
        "config": filtered_config,
        "key_pem": key_pem,
        "security_token": security_token,
    }


def default_allowed_egress() -> list[str]:
    configured = os.getenv("OCI_CODE_ALLOWED_EGRESS", "")
    if not configured.strip():
        return list(DEFAULT_ALLOWED_EGRESS)
    return [item.strip() for item in configured.split(",") if item.strip()]


def build_execution_request(
    *,
    code: str,
    input_data: dict[str, Any] | None,
    profile_name: str | None,
    snapshot_name: str | None,
    timeout_seconds: int,
    memory_limit_mib: int,
) -> ExecutionRequest:
    resolved_profile = _default_profile_name(profile_name)
    resolved_snapshot = snapshot_name or os.getenv("OCI_CODE_SNAPSHOT_NAME", DEFAULT_SNAPSHOT_NAME)
    return ExecutionRequest(
        request_id=uuid.uuid4().hex,
        code=code,
        input_data=input_data,
        profile_name=resolved_profile,
        snapshot_name=resolved_snapshot,
        auth_bundle=collect_auth_bundle(resolved_profile),
        allowed_egress=default_allowed_egress(),
        limits=ExecutionLimits(
            timeout_seconds=timeout_seconds,
            memory_limit_mib=memory_limit_mib,
        ),
    )


class FirecrackerCommandExecutor:
    """Host-side adapter that delegates microVM work to an external runner command."""

    executor_name = "firecracker-command"

    def __init__(
        self,
        runner_command: str | None = None,
        *,
        host_timeout_buffer_seconds: int = 5,
    ) -> None:
        self.runner_command = runner_command or os.getenv("OCI_CODE_FIRECRACKER_RUNNER_CMD", "").strip()
        self.host_timeout_buffer_seconds = host_timeout_buffer_seconds

    def _manifest(self, request: ExecutionRequest, result_path: Path) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "request_id": request.request_id,
            "snapshot_name": request.snapshot_name,
            "resume_snapshot": True,
            "destroy_after_request": True,
            "allowed_egress": request.allowed_egress,
            "limits": asdict(request.limits),
            "auth": request.auth_bundle,
            "code": request.code,
            "input": request.input_data,
            "result_path": str(result_path),
            "vm_id": f"oci-code-{request.request_id}",
            "guest_entrypoint": "python -m oracle.oci_code_mcp_server.guest_runner --manifest <manifest>",
        }

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if not self.runner_command:
            raise SandboxExecutionError(
                "OCI_CODE_FIRECRACKER_RUNNER_CMD is not configured; refusing to execute code without a sandbox"
            )

        command = shlex.split(self.runner_command)
        if not command:
            raise SandboxExecutionError("OCI_CODE_FIRECRACKER_RUNNER_CMD is empty")

        with tempfile.TemporaryDirectory(prefix="oci-code-host-") as temp_dir:
            temp_path = Path(temp_dir)
            manifest_path = temp_path / "request.json"
            result_path = temp_path / "result.json"
            manifest = self._manifest(request, result_path)
            manifest_path.write_text(json.dumps(manifest))

            started_at = time.monotonic()
            try:
                completed = subprocess.run(
                    [*command, "--manifest", str(manifest_path)],
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=False,
                    timeout=request.limits.timeout_seconds + self.host_timeout_buffer_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                raise SandboxExecutionError("Firecracker runner exceeded the host timeout buffer") from exc

            payload: dict[str, Any] | None = None
            if result_path.exists() or completed.stdout.strip():
                payload = _load_result_payload(result_path, completed.stdout)

            if completed.returncode != 0:
                if payload and not payload.get("ok"):
                    error = payload.get("error", {})
                    error_type = error.get("type", "ExecutionError")
                    error_message = error.get("message", "unknown sandbox error")
                    raise SandboxExecutionError(f"{error_type}: {error_message}")
                stderr = (completed.stderr or "").strip()
                raise SandboxExecutionError(
                    f"Firecracker runner failed with exit code {completed.returncode}: {stderr or 'no stderr'}"
                )

            if payload is None:
                raise SandboxExecutionError("Firecracker runner finished without producing a result payload")
            duration_ms = int((time.monotonic() - started_at) * 1000)
            if not payload.get("ok"):
                error = payload.get("error", {})
                error_type = error.get("type", "ExecutionError")
                error_message = error.get("message", "unknown sandbox error")
                raise SandboxExecutionError(f"{error_type}: {error_message}")

            return ExecutionResult(
                request_id=request.request_id,
                result=payload.get("result"),
                snapshot_name=request.snapshot_name,
                resumed_from_snapshot=bool(payload.get("resumed_from_snapshot", True)),
                vm_id=payload.get("vm_id"),
                execution_time_ms=duration_ms,
                executor_name=self.executor_name,
            )


def _load_result_payload(result_path: Path, stdout: str) -> dict[str, Any]:
    if result_path.exists():
        return json.loads(result_path.read_text())
    if stdout.strip():
        return json.loads(stdout)
    raise SandboxExecutionError("Firecracker runner finished without producing a result payload")
