"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os


class Denylist:
    _denylist_path = os.path.join(os.path.dirname(__file__), "denylist")

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

    def remove_params_from_command(self, command: str) -> str:
        """Removes parameters from an OCI CLI command."""
        command_parts = command.split()
        filtered_parts = []
        i = 0
        while i < len(command_parts):
            if command_parts[i].startswith("--"):
                i += (
                    1
                    if i + 1 >= len(command_parts)
                    or command_parts[i + 1].startswith("--")
                    else 2
                )
            else:
                filtered_parts.append(command_parts[i])
                i += 1
        return " ".join(filtered_parts)

    def isCommandInDenyList(self, command: str) -> bool:
        command_without_params = self.remove_params_from_command(command.strip())
        self.logger.info("Checking command: %s", command_without_params)
        return command_without_params in self.denylist
