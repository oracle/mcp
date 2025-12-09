"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_object_storage_mcp_server.models import (
    Bucket,
    BucketSummary,
    ListObjects,
    ObjectSummary,
    ObjectVersionCollection,
    ObjectVersionSummary,
)
from oracle.oci_object_storage_mcp_server.server import mcp


def parse(double_encoded_text: str):
    return json.loads(json.loads(double_encoded_text))


def parse_array(array_str: str):
    items = json.loads(array_str)
    return [json.loads(item) for item in items]


class TestObjectStorageTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_get_namespace(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        async with Client(mcp) as client:
            result = (
                (
                    await client.call_tool(
                        "get_namespace", {"compartment_id": "test_compartment"}
                    )
                )
                .content[0]
                .text
            )

            assert result == "test_namespace"

    @pytest.mark.asyncio
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_list_buckets(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            BucketSummary(
                name="bucket1",
                etag="etag1",
                time_created="2021-01-01T00:00:00.000Z",
            )
        ]
        mock_client.list_buckets.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_buckets", {"compartment_id": "test_compartment"}
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "bucket1"

    @pytest.mark.asyncio
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_get_bucket_details(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = Bucket(
            name="bucket1",
            etag="etag1",
            time_created="2021-01-01T00:00:00.000Z",
            approximate_size=100,
            approximate_count=10,
            auto_tiering="INFREQUENT",
        )
        mock_client.get_bucket.return_value = mock_get_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    name="get_bucket_details",
                    arguments={
                        "bucket_name": "bucket1",
                        "compartment_id": "test_compartment",
                    },
                )
            ).structured_content

            assert result["name"] == "bucket1"
            assert result["approximate_size"] == 100

    @pytest.mark.asyncio
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_list_objects(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = ListObjects(
            objects=[
                ObjectSummary(
                    name="object1",
                    size=100,
                    time_modified="2021-01-01T00:00:00.000Z",
                    archival_state="ARCHIVED",
                    storage_tier="STANDARD",
                )
            ]
        )
        mock_client.list_objects.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_objects",
                    {
                        "bucket_name": "bucket1",
                        "compartment_id": "test_compartment",
                    },
                )
            ).structured_content["objects"]

            assert len(result) == 1
            assert result[0]["name"] == "object1"

    @pytest.mark.asyncio
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_list_object_versions(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = ObjectVersionCollection(
            items=[
                ObjectVersionSummary(
                    name="object1",
                    time_modified="2021-01-01T00:00:00.000Z",
                    is_delete_marker=False,
                    version_id="version_1",
                )
            ]
        )
        mock_client.list_object_versions.return_value = mock_list_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_object_versions",
                    {
                        "bucket_name": "bucket1",
                        "compartment_id": "test_compartment",
                    },
                )
            ).structured_content

            assert len(result["items"]) == 1
            assert result["items"][0]["name"] == "object1"
            assert result["items"][0]["version_id"] == "version_1"


class TestServer:
    @patch("oracle.oci_object_storage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_object_storage_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_object_storage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_object_storage_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_object_storage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_object_storage_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_object_storage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_object_storage_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
