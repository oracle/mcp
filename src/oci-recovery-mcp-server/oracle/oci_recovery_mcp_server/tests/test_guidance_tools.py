"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest
from fastmcp import Client

from oracle.oci_recovery_mcp_server.prompt_tools import (
    DIAGNOSE_RECOVERY_SERVICE_ISSUE_PROMPT,
    OCI_RECOVERY_SERVICE_DASHBOARD_PROMPT,
    ONBOARD_DATABASE_TO_RECOVERY_SERVICE_PROMPT,
)
from oracle.oci_recovery_mcp_server.server import mcp


class TestGuidanceTools:
    """
    The three prompt-backed tools that serve guidance text to clients that cannot
    read MCP prompts.
    """

    @pytest.mark.asyncio
    async def test_dashboard_prompt_is_available_as_a_tool(self):
        """The dashboard tool is registered, and returns the prompt text verbatim."""
        async with Client(mcp) as client:
            tools = await client.list_tools()
            result = await client.call_tool("oci_recovery_service_dashboard_prompt", {})

        assert "oci_recovery_service_dashboard_prompt" in {tool.name for tool in tools}
        assert result.structured_content["result"] == OCI_RECOVERY_SERVICE_DASHBOARD_PROMPT
        assert "cloud-protected databases" in result.structured_content["result"]

    @pytest.mark.asyncio
    async def test_cloud_protect_onboarding_guidance_is_available_as_a_tool(self):
        """The onboarding tool is registered, and returns the prompt text verbatim."""
        async with Client(mcp) as client:
            tools = await client.list_tools()
            result = await client.call_tool("onboard_database_to_recovery_service", {})

        assert "onboard_database_to_recovery_service" in {tool.name for tool in tools}
        assert result.structured_content["result"] == ONBOARD_DATABASE_TO_RECOVERY_SERVICE_PROMPT
        assert "Recovery Service subnet OCID" in result.structured_content["result"]

    @pytest.mark.asyncio
    async def test_diagnostic_guidance_is_available_as_a_tool(self):
        """The diagnostic tool is registered, and returns the prompt text verbatim."""
        async with Client(mcp) as client:
            tools = await client.list_tools()
            result = await client.call_tool("diagnose_recovery_service_issue", {})

        assert "diagnose_recovery_service_issue" in {tool.name for tool in tools}
        assert result.structured_content["result"] == DIAGNOSE_RECOVERY_SERVICE_ISSUE_PROMPT
        assert "Recovery Service Diagnostic Assistant" in result.structured_content["result"]
