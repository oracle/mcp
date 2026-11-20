"""
Copyright (c) 2025, 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import time

from behave import given, then, when
from codex_runner import parse_events, run_process


@given("the mock OCI services are running")
def step_impl(context):
    assert context.mock_proc.poll() is None, "Mock OCI server is not running"
    assert context.shim_proc.poll() is None, "Mock OCI proxy is not running"


@given("the Codex CLI is configured with OCI tools")
def step_impl_codex(context):
    # required=true makes Codex fail the turn if an enabled MCP server cannot start.
    assert context.codex.servers, "No enabled MCP servers"


@when('I send a request with the prompt "{prompt}"')
def step_impl_prompt(context, prompt):
    session = context.codex
    start = time.monotonic()
    output = run_process(
        session.command,
        context.system_prompt + "\n\n" + prompt,
        session.env,
        session.cwd,
        timeout=context.codex_timeout,
    )
    context.result = parse_events(output, session.servers)
    for warning in context.result.warnings:
        print(f"Codex startup warning: {warning[:1000]}")
    print(f"Codex: {time.monotonic() - start:.2f}s; usage={context.result.usage}")
    print("MCP calls:", ", ".join(f"{call['server']}.{call['tool']}" for call in context.result.calls))
    if context.result.resource_calls:
        print("MCP resource calls:", ", ".join(call["tool"] for call in context.result.resource_calls))
    if context.result.failed_calls:
        print(
            "Failed MCP attempts (diagnostic):",
            ", ".join(f"{call['server']}.{call['tool']}" for call in context.result.failed_calls),
        )
    if not context.inventory_only:
        assert context.result.calls, "Operation scenario completed without a successful MCP call"


@then("the response should contain a list of tools available")
def step_impl_tools_available(context):
    # Inventory scenarios need a live required catalog and names, not a fabricated tool call.
    content = context.result.text.replace("-", "_")
    for server in context.mcp_servers:
        assert server.replace("-", "_") in content, f"{server} is missing from tools"
