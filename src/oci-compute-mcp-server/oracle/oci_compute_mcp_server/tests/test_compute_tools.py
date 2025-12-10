"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client
from oracle.oci_compute_mcp_server.server import mcp


class TestComputeTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_instances(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.Instance(
                id="instance1",
                display_name="Instance 1",
                lifecycle_state="RUNNING",
                shape="VM.Standard.E2.1",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_instances.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_instances", {"compartment_id": "test_compartment"}
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "instance1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_get_instance(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.Instance(
            id="instance1", display_name="Instance 1", lifecycle_state="RUNNING"
        )
        mock_client.get_instance.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_instance", {"instance_id": "instance1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "instance1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_launch_instance(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_launch_response = create_autospec(oci.response.Response)
        mock_launch_response.data = oci.core.models.Instance(
            id="instance1", display_name="Instance 1", lifecycle_state="PROVISIONING"
        )
        mock_client.launch_instance.return_value = mock_launch_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "launch_instance",
                    {
                        "compartment_id": "test_compartment",
                        "display_name": "test_instance",
                        "availability_domain": "AD1",
                        "image_id": "image1",
                        "subnet_id": "subnet1",
                    },
                )
            ).structured_content

            assert result["id"] == "instance1"
            assert result["lifecycle_state"] == "PROVISIONING"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_terminate_instance(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_delete_response = create_autospec(oci.response.Response)
        mock_delete_response.status = 204
        mock_client.terminate_instance.return_value = mock_delete_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "terminate_instance",
                {
                    "instance_id": "instance1",
                },
            )
            result = call_tool_result.structured_content

            assert result["status"] == 204

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_update_instance(self, mock_get_client):
        ocpus = 2
        memory_in_gbs = 16

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_update_response = create_autospec(oci.response.Response)
        mock_update_response.data = oci.core.models.Instance(
            shape_config=oci.core.models.UpdateInstanceShapeConfigDetails(
                ocpus=ocpus,
                memory_in_gbs=memory_in_gbs,
            )
        )
        mock_client.update_instance.return_value = mock_update_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "update_instance",
                {
                    "instance_id": "instance1",
                    "ocpus": ocpus,
                    "memory_in_gbs": memory_in_gbs,
                },
            )
            result = call_tool_result.structured_content

            assert result["shape_config"]["ocpus"] == ocpus
            assert result["shape_config"]["memory_in_gbs"] == memory_in_gbs

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_images(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.Image(
                id="image1",
                display_name="Image 1",
                operating_system="Oracle Linux",
                operating_system_version="8",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_images.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_images",
                {
                    "compartment_id": "test_compartment",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "image1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_get_image(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.Image(
            id="image1",
            display_name="Image 1",
            operating_system="Oracle Linux",
            operating_system_version="8",
        )
        mock_client.get_image.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_image",
                {
                    "image_id": "image1",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "image1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_instance_action(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_action_response = create_autospec(oci.response.Response)
        mock_action_response.data = oci.core.models.Instance(
            id="instance1",
            display_name="Instance 1",
            lifecycle_state="STOPPING",
            shape="VM.Standard.E2.1",
        )
        mock_client.instance_action.return_value = mock_action_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "instance_action",
                {
                    "instance_id": "instance1",
                    "action": "STOP",
                },
            )
            result = call_tool_result.structured_content

            assert result["id"] == "instance1"
            assert result["lifecycle_state"] == "STOPPING"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_vnic_attachments(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.VnicAttachment(
                id="vnicattachment1",
                display_name="VNIC attachment 1",
                lifecycle_state="ATTACHED",
            )
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_vnic_attachments.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_vnic_attachments",
                {
                    "compartment_id": "test_compartment",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "vnicattachment1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_get_vnic_attachment(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.core.models.VnicAttachment(
            id="vnicattachment1",
            display_name="VNIC attachment 1",
            lifecycle_state="ATTACHED",
        )
        mock_client.get_vnic_attachment.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_vnic_attachment", {"vnic_attachment_id": "vnicattachment1"}
            )
            result = call_tool_result.structured_content

            assert result["id"] == "vnicattachment1"


class TestServer:
    @patch("oracle.oci_compute_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
        }

        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_compute_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(
            transport="http",
            host=mock_env["ORACLE_MCP_HOST"],
            port=int(mock_env["ORACLE_MCP_PORT"]),
        )

    @patch("oracle.oci_compute_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None
        import oracle.oci_compute_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_compute_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_host(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_compute_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_compute_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x: mock_env.get(x)
        import oracle.oci_compute_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
