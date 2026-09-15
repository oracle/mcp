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
        "--auth-purpose",
        "--cert-bundle",
        "--cli-rc-file",
        "--connection-timeout",
        "--config-file",
        "--defaults-file",
        "--enable-propagation",
        "--endpoint",
        "--federation-endpoint",
        "--generate-param-json-input",
        "--max-retries",
        "--opc-client-request-id",
        "--opc-request-id",
        "--output",
        "--profile",
        "--proxy",
        "--query",
        "--read-timeout",
        "--region",
        "--request-id",
    }
    _global_flags_without_values = {
        "--cli-auto-prompt",
        "--debug",
        "--enable-dual-stack",
        "--generate-full-command-json-input",
        "--help",
        "--latest-version",
        "--no-retry",
        "--raw-output",
        "--realm-specific-endpoint",
        "--release-info",
        "--version",
        "-?",
        "-d",
        "-h",
        "-i",
        "-v",
    }

    def __init__(self, logger, user_specific_path: str = ""):
        self.logger = logger
        self.denylist_path = user_specific_path or self._denylist_path
        self.denylist = self.read_denylist()
        self.logger.info(
            "Read denylist from %s successfully. Blocking %d commands",
            self.denylist_path,
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
        except FileNotFoundError as exc:
            message = f"Denylist file not found at {self.denylist_path}"
            self.logger.error(message)
            raise RuntimeError(message) from exc

    def _is_short_global_flag_cluster(self, token: str) -> bool:
        return (
            token.startswith("-")
            and not token.startswith("--")
            and len(token) > 2
            and all(
                f"-{short_option}" in self._global_flags_without_values
                for short_option in token[1:]
            )
        )

    def _command_words(self, command: str) -> list[str]:
        """Return the OCI command path, excluding global options."""
        command_parts = shlex.split(command)
        if command_parts and command_parts[0] == "oci":
            command_parts = command_parts[1:]

        command_words = []
        i = 0
        while i < len(command_parts):
            part = command_parts[i]
            if part.startswith("-"):
                option = part.split("=", 1)[0]
                if option in self._global_flags_without_values and "=" not in part:
                    i += 1
                elif self._is_short_global_flag_cluster(part):
                    i += 1
                elif option in self._global_options_with_values:
                    if "=" in part:
                        i += 1
                    elif i + 1 < len(command_parts):
                        i += 2
                    else:
                        raise ValueError(f"Missing value for global OCI option: {option}")
                elif command_words:
                    break
                else:
                    raise ValueError(f"Unsupported leading OCI option: {option}")
            else:
                command_words.append(part)
                i += 1

        return command_words

    def remove_params_from_command(self, command: str) -> str:
        """Removes parameters from an OCI CLI command."""
        return " ".join(self._command_words(command))

    def isCommandInDenyList(self, command: str) -> bool:
        try:
            command_without_params = self.remove_params_from_command(command.strip())
        except ValueError as exc:
            self.logger.warning("Denying command with ambiguous command path: %s", exc)
            return True
        self.logger.info("Checking command: %s", command_without_params)
        return any(
            command_without_params == denied_command
            or command_without_params.startswith(f"{denied_command} ")
            for denied_command in self.denylist
        )
