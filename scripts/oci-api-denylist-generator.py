"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from tempfile import NamedTemporaryFile

import click
from oci_cli import dynamic_loader
from oci_cli.cli_root import cli


DENIED_ACTIONS = frozenset(
    {
        "delete",
        "patch",
        "put",
        "remove",
        "replace",
        "terminate",
        "update",
    }
)
EXCLUDED_ACTION_PREFIXES = ("cancel-", "create-", "get-", "list-")
ALWAYS_DENIED_COMMANDS = frozenset({"raw-request"})
OUTPUT_DIR = Path(__file__).resolve().parent


def write_file(path: Path, content: str) -> None:
    """Replace a generated file without following destination symlinks."""
    temporary_path = None
    try:
        with NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
            temporary_path = Path(f.name)
            f.write(content)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def is_denied_command(command: str) -> bool:
    """Return whether a canonical CLI path is a denylist candidate."""
    action = command.rsplit(" ", 1)[-1]
    if action.startswith(EXCLUDED_ACTION_PREFIXES):
        return False
    return bool(DENIED_ACTIONS.intersection(action.split("-")))


def get_denied_commands(commands: list[str]) -> list[str]:
    """Return the reviewed-action candidates plus mandatory denied commands."""
    return sorted(
        ALWAYS_DENIED_COMMANDS.union(
            command for command in commands if is_denied_command(command)
        )
    )


def get_oci_version():
    return version("oci-cli")


def get_canonical_commands() -> list[str]:
    """Return every canonical leaf command from the installed OCI CLI."""
    dynamic_loader.load_all_services()
    commands = []
    groups = [("", cli)]
    while groups:
        prefix, group = groups.pop()
        for name, command in group.commands.items():
            command_path = f"{prefix} {name}".strip()
            if isinstance(command, click.Group):
                groups.append((command_path, command))
            else:
                commands.append(command_path)
    return sorted(commands)


def get_commands(version):
    commands_file = OUTPUT_DIR / f"commands_{version}.txt"
    print(f"Creating {commands_file} file..")
    header = (
        "# Copyright (c) 2025, Oracle and/or its affiliates.\n"
        "# Licensed under the Universal Permissive License v1.0 as shown at\n"
        "# https://oss.oracle.com/licenses/upl.\n\n"
        "# This list contains all OCI cli commands\n\n"
    )
    write_file(commands_file, header + "\n".join(get_canonical_commands()) + "\n")


def create_denylist(version):
    denylist_prefix = OUTPUT_DIR / "denylist"
    denylist_filename = OUTPUT_DIR / f"denylist_{version}"
    commands_file = OUTPUT_DIR / f"commands_{version}.txt"

    if os.path.exists(denylist_filename):
        backup_filename = denylist_filename.with_name(
            f"{denylist_filename.name}_backup_{datetime.now().strftime('%d%b%y_%H%M')}"
        )
        os.rename(denylist_filename, backup_filename)

    with open(commands_file, "r") as f:
        commands = [line.strip() for line in f if not line.strip().startswith("#") and len(line.strip()) > 0]

    denied_commands = get_denied_commands(commands)

    write_file(denylist_filename, "\n".join(denied_commands) + "\n")

    header = (
        "# Copyright (c) 2025, Oracle and/or its affiliates.\n"
        "# Licensed under the Universal Permissive License v1.0 as shown at\n"
        "# https://oss.oracle.com/licenses/upl.\n\n"
        "# This list contains the list of commands that can change the configuration of the cloud system.\n"  # noqa E501
        "# These commands will be denied execution and the AI client should immediately stop processing the command.\n"  # noqa E501
        "# It should also stop suggesting any alternatives to the user\n\n"
    )
    write_file(denylist_prefix, header + "\n".join(denied_commands) + "\n")

    print(f"{denylist_prefix} has been created successfully")

    denied_count = len(denied_commands)
    total_count = len(commands)
    print(f"{denied_count} commands will be denied out of {total_count} commands")


def main():
    version = get_oci_version()
    get_commands(version)
    create_denylist(version)


if __name__ == "__main__":
    main()
