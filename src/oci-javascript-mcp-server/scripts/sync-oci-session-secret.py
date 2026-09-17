#!/usr/bin/env python3
"""Synchronize one local OCI profile into the trusted Kubernetes host Secret."""

from __future__ import annotations

import argparse
import configparser
import os
from pathlib import Path
import subprocess
import sys
import tempfile

DEFAULT_NAMESPACE = "oci-js-standard-host"
DEFAULT_SECRET_NAME = "oci-js-host-oci-config"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create or replace the OCI credential Secret mounted only by the "
            "trusted Kubernetes host. Credential values are never printed."
        )
    )
    parser.add_argument(
        "--config-file",
        type=Path,
        default=Path(os.environ.get("OCI_CONFIG_FILE", Path.home() / ".oci" / "config")),
        help="Local OCI config file (default: OCI_CONFIG_FILE or ~/.oci/config).",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT"),
        help="Local OCI profile to synchronize (default: OCI_CONFIG_PROFILE or DEFAULT).",
    )
    parser.add_argument("--namespace", default=DEFAULT_NAMESPACE)
    parser.add_argument("--secret-name", default=DEFAULT_SECRET_NAME)
    parser.add_argument("--host-deployment", default="oci-js-standard-host")
    parser.add_argument("--context", help="Optional kubectl context.")
    parser.add_argument(
        "--refresh-session",
        action="store_true",
        help="Run 'oci session refresh' for the selected profile before synchronizing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate local inputs and report the target without calling kubectl.",
    )
    parser.add_argument(
        "--restart-host",
        action="store_true",
        help="Restart the trusted host Deployment after a successful Secret update.",
    )
    return parser.parse_args()


def resolve_path(value: str, config_file: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else config_file.parent / path


def profile_values(config_file: Path, profile: str) -> dict[str, str]:
    parser = configparser.RawConfigParser(interpolation=None)
    read = parser.read(config_file)
    if not read:
        raise ValueError(f"OCI config file does not exist or cannot be read: {config_file}")
    if profile.upper() == "DEFAULT":
        values = dict(parser.defaults())
    elif parser.has_section(profile):
        # OCI profiles are independent. Do not inherit DEFAULT's
        # security_token_file into an API-key profile.
        values = dict(parser._sections[profile])
    else:
        raise ValueError(f"OCI profile does not exist: {profile}")
    return {key: value.strip() for key, value in values.items() if value.strip()}


def required_path(values: dict[str, str], key: str, config_file: Path) -> Path:
    raw = values.get(key)
    if raw is None:
        raise ValueError(f"OCI profile is missing required {key}")
    path = resolve_path(raw, config_file)
    if not path.is_file():
        raise ValueError(f"OCI profile {key} does not name a readable file: {path}")
    return path


def pod_config(values: dict[str, str], has_session_token: bool) -> str:
    required = ["fingerprint", "tenancy", "region"]
    missing = [name for name in required if name not in values]
    if missing:
        raise ValueError(f"OCI profile is missing required values: {', '.join(missing)}")
    if not has_session_token and "user" not in values:
        raise ValueError("API-key OCI profiles must include user")

    lines = ["[DEFAULT]"]
    for key in ("user", "fingerprint", "tenancy", "region"):
        if key in values:
            lines.append(f"{key}={values[key]}")
    lines.append("key_file=/var/run/oci/private-key.pem")
    if has_session_token:
        lines.append("security_token_file=/var/run/oci/token")
    return "\n".join(lines) + "\n"


def kubectl_command(context: str | None, *arguments: str) -> list[str]:
    command = ["kubectl"]
    if context:
        command.extend(["--context", context])
    command.extend(arguments)
    return command


def refresh_session(arguments: argparse.Namespace) -> None:
    command = [
        "oci",
        "--config-file",
        str(arguments.config_file),
        "--profile",
        arguments.profile,
        "session",
        "refresh",
    ]
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError as error:
        raise ValueError("OCI CLI is required for --refresh-session") from error
    except subprocess.CalledProcessError as error:
        raise ValueError("OCI session refresh failed; the Kubernetes Secret was not changed") from error


def synchronize(arguments: argparse.Namespace) -> None:
    config_file = arguments.config_file.expanduser().resolve()
    if arguments.refresh_session:
        refresh_session(arguments)
    values = profile_values(config_file, arguments.profile)
    private_key = required_path(values, "key_file", config_file)
    token = (
        required_path(values, "security_token_file", config_file)
        if "security_token_file" in values
        else None
    )
    rendered_config = pod_config(values, token is not None)

    if arguments.dry_run:
        mode = "session" if token else "API-key"
        print(
            f"Validated {mode} profile {arguments.profile!r}; would update "
            f"Secret {arguments.secret_name!r} in namespace {arguments.namespace!r}."
        )
        return

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as output:
        output.write(rendered_config)
        output_path = Path(output.name)
    try:
        os.chmod(output_path, 0o600)
        create = kubectl_command(
            arguments.context,
            "create",
            "secret",
            "generic",
            arguments.secret_name,
            "--namespace",
            arguments.namespace,
            f"--from-file=config={output_path}",
            f"--from-file=private-key.pem={private_key}",
            "--dry-run=client",
            "--output=yaml",
        )
        if token:
            create.append(f"--from-file=token={token}")
        rendered_secret = subprocess.run(create, check=True, capture_output=True).stdout
        apply = kubectl_command(arguments.context, "apply", "--filename=-")
        subprocess.run(apply, input=rendered_secret, check=True)
        if arguments.restart_host:
            restart = kubectl_command(
                arguments.context,
                "rollout",
                "restart",
                "--namespace",
                arguments.namespace,
                f"deployment/{arguments.host_deployment}",
            )
            subprocess.run(restart, check=True)
    except FileNotFoundError as error:
        raise ValueError("kubectl is required to synchronize the Kubernetes Secret") from error
    except subprocess.CalledProcessError as error:
        raise ValueError("Kubernetes Secret synchronization failed") from error
    finally:
        output_path.unlink(missing_ok=True)

    suffix = (
        " and restarted the trusted host Deployment."
        if arguments.restart_host
        else "; restart the host Deployment to reload OCI authentication."
    )
    print(f"Updated Secret {arguments.secret_name!r} in namespace {arguments.namespace!r}{suffix}")


def main() -> int:
    try:
        synchronize(parse_arguments())
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
