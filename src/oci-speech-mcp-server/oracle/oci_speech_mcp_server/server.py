"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import logging

from fastmcp import FastMCP

from . import __project__, __version__
from .prompts import register_prompts
from .resources import register_resources
from .tools import register_tools

logger = logging.getLogger(__name__)
mcp = FastMCP(name=__project__)

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


def main() -> None:
    """Run the server over stdio for local MCP clients."""
    logger.info("Starting %s %s over stdio", __project__, __version__)
    mcp.run()


if __name__ == "__main__":
    main()
