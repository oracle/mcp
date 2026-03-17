"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_object_storage_mcp_server import server
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
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_get_namespace(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        async with Client(mcp) as client:
            response = await client.call_tool("get_namespace", {"compartment_id": "test_compartment"})
            result = response.content[0].text

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
                await client.call_tool("list_buckets", {"compartment_id": "test_compartment"})
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

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

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

    @pytest.mark.asyncio
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_get_object(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = ObjectSummary(name="object1", size=42)
        mock_client.get_object.return_value = mock_get_response

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
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_upload_object_success(self, mock_get_client, tmp_path):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        p = tmp_path / "file.txt"
        p.write_bytes(b"hello world")

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "upload_object",
                    {
                        "bucket_name": "bucket1",
                        "compartment_id": "test_compartment",
                        "file_path": str(p),
                        "object_name": "file.txt",
                    },
                )
            ).structured_content

        assert result["message"] == "Object uploaded successfully"
        mock_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.oci_object_storage_mcp_server.server.get_object_storage_client")
    async def test_upload_object_error(self, mock_get_client, tmp_path):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_namespace_response = create_autospec(oci.response.Response)
        mock_namespace_response.data = "test_namespace"
        mock_client.get_namespace.return_value = mock_namespace_response

        bad_path = tmp_path / "does_not_exist.bin"

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "upload_object",
                    {
                        "bucket_name": "bucket1",
                        "compartment_id": "test_compartment",
                        "file_path": str(bad_path),
                        "object_name": "file.bin",
                    },
                )
            ).structured_content

        assert "error" in result
        assert "No such file" in result["error"] or "No such file or directory" in result["error"]


class TestServer:
    @patch("oracle.oci_object_storage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)

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

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_object_storage_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)

        server.main()
        mock_mcp_run.assert_called_once_with()


class TestGetClient:
    @patch("oracle.oci_object_storage_mcp_server.server.oci.object_storage.ObjectStorageClient")
    @patch("oracle.oci_object_storage_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_object_storage_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_object_storage_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_object_storage_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_object_storage_mcp_server.server.os.getenv")
    def test_get_object_storage_client_with_profile_env(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: provide profile via env var and minimal config dict
        mock_getenv.side_effect = lambda k, default=None: (
            "MYPROFILE" if k == "OCI_CONFIG_PROFILE" else default
        )
        config = {
            "key_file": "/abs/path/to/key.pem",
            "security_token_file": "/abs/path/to/token",
        }
        mock_from_file.return_value = config
        private_key_obj = object()
        mock_load_private_key.return_value = private_key_obj

        # Act
        result = server.get_object_storage_client()

        # Assert calls
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name="MYPROFILE",
        )
        mock_open_file.assert_called_once_with("/abs/path/to/token", "r")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key_obj)
        # Ensure user agent was set on the same config dict passed into client
        args, _ = mock_client.call_args
        passed_config = args[0]
        assert passed_config is config
        expected_user_agent = (
            f"{server.__project__.split('oracle.', 1)[1].split('-server', 1)[0]}/{server.__version__}"  # noqa
        )
        assert passed_config.get("additional_user_agent") == expected_user_agent
        # And we returned the client instance
        assert result == mock_client.return_value

    @patch("oracle.oci_object_storage_mcp_server.server.oci.object_storage.ObjectStorageClient")
    @patch("oracle.oci_object_storage_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_object_storage_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_object_storage_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_object_storage_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_object_storage_mcp_server.server.os.getenv")
    def test_get_object_storage_client_uses_default_profile_when_env_missing(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        # Arrange: no env var present; from_file should be called with DEFAULT_PROFILE
        mock_getenv.side_effect = lambda k, default=None: default
        config = {"key_file": "/k.pem", "security_token_file": "/tkn"}
        mock_from_file.return_value = config
        priv = object()
        mock_load_private_key.return_value = priv

        # Act
        srv_client = server.get_object_storage_client()

        # Assert: profile defaulted
        mock_from_file.assert_called_once_with(
            file_location=oci.config.DEFAULT_LOCATION,
            profile_name=oci.config.DEFAULT_PROFILE,
        )
        # Token file opened and read
        mock_open_file.assert_called_once_with("/tkn", "r")
        mock_security_token_signer.assert_called_once()
        signer_args, _ = mock_security_token_signer.call_args
        assert signer_args[0] == "TOK"
        assert signer_args[1] is priv
        # additional_user_agent set on original config and passed through
        cc_args, _ = mock_client.call_args
        assert cc_args[0] is config
        assert "additional_user_agent" in config
        assert isinstance(config["additional_user_agent"], str) and "/" in config["additional_user_agent"]
        # Returned object is client instance
        assert srv_client is mock_client.return_value
