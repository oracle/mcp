"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

MCP prompt registrations.
"""

from __future__ import annotations


_REGISTERED = False


def register_prompts() -> None:
    """Import prompt modules once so their decorators register with FastMCP."""
    global _REGISTERED
    if _REGISTERED:
        return

    from . import vision_workflows  # noqa: F401

    _REGISTERED = True
