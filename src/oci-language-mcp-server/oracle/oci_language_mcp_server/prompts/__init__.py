# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Server instructions used by MCP clients during discovery."""

from __future__ import annotations

from importlib.resources import files


def load_instructions() -> str:
    return files(__package__).joinpath("server_instructions.md").read_text(encoding="utf-8")
