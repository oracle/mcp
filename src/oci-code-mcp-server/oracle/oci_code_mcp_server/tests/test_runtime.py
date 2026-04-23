"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from oracle.oci_code_mcp_server.executor import (
    DEFAULT_ALLOWED_EGRESS,
    DEFAULT_SNAPSHOT_NAME,
    ExecutionLimits,
    ExecutionRequest,
    FirecrackerCommandExecutor,
    SandboxExecutionError,
    _config_file_location,
    _default_profile_name,
    _load_result_payload,
    _user_agent,
    build_execution_request,
    collect_auth_bundle,
    default_allowed_egress,
)
from oracle.oci_code_mcp_server.guest_runner import (
    _install_auth_bundle,
    _invoke_main,
    _serialize_value,
    build_oci_signer,
    create_oci_client,
    load_oci_config,
    main as guest_main,
    run_manifest,
)
from oracle.oci_code_mcp_server.policy import (
    CodePolicyError,
    MAX_CODE_BYTES,
    make_restricted_builtins,
    validate_user_code,
)
from oracle.oci_code_mcp_server.server import code_execution_contract, get_executor


def _request() -> ExecutionRequest:
    return ExecutionRequest(
        request_id="req-test",
        code="result = 1",
        input_data={"value": 1},
        profile_name="DEFAULT",
        snapshot_name=DEFAULT_SNAPSHOT_NAME,
        auth_bundle={"profile_name": "DEFAULT", "config": {}, "key_pem": "KEY", "security_token": None},
        allowed_egress=["*.oraclecloud.com"],
        limits=ExecutionLimits(timeout_seconds=30, memory_limit_mib=512, vcpu_count=1, max_result_bytes=262144),
    )


class TestPolicyCoverage:
    def test_validate_user_code_rejects_non_string_empty_and_oversized(self):
        with pytest.raises(CodePolicyError, match="code must be a string"):
            validate_user_code(123)  # type: ignore[arg-type]
        with pytest.raises(CodePolicyError, match="code must not be empty"):
            validate_user_code("   ")
        with pytest.raises(CodePolicyError, match=str(MAX_CODE_BYTES)):
            validate_user_code("x" * (MAX_CODE_BYTES + 1))

    def test_validate_user_code_rejects_syntax_and_missing_entrypoint(self):
        with pytest.raises(CodePolicyError, match="Invalid Python syntax"):
            validate_user_code("def broken(:\n    pass\n")
        with pytest.raises(CodePolicyError, match="must define main"):
            validate_user_code("value = 1\n")

    def test_validate_user_code_rejects_relative_imports_and_banned_access(self):
        with pytest.raises(CodePolicyError, match="Relative imports are not allowed"):
            validate_user_code("from .x import y\nresult = 1\n")
        with pytest.raises(CodePolicyError, match="Call to 'open' is not allowed"):
            validate_user_code("def main(input_data):\n    return open('x')\n")
        with pytest.raises(CodePolicyError, match="Attribute '__class__' is not allowed"):
            validate_user_code("def main(input_data):\n    return input_data.__class__\n")
        with pytest.raises(CodePolicyError, match="Name 'sys' is not allowed"):
            validate_user_code("def main(input_data):\n    return sys.version\n")

    def test_validate_user_code_allows_supported_result_entrypoints(self):
        tree = validate_user_code("result: int = 1\n")
        assert tree.body
        tree = validate_user_code("from oci.identity import IdentityClient\n\ndef main():\n    return IdentityClient\n")
        assert tree.body

    def test_make_restricted_builtins_removes_quit_and_open(self):
        safe = make_restricted_builtins()
        assert "quit" not in safe
        assert "open" not in safe
        assert "sum" in safe


class TestGuestRunnerCoverage:
    def test_serialize_value_handles_paths_sets_and_fallbacks(self, tmp_path: Path):
        assert _serialize_value(tmp_path) == str(tmp_path)
        assert sorted(_serialize_value({"items": {3, 1}})["items"]) == [1, 3]

        with patch("oracle.oci_code_mcp_server.guest_runner.oci.util.to_dict", return_value={"x": 1}):
            assert _serialize_value(object()) == {"x": 1}

        class Unserializable:
            def __str__(self) -> str:
                return "custom"

        with patch("oracle.oci_code_mcp_server.guest_runner.oci.util.to_dict", side_effect=RuntimeError("nope")):
            assert _serialize_value(Unserializable()) == "custom"

    def test_load_oci_config_and_build_oci_signer_with_and_without_token(self, tmp_path: Path):
        key_file = tmp_path / "key.pem"
        key_file.write_text("KEY")
        token_file = tmp_path / "token"
        token_file.write_text("TOKEN")
        config = {
            "key_file": str(key_file),
            "security_token_file": str(token_file),
            "tenancy": "tenancy",
            "user": "user",
            "fingerprint": "fp",
        }

        with patch("oracle.oci_code_mcp_server.guest_runner.oci.config.from_file", return_value=config) as from_file:
            loaded = load_oci_config()
        assert loaded == config
        from_file.assert_called_once()

        with (
            patch("oracle.oci_code_mcp_server.guest_runner.oci.signer.load_private_key_from_file", return_value="PRIVATE"),
            patch("oracle.oci_code_mcp_server.guest_runner.oci.auth.signers.SecurityTokenSigner", return_value="TOKEN_SIGNER") as token_signer,
        ):
            assert build_oci_signer(config) == "TOKEN_SIGNER"
        token_signer.assert_called_once_with("TOKEN", "PRIVATE")

        config_no_token = dict(config)
        config_no_token["security_token_file"] = str(tmp_path / "missing-token")
        with (
            patch("oracle.oci_code_mcp_server.guest_runner.oci.signer.load_private_key_from_file", return_value="PRIVATE"),
            patch("oracle.oci_code_mcp_server.guest_runner.oci.signer.Signer", return_value="SIGNER") as signer_cls,
        ):
            assert build_oci_signer(config_no_token) == "SIGNER"
        signer_cls.assert_called_once()

    def test_create_oci_client_and_install_auth_bundle(self, tmp_path: Path):
        class DummyClient:
            def __init__(self, config, signer=None):
                self.config = config
                self.signer = signer

        with patch("oracle.oci_code_mcp_server.guest_runner.build_oci_signer", return_value="SIGNER"):
            client = create_oci_client(DummyClient, {"region": "us-ashburn-1"})
        assert client.config == {"region": "us-ashburn-1"}
        assert client.signer == "SIGNER"

        auth_bundle = {
            "profile_name": "ALT",
            "config": {"tenancy": "ocid1.tenancy", "user": "ocid1.user", "fingerprint": "fp", "region": "us-phoenix-1"},
            "key_pem": "KEY",
            "security_token": "TOKEN",
        }
        _install_auth_bundle(auth_bundle, tmp_path)
        assert Path(tmp_path / "oci_api_key.pem").read_text() == "KEY"
        assert Path(tmp_path / "security_token").read_text() == "TOKEN"
        config_text = Path(tmp_path / "config").read_text()
        assert "[ALT]" in config_text
        assert "security_token_file=" in config_text

    def test_invoke_main_validates_signatures(self):
        assert _invoke_main(lambda: "ok", {"x": 1}) == "ok"
        assert _invoke_main(lambda input_data=None: input_data["x"], {"x": 2}) == 2

        async def async_main():
            return "nope"

        def too_many(a, b):
            return a, b

        with pytest.raises(CodePolicyError, match="async main"):
            _invoke_main(async_main, {})
        with pytest.raises(CodePolicyError, match="zero or one positional"):
            _invoke_main(too_many, {})

    def test_run_manifest_success_and_guest_main(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]):
        payload = run_manifest(
            {
                "request_id": "req-success",
                "code": "print('hello')\nresult = {'value': INPUT['value'] + 2}\n",
                "input": {"value": 3},
                "vm_id": "vm-9",
                "resume_snapshot": False,
            }
        )
        assert payload["ok"] is True
        assert payload["result"] == {"value": 5}
        assert payload["guest_stdout"].strip() == "hello"
        assert payload["vm_id"] == "vm-9"
        assert payload["resumed_from_snapshot"] is False

        result_path = tmp_path / "result.json"
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "request_id": "req-cli",
                    "code": "result = 9\n",
                    "input": {},
                    "result_path": str(result_path),
                }
            )
        )
        assert guest_main(["--manifest", str(manifest_path)]) == 0
        assert json.loads(result_path.read_text())["result"] == 9

        stdout_manifest = tmp_path / "stdout-manifest.json"
        stdout_manifest.write_text(json.dumps({"request_id": "req-cli-stdout", "code": "result = 7\n", "input": {}}))
        assert guest_main(["--manifest", str(stdout_manifest)]) == 0
        assert json.loads(capsys.readouterr().out)["result"] == 7


class TestExecutorCoverage:
    def test_helpers_for_profiles_egress_and_user_agent(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("OCI_CONFIG_PROFILE", raising=False)
        monkeypatch.delenv("OCI_CODE_ALLOWED_EGRESS", raising=False)
        monkeypatch.delenv("OCI_CONFIG_FILE", raising=False)
        assert _default_profile_name(None) == "DEFAULT"
        assert _default_profile_name("ALT") == "ALT"
        assert default_allowed_egress() == list(DEFAULT_ALLOWED_EGRESS)
        assert _config_file_location().endswith("config")
        assert _user_agent()

        monkeypatch.setenv("OCI_CODE_ALLOWED_EGRESS", " foo.oraclecloud.com, bar.oraclecloud.com ")
        assert default_allowed_egress() == ["foo.oraclecloud.com", "bar.oraclecloud.com"]

    def test_collect_auth_bundle_and_build_execution_request(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        key_file = tmp_path / "key.pem"
        key_file.write_text("KEY")
        token_file = tmp_path / "token"
        token_file.write_text("TOKEN")
        fake_config = {
            "fingerprint": "fp",
            "key_file": str(key_file),
            "pass_phrase": "pw",
            "region": "us-ashburn-1",
            "security_token_file": str(token_file),
            "tenancy": "tenancy",
            "user": "user",
            "extra": "ignored",
        }

        with patch("oracle.oci_code_mcp_server.executor.oci.config.from_file", return_value=fake_config):
            bundle = collect_auth_bundle("ALT")
        assert bundle["profile_name"] == "ALT"
        assert bundle["key_pem"] == "KEY"
        assert bundle["security_token"] == "TOKEN"
        assert "extra" not in bundle["config"]
        assert bundle["config"]["additional_user_agent"] == _user_agent()

        monkeypatch.setenv("OCI_CODE_SNAPSHOT_NAME", "snapshot-x")
        monkeypatch.setenv("OCI_CODE_ALLOWED_EGRESS", "*.oraclecloud.com,iad.oraclecloud.com")
        with (
            patch("oracle.oci_code_mcp_server.executor.collect_auth_bundle", return_value={"token": "bundle"}),
            patch("oracle.oci_code_mcp_server.executor.uuid.uuid4") as uuid4,
        ):
            uuid4.return_value.hex = "abc123"
            request = build_execution_request(
                code="result = 1",
                input_data={"x": 1},
                profile_name=None,
                snapshot_name=None,
                timeout_seconds=11,
                memory_limit_mib=222,
            )
        assert request.request_id == "abc123"
        assert request.snapshot_name == "snapshot-x"
        assert request.allowed_egress == ["*.oraclecloud.com", "iad.oraclecloud.com"]
        assert request.auth_bundle == {"token": "bundle"}
        assert request.limits.timeout_seconds == 11
        assert request.limits.memory_limit_mib == 222

    def test_executor_manifest_and_result_loading(self, tmp_path: Path):
        executor = FirecrackerCommandExecutor("/bin/echo")
        manifest = executor._manifest(_request(), tmp_path / "result.json")
        assert manifest["guest_entrypoint"].startswith("python -m")
        assert manifest["vm_id"].startswith("oci-code-")

        assert _load_result_payload(tmp_path / "missing.json", '{"ok": true, "result": 5}')["result"] == 5
        with pytest.raises(SandboxExecutionError, match="without producing a result payload"):
            _load_result_payload(tmp_path / "missing.json", "")

    def test_executor_success_and_error_paths(self, tmp_path: Path):
        request = _request()
        result_path = tmp_path / "result.json"

        def run_success(*args, **kwargs):
            result_path.write_text(json.dumps({"ok": True, "result": {"done": True}, "vm_id": "vm-ok"}))
            return MagicMock(returncode=0, stdout="", stderr="")

        executor = FirecrackerCommandExecutor("/bin/runner", host_timeout_buffer_seconds=2)
        with (
            patch("oracle.oci_code_mcp_server.executor.tempfile.TemporaryDirectory") as tempdir,
            patch("oracle.oci_code_mcp_server.executor.subprocess.run", side_effect=run_success),
            patch("oracle.oci_code_mcp_server.executor.time.monotonic", side_effect=[10.0, 10.25]),
        ):
            tempdir.return_value.__enter__.return_value = str(tmp_path)
            tempdir.return_value.__exit__.return_value = False
            result = executor.execute(request)
        assert result.result == {"done": True}
        assert result.execution_time_ms == 250

        executor = FirecrackerCommandExecutor("/bin/runner")
        with (
            patch("oracle.oci_code_mcp_server.executor.tempfile.TemporaryDirectory") as tempdir,
            patch(
                "oracle.oci_code_mcp_server.executor.subprocess.run",
                return_value=MagicMock(returncode=1, stdout="", stderr="boom"),
            ),
        ):
            tempdir.return_value.__enter__.return_value = str(tmp_path)
            tempdir.return_value.__exit__.return_value = False
            if result_path.exists():
                result_path.unlink()
            with pytest.raises(SandboxExecutionError, match="exit code 1"):
                executor.execute(request)

        result_path.write_text(json.dumps({"ok": False, "error": {"type": "GuestError", "message": "bad"}}))
        with (
            patch("oracle.oci_code_mcp_server.executor.tempfile.TemporaryDirectory") as tempdir,
            patch(
                "oracle.oci_code_mcp_server.executor.subprocess.run",
                return_value=MagicMock(returncode=1, stdout="", stderr="boom"),
            ),
        ):
            tempdir.return_value.__enter__.return_value = str(tmp_path)
            tempdir.return_value.__exit__.return_value = False
            with pytest.raises(SandboxExecutionError, match="GuestError: bad"):
                executor.execute(request)

        result_path.write_text(json.dumps({"ok": False, "error": {"type": "GuestError", "message": "still bad"}}))
        with (
            patch("oracle.oci_code_mcp_server.executor.tempfile.TemporaryDirectory") as tempdir,
            patch(
                "oracle.oci_code_mcp_server.executor.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="", stderr=""),
            ),
        ):
            tempdir.return_value.__enter__.return_value = str(tmp_path)
            tempdir.return_value.__exit__.return_value = False
            with pytest.raises(SandboxExecutionError, match="GuestError: still bad"):
                executor.execute(request)

        if result_path.exists():
            result_path.unlink()
        with (
            patch("oracle.oci_code_mcp_server.executor.tempfile.TemporaryDirectory") as tempdir,
            patch(
                "oracle.oci_code_mcp_server.executor.subprocess.run",
                return_value=MagicMock(returncode=0, stdout="", stderr=""),
            ),
        ):
            tempdir.return_value.__enter__.return_value = str(tmp_path)
            tempdir.return_value.__exit__.return_value = False
            with pytest.raises(SandboxExecutionError, match="without producing a result payload"):
                executor.execute(request)

    def test_executor_translates_subprocess_timeout(self, tmp_path: Path):
        request = _request()
        executor = FirecrackerCommandExecutor("/bin/runner")
        with (
            patch("oracle.oci_code_mcp_server.executor.tempfile.TemporaryDirectory") as tempdir,
            patch(
                "oracle.oci_code_mcp_server.executor.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["runner"], timeout=1),
            ),
        ):
            tempdir.return_value.__enter__.return_value = str(tmp_path)
            tempdir.return_value.__exit__.return_value = False
            with pytest.raises(SandboxExecutionError, match="host timeout buffer"):
                executor.execute(request)


class TestServerHelpers:
    def test_contract_and_executor_factory(self):
        assert "OCI code execution contract" in code_execution_contract.fn()
        assert isinstance(get_executor(), FirecrackerCommandExecutor)
