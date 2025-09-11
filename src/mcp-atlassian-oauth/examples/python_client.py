"""
Example: Programmatically start the MCP Atlassian server and call a tool.

Note:
- This example relies on the MCP Python client API being available in your installed "mcp" package.
- The exact client API may differ by version. If imports fail, consult the MCP Python SDK docs.
- Prefer configuring this server in Cline and using use_mcp_tool for day-to-day use.

Usage:
  python examples/python_client.py
"""

import asyncio
import os
import sys

try:
    # The client API location may vary by version; adjust if needed.
    from mcp.client.stdio import stdio_client  # type: ignore
except Exception as e:
    print("[error] MCP Python client API not found in 'mcp' package.")
    print("Install/upgrade MCP SDK and see https://github.com/modelcontextprotocol for client usage.")
    print(f"Import error: {e}")
    sys.exit(1)


async def main():
    # Ensure required env vars are set before running.
    required = ["JIRA_BASE_URL", "CONF_BASE_URL"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[warn] Missing environment variables: {', '.join(missing)}")
        print("       You can copy examples/.env.example to examples/.env and use tools/run_local.sh")
        # Continue anyway; some tools may not require both services for a simple list

    # Command to launch this server via stdio
    command = sys.executable
    args = ["-m", "mcp_atlassian_oauth"]

    print(f"[info] Spawning server: {command} {' '.join(args)}")
    # Connect to the server over stdio. Exact tuple contents depend on SDK version.
    async with stdio_client(command, args) as (client, read, write):  # type: ignore
        # Initialize handshake (method name may vary with SDK)
        if hasattr(client, "initialize"):
            await client.initialize()
        print("[info] Initialized MCP client.")

        # List tools
        tools = []
        if hasattr(client, "list_tools"):
            tools = await client.list_tools()
        elif hasattr(client, "listTools"):
            tools = await client.listTools()
        else:
            print("[warn] Client SDK does not expose list_tools(); skipping.")
        print("[info] Tools available:", [getattr(t, "name", str(t)) for t in tools])

        # Example tool call: jira_get_myself (requires JIRA_* env and valid token)
        tool_name = "jira_get_myself"
        print(f"[info] Attempting tool call: {tool_name}")
        result = None
        if hasattr(client, "call_tool"):
            result = await client.call_tool(tool_name, {})
        elif hasattr(client, "callTool"):
            result = await client.callTool(tool_name, {})
        else:
            print("[warn] Client SDK does not expose call_tool(); skipping.")

        if result is not None:
            # Result format may differ by SDK; try to print safely
            try:
                # Many SDKs return a list of content parts
                print("[info] Tool result:", result)
            except Exception:
                print("[info] Tool result received (unprintable structure).")

        print("[info] Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
