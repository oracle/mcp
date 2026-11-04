"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Run initialization, tool discovery and ping against an installed stdio command.
Usage: python3 tests/stdio_smoke.py command [arguments ...]
"""

import asyncio
import json
import sys
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def smoke(command: str, args: list[str]) -> None:
    params = StdioServerParameters(command=command, args=args)
    async with stdio_client(params) as (read, write):
        async with ClientSession(
            read, write, read_timeout_seconds=timedelta(seconds=30)
        ) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "pricing_get_sku",
                "pricing_search_name",
                "ping",
            }
            result = await session.call_tool("ping", {})
            assert not result.isError, result
            assert result.content[0].text == "ok", result
            print(
                json.dumps(
                    {
                        "server": initialized.serverInfo.name,
                        "tools": [tool.name for tool in tools.tools],
                        "ping": "ok",
                    }
                )
            )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python3 tests/stdio_smoke.py command [arguments ...]")
    asyncio.run(smoke(sys.argv[1], sys.argv[2:]))
