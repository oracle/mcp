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

from oracle.oci_code_mcp_server.runner import (
    ManifestValidationError,
    execute_delegate_backend,
    execute_lima_backend,
    load_manifest,
    main,
    run_runner,
)


def _manifest_payload(result_path: str | None = None) -> dict:
    return {
        "schema_version": 1,
        "request_id": "req-test",
        "snapshot_name": "snapshot-a",
        "resume_snapshot": True,
        "destroy_after_request": True,
        "allowed_egress": ["*.oraclecloud.com"],
        "limits": {
            "timeout_seconds": 30,
            "memory_limit_mib": 512,
            "vcpu_count": 1,
            "max_result_bytes": 262144,
        },
        "auth": {
            "profile_name": "DEFAULT",
            "config": {},
            "key_pem": "PRIVATE KEY",
            "security_token": None,
        },
        "code": "result = {'ok': True}",
        "input": {"value": 1},
        "result_path": result_path,
        "vm_id": "vm-1",
        "guest_entrypoint": "python -m oracle.oci_code_mcp_server.guest_runner --manifest <manifest>",
    }


class TestLoadManifest:
    def test_load_manifest_validates_required_fields(self, tmp_path: Path):
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps({"schema_version": 1}))

        with pytest.raises(ManifestValidationError):
            load_manifest(manifest_path)


class TestRunnerBackends:
    def test_emulator_backend_writes_result_file(self, tmp_path: Path):
        result_path = tmp_path / "result.json"
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps(_manifest_payload(str(result_path))))

        exit_code = run_runner(manifest_path, cli_backend="emulator")

        assert exit_code == 0
        payload = json.loads(result_path.read_text())
        assert payload["ok"] is True
        assert payload["result"] == {"ok": True}

    @patch("oracle.oci_code_mcp_server.runner.subprocess.run")
    def test_delegate_backend_invokes_delegate_command(self, mock_run, tmp_path: Path):
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps(_manifest_payload()))
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""

        with patch.dict(
            "os.environ",
            {
                "OCI_CODE_FIRECRACKER_DELEGATE_CMD": "/usr/local/bin/real-runner --flag",
            },
            clear=False,
        ):
            execute_delegate_backend(manifest_path)

        mock_run.assert_called_once()
        called_args = mock_run.call_args.args[0]
        assert called_args[:2] == ["/usr/local/bin/real-runner", "--flag"]
        assert called_args[-2:] == ["--manifest", str(manifest_path)]

    @patch("oracle.oci_code_mcp_server.runner._run_subprocess")
    @patch("oracle.oci_code_mcp_server.runner._lima_instance_dir")
    def test_lima_backend_invokes_limactl_flow(self, mock_instance_dir, mock_run, tmp_path: Path):
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps(_manifest_payload()))
        manifest = load_manifest(manifest_path)
        mock_instance_dir.return_value = tmp_path / "missing-instance"

        def completed(returncode: int = 0, stdout: str = "", stderr: str = ""):
            class Result:
                def __init__(self):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            return Result()

        mock_run.side_effect = [
            completed(),  # limactl start
            completed(),  # kvm preflight
            completed(),  # guest prep
            completed(),  # copy in
            completed(),  # guest run
            completed(),  # copy out
            completed(),  # cleanup
        ]

        with patch.dict("os.environ", {"OCI_CODE_LIMA_INSTANCE": "firecracker-dev"}, clear=False):
            returncode, _, _ = execute_lima_backend(manifest_path, manifest)

        assert returncode == 0
        calls = [call.args[0] for call in mock_run.call_args_list]
        assert calls[0][:8] == [
            "limactl",
            "start",
            "-y",
            "--timeout",
            "10m",
            "--vm-type",
            "vz",
            "--name",
        ]
        assert calls[0][-1] == "template:default"
        assert "--nested-virt" in calls[0]
        assert calls[1][:4] == ["limactl", "shell", "--start", "firecracker-dev"]
        assert "/dev/kvm" in calls[1][-1]
        assert calls[2][:4] == ["limactl", "shell", "--start", "firecracker-dev"]
        assert calls[3][:4] == ["limactl", "copy", "--backend", "auto"]
        assert calls[4][:4] == ["limactl", "shell", "--start", "firecracker-dev"]
        assert calls[5][:4] == ["limactl", "copy", "--backend", "auto"]

    @patch("oracle.oci_code_mcp_server.runner._run_subprocess")
    @patch("oracle.oci_code_mcp_server.runner._lima_instance_dir")
    def test_lima_backend_preserves_backend_authored_failure_payload(self, mock_instance_dir, mock_run, tmp_path: Path):
        result_path = tmp_path / "result.json"
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps(_manifest_payload(str(result_path))))
        mock_instance_dir.return_value = tmp_path / "existing-instance"
        mock_instance_dir.return_value.mkdir()

        def fake_run(command: list[str]):
            class Result:
                def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            if command[:2] == ["limactl", "start"]:
                return Result(0)
            if command[:2] == ["limactl", "shell"] and "/dev/kvm" in command[-1]:
                return Result(0)
            if command[:2] == ["limactl", "shell"] and "rm -rf" in command[-1] and "mkdir -p" in command[-1]:
                return Result(0)
            if command[:2] == ["limactl", "copy"] and command[-1].endswith("/"):
                return Result(0)
            if command[:2] == ["limactl", "shell"] and "oci-code-lima-guest-runner.sh" in command[-1]:
                return Result(1, stderr="guest firecracker delegate failed")
            if command[:2] == ["limactl", "copy"] and command[-1] == str(result_path):
                result_path.write_text(
                    json.dumps(
                        {
                            "ok": False,
                            "request_id": "req-test",
                            "error": {"type": "RunnerError", "message": "firecracker launch failed"},
                        }
                    )
                )
                return Result(0)
            if command[:2] == ["limactl", "shell"] and command[-1].startswith("rm -rf"):
                return Result(0)
            raise AssertionError(f"Unexpected command: {command}")

        with patch.dict("os.environ", {"OCI_CODE_LIMA_INSTANCE": "firecracker-dev"}, clear=False):
            mock_run.side_effect = fake_run
            exit_code = run_runner(manifest_path, cli_backend="lima")

        assert exit_code == 1
        payload = json.loads(result_path.read_text())
        assert payload["error"]["message"] == "firecracker launch failed"

    def test_main_writes_error_payload_for_bad_manifest(self, tmp_path: Path):
        result_path = tmp_path / "result.json"
        manifest_path = tmp_path / "request.json"
        payload = _manifest_payload(str(result_path))
        del payload["allowed_egress"]
        manifest_path.write_text(json.dumps(payload))

        exit_code = main(["--manifest", str(manifest_path), "--backend", "emulator"])

        assert exit_code == 1
        error_payload = json.loads(result_path.read_text())
        assert error_payload["ok"] is False
        assert error_payload["error"]["type"] == "ManifestValidationError"
