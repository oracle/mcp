"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from .prompts import register_prompts
from .runtime.mcp_app import mcp
from .tools import register_tools


register_tools()
register_prompts()


def main() -> None:
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()

__all__ = ["main", "mcp"]
