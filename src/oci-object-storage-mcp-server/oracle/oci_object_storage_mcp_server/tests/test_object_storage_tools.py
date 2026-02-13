"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

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


class TestObjectStorageTools:
    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_namespace(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        async with Client(mcp) as client:
            response = await client.call_tool(
                "get_namespace", {"compartment_id": "test_compartment"}
            )
            # get_namespace returns unstructured text content only
            assert response.content[0].text == "test_namespace"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_buckets(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_bucket_response = create_autospec(oci.response.Response)
        mock_bucket_response.data = [BucketSummary(name="bucket1")]
        mock_client.list_buckets.return_value = mock_bucket_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_buckets", {"compartment_id": "test_compartment"}
                )
            ).structured_content["result"]

        assert len(result) == 1
        assert result[0]["name"] == "bucket1"

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_bucket_details(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_bucket_response = create_autospec(oci.response.Response)
        mock_bucket_response.data = Bucket(
            name="bucket1",
            approximate_size=100,
        )
        mock_client.get_bucket.return_value = mock_bucket_response

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
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_objects(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_list_objects_response = create_autospec(oci.response.Response)
        mock_list_objects_response.data = ListObjects(
            objects=[
                ObjectSummary(
                    name="object1",
                    size=100,
                    storage_tier="STANDARD",
                )
            ]
        )
        mock_client.list_objects.return_value = mock_list_objects_response

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
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_object_versions(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_list_response = ObjectVersionCollection(
            items=[
                ObjectVersionSummary(
                    name="object1",
                    time_modified="2021-01-01T00:00:00.000Z",
                    is_delete_marker=False,
                    version_id="version_1",
                )
            ]
        )
        mock_list_versions_response = create_autospec(oci.response.Response)
        mock_list_versions_response.data = mock_list_response
        mock_client.list_object_versions.return_value = mock_list_versions_response

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

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_object(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_get_object_response = create_autospec(oci.response.Response)
        mock_get_object_response.data = ObjectSummary(name="object1", size=42)
        mock_client.get_object.return_value = mock_get_object_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "get_object",
                    {
                        "bucket_name": "bucket1",
                        "compartment_id": "test_compartment",
                        "object_name": "object1",
                    },
                )
            ).structured_content

        assert result["name"] == "object1"
        assert result["size"] == 42

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_upload_object_success(self, mock_create_client, tmp_path):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        p = tmp_path / "file.txt"
        p.write_bytes(b"hello world")

        async with Client(mcp) as client:
            response = await client.call_tool(
                "upload_object",
                {
                    "bucket_name": "bucket1",
                    "compartment_id": "test_compartment",
                    "file_path": str(p),
                    "object_name": "file.txt",
                },
            )

        structured = response.structured_content or {}
        structured = structured.get("result", structured)
        assert structured["message"] == "Object uploaded successfully"
        mock_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_upload_object_error(self, mock_create_client, tmp_path):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        bad_path = tmp_path / "does_not_exist.bin"

        async with Client(mcp) as client:
            response = await client.call_tool(
                "upload_object",
                {
                    "bucket_name": "bucket1",
                    "compartment_id": "test_compartment",
                    "file_path": str(bad_path),
                    "object_name": "file.bin",
                },
            )

        structured = response.structured_content or {}
        structured = structured.get("result", structured)
        assert "error" in structured
        assert (
            "No such file" in structured["error"]
            or "No such file or directory" in structured["error"]
        )
