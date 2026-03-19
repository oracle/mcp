"""
Temporary manual JMS MCP validation client.

This script connects to an already-running HTTP MCP server and exercises the
JMS tool surface for quick operator testing. Remove it before committing.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

from fastmcp import Client

DEFAULT_URL = "http://127.0.0.1:8888/mcp"

#compartment = JMS-TEST-CANARY
DEFAULT_COMPARTMENT_ID = (
    ""
)

#fleet name = auto-ol8-epp-test
DEFAULT_FLEET_ID = (
    ""
)

TOOL_ORDER = [
    "list_fleets",
    "get_fleet",
    "list_jms_plugins",
    "get_jms_plugin",
    "list_installation_sites",
    "get_fleet_agent_configuration",
    "get_fleet_advanced_feature_configuration",
    "summarize_resource_inventory",
    "summarize_managed_instance_usage",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run manual validation against a running JMS MCP HTTP server."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="MCP HTTP endpoint URL.")
    parser.add_argument(
        "--compartment-id",
        default=DEFAULT_COMPARTMENT_ID,
        help="Compartment OCID used by list and summarize calls.",
    )
    parser.add_argument(
        "--fleet-id",
        default=DEFAULT_FLEET_ID,
        help="Fleet OCID used by fleet-scoped calls.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit for list-style tool calls.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Per-tool timeout in seconds.",
    )
    parser.add_argument(
        "--tool",
        choices=["all", *TOOL_ORDER],
        default="all",
        help="Run one tool or the full tool suite.",
    )
    return parser.parse_args()


def summarize_structured_content(structured: Any) -> tuple[str, str | None]:
    if isinstance(structured, dict):
        if "result" in structured and isinstance(structured["result"], list):
            items = structured["result"]
            first_id = None
            if items and isinstance(items[0], dict):
                first_id = items[0].get("id")
            summary = f"count={len(items)}"
            if first_id:
                summary += f" first_id={first_id}"
            return summary, first_id
        if "id" in structured:
            return f"id={structured['id']}", structured["id"]
        keys = ",".join(sorted(structured.keys())[:5])
        return f"keys={keys}", None

    if isinstance(structured, list):
        first_id = None
        if structured and isinstance(structured[0], dict):
            first_id = structured[0].get("id")
        summary = f"count={len(structured)}"
        if first_id:
            summary += f" first_id={first_id}"
        return summary, first_id

    return f"type={type(structured).__name__}", None


async def call_tool(
    client: Client,
    tool_name: str,
    payload: dict[str, Any],
    timeout: int,
) -> tuple[str, str | None]:
    try:
        result = await asyncio.wait_for(client.call_tool(tool_name, payload), timeout=timeout)
        summary, first_id = summarize_structured_content(result.structured_content)
        return f"PASS {tool_name}: {summary}", first_id
    except asyncio.TimeoutError:
        return f"TIMEOUT {tool_name}: timed out after {timeout}s", None
    except Exception as exc:  # noqa: BLE001
        return f"FAIL {tool_name}: {type(exc).__name__}: {exc}", None


async def run_suite(args: argparse.Namespace) -> int:
    requested_tools = TOOL_ORDER if args.tool == "all" else [args.tool]
    results: list[str] = []
    failures = 0
    plugin_id: str | None = None

    async with Client(args.url) as client:
        tools = await asyncio.wait_for(client.list_tools(), timeout=args.timeout)
        tool_names = [tool.name for tool in tools]
        results.append(f"Connected to {args.url}")
        results.append(f"Discovered {len(tool_names)} tools: {', '.join(tool_names)}")

        if args.tool in ("all", "list_fleets"):
            line, _ = await call_tool(
                client,
                "list_fleets",
                {
                    "compartment_id": args.compartment_id,
                    "limit": args.limit,
                    "sort_order": "ASC",
                    "sort_by": "displayName",
                },
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

        if args.tool in ("all", "get_fleet"):
            line, _ = await call_tool(
                client,
                "get_fleet",
                {"fleet_id": args.fleet_id},
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

        if args.tool in ("all", "list_jms_plugins"):
            line, plugin_id = await call_tool(
                client,
                "list_jms_plugins",
                {
                    "fleet_id": args.fleet_id,
                    "limit": args.limit,
                    "sort_order": "ASC",
                },
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

        if args.tool == "get_jms_plugin":
            plugin_id = None

        if args.tool in ("all", "get_jms_plugin"):
            if plugin_id is None:
                if args.tool == "get_jms_plugin":
                    results.append(
                        "FAIL get_jms_plugin: requires a plugin returned by list_jms_plugins in all-tools mode"
                    )
                    failures += 1
                else:
                    results.append("SKIPPED get_jms_plugin: no plugin returned by list_jms_plugins")
            else:
                line, _ = await call_tool(
                    client,
                    "get_jms_plugin",
                    {"jms_plugin_id": plugin_id},
                    args.timeout,
                )
                results.append(line)
                failures += int(not line.startswith("PASS"))

        if args.tool in ("all", "list_installation_sites"):
            line, _ = await call_tool(
                client,
                "list_installation_sites",
                {
                    "fleet_id": args.fleet_id,
                    "limit": args.limit,
                    "sort_order": "ASC",
                },
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

        if args.tool in ("all", "get_fleet_agent_configuration"):
            line, _ = await call_tool(
                client,
                "get_fleet_agent_configuration",
                {"fleet_id": args.fleet_id},
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

        if args.tool in ("all", "get_fleet_advanced_feature_configuration"):
            line, _ = await call_tool(
                client,
                "get_fleet_advanced_feature_configuration",
                {"fleet_id": args.fleet_id},
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

        if args.tool in ("all", "summarize_resource_inventory"):
            line, _ = await call_tool(
                client,
                "summarize_resource_inventory",
                {"compartment_id": args.compartment_id},
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

        if args.tool in ("all", "summarize_managed_instance_usage"):
            line, _ = await call_tool(
                client,
                "summarize_managed_instance_usage",
                {
                    "fleet_id": args.fleet_id,
                    "limit": args.limit,
                    "sort_order": "ASC",
                },
                args.timeout,
            )
            results.append(line)
            failures += int(not line.startswith("PASS"))

    for line in results:
        print(line)

    executed = sum(
        line.startswith(("PASS", "FAIL", "TIMEOUT", "SKIPPED")) for line in results
    )
    passed = sum(line.startswith("PASS") for line in results)
    skipped = sum(line.startswith("SKIPPED") for line in results)
    print(f"Summary: passed={passed} failed={failures} skipped={skipped} executed={executed}")
    return 0 if failures == 0 else 1


def main() -> int:
    args = parse_args()
    return asyncio.run(run_suite(args))


if __name__ == "__main__":
    raise SystemExit(main())
