"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .guest_runner import run_manifest


class ManifestValidationError(ValueError):
    """Raised when the host manifest is malformed."""


class RunnerConfigurationError(RuntimeError):
    """Raised when the runner backend is not configured correctly."""


@dataclass(slots=True)
class RunnerManifest:
    schema_version: int
    request_id: str
    snapshot_name: str
    allowed_egress: list[str]
    limits: dict[str, Any]
    code: str
    input_data: Any
    auth: dict[str, Any] | None
    result_path: str | None
    vm_id: str | None
    resume_snapshot: bool
    destroy_after_request: bool
    guest_entrypoint: str | None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text())
    except FileNotFoundError as exc:
        raise ManifestValidationError(f"Manifest file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ManifestValidationError(f"Manifest file is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ManifestValidationError("Manifest root must be a JSON object")
    return payload


def _require_type(payload: dict[str, Any], key: str, expected_type: type | tuple[type, ...]) -> Any:
    if key not in payload:
        raise ManifestValidationError(f"Manifest is missing required field '{key}'")
    value = payload[key]
    if not isinstance(value, expected_type):
        expected_name = (
            ", ".join(item.__name__ for item in expected_type)
            if isinstance(expected_type, tuple)
            else expected_type.__name__
        )
        raise ManifestValidationError(f"Manifest field '{key}' must be of type {expected_name}")
    return value


def load_manifest(path: str | Path) -> RunnerManifest:
    payload = _read_json(Path(path))
    schema_version = _require_type(payload, "schema_version", int)
    request_id = _require_type(payload, "request_id", str)
    snapshot_name = _require_type(payload, "snapshot_name", str)
    allowed_egress = _require_type(payload, "allowed_egress", list)
    limits = _require_type(payload, "limits", dict)
    code = _require_type(payload, "code", str)

    input_data = payload.get("input")
    auth = payload.get("auth")
    result_path = payload.get("result_path")
    vm_id = payload.get("vm_id")
    resume_snapshot = bool(payload.get("resume_snapshot", True))
    destroy_after_request = bool(payload.get("destroy_after_request", True))
    guest_entrypoint = payload.get("guest_entrypoint")

    if schema_version != 1:
        raise ManifestValidationError(f"Unsupported manifest schema version: {schema_version}")
    if not request_id.strip():
        raise ManifestValidationError("Manifest field 'request_id' must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in allowed_egress):
        raise ManifestValidationError("Manifest field 'allowed_egress' must contain non-empty strings")
    if not isinstance(result_path, (str, type(None))):
        raise ManifestValidationError("Manifest field 'result_path' must be a string when provided")
    if auth is not None and not isinstance(auth, dict):
        raise ManifestValidationError("Manifest field 'auth' must be an object when provided")

    return RunnerManifest(
        schema_version=schema_version,
        request_id=request_id,
        snapshot_name=snapshot_name,
        allowed_egress=allowed_egress,
        limits=limits,
        code=code,
        input_data=input_data,
        auth=auth,
        result_path=result_path,
        vm_id=vm_id,
        resume_snapshot=resume_snapshot,
        destroy_after_request=destroy_after_request,
        guest_entrypoint=guest_entrypoint,
    )


def backend_name(cli_backend: str | None = None) -> str:
    return (cli_backend or os.getenv("OCI_CODE_RUNNER_BACKEND", "delegate")).strip().lower()


def _run_subprocess(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )


def _delegate_command() -> list[str]:
    command = os.getenv("OCI_CODE_FIRECRACKER_DELEGATE_CMD", "").strip()
    if not command:
        raise RunnerConfigurationError(
            "OCI_CODE_FIRECRACKER_DELEGATE_CMD is required when OCI_CODE_RUNNER_BACKEND=delegate"
        )
    parts = shlex.split(command)
    if not parts:
        raise RunnerConfigurationError("OCI_CODE_FIRECRACKER_DELEGATE_CMD is empty")
    return parts


def _payload_to_manifest_dict(manifest: RunnerManifest) -> dict[str, Any]:
    payload = {
        "schema_version": manifest.schema_version,
        "request_id": manifest.request_id,
        "snapshot_name": manifest.snapshot_name,
        "allowed_egress": manifest.allowed_egress,
        "limits": manifest.limits,
        "code": manifest.code,
        "input": manifest.input_data,
        "resume_snapshot": manifest.resume_snapshot,
        "destroy_after_request": manifest.destroy_after_request,
    }
    if manifest.auth is not None:
        payload["auth"] = manifest.auth
    if manifest.result_path is not None:
        payload["result_path"] = manifest.result_path
    if manifest.vm_id is not None:
        payload["vm_id"] = manifest.vm_id
    if manifest.guest_entrypoint is not None:
        payload["guest_entrypoint"] = manifest.guest_entrypoint
    return payload


def execute_emulator_backend(manifest: RunnerManifest) -> dict[str, Any]:
    return run_manifest(_payload_to_manifest_dict(manifest))


def execute_delegate_backend(manifest_path: Path) -> tuple[int, str, str]:
    command = _delegate_command()
    completed = _run_subprocess([*command, "--manifest", str(manifest_path)])
    return completed.returncode, completed.stdout, completed.stderr


def _limactl_binary() -> str:
    return os.getenv("OCI_CODE_LIMACTL_BIN", "limactl").strip() or "limactl"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _scripts_dir() -> Path:
    return _repo_root() / "scripts"


def _lima_instance_name() -> str:
    return os.getenv("OCI_CODE_LIMA_INSTANCE", "firecracker-dev").strip() or "firecracker-dev"


def _lima_template() -> str:
    return os.getenv("OCI_CODE_LIMA_START_TEMPLATE", "template:default").strip() or "template:default"


def _lima_vm_type() -> str:
    return os.getenv("OCI_CODE_LIMA_VM_TYPE", "vz").strip() or "vz"


def _lima_start_timeout() -> str:
    return os.getenv("OCI_CODE_LIMA_START_TIMEOUT", "10m").strip() or "10m"


def _lima_copy_backend() -> str:
    return os.getenv("OCI_CODE_LIMA_COPY_BACKEND", "auto").strip() or "auto"


def _lima_guest_root(request_id: str) -> str:
    root = os.getenv("OCI_CODE_LIMA_GUEST_ROOT", "/tmp/oci-code-mcp").strip() or "/tmp/oci-code-mcp"
    return f"{root.rstrip('/')}/{request_id}"


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _lima_instance_dir() -> Path:
    lima_home = Path(os.getenv("LIMA_HOME", str(Path.home() / ".lima")))
    return lima_home / _lima_instance_name()


def _shell_assignment(name: str, value: str) -> str:
    return f"{name}={shlex.quote(value)}"


def _rewrite_manifest_for_guest(manifest_path: Path, guest_result_path: str) -> dict[str, Any]:
    payload = _read_json(manifest_path)
    payload["result_path"] = guest_result_path
    return payload


def _build_lima_stage_bundle(manifest_path: Path, manifest: RunnerManifest) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
    temp_dir = tempfile.TemporaryDirectory(prefix="oci-code-lima-")
    host_bundle_root = Path(temp_dir.name) / manifest.request_id
    host_stage_dir = host_bundle_root / "stage"
    host_project_dir = host_bundle_root / "project"
    host_scripts_dir = host_project_dir / "scripts"
    guest_root = _lima_guest_root(manifest.request_id)
    guest_result_path = f"{guest_root}/stage/result.json"

    host_stage_dir.mkdir(parents=True)
    host_project_dir.mkdir(parents=True)
    host_scripts_dir.mkdir(parents=True)

    rewritten_manifest = _rewrite_manifest_for_guest(manifest_path, guest_result_path)
    (host_stage_dir / "request.json").write_text(json.dumps(rewritten_manifest, sort_keys=True, indent=2))

    shutil.copytree(_repo_root() / "oracle", host_project_dir / "oracle", dirs_exist_ok=True)
    shutil.copy2(_scripts_dir() / "oci-code-lima-guest-runner.sh", host_scripts_dir / "oci-code-lima-guest-runner.sh")

    return temp_dir, host_bundle_root, guest_root


def _ensure_lima_instance_running() -> tuple[int, str, str]:
    limactl = _limactl_binary()
    instance = _lima_instance_name()
    timeout = _lima_start_timeout()

    if _lima_instance_dir().exists():
        completed = _run_subprocess([limactl, "start", "-y", "--timeout", timeout, instance])
        return completed.returncode, completed.stdout, completed.stderr

    command = [
        limactl,
        "start",
        "-y",
        "--timeout",
        timeout,
        "--vm-type",
        _lima_vm_type(),
        "--name",
        instance,
    ]
    if _bool_env("OCI_CODE_LIMA_ENABLE_NESTED_VIRT", True):
        command.append("--nested-virt")
    command.append(_lima_template())
    completed = _run_subprocess(command)
    return completed.returncode, completed.stdout, completed.stderr


def _lima_kvm_preflight_command(instance: str) -> list[str]:
    shell_command = (
        "test -c /dev/kvm || "
        "{ echo '/dev/kvm is not available inside the Lima guest; nested virtualization is not active.' >&2; exit 42; }"
    )
    return [_limactl_binary(), "shell", "--start", instance, "sh", "-lc", shell_command]


def _lima_guest_shell_command(guest_root: str) -> str:
    exports: list[str] = []

    optional_names = (
        "OCI_CODE_LIMA_GUEST_FIRECRACKER_CMD",
        "OCI_CODE_LIMA_GUEST_VENV_ROOT",
        "OCI_CODE_LIMA_GUEST_OCI_PIP_SPEC",
    )
    for name in optional_names:
        value = os.getenv(name, "").strip()
        if value:
            exports.append(_shell_assignment(name, value))

    guest_script = f"{guest_root}/project/scripts/oci-code-lima-guest-runner.sh"
    return " && ".join(
        [
            *(f"export {assignment}" for assignment in exports),
            f"bash {shlex.quote(guest_script)} {shlex.quote(guest_root)}",
        ]
    )


def execute_lima_backend(manifest_path: Path, manifest: RunnerManifest) -> tuple[int, str, str]:
    limactl = _limactl_binary()
    instance = _lima_instance_name()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def record_output(stdout: str, stderr: str) -> None:
        if stdout.strip():
            stdout_chunks.append(stdout.strip())
        if stderr.strip():
            stderr_chunks.append(stderr.strip())

    start_code, start_stdout, start_stderr = _ensure_lima_instance_running()
    record_output(start_stdout, start_stderr)
    if start_code != 0:
        return start_code, "\n".join(stdout_chunks), "\n".join(stderr_chunks)

    kvm_check = _run_subprocess(_lima_kvm_preflight_command(instance))
    record_output(kvm_check.stdout, kvm_check.stderr)
    if kvm_check.returncode != 0:
        return kvm_check.returncode, "\n".join(stdout_chunks), "\n".join(stderr_chunks)

    temp_dir, host_bundle_root, guest_root = _build_lima_stage_bundle(manifest_path, manifest)
    guest_parent = str(Path(guest_root).parent)
    guest_result_path = f"{guest_root}/stage/result.json"

    try:
        prepare_guest = _run_subprocess(
            [
                limactl,
                "shell",
                "--start",
                instance,
                "sh",
                "-lc",
                f"rm -rf {shlex.quote(guest_root)} && mkdir -p {shlex.quote(guest_parent)}",
            ]
        )
        record_output(prepare_guest.stdout, prepare_guest.stderr)
        if prepare_guest.returncode != 0:
            return prepare_guest.returncode, "\n".join(stdout_chunks), "\n".join(stderr_chunks)

        copy_in = _run_subprocess(
            [
                limactl,
                "copy",
                "--backend",
                _lima_copy_backend(),
                "-r",
                str(host_bundle_root),
                f"{instance}:{guest_parent}/",
            ]
        )
        record_output(copy_in.stdout, copy_in.stderr)
        if copy_in.returncode != 0:
            return copy_in.returncode, "\n".join(stdout_chunks), "\n".join(stderr_chunks)

        guest_run = _run_subprocess(
            [
                limactl,
                "shell",
                "--start",
                instance,
                "sh",
                "-lc",
                _lima_guest_shell_command(guest_root),
            ]
        )
        record_output(guest_run.stdout, guest_run.stderr)

        local_result_path: Path
        capture_stdout_from_result = False
        if manifest.result_path:
            local_result_path = Path(manifest.result_path)
        else:
            local_result_path = Path(temp_dir.name) / "result.json"
            capture_stdout_from_result = True

        copy_out = _run_subprocess(
            [
                limactl,
                "copy",
                "--backend",
                _lima_copy_backend(),
                f"{instance}:{guest_result_path}",
                str(local_result_path),
            ]
        )
        record_output(copy_out.stdout, copy_out.stderr)

        if capture_stdout_from_result and local_result_path.exists():
            stdout_chunks.append(local_result_path.read_text())

        if guest_run.returncode != 0:
            return guest_run.returncode, "\n".join(stdout_chunks), "\n".join(stderr_chunks)
        if copy_out.returncode != 0:
            return copy_out.returncode, "\n".join(stdout_chunks), "\n".join(stderr_chunks)

        return 0, "\n".join(stdout_chunks), "\n".join(stderr_chunks)
    finally:
        if not _bool_env("OCI_CODE_LIMA_KEEP_GUEST_BUNDLE", False):
            cleanup = _run_subprocess(
                [
                    limactl,
                    "shell",
                    "--start",
                    instance,
                    "sh",
                    "-lc",
                    f"rm -rf {shlex.quote(guest_root)}",
                ]
            )
            record_output(cleanup.stdout, cleanup.stderr)
        temp_dir.cleanup()


def _failure_payload(request_id: str, error_type: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "request_id": request_id,
        "error": {
            "type": error_type,
            "message": message,
        },
    }


def emit_result(manifest: RunnerManifest, payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload)
    if manifest.result_path:
        Path(manifest.result_path).write_text(serialized)
    else:
        print(serialized)


def _finalize_proxy_backend_result(
    manifest: RunnerManifest, returncode: int, stdout: str, stderr: str, *, backend_name: str
) -> int:
    if returncode == 0:
        if not manifest.result_path and stdout.strip():
            sys.stdout.write(stdout)
        return 0

    if manifest.result_path and Path(manifest.result_path).exists():
        return returncode

    payload = _failure_payload(
        manifest.request_id,
        f"{backend_name.title()}ExecutionError",
        stderr.strip() or stdout.strip() or f"{backend_name} backend exited with status {returncode}",
    )
    emit_result(manifest, payload)
    return returncode


def run_runner(manifest_path: Path, *, cli_backend: str | None = None) -> int:
    manifest = load_manifest(manifest_path)
    backend = backend_name(cli_backend)

    if backend == "emulator":
        payload = execute_emulator_backend(manifest)
        emit_result(manifest, payload)
        return 0 if payload.get("ok") else 1

    if backend == "lima":
        returncode, stdout, stderr = execute_lima_backend(manifest_path, manifest)
        return _finalize_proxy_backend_result(
            manifest, returncode, stdout, stderr, backend_name="lima"
        )

    if backend == "delegate":
        returncode, stdout, stderr = execute_delegate_backend(manifest_path)
        return _finalize_proxy_backend_result(
            manifest, returncode, stdout, stderr, backend_name="delegate"
        )

    raise RunnerConfigurationError(
        f"Unsupported OCI_CODE_RUNNER_BACKEND '{backend}'. Expected 'delegate', 'emulator', or 'lima'."
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manifest-driven OCI code Firecracker runner wrapper")
    parser.add_argument("--manifest", required=True, help="Path to the JSON manifest created by the MCP host")
    parser.add_argument(
        "--backend",
        choices=("delegate", "emulator", "lima"),
        default=None,
        help="Optional backend override. Defaults to OCI_CODE_RUNNER_BACKEND or 'delegate'.",
    )
    args = parser.parse_args(argv)

    try:
        return run_runner(Path(args.manifest), cli_backend=args.backend)
    except (ManifestValidationError, RunnerConfigurationError) as exc:
        request_id = "unknown-request"
        try:
            raw_payload = _read_json(Path(args.manifest))
            request_id = str(raw_payload.get("request_id", request_id))
            result_path = raw_payload.get("result_path")
            if isinstance(result_path, str) and result_path:
                Path(result_path).write_text(
                    json.dumps(_failure_payload(request_id, type(exc).__name__, str(exc)))
                )
            else:
                print(json.dumps(_failure_payload(request_id, type(exc).__name__, str(exc))))
        except Exception:
            print(json.dumps(_failure_payload(request_id, type(exc).__name__, str(exc))))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
