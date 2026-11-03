"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, mock_open, patch

import fastmcp.exceptions
import oci
import oracle.oci_compute_mcp_server.server as server
import pytest
from fastmcp import Client
from fastmcp.server.auth import AccessToken
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
                "list_instances",
                {"compartment_id": "test_compartment", "lifecycle_state": "RUNNING"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "instance1"
    

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_instances_respects_limit_across_pages(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        page1 = create_autospec(oci.response.Response)
        page1.data = [
            oci.core.models.Instance(
                id=f"instance-{i}",
                display_name=f"Instance {i}",
                lifecycle_state="RUNNING",
                shape="VM.Standard.E2.1",
            )
            for i in range(1, 3)
        ]
        page1.has_next_page = True
        page1.next_page = "token-1"

        page2 = create_autospec(oci.response.Response)
        page2.data = [
            oci.core.models.Instance(
                id=f"instance-{i}",
                display_name=f"Instance {i}",
                lifecycle_state="RUNNING",
                shape="VM.Standard.E2.1",
            )
            for i in range(3, 5)
        ]
        # A next page exists, but the requested result cap is reached.
        page2.has_next_page = True
        page2.next_page = "token-2"

        mock_client.list_instances.side_effect = [page1, page2]

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_instances",
                    {"compartment_id": "test_compartment", "limit": 3},
                )
            ).structured_content["result"]

        assert len(result) == 3
        assert [item["id"] for item in result] == [
            "instance-1",
            "instance-2",
            "instance-3",
        ]

        calls = mock_client.list_instances.call_args_list
        assert [call.kwargs["limit"] for call in calls] == [3, 1]
        assert [call.kwargs["page"] for call in calls] == [None, "token-1"]
        assert mock_client.list_instances.call_count == 2

    
    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_instances_continues_after_empty_page_without_limit(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        page1 = create_autospec(oci.response.Response)
        page1.data = []
        page1.has_next_page = True
        page1.next_page = "token-1"

        page2 = create_autospec(oci.response.Response)
        page2.data = [
            oci.core.models.Instance(
                id="instance-1",
                display_name="Instance 1",
                lifecycle_state="RUNNING",
                shape="VM.Standard.E2.1",
            )
        ]
        page2.has_next_page = True
        page2.next_page = "token-2"

        page3 = create_autospec(oci.response.Response)
        page3.data = [
            oci.core.models.Instance(
                id="instance-2",
                display_name="Instance 2",
                lifecycle_state="RUNNING",
                shape="VM.Standard.E2.1",
            )
        ]
        page3.has_next_page = False
        page3.next_page = None

        mock_client.list_instances.side_effect = [page1, page2, page3]

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_instances",
                    {"compartment_id": "test_compartment"},
                )
            ).structured_content["result"]

        assert [item["id"] for item in result] == [
            "instance-1",
            "instance-2",
        ]
        assert mock_client.list_instances.call_count == 3

        calls = mock_client.list_instances.call_args_list
        assert [call.kwargs["page"] for call in calls] == [
            None,
            "token-1",
            "token-2",
        ]
        assert all(call.kwargs["limit"] is None for call in calls)

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_instances_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.list_instances.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool("list_instances", {"compartment_id": "test_compartment"})

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'list_instances'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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
            call_tool_result = await client.call_tool("get_instance", {"instance_id": "instance1"})
            result = call_tool_result.structured_content

            assert result["id"] == "instance1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_get_instance_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.get_instance.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool("get_instance", {"instance_id": "instance1"})

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'get_instance'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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

            source_details = mock_client.launch_instance.call_args.args[0].source_details
            assert isinstance(source_details, oci.core.models.InstanceSourceViaImageDetails)
            assert source_details.image_id == "image1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_launch_instance_from_boot_volume(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_launch_response = create_autospec(oci.response.Response)
        mock_launch_response.data = oci.core.models.Instance(
            id="instance1", display_name="Instance 1", lifecycle_state="PROVISIONING"
        )
        mock_client.launch_instance.return_value = mock_launch_response

        async with Client(mcp) as client:
            await client.call_tool(
                "launch_instance",
                {
                    "compartment_id": "test_compartment",
                    "display_name": "test_instance",
                    "availability_domain": "AD1",
                    "boot_volume_id": "ocid1.bootvolume.oc1..example",
                    "subnet_id": "subnet1",
                },
            )

        source_details = mock_client.launch_instance.call_args.args[0].source_details
        assert isinstance(source_details, oci.core.models.InstanceSourceViaBootVolumeDetails)
        assert source_details.boot_volume_id == "ocid1.bootvolume.oc1..example"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_launch_instance_rejects_empty_boot_volume_id(self, mock_get_client):
        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError, match="boot_volume_id must not be empty"):
                await client.call_tool(
                    "launch_instance",
                    {
                        "compartment_id": "test_compartment",
                        "display_name": "test_instance",
                        "availability_domain": "AD1",
                        "boot_volume_id": "",
                        "subnet_id": "subnet1",
                    },
                )

        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_launch_instance_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.launch_instance.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
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

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'launch_instance'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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
    async def test_terminate_instance_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.terminate_instance.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool(
                    "terminate_instance",
                    {
                        "instance_id": "instance1",
                    },
                )

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'terminate_instance'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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
    async def test_update_instance_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.update_instance.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool(
                    "update_instance",
                    {
                        "instance_id": "instance1",
                        "ocpus": 2,
                        "memory_in_gbs": 16,
                    },
                )

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'update_instance'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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
                    "operating_system": "Oracle Linux",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "image1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_images_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.list_images.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool(
                    "list_images",
                    {
                        "compartment_id": "test_compartment",
                    },
                )

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'list_images'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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
                {"image_id": "image1"},
            )
            result = call_tool_result.structured_content

            assert result["id"] == "image1"

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_get_image_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.get_image.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool(
                    "get_image",
                    {
                        "image_id": "image1",
                    },
                )

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'get_image'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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
    async def test_instance_action_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.instance_action.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool(
                    "instance_action",
                    {
                        "instance_id": "instance1",
                        "action": "STOP",
                    },
                )

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'instance_action'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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
                {"compartment_id": "test_compartment", "instance_id": "instance1"},
            )
            result = call_tool_result.structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == "vnicattachment1"
    

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_vnic_attachments_respects_limit_across_pages(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        page1 = create_autospec(oci.response.Response)
        page1.data = [
            oci.core.models.VnicAttachment(
                id=f"vnic-{i}",
                display_name=f"VNIC {i}",
                lifecycle_state="ATTACHED",
            )
            for i in range(1, 3)
        ]
        page1.has_next_page = True
        page1.next_page = "token-1"

        page2 = create_autospec(oci.response.Response)
        page2.data = [
            oci.core.models.VnicAttachment(
                id=f"vnic-{i}",
                display_name=f"VNIC {i}",
                lifecycle_state="ATTACHED",
            )
            for i in range(3, 5)
        ]
        page2.has_next_page = True
        page2.next_page = "token-2"

        mock_client.list_vnic_attachments.side_effect = [page1, page2]

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_vnic_attachments",
                    {"compartment_id": "test_compartment", "limit": 3},
                )
            ).structured_content["result"]

        assert len(result) == 3
        assert [item["id"] for item in result] == [
            "vnic-1",
            "vnic-2",
            "vnic-3",
        ]

        calls = mock_client.list_vnic_attachments.call_args_list
        assert [call.kwargs["limit"] for call in calls] == [3, 1]
        assert [call.kwargs["page"] for call in calls] == [None, "token-1"]
        assert mock_client.list_vnic_attachments.call_count == 2

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_vnic_attachments_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.list_vnic_attachments.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool(
                    "list_vnic_attachments",
                    {
                        "compartment_id": "test_compartment",
                    },
                )

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'list_vnic_attachments'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)

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

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_get_vnic_attachment_exception(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock the client to raise an exception
        mock_client.get_vnic_attachment.side_effect = oci.exceptions.ServiceError(
            status=500,
            code="InternalServerError",
            message="Internal server error",
            opc_request_id="test_request_id",
            headers={},
        )

        async with Client(mcp) as client:
            with pytest.raises(fastmcp.exceptions.ToolError) as e:
                await client.call_tool("get_vnic_attachment", {"vnic_attachment_id": "vnicattachment1"})

            # Verify the ToolError message contains the expected details
            assert "Error calling tool 'get_vnic_attachment'" in str(e.value)
            assert "'status': 500" in str(e.value)
            assert "'code': 'InternalServerError'" in str(e.value)
            assert "'message': 'Internal server error'" in str(e.value)


class TestServer:
    @patch("oracle.oci_compute_mcp_server.server.oci.auth.signers.TokenExchangeSigner", return_value="signer")
    @patch("oracle.oci_compute_mcp_server.server.oci.config.from_file", side_effect=AssertionError)
    @patch("oracle.oci_compute_mcp_server.server.get_access_token")
    def test_http_signer_uses_region_without_loading_config(
        self, mock_get_access_token, _mock_from_file, mock_token_exchange_signer, monkeypatch
    ):
        mock_get_access_token.return_value = AccessToken(token="token", client_id="client", scopes=[], claims={})
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
        monkeypatch.setenv("OCI_REGION", "us-phoenix-1")

        config, signer = server._get_http_config_and_signer()

        assert config["region"] == "us-phoenix-1"
        assert signer == "signer"
        mock_token_exchange_signer.assert_called_once()

    @patch("oracle.oci_compute_mcp_server.server.get_access_token", return_value=None)
    def test_http_signer_requires_authenticated_token(self, _mock_get_access_token, monkeypatch):
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")

        with pytest.raises(RuntimeError, match="authenticated IDCS access token"):
            server._get_http_config_and_signer()

    def test_http_signer_requires_region(self, monkeypatch):
        monkeypatch.setattr(
            server,
            "get_access_token",
            lambda: AccessToken(token="token", client_id="client", scopes=[], claims={}),
        )
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

        with pytest.raises(RuntimeError, match="OCI_REGION"):
            server._get_http_config_and_signer()

    @patch("oracle.oci_compute_mcp_server.server.OCIProvider")
    @patch("oracle.oci_compute_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run, mock_provider):
        mock_env = {
            "ORACLE_MCP_HOST": "1.2.3.4",
            "ORACLE_MCP_PORT": "8888",
            "IDCS_DOMAIN": "idcs.example.com",
            "IDCS_CLIENT_ID": "client-id",
            "IDCS_CLIENT_SECRET": "client-secret",
            "IDCS_AUDIENCE": "mcp-audience",
            "ORACLE_MCP_BASE_URL": "https://mcp.example.com",
        }

        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)
        mock_provider.return_value = MagicMock()
        import oracle.oci_compute_mcp_server.server as server

        server.main()
        mock_provider.assert_called_once_with(
            config_url="https://idcs.example.com/.well-known/openid-configuration",
            client_id="client-id",
            client_secret="client-secret",
            audience="mcp-audience",
            required_scopes=f"openid profile email oci_mcp.{server.__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
            base_url="https://mcp.example.com",
        )
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
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)
        import oracle.oci_compute_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @patch("oracle.oci_compute_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_only_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_PORT": "8888",
        }
        mock_getenv.side_effect = lambda x, d=None: mock_env.get(x, d)
        import oracle.oci_compute_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_images_without_filter(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            oci.core.models.Image(
                id="image1",
                display_name="Image 1",
                operating_system="Oracle Linux",
                operating_system_version="8",
            ),
            oci.core.models.Image(
                id="image2",
                display_name="Image 2",
                operating_system="Ubuntu",
                operating_system_version="22.04",
            ),
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

            assert len(result) == 2
            assert {img["id"] for img in result} == {"image1", "image2"}


class TestGetClient:
    @patch("oracle.oci_compute_mcp_server.server.oci.core.ComputeClient")
    @patch("oracle.oci_compute_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_compute_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_compute_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_compute_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_compute_mcp_server.server.os.getenv")
    def test_get_compute_client_with_profile_env(
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
        result = server.get_compute_client()

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

    @patch("oracle.oci_compute_mcp_server.server.oci.core.ComputeClient")
    @patch("oracle.oci_compute_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_compute_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_compute_mcp_server.server.open",
        new_callable=mock_open,
        read_data="TOK",
    )
    @patch("oracle.oci_compute_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_compute_mcp_server.server.os.getenv")
    def test_get_compute_client_uses_default_profile_when_env_missing(
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
        srv_client = server.get_compute_client()

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

    @pytest.mark.asyncio
    @patch("oracle.oci_compute_mcp_server.server.get_compute_client")
    async def test_list_images_filtered_pagination_respects_limit(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # First page contains no matching images but has another page.
        resp_page_1 = create_autospec(oci.response.Response)
        resp_page_1.data = [
            oci.core.models.Image(
                id="ubuntu-image",
                display_name="Ubuntu Image",
                operating_system="Ubuntu",
                operating_system_version="22.04",
            )
        ]
        resp_page_1.has_next_page = True
        resp_page_1.next_page = "token-1"

        # The second page deliberately returns more matching images than
        # the remaining allowance to verify local limit enforcement.
        resp_page_2 = create_autospec(oci.response.Response)
        resp_page_2.data = [
            oci.core.models.Image(
                id="oracle-image-1",
                display_name="Oracle Linux 1",
                operating_system="Oracle Linux",
                operating_system_version="8",
            ),
            oci.core.models.Image(
                id="oracle-image-2",
                display_name="Oracle Linux 2",
                operating_system="Oracle Linux",
                operating_system_version="8",
            ),
            oci.core.models.Image(
                id="oracle-image-3",
                display_name="Oracle Linux 3",
                operating_system="Oracle Linux",
                operating_system_version="8",
            ),
        ]
        resp_page_2.has_next_page = False
        resp_page_2.next_page = None

        mock_client.list_images.side_effect = [resp_page_1, resp_page_2]

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_images",
                    {
                        "compartment_id": "test_compartment",
                        "operating_system": "Oracle Linux",
                        "limit": 2,
                    },
                )
            ).structured_content["result"]

        # Only matching images count toward the emitted result limit.
        assert len(result) == 2
        assert [image["id"] for image in result] == [
            "oracle-image-1",
            "oracle-image-2",
        ]

        # Continue after the filtered-out page and pass the remaining allowance.
        calls = mock_client.list_images.call_args_list
        assert [call.kwargs["limit"] for call in calls] == [2, 2]
        assert calls[0].kwargs["page"] is None
        assert calls[1].kwargs["page"] == "token-1"
