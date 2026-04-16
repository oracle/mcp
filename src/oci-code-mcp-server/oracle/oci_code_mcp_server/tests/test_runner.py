"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from oracle.oci_code_mcp_server.runner import (
    ManifestValidationError,
    RunnerManifest,
    RunnerConfigurationError,
    _bool_env,
    _delegate_command,
    _ensure_lima_instance_running,
    _finalize_proxy_backend_result,
    _limactl_binary,
    _lima_copy_backend,
    _lima_guest_root,
    _lima_guest_shell_command,
    _lima_instance_name,
    _lima_start_timeout,
    _lima_template,
    _lima_vm_type,
    _payload_to_manifest_dict,
    _read_json,
    _require_type,
    _shell_assignment,
    backend_name,
    emit_result,
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


def _completed(returncode: int = 0, stdout: str = "", stderr: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


class TestLoadManifest:
    def test_load_manifest_validates_required_fields(self, tmp_path: Path):
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps({"schema_version": 1}))

        with pytest.raises(ManifestValidationError):
            load_manifest(manifest_path)

    def test_load_manifest_rejects_bad_shapes_and_helper_errors(self, tmp_path: Path):
        missing_path = tmp_path / "missing.json"
        with pytest.raises(ManifestValidationError, match="does not exist"):
            _read_json(missing_path)

        invalid_json = tmp_path / "invalid.json"
        invalid_json.write_text("{")
        with pytest.raises(ManifestValidationError, match="not valid JSON"):
            _read_json(invalid_json)

        invalid_root = tmp_path / "invalid-root.json"
        invalid_root.write_text("[]")
        with pytest.raises(ManifestValidationError, match="root must be a JSON object"):
            _read_json(invalid_root)

        with pytest.raises(ManifestValidationError, match="must be of type str"):
            _require_type({"request_id": 1}, "request_id", str)

        payload = _manifest_payload()
        payload["schema_version"] = 2
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps(payload))
        with pytest.raises(ManifestValidationError, match="Unsupported manifest schema version"):
            load_manifest(manifest_path)

        payload["schema_version"] = 1
        payload["request_id"] = "   "
        manifest_path.write_text(json.dumps(payload))
        with pytest.raises(ManifestValidationError, match="must not be empty"):
            load_manifest(manifest_path)

        payload["request_id"] = "req-test"
        payload["allowed_egress"] = [""]
        manifest_path.write_text(json.dumps(payload))
        with pytest.raises(ManifestValidationError, match="allowed_egress"):
            load_manifest(manifest_path)

        payload["allowed_egress"] = ["*.oraclecloud.com"]
        payload["result_path"] = 123
        manifest_path.write_text(json.dumps(payload))
        with pytest.raises(ManifestValidationError, match="result_path"):
            load_manifest(manifest_path)

        payload["result_path"] = None
        payload["auth"] = "nope"
        manifest_path.write_text(json.dumps(payload))
        with pytest.raises(ManifestValidationError, match="auth"):
            load_manifest(manifest_path)

    def test_helper_accessors_and_payload_helpers(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("OCI_CODE_RUNNER_BACKEND", raising=False)
        assert backend_name() == "delegate"
        assert backend_name(" LiMa ") == "lima"

        monkeypatch.setenv("OCI_CODE_LIMACTL_BIN", " ")
        monkeypatch.setenv("OCI_CODE_LIMA_INSTANCE", " ")
        monkeypatch.setenv("OCI_CODE_LIMA_START_TEMPLATE", " ")
        monkeypatch.setenv("OCI_CODE_LIMA_VM_TYPE", " ")
        monkeypatch.setenv("OCI_CODE_LIMA_START_TIMEOUT", " ")
        monkeypatch.setenv("OCI_CODE_LIMA_COPY_BACKEND", " ")
        monkeypatch.setenv("OCI_CODE_LIMA_GUEST_ROOT", " ")
        assert _limactl_binary() == "limactl"
        assert _lima_instance_name() == "firecracker-dev"
        assert _lima_template() == "template:default"
        assert _lima_vm_type() == "vz"
        assert _lima_start_timeout() == "10m"
        assert _lima_copy_backend() == "auto"
        assert _lima_guest_root("req-1") == "/tmp/oci-code-mcp/req-1"

        assert _bool_env("MISSING_BOOL", False) is False
        monkeypatch.setenv("TEST_BOOL", "on")
        assert _bool_env("TEST_BOOL", False) is True
        monkeypatch.setenv("TEST_BOOL", "off")
        assert _bool_env("TEST_BOOL", True) is False
        assert _shell_assignment("NAME", "value with spaces") == "NAME='value with spaces'"

        minimal = RunnerManifest(
            schema_version=1,
            request_id="req-1",
            snapshot_name="snap",
            allowed_egress=["*.oraclecloud.com"],
            limits={"timeout_seconds": 30},
            code="result = 1",
            input_data={},
            auth=None,
            result_path=None,
            vm_id=None,
            resume_snapshot=True,
            destroy_after_request=True,
            guest_entrypoint=None,
        )
        assert _payload_to_manifest_dict(minimal) == {
            "schema_version": 1,
            "request_id": "req-1",
            "snapshot_name": "snap",
            "allowed_egress": ["*.oraclecloud.com"],
            "limits": {"timeout_seconds": 30},
            "code": "result = 1",
            "input": {},
            "resume_snapshot": True,
            "destroy_after_request": True,
        }


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

    def test_delegate_and_lima_helper_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys):
        monkeypatch.delenv("OCI_CODE_FIRECRACKER_DELEGATE_CMD", raising=False)
        with pytest.raises(RunnerConfigurationError, match="required"):
            _delegate_command()

        with (
            patch("oracle.oci_code_mcp_server.runner.shlex.split", return_value=[]),
            patch.dict("os.environ", {"OCI_CODE_FIRECRACKER_DELEGATE_CMD": "runner"}, clear=False),
        ):
            with pytest.raises(RunnerConfigurationError, match="is empty"):
                _delegate_command()

        existing_instance = tmp_path / "firecracker-dev"
        existing_instance.mkdir()
        with (
            patch("oracle.oci_code_mcp_server.runner._lima_instance_dir", return_value=existing_instance),
            patch("oracle.oci_code_mcp_server.runner._run_subprocess", return_value=_completed(0, "started", "")) as mock_run,
        ):
            assert _ensure_lima_instance_running() == (0, "started", "")
        assert mock_run.call_args.args[0] == ["limactl", "start", "-y", "--timeout", "10m", "firecracker-dev"]

        missing_instance = tmp_path / "missing"
        with (
            patch("oracle.oci_code_mcp_server.runner._lima_instance_dir", return_value=missing_instance),
            patch("oracle.oci_code_mcp_server.runner._run_subprocess", return_value=_completed()) as mock_run,
            patch.dict(
                "os.environ",
                {
                    "OCI_CODE_LIMA_ENABLE_NESTED_VIRT": "false",
                    "OCI_CODE_LIMA_VM_TYPE": "qemu",
                    "OCI_CODE_LIMA_START_TEMPLATE": "template://custom",
                },
                clear=False,
            ),
        ):
            _ensure_lima_instance_running()
        command = mock_run.call_args.args[0]
        assert "--nested-virt" not in command
        assert command[-1] == "template://custom"

        with patch.dict(
            "os.environ",
            {
                "OCI_CODE_LIMA_GUEST_FIRECRACKER_CMD": "/usr/local/bin/run-fc --flag",
                "OCI_CODE_LIMA_GUEST_VENV_ROOT": "/opt/venvs",
                "OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC": "oci==2.0.0",
            },
            clear=False,
        ):
            shell_command = _lima_guest_shell_command("/guest/root")
        assert "OCI_CODE_LIMA_GUEST_FIRECRACKER_CMD='/usr/local/bin/run-fc --flag'" in shell_command
        assert "OCI_CODE_LIMA_GUEST_VENV_ROOT=/opt/venvs" in shell_command
        assert "OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC=oci==2.0.0" in shell_command
        assert shell_command.endswith("bash /guest/root/project/scripts/oci-code-lima-guest-runner.sh /guest/root")

        manifest = RunnerManifest(
            schema_version=1,
            request_id="req-stdout",
            snapshot_name="snap",
            allowed_egress=["*.oraclecloud.com"],
            limits={"timeout_seconds": 30},
            code="result = 1",
            input_data={},
            auth=None,
            result_path=None,
            vm_id=None,
            resume_snapshot=True,
            destroy_after_request=True,
            guest_entrypoint=None,
        )
        assert _finalize_proxy_backend_result(manifest, 0, '{"ok": true}', "", backend_name="lima") == 0
        assert capsys.readouterr().out == '{"ok": true}'

        assert _finalize_proxy_backend_result(manifest, 7, "stdout detail", "", backend_name="delegate") == 7
        error_payload = json.loads(capsys.readouterr().out)
        assert error_payload["error"]["type"] == "DelegateExecutionError"
        assert error_payload["error"]["message"] == "stdout detail"

    def test_emit_result_and_run_runner_paths(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps(_manifest_payload()))

        manifest = RunnerManifest(
            schema_version=1,
            request_id="req-print",
            snapshot_name="snap",
            allowed_egress=["*.oraclecloud.com"],
            limits={"timeout_seconds": 30},
            code="result = 1",
            input_data={},
            auth=None,
            result_path=None,
            vm_id=None,
            resume_snapshot=True,
            destroy_after_request=True,
            guest_entrypoint=None,
        )
        emit_result(manifest, {"ok": False, "request_id": "req-print"})
        assert json.loads(capsys.readouterr().out)["request_id"] == "req-print"

        with patch("oracle.oci_code_mcp_server.runner.execute_delegate_backend", return_value=(0, "", "")):
            assert run_runner(manifest_path, cli_backend="delegate") == 0

        with patch("oracle.oci_code_mcp_server.runner.backend_name", return_value="mystery"):
            with pytest.raises(RunnerConfigurationError, match="Unsupported OCI_CODE_RUNNER_BACKEND"):
                run_runner(manifest_path, cli_backend=None)

    def test_lima_backend_covers_failure_and_copy_out_paths(self, tmp_path: Path):
        manifest_path = tmp_path / "request.json"
        manifest_path.write_text(json.dumps(_manifest_payload()))
        manifest = load_manifest(manifest_path)

        class TempDir:
            def __init__(self, name: str):
                self.name = name
                self.cleaned = False

            def cleanup(self) -> None:
                self.cleaned = True

        with patch("oracle.oci_code_mcp_server.runner._ensure_lima_instance_running", return_value=(9, "start-out", "start-err")):
            returncode, stdout, stderr = execute_lima_backend(manifest_path, manifest)
        assert (returncode, stdout, stderr) == (9, "start-out", "start-err")

        with (
            patch("oracle.oci_code_mcp_server.runner._ensure_lima_instance_running", return_value=(0, "", "")),
            patch("oracle.oci_code_mcp_server.runner._run_subprocess", return_value=_completed(42, "", "no kvm")),
        ):
            returncode, stdout, stderr = execute_lima_backend(manifest_path, manifest)
        assert (returncode, stdout, stderr) == (42, "", "no kvm")

        temp_dir = TempDir(str(tmp_path / "bundle"))
        (tmp_path / "bundle").mkdir()
        with (
            patch("oracle.oci_code_mcp_server.runner._ensure_lima_instance_running", return_value=(0, "", "")),
            patch("oracle.oci_code_mcp_server.runner._build_lima_stage_bundle", return_value=(temp_dir, tmp_path / "bundle-root", "/guest/root")),
            patch(
                "oracle.oci_code_mcp_server.runner._run_subprocess",
                side_effect=[_completed(0), _completed(1, "prep-out", "prep-err"), _completed(0)],
            ),
        ):
            returncode, stdout, stderr = execute_lima_backend(manifest_path, manifest)
        assert returncode == 1
        assert "prep-out" in stdout
        assert "prep-err" in stderr
        assert temp_dir.cleaned is True

        stdout_manifest_path = tmp_path / "stdout-request.json"
        stdout_manifest_path.write_text(json.dumps(_manifest_payload(None)))
        stdout_manifest = load_manifest(stdout_manifest_path)
        temp_dir = TempDir(str(tmp_path / "stdout-bundle"))
        (tmp_path / "stdout-bundle").mkdir()
        staged_result = Path(temp_dir.name) / "result.json"

        def fake_run(command: list[str]):
            if command[:2] == ["limactl", "shell"] and "/dev/kvm" in command[-1]:
                return _completed(0)
            if command[:2] == ["limactl", "shell"] and "mkdir -p" in command[-1]:
                return _completed(0)
            if command[:2] == ["limactl", "copy"] and command[-1].endswith("/"):
                return _completed(0)
            if command[:2] == ["limactl", "shell"] and "oci-code-lima-guest-runner.sh" in command[-1]:
                return _completed(0)
            if command[:2] == ["limactl", "copy"] and command[-1] == str(staged_result):
                staged_result.write_text('{"ok": true}')
                return _completed(5, "copy-out", "copy failed")
            if command[:2] == ["limactl", "shell"] and command[-1].startswith("rm -rf"):
                return _completed(0)
            raise AssertionError(f"Unexpected command: {command}")

        with (
            patch("oracle.oci_code_mcp_server.runner._ensure_lima_instance_running", return_value=(0, "", "")),
            patch("oracle.oci_code_mcp_server.runner._build_lima_stage_bundle", return_value=(temp_dir, tmp_path / "bundle-root", "/guest/root")),
            patch("oracle.oci_code_mcp_server.runner._run_subprocess", side_effect=fake_run),
        ):
            returncode, stdout, stderr = execute_lima_backend(stdout_manifest_path, stdout_manifest)
        assert returncode == 5
        assert '{"ok": true}' in stdout
        assert "copy failed" in stderr

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

    def test_main_prints_error_when_manifest_cannot_be_read(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        manifest_path = tmp_path / "missing.json"

        exit_code = main(["--manifest", str(manifest_path), "--backend", "emulator"])

        assert exit_code == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["type"] == "ManifestValidationError"
