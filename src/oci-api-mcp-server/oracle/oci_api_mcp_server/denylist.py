"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import shlex


class Denylist:
    _denylist_path = os.path.join(os.path.dirname(__file__), "denylist")
    _global_options_with_values = {
        "--auth",
        "--cert-bundle",
        "--cli-rc-file",
        "--config-file",
        "--endpoint",
        "--max-retries",
        "--output",
        "--profile",
        "--query",
        "--region",
        "--realm-specific-endpoint",
    }
    _global_flags_without_values = {
        "--all",
        "--debug",
        "--generate-full-command-json-input",
        "--help",
        "--no-retry",
        "--raw-output",
        "--version",
    }

    def __init__(self, logger, user_specific_path: str = ""):
        self.logger = logger
        self.denylist_path = user_specific_path or self._denylist_path
        self.denylist = self.read_denylist()
        self.logger.info(
            "Read denylist from %s successfully. Blocking %d commands",
            self._denylist_path,
            len(self.denylist),
        )

    def read_denylist(self):
        try:
            with open(self.denylist_path, "r") as denylist_file:
                return [
                    line.strip()
                    for line in denylist_file.read().splitlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
        except FileNotFoundError:
            self.logger.warning(f"Denylist file not found at {self.denylist_path}")
            return []

    def _command_words(self, command: str) -> list[str]:
        """Return the OCI command path without option flags or option values."""
        command_parts = shlex.split(command)
        if command_parts and command_parts[0] == "oci":
            command_parts = command_parts[1:]

        command_words = []
        i = 0
        while i < len(command_parts):
            part = command_parts[i]
            if part.startswith("--"):
                option = part.split("=", 1)[0]
                if "=" in part or option in self._global_flags_without_values:
                    i += 1
                elif option in self._global_options_with_values:
                    i += 2 if i + 1 < len(command_parts) else 1
                elif command_words:
                    i += 2 if i + 1 < len(command_parts) and not command_parts[i + 1].startswith("-") else 1
                else:
                    i += 1
            else:
                command_words.append(part)
                i += 1
        return command_words

    def remove_params_from_command(self, command: str) -> str:
        """Removes parameters from an OCI CLI command."""
        return " ".join(self._command_words(command))

    def isCommandInDenyList(self, command: str) -> bool:
        command_without_params = self.remove_params_from_command(command.strip())
        self.logger.info("Checking command: %s", command_without_params)
        return any(
            command_without_params == denied_command
            or command_without_params.startswith(f"{denied_command} ")
            for denied_command in self.denylist
        )
