"""
Example: Streamable HTTP client for the Atlassian MCP server.

This example sends a couple of JSON-RPC messages over a single HTTP POST
using NDJSON and prints streamed NDJSON responses from the server.

Prereqs:
  - Server running (in another terminal):
      uv run -m mcp_atlassian_oauth
    Default endpoint: http://localhost:8765/mcp

  - httpx must be available (included in [dev] extras):
      uv run -m pytest -q   # just to ensure environment is synced
      # or simply: uv run python examples/python_client.py

Usage:
  uv run python src/mcp-atlassian-oauth/examples/python_client.py
"""

import asyncio
import json
import os
from typing import AsyncGenerator

import httpx


def ndjson_line(obj) -> bytes:
    return (json.dumps(obj) + "\n").encode("utf-8")


async def request_body() -> AsyncGenerator[bytes, None]:
    # Minimal handshake and a tools/list request.
    # You can add more lines here to exercise call_tool, etc.
    initialize = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "examples/python_client.py", "version": "0.1.0"},
            "capabilities": {}
        },
    }
    list_tools = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/list"
    }

    # Send initialize, wait for server to process, then initialized + list_tools
    yield ndjson_line(initialize)
    # Give the server a brief moment to emit the initialize result
    await asyncio.sleep(0.5)

    initialized = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    yield ndjson_line(initialized)
    await asyncio.sleep(0.5)

    yield ndjson_line(list_tools)
    await asyncio.sleep(0.5)

    # Optionally, you can call tools/call after verifying tools/list succeeds.
    # Example:
    # call_set_defaults_show = {
    #     "jsonrpc": "2.0",
    #     "id": "3",
    #     "method": "tools/call",
    #     "params": {
    #         "name": "set_defaults",
    #         "arguments": {"show": True}
    #     }
    # }
    # yield ndjson_line(call_set_defaults_show)
    # await asyncio.sleep(0.15)

    # End of request body (generator completes).
    # For interactive sessions, you could await input() and yield more lines.


async def main() -> None:
    url = os.environ.get("MCP_URL", "http://localhost:8765/mcp")
    headers = {"Content-Type": "application/x-ndjson"}

    print(f"[client] Connecting to {url}")
    async with httpx.AsyncClient(timeout=None) as client:
        # Stream both upload (content=request_body()) and response chunks
        async with client.stream("POST", url, headers=headers, content=request_body()) as resp:
            print(f"[client] HTTP {resp.status_code}")
            async for chunk in resp.aiter_bytes():
                if not chunk:
                    continue
                # Response may contain multiple NDJSON lines per chunk; split safely
                for line in chunk.split(b"\n"):
                    s = line.strip()
                    if not s:
                        continue
                    try:
                        obj = json.loads(s.decode("utf-8"))
                        print("[server]", json.dumps(obj, indent=2))
                    except Exception:
                        print("[server/raw]", s)

    print("[client] Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
