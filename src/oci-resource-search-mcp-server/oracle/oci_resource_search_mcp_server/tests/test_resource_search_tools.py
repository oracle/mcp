"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_resource_search_mcp_server.server import mcp


class TestResourceSearchTools:
    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_all_resources(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_search_response = create_autospec(oci.response.Response)
        mock_search_response.data = (
            oci.resource_search.models.ResourceSummaryCollection(
                items=[
                    oci.resource_search.models.ResourceSummary(
                        identifier="resource1",
                        display_name="Resource 1",
                        resource_type="instance",
                        lifecycle_state="RUNNING",
                    )
                ]
            )
        )
        mock_search_response.has_next_page = False
        mock_search_response.next_page = None
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_all_resources",
                    {
                        "tenant_id": "tenant1",
                        "compartment_id": "compartment1",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["identifier"] == "resource1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_search_response = create_autospec(oci.response.Response)
        mock_search_response.data = (
            oci.resource_search.models.ResourceSummaryCollection(
                items=[
                    oci.resource_search.models.ResourceSummary(
                        identifier="resource1",
                        display_name="Resource 1",
                        resource_type="instance",
                        lifecycle_state="RUNNING",
                    )
                ]
            )
        )
        mock_search_response.has_next_page = False
        mock_search_response.next_page = None
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources",
                    {
                        "tenant_id": "tenant1",
                        "compartment_id": "compartment1",
                        "display_name": "Resource",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["identifier"] == "resource1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_free_form(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_search_response = create_autospec(oci.response.Response)
        mock_search_response.data = (
            oci.resource_search.models.ResourceSummaryCollection(
                items=[
                    oci.resource_search.models.ResourceSummary(
                        identifier="resource1",
                        display_name="Resource 1",
                        resource_type="instance",
                        lifecycle_state="RUNNING",
                    )
                ]
            )
        )
        mock_search_response.has_next_page = False
        mock_search_response.next_page = None
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources_free_form",
                    {
                        "tenant_id": "tenant1",
                        "text": "Resource",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["identifier"] == "resource1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_by_type(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_search_response = create_autospec(oci.response.Response)
        mock_search_response.data = (
            oci.resource_search.models.ResourceSummaryCollection(
                items=[
                    oci.resource_search.models.ResourceSummary(
                        identifier="db1",
                        display_name="DB 1",
                        resource_type="dbsystem",
                        lifecycle_state="AVAILABLE",
                    )
                ]
            )
        )
        mock_search_response.has_next_page = False
        mock_search_response.next_page = None
        mock_client.search_resources.return_value = mock_search_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources_by_type",
                    {
                        "tenant_id": "tenant1",
                        "compartment_id": "compartment1",
                        "resource_type": "DBSystem",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["resource_type"] == "dbsystem"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_resource_types(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.resource_search.models.ResourceType(name="instance"),
            oci.resource_search.models.ResourceType(name="volume"),
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_resource_types.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (await client.call_tool("list_resource_types", {})).data

            assert result == ["instance", "volume"]

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_all_resources_pagination(self, mock_get_client):
        # Two pages, second response lacks next_page attribute to hit hasattr False branch
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        first = create_autospec(oci.response.Response)
        first.data = oci.resource_search.models.ResourceSummaryCollection(
            items=[oci.resource_search.models.ResourceSummary(identifier="r1")]
        )
        first.has_next_page = True
        first.next_page = "token-2"

        second = create_autospec(oci.response.Response)
        second.data = oci.resource_search.models.ResourceSummaryCollection(
            items=[oci.resource_search.models.ResourceSummary(identifier="r2")]
        )
        second.has_next_page = False
        # Deliberately no next_page attribute
        if hasattr(second, "next_page"):
            delattr(second, "next_page")

        mock_client.search_resources.side_effect = [first, second]

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_all_resources",
                    {"tenant_id": "t1", "compartment_id": "c1"},
                )
            ).structured_content["result"]

        assert [r["identifier"] for r in result] == ["r1", "r2"]

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_resource_types_no_next_page_attr(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        resp = create_autospec(oci.response.Response)
        resp.data = [oci.resource_search.models.ResourceType(name="instance")]
        resp.has_next_page = False
        # Remove next_page to exercise hasattr False
        if hasattr(resp, "next_page"):
            delattr(resp, "next_page")
        mock_client.list_resource_types.return_value = resp

        async with Client(mcp) as client:
            result = (await client.call_tool("list_resource_types", {})).data

        assert result == ["instance"]

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_no_next_page_attr(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        resp = create_autospec(oci.response.Response)
        resp.data = oci.resource_search.models.ResourceSummaryCollection(
            items=[oci.resource_search.models.ResourceSummary(identifier="x")]
        )
        resp.has_next_page = False
        if hasattr(resp, "next_page"):
            delattr(resp, "next_page")
        mock_client.search_resources.return_value = resp
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources",
                    {
                        "tenant_id": "t1",
                        "compartment_id": "c1",
                        "display_name": "name",
                    },
                )
            ).structured_content["result"]
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_free_form_no_next_page_attr(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        resp = create_autospec(oci.response.Response)
        resp.data = oci.resource_search.models.ResourceSummaryCollection(
            items=[oci.resource_search.models.ResourceSummary(identifier="y")]
        )
        resp.has_next_page = False
        if hasattr(resp, "next_page"):
            delattr(resp, "next_page")
        mock_client.search_resources.return_value = resp
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources_free_form",
                    {"tenant_id": "t1", "text": "any"},
                )
            ).structured_content["result"]
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_by_type_no_next_page_attr(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        resp = create_autospec(oci.response.Response)
        resp.data = oci.resource_search.models.ResourceSummaryCollection(
            items=[oci.resource_search.models.ResourceSummary(identifier="z")]
        )
        resp.has_next_page = False
        if hasattr(resp, "next_page"):
            delattr(resp, "next_page")
        mock_client.search_resources.return_value = resp
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "search_resources_by_type",
                    {
                        "tenant_id": "t1",
                        "compartment_id": "c1",
                        "resource_type": "instance",
                    },
                )
            ).structured_content["result"]
        assert len(result) == 1

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_all_resources_respects_limit(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = oci.resource_search.models.ResourceSummaryCollection(
            items=[
                oci.resource_search.models.ResourceSummary(identifier="a"),
                oci.resource_search.models.ResourceSummary(identifier="b"),
            ]
        )
        resp.has_next_page = True
        resp.next_page = "tok"
        mock_client.search_resources.return_value = resp

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_all_resources",
                    {"tenant_id": "t1", "compartment_id": "c1", "limit": 1},
                )
            ).structured_content["result"]
        # The server appends all items from a page before checking the limit
        assert len(result) == 2
        # Only one SDK call occurred because the loop stops paging once len(resources) >= limit
        mock_client.search_resources.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_all_resources_error_path(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_resources.side_effect = RuntimeError("boom")
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "list_all_resources",
                    {"tenant_id": "t1", "compartment_id": "c1"},
                )

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_error_path(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_resources.side_effect = RuntimeError("err")
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "search_resources",
                    {
                        "tenant_id": "t1",
                        "compartment_id": "c1",
                        "display_name": "x",
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_free_form_error_path(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_resources.side_effect = RuntimeError("ff")
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "search_resources_free_form",
                    {"tenant_id": "t1", "text": "any"},
                )

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_search_resources_by_type_error_path(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search_resources.side_effect = RuntimeError("type")
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool(
                    "search_resources_by_type",
                    {
                        "tenant_id": "t1",
                        "compartment_id": "c1",
                        "resource_type": "instance",
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_resource_types_error_path(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_resource_types.side_effect = RuntimeError("oops")
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("list_resource_types", {})
