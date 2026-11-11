"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

The FastMCP app and the scaffolding every tool family shares.

Separate from server.py so a tool family can reach ``mcp`` without importing the
module that imports it: server.py imports each family to register its tools, and
a family that reached back into server.py for the decorator would close that
loop. Everything here is imported by the families, never the reverse.
"""

import os
import time
from typing import Optional

from fastmcp import FastMCP

from . import __project__


# Every tool here reads; none creates, updates or deletes an OCI resource. These
# hints tell an MCP host that much without a human reading the README, so a host
# can skip a confirmation prompt it would otherwise raise on an unknown tool.
_READ_ONLY_TOOL = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    # Results come from OCI, not from a closed set the server owns.
    "openWorldHint": True,
}


# The guidance tools return static text and never reach the network.
_LOCAL_GUIDANCE_TOOL = {**_READ_ONLY_TOOL, "openWorldHint": False}


# Create the FastMCP app that exposes the functions decorated with @mcp.tool.
# main() attaches the OCI IAM OAuth provider when it selects the HTTP transport.
mcp = FastMCP(name=__project__)


_TOOL_DEADLINE_SECONDS = float(os.getenv("ORACLE_MCP_TOOL_DEADLINE_SECONDS", "120"))


class _Deadline:
    """A cooperative monotonic-time budget for a fan-out the caller cannot see.

    The summary tools issue one request per protected database across every
    compartment in scope, so a large tenancy turns a single tool call into
    hundreds of sequential round trips -- long past the point where an MCP client
    has given up waiting. Stopping at a deadline and saying so is more useful
    than a request that never returns. Set ORACLE_MCP_TOOL_DEADLINE_SECONDS to 0
    to scan without a limit. An OCI request already in flight is allowed to
    finish; callers check the budget between requests.
    """

    def __init__(self, seconds: Optional[float] = None):
        """
        Start the budget, defaulting to ORACLE_MCP_TOOL_DEADLINE_SECONDS.

        A budget of 0 (or None resolving to 0) means no deadline at all.
        """
        budget = _TOOL_DEADLINE_SECONDS if seconds is None else seconds
        self._expires_at = (time.monotonic() + budget) if budget and budget > 0 else None
        self.expired = False

    def reached(self) -> bool:
        """Report whether the budget is spent, latching ``expired`` once it is."""
        if self._expires_at is not None and time.monotonic() >= self._expires_at:
            self.expired = True
        return self.expired
