"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import argparse
import contextlib
import inspect
import io
import json
import os
import tempfile
import traceback
from pathlib import Path
from typing import Any, Sequence

import oci

from .policy import CodePolicyError, make_restricted_builtins, validate_user_code


def _serialize_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_serialize_value(item) for item in value]
    if isinstance(value, Path):
        return str(value)

    try:
        converted = oci.util.to_dict(value)
    except Exception:
        converted = value

    if converted is not value:
        return _serialize_value(converted)

    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def load_oci_config() -> dict[str, Any]:
    return oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )


def build_oci_signer(config: dict[str, Any] | None = None) -> Any:
    cfg = config or load_oci_config()
    private_key = oci.signer.load_private_key_from_file(cfg["key_file"])
    token_file = os.path.expanduser(cfg.get("security_token_file", "") or "")

    if token_file and os.path.exists(token_file):
        token = Path(token_file).read_text()
        return oci.auth.signers.SecurityTokenSigner(token, private_key)

    return oci.signer.Signer(
        tenancy=cfg["tenancy"],
        user=cfg["user"],
        fingerprint=cfg["fingerprint"],
        private_key_file_location=cfg["key_file"],
        pass_phrase=cfg.get("pass_phrase"),
    )


def create_oci_client(client_class: type[Any], config: dict[str, Any] | None = None) -> Any:
    cfg = config or load_oci_config()
    signer = build_oci_signer(cfg)
    return client_class(cfg, signer=signer)


def _install_auth_bundle(auth_bundle: dict[str, Any], workdir: Path) -> None:
    profile_name = auth_bundle.get("profile_name", oci.config.DEFAULT_PROFILE)
    config_values = dict(auth_bundle.get("config", {}))
    key_file = workdir / "oci_api_key.pem"
    key_file.write_text(auth_bundle["key_pem"])
    config_values["key_file"] = str(key_file)

    token = auth_bundle.get("security_token")
    if token:
        token_file = workdir / "security_token"
        token_file.write_text(token)
        config_values["security_token_file"] = str(token_file)

    config_path = workdir / "config"
    lines = [f"[{profile_name}]"]
    for key, value in sorted(config_values.items()):
        lines.append(f"{key}={value}")
    config_path.write_text("\n".join(lines) + "\n")

    os.environ["OCI_CONFIG_FILE"] = str(config_path)
    os.environ["OCI_CONFIG_PROFILE"] = profile_name


def _invoke_main(entrypoint: Any, input_data: dict[str, Any] | None) -> Any:
    if inspect.iscoroutinefunction(entrypoint):
        raise CodePolicyError("async main is not supported")

    signature = inspect.signature(entrypoint)
    positional_params = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
    ]
    required_params = [
        parameter for parameter in positional_params if parameter.default is inspect.Parameter.empty
    ]

    if len(positional_params) == 0:
        return entrypoint()
    if len(required_params) <= 1:
        return entrypoint(input_data)

    raise CodePolicyError("main must accept zero or one positional argument")


def execute_user_code(code: str, input_data: dict[str, Any] | None) -> dict[str, Any]:
    validate_user_code(code)

    namespace = {
        "__builtins__": make_restricted_builtins(),
        "__name__": "__main__",
        "INPUT": input_data,
        "build_oci_signer": build_oci_signer,
        "create_oci_client": create_oci_client,
        "load_oci_config": load_oci_config,
    }

    stdout_buffer = io.StringIO()
    with contextlib.redirect_stdout(stdout_buffer):
        compiled = compile(code, "<oci-code-mcp>", "exec")
        exec(compiled, namespace, namespace)
        if callable(namespace.get("main")):
            raw_result = _invoke_main(namespace["main"], input_data)
        else:
            raw_result = namespace.get("result")

    return {
        "result": _serialize_value(raw_result),
        "stdout": stdout_buffer.getvalue(),
    }


def run_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    request_id = manifest["request_id"]

    try:
        with tempfile.TemporaryDirectory(prefix="oci-code-guest-") as temp_dir:
            workdir = Path(temp_dir)
            auth_bundle = manifest.get("auth")
            if auth_bundle:
                _install_auth_bundle(auth_bundle, workdir)

            execution = execute_user_code(manifest["code"], manifest.get("input"))

        return {
            "ok": True,
            "request_id": request_id,
            "result": execution["result"],
            "guest_stdout": execution["stdout"][-4_096:],
            "vm_id": manifest.get("vm_id"),
            "resumed_from_snapshot": bool(manifest.get("resume_snapshot", True)),
        }
    except Exception as exc:
        return {
            "ok": False,
            "request_id": request_id,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
            },
            "traceback": traceback.format_exc(limit=8),
            "vm_id": manifest.get("vm_id"),
            "resumed_from_snapshot": bool(manifest.get("resume_snapshot", True)),
        }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute OCI code inside the guest sandbox")
    parser.add_argument("--manifest", required=True, help="Path to the JSON execution manifest")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text())
    result = run_manifest(manifest)

    result_path = manifest.get("result_path")
    if result_path:
        Path(result_path).write_text(json.dumps(result))
    else:
        print(json.dumps(result))

    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
