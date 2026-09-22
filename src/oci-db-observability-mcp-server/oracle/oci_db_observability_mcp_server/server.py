"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Unified DBO MCP process entry point.
"""
from __future__ import annotations

from .mcp import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
