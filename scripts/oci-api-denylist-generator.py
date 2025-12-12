"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import re
import subprocess
import time
from datetime import datetime

COMMANDS_FILENAME = "commands.txt"
DENYLIST_FILENAME = "denylist"


def create_backup(filename):
    if os.path.exists(filename):
        backup_filename = f"{filename}_backup_{datetime.now().strftime('%d%b%y_%H%M')}"
        os.rename(filename, backup_filename)


def get_oci_version():
    result = subprocess.run(
        ["oci", "--version", "--raw-output"], capture_output=True, text=True
    )
    return result.stdout.strip()


def get_commands_version():
    """Read the version from the 5th line of COMMANDS_FILENAME."""
    if not os.path.exists(COMMANDS_FILENAME):
        return None
    with open(COMMANDS_FILENAME, "r") as f:
        lines = f.readlines()
    if len(lines) < 6:
        return None
    version_line = lines[5].strip()
    if version_line.startswith("# Version: "):
        return version_line[11:].strip()  # Skip "# Version: "
    return None


def get_services():
    result = subprocess.run(["oci", "--help"], capture_output=True, text=True)
    output = result.stdout.splitlines()
    services = []
    for line in output:
        match = re.match(r"^\s{4}(\w+(-\w+)*)", line)
        if match:
            services.append(match.group(1))
    services = services[5:]  # Skipping the first 5 lines as they are not services
    services.sort()
    return services


def get_sub_commands(command: str):
    indentation_level = len(command.split())
    print(f"{'  '*indentation_level}Getting subcommands for: {command}")
    try:
        result = subprocess.run(
            f"oci {command} --help", shell=True, capture_output=True, text=True
        )
        output = result.stdout.splitlines()
        sub_commands = []
        in_commands_section = False
        for line in output:
            if "Commands:" in line:
                in_commands_section = True
                continue
            if in_commands_section:
                if line.startswith("   "):
                    continue
                # match = re.match(r"^\s{2}(\w+)", line)
                match = line.split()[0]
                if match:
                    print(
                        f"{'  '*indentation_level+'\033[K'}Appending sub command {match}",
                        end="\r",
                    )
                    time.sleep(0.5)
                    sub_commands.append(match)
        if not sub_commands:
            return [command]
        else:
            commands = []
            for sub_command in sub_commands:
                commands.extend(get_sub_commands(f"{command} {sub_command}"))
            return commands
    except Exception as e:
        print(f"Error getting sub-commands for {command}: {e}")
        return []


def get_commands(version):
    commands_version = get_commands_version()
    if not os.path.exists(COMMANDS_FILENAME) or (commands_version != version):
        print(f"Creating {COMMANDS_FILENAME} file..")
        create_backup(COMMANDS_FILENAME)

        services = get_services()
        with open(COMMANDS_FILENAME, "w") as f:
            f.write(
                (
                    "# Copyright (c) 2025, Oracle and/or its affiliates.\n"
                    "# Licensed under the Universal Permissive License v1.0 as shown at\n"
                    "# https://oss.oracle.com/licenses/upl.\n\n"
                    "# This list contains all OCI cli commands\n"
                    f"# Version: {version}\n\n"
                )
            )
            num_services = len(services)
            for index, service in enumerate(services):
                print(
                    f"\nGenerating commands for service: {service} - [{index+1} out of {num_services}]"
                )
                commands = get_sub_commands(service)
                for command in commands:
                    f.write(command + "\n")
                    f.flush()
    else:
        print(f"Commands already exist for version {version}")


def create_denylist(version):
    create_backup(DENYLIST_FILENAME)

    with open(COMMANDS_FILENAME, "r") as f:
        commands = [
            line.strip()
            for line in f
            if not line.strip().startswith("#") and len(line.strip()) > 0
        ]

    actions = [
        "delete",
        "terminate",
        "put",
        "update",
        "replace",
        "remove",
        "patch",
    ]

    denied_commands = [
        cmd.strip()
        for cmd in commands
        if any(cmd.split()[-1].startswith(action) for action in actions)
    ]

    with open(DENYLIST_FILENAME, "w") as f:
        f.write(
            (
                "# Copyright (c) 2025, Oracle and/or its affiliates.\n"
                "# Licensed under the Universal Permissive License v1.0 as shown at\n"
                "# https://oss.oracle.com/licenses/upl.\n\n"
                "# This list contains the list of commands that can change the configuration of the cloud system.\n"  # noqa E501
                f"# This list has been generated from version {version} of the OCI CLI.\n"
                "# These commands will be denied execution and the AI client should immediately stop processing the command.\n"  # noqa E501
                "# It should also stop suggesting any alternatives to the user\n\n"
            )
        )
        f.write("\n".join(sorted(denied_commands)))

    print(f"{DENYLIST_FILENAME} has been created successfully")

    denied_count = len(denied_commands)
    total_count = len(commands)
    print(f"{denied_count} commands will be denied out of {total_count} commands")


def main():
    version = get_oci_version()
    get_commands(version)
    create_denylist(version)


if __name__ == "__main__":
    main()
