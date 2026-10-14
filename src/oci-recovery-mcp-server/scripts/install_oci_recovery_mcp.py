"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Install the OCI Recovery MCP server from the Oracle MCP repository.
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Mapping


REPOSITORY_URL = "https://github.com/oracle/mcp.git"
REPOSITORY_NAME = "oracle/mcp"
SERVER_PROJECT = Path("src/oci-recovery-mcp-server")
SERVER_COMMAND = "oracle.oci-recovery-mcp-server"
SUGGESTED_PROFILE_NAME = "OCI_RECOVERY"


class InstallError(RuntimeError):
    """An expected setup failure with a user-facing explanation."""


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=capture_output,
            check=False,
        )
    except OSError as exc:
        raise InstallError(f"Could not run {command[0]}: {exc}") from exc

    if check and result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        message = f"Command failed with exit code {result.returncode}: {command[0]}"
        if detail:
            message += f"\n{detail}"
        raise InstallError(message)
    return result


def _find_uv() -> str:
    configured = os.environ.get("OCI_RECOVERY_UV")
    uv = configured or shutil.which("uv")
    if not uv or not Path(uv).is_file():
        raise InstallError(
            "uv was not found. Start this installer with the platform launcher in the "
            "Recovery MCP README; it installs uv and Python when needed."
        )
    return str(Path(uv).resolve())


def _prompt(value: str | None, label: str, default: str | None = None) -> str:
    if value:
        return value.strip()
    if not sys.stdin.isatty():
        if default:
            return default
        raise InstallError(
            f"{label} is required in a non-interactive run. Supply it as a command-line option."
        )

    hint = f" [{default}]" if default else ""
    answer = input(f"{label}{hint}: ").strip()
    return answer or (default or "")


def _get_install_parent(value: str | None) -> Path:
    answer = _prompt(value, "Parent directory for .local-rcv-mcp", str(Path.cwd()))
    parent = Path(answer).expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    return parent


def _canonical_repository_url(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized.removeprefix("git@github.com:")
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    return normalized.rstrip("/")


def _ensure_checkout(checkout: Path) -> None:
    git = shutil.which("git")
    if not git:
        raise InstallError(
            "Git is required to clone and update the Recovery MCP repository. "
            "Install Git for your operating system, then run this installer again."
        )

    if not checkout.exists():
        print(f"Cloning {REPOSITORY_URL} (main) into {checkout}")
        _run([git, "clone", "--branch", "main", "--single-branch", REPOSITORY_URL, str(checkout)])
        return

    if not checkout.is_dir():
        raise InstallError(f"The install path exists and is not a directory: {checkout}")

    is_repository = _run(
        [git, "-C", str(checkout), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        check=False,
    )
    if is_repository.returncode or is_repository.stdout.strip() != "true":
        raise InstallError(
            f"{checkout} already exists but is not a Git checkout. Move it or choose another parent directory."
        )

    origin = _run(
        [git, "-C", str(checkout), "remote", "get-url", "origin"],
        capture_output=True,
        check=False,
    )
    if origin.returncode or _canonical_repository_url(origin.stdout) != f"https://github.com/{REPOSITORY_NAME}":
        raise InstallError(
            f"{checkout} is a Git checkout, but its origin is not {REPOSITORY_URL}. "
            "Move it or choose another parent directory."
        )

    changes = _run(
        [git, "-C", str(checkout), "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        check=False,
    )
    if changes.returncode:
        raise InstallError(f"Could not inspect the checkout at {checkout}.")
    if changes.stdout.strip():
        raise InstallError(
            f"The checkout at {checkout} has tracked local changes. Commit or stash them before updating."
        )

    branch = _run(
        [git, "-C", str(checkout), "branch", "--show-current"],
        capture_output=True,
    ).stdout.strip()
    if branch != "main":
        raise InstallError(
            f"The checkout at {checkout} is on branch {branch or '(detached)'}, not main. "
            "Switch it to main before rerunning this installer."
        )

    print(f"Updating existing checkout at {checkout} from origin/main")
    _run([git, "-C", str(checkout), "pull", "--ff-only", "origin", "main"])


def _python_313(uv: str) -> str:
    found = _run([uv, "python", "find", "3.13"], capture_output=True, check=False)
    if found.returncode == 0 and found.stdout.strip():
        python = found.stdout.strip().splitlines()[-1]
        print(f"Using Python 3.13 at {python}")
        return python

    print("Python 3.13 was not found; installing it with uv")
    _run([uv, "python", "install", "3.13"])
    found = _run([uv, "python", "find", "3.13"], capture_output=True)
    python = found.stdout.strip().splitlines()[-1]
    print(f"Using Python 3.13 at {python}")
    return python


def _sync_server(uv: str, python: str, checkout: Path) -> Path:
    project = checkout / SERVER_PROJECT
    print("Installing the Recovery MCP server into its project virtual environment")
    _run(
        [
            uv,
            "sync",
            "--project",
            str(project),
            "--python",
            python,
            "--locked",
            "--no-dev",
        ]
    )

    if os.name == "nt":
        command = project / ".venv" / "Scripts" / f"{SERVER_COMMAND}.exe"
    else:
        command = project / ".venv" / "bin" / SERVER_COMMAND
    if not command.is_file():
        raise InstallError(f"The server entry point was not created: {command}")
    return command.resolve()


def _local_oci_cli(uv: str, python: str, checkout: Path) -> str:
    cli_environment = checkout / ".venv"
    if os.name == "nt":
        cli_command = cli_environment / "Scripts" / "oci.exe"
    else:
        cli_command = cli_environment / "bin" / "oci"

    if not cli_command.is_file():
        print("OCI CLI was not found on PATH; installing it in the checkout's isolated .venv")
        _run([uv, "venv", "--python", python, str(cli_environment)])
        _run([uv, "pip", "install", "--python", str(cli_environment), "oci-cli"])

    if not cli_command.is_file():
        raise InstallError(f"OCI CLI installation did not create the expected command: {cli_command}")
    version = _run([str(cli_command), "--version"], capture_output=True, check=False)
    auth_help = _run(
        [str(cli_command), "session", "authenticate", "--help"],
        capture_output=True,
        check=False,
    )
    if version.returncode or auth_help.returncode:
        raise InstallError(
            f"OCI CLI was installed at {cli_command}, but its session authentication command is unavailable."
        )
    return str(cli_command.resolve())


def _select_oci_cli(uv: str, python: str, checkout: Path) -> str:
    available = shutil.which("oci")
    if available:
        version = _run([available, "--version"], capture_output=True, check=False)
        auth_help = _run(
            [available, "session", "authenticate", "--help"],
            capture_output=True,
            check=False,
        )
        if version.returncode == 0 and auth_help.returncode == 0:
            print(f"Using OCI CLI found on PATH: {available}")
            return available
        print(
            "OCI CLI was found on PATH but could not run or lacks session authentication; "
            "using the isolated local installation instead."
        )
    return _local_oci_cli(uv, python, checkout)


def _configured_oci_config_file() -> str | None:
    return os.environ.get("OCI_CONFIG_FILE") or os.environ.get("OCI_CLI_CONFIG_FILE")


def _profile_in_config(profile: str) -> bool:
    config_path = _oci_config_path()
    if not config_path.is_file():
        return False
    parser = configparser.ConfigParser()
    try:
        parser.read(config_path, encoding="utf-8")
    except (OSError, configparser.Error):
        return False
    return parser.has_section(profile)


def _oci_config_path() -> Path:
    configured = _configured_oci_config_file()
    path = Path(configured).expanduser() if configured else Path.home() / ".oci" / "config"
    return path.resolve()


def _profile_name() -> str:
    suggested = SUGGESTED_PROFILE_NAME
    if _profile_in_config(suggested):
        suffix = 2
        while _profile_in_config(f"{SUGGESTED_PROFILE_NAME}_{suffix}"):
            suffix += 1
        suggested = f"{SUGGESTED_PROFILE_NAME}_{suffix}"
    profile = _prompt(None, "OCI profile name", suggested)
    if not profile:
        raise InstallError("OCI profile name cannot be empty.")
    return profile


def _authenticate(oci_command: str, profile: str) -> None:
    command = [oci_command, "session", "authenticate", "--profile-name", profile]
    print(
        "\nOCI session authentication will open the OCI sign-in flow. The OCI CLI "
        "will prompt for the region and create the selected profile.\n"
    )
    environment = os.environ.copy()
    if _configured_oci_config_file():
        environment["OCI_CLI_CONFIG_FILE"] = str(_oci_config_path())
    result = _run(command, env=environment, check=False)
    if result.returncode:
        raise InstallError(
            "OCI session authentication did not complete. Rerun this installer after "
            "resolving the OCI CLI error, or run the same oci session authenticate command manually."
        )


def _config_outputs(server_command: Path, profile: str) -> tuple[str, str]:
    environment = {
        "OCI_CONFIG_PROFILE": profile,
        "OCI_MCP_AUTH_TYPE": "security_token",
    }
    configured = _configured_oci_config_file()
    if configured:
        environment["OCI_CONFIG_FILE"] = str(_oci_config_path())
    entry = {
        "type": "stdio",
        "command": str(server_command),
        "args": [],
        "env": environment,
    }
    json_config = json.dumps({"mcpServers": {"oci-recovery": entry}}, indent=2, ensure_ascii=False)
    toml_environment = ", ".join(f"{name} = {json.dumps(value)}" for name, value in environment.items())
    toml_config = "\n".join(
        [
            "[mcp_servers.oci_recovery]",
            f"command = {json.dumps(str(server_command))}",
            "args = []",
            f"env = {{ {toml_environment} }}",
            "",
        ]
    )
    return json_config, toml_config


def _shell_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clone or update OCI Recovery MCP, install it, authenticate, and print client configs."
    )
    parser.add_argument("--parent-dir", help="Parent directory for the .local-rcv-mcp checkout")
    options = parser.parse_args()

    try:
        uv = _find_uv()
        parent = _get_install_parent(options.parent_dir)
        checkout = parent / ".local-rcv-mcp"
        _ensure_checkout(checkout)

        python = _python_313(uv)
        server_command = _sync_server(uv, python, checkout)
        oci_command = _select_oci_cli(uv, python, checkout)
        profile = _profile_name()
        _authenticate(oci_command, profile)

        json_config, toml_config = _config_outputs(server_command, profile)
        print("\nRecovery MCP is installed and authenticated.\n")
        print(f"Checkout: {checkout}")
        print(f"OCI profile: {profile}")
        if _configured_oci_config_file():
            print(f"OCI config file: {_oci_config_path()}")
        print("\nFor Claude Code/Desktop, Cursor, or Cline, merge this JSON into the client's MCP server configuration:")
        print(json_config)
        print("\nFor Codex, add this TOML block to ~/.codex/config.toml:")
        print(toml_config)

        refresh_command = [oci_command, "session", "authenticate", "--profile-name", profile]
        print("\nRefresh the session later with:")
        rendered_refresh_command = _shell_command(refresh_command)
        if _configured_oci_config_file():
            config_file = str(_oci_config_path())
            if os.name == "nt":
                rendered_refresh_command = (
                    f"$env:OCI_CLI_CONFIG_FILE = {json.dumps(config_file)}; "
                    f"& {rendered_refresh_command}"
                )
            else:
                rendered_refresh_command = (
                    f"OCI_CLI_CONFIG_FILE={shlex.quote(config_file)} {rendered_refresh_command}"
                )
        print(rendered_refresh_command)
        print("\nRestart your MCP client after saving its configuration.")
        return 0
    except (InstallError, EOFError, KeyboardInterrupt) as exc:
        if isinstance(exc, KeyboardInterrupt):
            print("\nInstallation cancelled.", file=sys.stderr)
            return 130
        print(f"\nInstaller error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
