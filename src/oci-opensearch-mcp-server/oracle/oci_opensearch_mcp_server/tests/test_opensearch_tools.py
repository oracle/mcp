"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock, create_autospec, patch

import oci
import pytest
from fastmcp import Client

from oracle.oci_opensearch_mcp_server import server
from oracle.oci_opensearch_mcp_server.scripts import (
    OPENSEARCH_API_GUIDE,
    TOOL_SURFACE_SUMMARY,
    WORK_REQUEST_GUIDE,
    get_script_content,
)
from oracle.oci_opensearch_mcp_server.server import mcp


async def _tools_by_name():
    return {tool.name: tool for tool in await mcp.list_tools()}


def _object_schema(schema: dict, property_name: str) -> dict:
    property_schema = schema["properties"][property_name]
    candidates = property_schema.get("anyOf") or [property_schema]
    for candidate in candidates:
        ref = candidate.get("$ref")
        if ref:
            return schema["$defs"][ref.split("/")[-1]]
        if candidate.get("type") == "object":
            return candidate
    raise AssertionError(f"No object schema found for {property_name}")


class TestOpenSearchTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_opensearch_clusters(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.opensearch.models.OpensearchClusterCollection(
            items=[
                oci.opensearch.models.OpensearchClusterSummary(
                    id="ocid1.opensearchcluster.oc1..cluster1",
                    display_name="cluster-one",
                    compartment_id="ocid1.compartment.oc1..compartment1",
                    lifecycle_state="ACTIVE",
                    software_version="3.2.0",
                )
            ]
        )
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_opensearch_clusters.return_value = mock_list_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_opensearch_clusters",
                {"compartment_id": "ocid1.compartment.oc1..compartment1"},
            )

        payload = result.structured_content["result"]
        assert len(payload) == 1
        assert payload[0]["display_name"] == "cluster-one"
        mock_client.list_opensearch_clusters.assert_called_once_with("ocid1.compartment.oc1..compartment1")

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_opensearch_clusters_with_explicit_optional_parameters(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.opensearch.models.OpensearchClusterCollection(items=[])
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_opensearch_clusters.return_value = mock_list_response

        async with Client(mcp) as client:
            await client.call_tool(
                "list_opensearch_clusters",
                {
                    "compartment_id": "ocid1.compartment.oc1..compartment1",
                    "lifecycle_state": "ACTIVE",
                    "sort_by": "timeCreated",
                    "sort_order": "ASC",
                    "limit": 10,
                    "opc_request_id": "req-list-clusters",
                },
            )

        mock_client.list_opensearch_clusters.assert_called_once_with(
            "ocid1.compartment.oc1..compartment1",
            lifecycle_state="ACTIVE",
            sort_by="timeCreated",
            sort_order="ASC",
            opc_request_id="req-list-clusters",
            limit=10,
        )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_opensearch_clusters_with_identity_filters_and_empty_result(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = oci.opensearch.models.OpensearchClusterCollection(items=[])
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_opensearch_clusters.return_value = mock_list_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_opensearch_clusters",
                {
                    "compartment_id": "ocid1.compartment.oc1..compartment1",
                    "display_name": "cluster-one",
                    "cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                },
            )

        assert result.structured_content["result"] == []
        mock_client.list_opensearch_clusters.assert_called_once_with(
            "ocid1.compartment.oc1..compartment1",
            display_name="cluster-one",
            id="ocid1.opensearchcluster.oc1..cluster1",
        )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_opensearch_clusters_service_error_returns_clean_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_opensearch_clusters.side_effect = oci.exceptions.ServiceError(
            status=403,
            code="NotAuthorizedOrNotFound",
            headers={"opc-request-id": "request-list-clusters-error"},
            message="Authorization failed or requested resource not found.",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_opensearch_clusters",
                {"compartment_id": "ocid1.compartment.oc1..compartment1"},
            )

        payload = result.structured_content["result"]
        assert payload["status"] == 403
        assert payload["code"] == "NotAuthorizedOrNotFound"
        assert "Authorization" in payload["message"]
        assert payload["opc_request_id"] == "request-list-clusters-error"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_opensearch_cluster_shapes(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = oci.opensearch.models.ShapesDetails(
            shapes=["VM.Standard.A1.Flex", "VM.Standard.E4.Flex"]
        )
        mock_client.list_opensearch_cluster_shapes.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_opensearch_cluster_shapes",
                {"compartment_id": "ocid1.compartment.oc1..compartment1"},
            )

        assert result.structured_content["shapes"] == [
            "VM.Standard.A1.Flex",
            "VM.Standard.E4.Flex",
        ]
        mock_client.list_opensearch_cluster_shapes.assert_called_once_with(
            "ocid1.compartment.oc1..compartment1"
        )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_opensearch_cluster_shapes_service_error_returns_clean_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_opensearch_cluster_shapes.side_effect = oci.exceptions.ServiceError(
            status=401,
            code="NotAuthenticated",
            headers={"opc-request-id": "request-list-shapes-error"},
            message="Authentication failed.",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_opensearch_cluster_shapes",
                {"compartment_id": "ocid1.compartment.oc1..compartment1"},
            )

        assert result.structured_content["status"] == 401
        assert result.structured_content["code"] == "NotAuthenticated"
        assert result.structured_content["message"] == "Authentication failed."
        assert result.structured_content["opc_request_id"] == "request-list-shapes-error"

    @pytest.mark.asyncio
    async def test_shape_tool_and_shape_fields_are_discoverable_for_agents(self):
        tools = await _tools_by_name()

        shape_tool = tools["list_opensearch_cluster_shapes"].model_dump()
        create_tool = tools["create_opensearch_cluster"].model_dump()
        resize_tool = tools["resize_opensearch_cluster_vertical"].model_dump()

        assert "*_host_shape" in shape_tool["description"]
        assert "list_opensearch_cluster_shapes" in create_tool["description"]
        assert "list_opensearch_cluster_shapes" in resize_tool["description"]

        create_schema = create_tool["parameters"]
        detail_schema = _object_schema(create_schema, "create_opensearch_cluster_details")
        assert (
            "list_opensearch_cluster_shapes"
            in detail_schema["properties"]["master_node_host_shape"]["description"]
        )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_get_opensearch_cluster(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = oci.opensearch.models.OpensearchCluster(
            id="ocid1.opensearchcluster.oc1..cluster1",
            display_name="cluster-one",
            compartment_id="ocid1.compartment.oc1..compartment1",
            lifecycle_state="ACTIVE",
            software_version="3.2.0",
        )
        mock_client.get_opensearch_cluster.return_value = mock_get_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_opensearch_cluster",
                {"opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1"},
            )

        assert result.structured_content["display_name"] == "cluster-one"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_get_opensearch_cluster_service_error_returns_clean_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_opensearch_cluster.side_effect = oci.exceptions.ServiceError(
            status=404,
            code="NotAuthorizedOrNotFound",
            headers={"opc-request-id": "request-get-cluster-error"},
            message="Cluster not found.",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_opensearch_cluster",
                {"opensearch_cluster_id": "ocid1.opensearchcluster.oc1..missing"},
            )

        assert result.structured_content["status"] == 404
        assert result.structured_content["code"] == "NotAuthorizedOrNotFound"
        assert result.structured_content["message"] == "Cluster not found."
        assert result.structured_content["opc_request_id"] == "request-get-cluster-error"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_with_sdk_aligned_key(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = oci.opensearch.models.OpensearchCluster(
            id="ocid1.opensearchcluster.oc1..cluster1",
            display_name="cluster-one",
            compartment_id="ocid1.compartment.oc1..compartment1",
            lifecycle_state="CREATING",
            software_version="3.2.0",
        )
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-create",
            "opc-request-id": "request-create",
        }
        mock_client.create_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                    }
                },
            )

        assert result.structured_content["status"] == 202
        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-create"
        assert result.structured_content["async_operation"] is True
        assert result.structured_content["status_check_policy"] == "single_get_work_request_then_ask_user"
        assert "polling continuously" in result.structured_content["recommended_next_action"]
        assert result.structured_content["opc_retry_token"].startswith("mcp-create-")
        assert result.structured_content["opc_retry_token_source"] == "generated"
        assert result.structured_content["cluster_id"] == "ocid1.opensearchcluster.oc1..cluster1"
        assert result.structured_content["lifecycle_state"] == "CREATING"
        mock_client.create_opensearch_cluster.assert_called_once()
        sdk_payload = mock_client.create_opensearch_cluster.call_args.args[0]
        assert (
            mock_client.create_opensearch_cluster.call_args.kwargs["opc_retry_token"]
            == result.structured_content["opc_retry_token"]
        )
        assert isinstance(sdk_payload, oci.opensearch.models.CreateOpensearchClusterDetails)
        assert sdk_payload.compartment_id == "ocid1.compartment.oc1..compartment1"
        assert sdk_payload.display_name == "cluster-one"
        assert sdk_payload.software_version == "3.2.0"
        assert sdk_payload.vcn_id == "ocid1.vcn.oc1..vcn1"
        assert sdk_payload.vcn_compartment_id == "ocid1.compartment.oc1..network1"
        assert sdk_payload.subnet_id == "ocid1.subnet.oc1..subnet1"
        assert sdk_payload.subnet_compartment_id == "ocid1.compartment.oc1..network1"
        assert sdk_payload.security_mode == "ENFORCING"
        assert sdk_payload.security_master_user_name == "admin1"
        assert sdk_payload.security_master_user_password_hash == "pbkdf2_stretch_1000$SALT$HASH"
        assert sdk_payload.master_node_host_shape is None
        assert sdk_payload.data_node_host_shape is None
        assert sdk_payload.opendashboard_node_host_shape is None

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_preserves_caller_retry_token(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-create"}
        mock_client.create_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "opc_retry_token": "caller-token-1",
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                    },
                },
            )

        assert result.structured_content["opc_retry_token"] == "caller-token-1"
        assert result.structured_content["opc_retry_token_source"] == "caller"
        assert mock_client.create_opensearch_cluster.call_args.kwargs["opc_retry_token"] == "caller-token-1"

    def test_generated_retry_token_is_deterministic_for_identical_payloads(self):
        payload = {
            "operation": "create_opensearch_cluster",
            "payload": {
                "display_name": "cluster-one",
                "compartment_id": "ocid1.compartment.oc1..compartment1",
            },
        }

        first = server._deterministic_retry_token("mcp-create-", payload)
        second = server._deterministic_retry_token("mcp-create-", dict(reversed(payload.items())))

        assert first == second
        assert first.startswith("mcp-create-")
        assert len(first) <= 64

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_rejects_invalid_retry_token(self, mock_get_client):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="opc_retry_token"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "opc_retry_token": "x" * 65,
                        "create_opensearch_cluster_details": {
                            "display_name": "cluster-one",
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_name": "admin1",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        },
                    },
                )

        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_rejects_plain_security_password_input(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Extra inputs are not permitted"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "display_name": "cluster-one",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_name": "admin1",
                            "security_master_user_password": "Admin#123",
                        }
                    },
                )

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_rejects_invalid_security_password_hash(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="pbkdf2_stretch_1000"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "display_name": "cluster-one",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_name": "admin1",
                            "security_master_user_password_hash": "Admin#123",
                        }
                    },
                )

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_rejects_missing_security_master_user_name(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="security_master_user_name"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "display_name": "cluster-one",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        }
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_rejects_reserved_security_master_user(self, mock_get_client):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="admin"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "display_name": "cluster-one",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_name": "admin",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        }
                    },
                )

        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_rejects_missing_security_master_user_password_hash(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="security_master_user_password_hash"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "display_name": "cluster-one",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_name": "admin1",
                        }
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_accepts_hash_only_security_input(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-create",
            "opc-request-id": "request-create",
        }
        mock_client.create_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                    }
                },
            )

        assert result.structured_content["status"] == 202
        mock_client.create_opensearch_cluster.assert_called_once()
        sdk_payload = mock_client.create_opensearch_cluster.call_args.args[0]
        assert isinstance(sdk_payload, oci.opensearch.models.CreateOpensearchClusterDetails)
        assert sdk_payload.compartment_id == "ocid1.compartment.oc1..compartment1"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_applies_non_shape_defaults_and_allows_partial_overrides(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-create",
            "opc-request-id": "request-create",
        }
        mock_client.create_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        "data_node_count": 3,
                    }
                },
            )

        assert result.structured_content["status"] == 202
        mock_client.create_opensearch_cluster.assert_called_once()
        sdk_payload = mock_client.create_opensearch_cluster.call_args.args[0]
        assert isinstance(sdk_payload, oci.opensearch.models.CreateOpensearchClusterDetails)
        assert sdk_payload.compartment_id == "ocid1.compartment.oc1..compartment1"
        assert sdk_payload.data_node_count == 3
        assert sdk_payload.master_node_host_type == "FLEX"
        assert sdk_payload.data_node_host_type == "FLEX"
        assert sdk_payload.master_node_host_shape is None
        assert sdk_payload.data_node_host_shape is None
        assert sdk_payload.opendashboard_node_host_shape is None

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_passes_explicit_shapes_and_ml_fields(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-create",
            "opc-request-id": "request-create",
        }
        mock_client.create_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        "master_node_host_shape": "VM.Standard.E4.Flex",
                        "data_node_host_shape": "VM.Standard.E4.Flex",
                        "opendashboard_node_host_shape": "VM.Standard.E4.Flex",
                        "search_node_count": 1,
                        "search_node_host_shape": "VM.Standard.E4.Flex",
                        "search_node_host_ocpu_count": 2,
                        "search_node_host_memory_gb": 20,
                        "search_node_storage_gb": 50,
                        "ml_node_count": 1,
                        "ml_node_host_shape": "VM.Standard.E4.Flex",
                        "ml_node_host_ocpu_count": 2,
                        "ml_node_host_memory_gb": 20,
                        "ml_node_storage_gb": 50,
                    }
                },
            )

        assert result.structured_content["status"] == 202
        sdk_payload = mock_client.create_opensearch_cluster.call_args.args[0]
        assert sdk_payload.master_node_host_shape == "VM.Standard.E4.Flex"
        assert sdk_payload.data_node_host_shape == "VM.Standard.E4.Flex"
        assert sdk_payload.opendashboard_node_host_shape == "VM.Standard.E4.Flex"
        assert sdk_payload.search_node_host_shape == "VM.Standard.E4.Flex"
        assert sdk_payload.search_node_host_type == "FLEX"
        assert sdk_payload.ml_node_host_shape == "VM.Standard.E4.Flex"
        assert sdk_payload.ml_node_host_type == "FLEX"
        assert sdk_payload.ml_node_count == 1
        assert sdk_payload.ml_node_host_ocpu_count == 2
        assert sdk_payload.ml_node_host_memory_gb == 20
        assert sdk_payload.ml_node_storage_gb == 50

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_passes_optional_sdk_supported_network_and_security_fields(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-create",
            "opc-request-id": "request-create",
        }
        mock_client.create_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "nsg_id": "ocid1.networksecuritygroup.oc1..nsg1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        "load_balancer_config": {
                            "load_balancer_service_type": "NETWORK_LOAD_BALANCER",
                            "load_balancer_min_bandwidth_in_mbps": 10,
                            "load_balancer_max_bandwidth_in_mbps": 100,
                        },
                        "certificate_config": {
                            "cluster_certificate_mode": "OPENSEARCH_SERVICE",
                            "dashboard_certificate_mode": "OPENSEARCH_SERVICE",
                        },
                        "security_attributes": {"oracle-zpr": {"sensitivity": "internal"}},
                    }
                },
            )

        assert result.structured_content["status"] == 202
        sdk_payload = mock_client.create_opensearch_cluster.call_args.args[0]
        assert sdk_payload.nsg_id == "ocid1.networksecuritygroup.oc1..nsg1"
        assert isinstance(sdk_payload.load_balancer_config, oci.opensearch.models.LoadBalancerConfig)
        assert sdk_payload.load_balancer_config.load_balancer_service_type == "NETWORK_LOAD_BALANCER"
        assert isinstance(sdk_payload.certificate_config, oci.opensearch.models.CertificateConfig)
        assert sdk_payload.certificate_config.cluster_certificate_mode == "OPENSEARCH_SERVICE"
        assert sdk_payload.security_attributes == {"oracle-zpr": {"sensitivity": "internal"}}

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_passes_advanced_optional_configs(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-create-advanced"}
        mock_client.create_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        "backup_policy": {
                            "is_enabled": True,
                            "retention_in_days": 14,
                            "frequency_in_hours": 24,
                        },
                        "security_saml_config": {
                            "is_enabled": True,
                            "idp_entity_id": "https://idp.example.com/entity",
                            "subject_key": "nameid",
                            "roles_key": "roles",
                        },
                        "reverse_connection_endpoint_customer_ips": ["203.0.113.10"],
                        "inbound_cluster_ids": ["ocid1.opensearchcluster.oc1..inbound1"],
                        "outbound_cluster_config": {
                            "is_enabled": True,
                            "outbound_clusters": [
                                {
                                    "display_name": "remote-one",
                                    "seed_cluster_id": "ocid1.opensearchcluster.oc1..remote1",
                                    "mode": "SEARCH_ONLY",
                                    "ping_schedule": "*/5 * * * *",
                                    "is_skip_unavailable": True,
                                }
                            ],
                        },
                        "certificate_config": {
                            "cluster_certificate_mode": "OCI_CERTIFICATES_SERVICE",
                            "dashboard_certificate_mode": "OCI_CERTIFICATES_SERVICE",
                            "open_search_api_certificate_id": "ocid1.certificate.oc1..api1",
                            "open_search_dashboard_certificate_id": "ocid1.certificate.oc1..dashboard1",
                        },
                        "maintenance_details": {"notification_email_ids": ["admin@example.com"]},
                        "freeform_tags": {"env": "qa"},
                        "defined_tags": {"Operations": {"CostCenter": "42"}},
                    }
                },
            )

        assert result.structured_content["status"] == 202
        sdk_payload = mock_client.create_opensearch_cluster.call_args.args[0]
        assert isinstance(sdk_payload.backup_policy, oci.opensearch.models.BackupPolicy)
        assert sdk_payload.backup_policy.is_enabled is True
        assert isinstance(sdk_payload.security_saml_config, oci.opensearch.models.SecuritySamlConfig)
        assert sdk_payload.security_saml_config.roles_key == "roles"
        assert sdk_payload.reverse_connection_endpoint_customer_ips == ["203.0.113.10"]
        assert sdk_payload.inbound_cluster_ids == ["ocid1.opensearchcluster.oc1..inbound1"]
        assert isinstance(
            sdk_payload.outbound_cluster_config,
            oci.opensearch.models.OutboundClusterConfig,
        )
        assert sdk_payload.outbound_cluster_config.is_enabled is True
        assert isinstance(
            sdk_payload.outbound_cluster_config.outbound_clusters[0],
            oci.opensearch.models.OutboundClusterSummary,
        )
        assert (
            sdk_payload.outbound_cluster_config.outbound_clusters[0].seed_cluster_id
            == "ocid1.opensearchcluster.oc1..remote1"
        )
        assert isinstance(sdk_payload.certificate_config, oci.opensearch.models.CertificateConfig)
        assert sdk_payload.certificate_config.cluster_certificate_mode == "OCI_CERTIFICATES_SERVICE"
        assert sdk_payload.certificate_config.dashboard_certificate_mode == "OCI_CERTIFICATES_SERVICE"
        assert sdk_payload.certificate_config.open_search_api_certificate_id == "ocid1.certificate.oc1..api1"
        assert isinstance(
            sdk_payload.maintenance_details,
            oci.opensearch.models.CreateMaintenanceDetails,
        )
        assert sdk_payload.freeform_tags == {"env": "qa"}
        assert sdk_payload.defined_tags == {"Operations": {"CostCenter": "42"}}

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_rejects_invalid_certificate_mode(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="OCI_CERTIFICATES_SERVICE"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "display_name": "cluster-one",
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_name": "admin1",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                            "certificate_config": {
                                "cluster_certificate_mode": "CUSTOMER_MANAGED",
                                "open_search_api_certificate_id": "ocid1.certificate.oc1..api1",
                            },
                        }
                    },
                )

    def test_build_create_payload_defaults_host_types_without_shape_defaults(self):
        payload = server._build_create_opensearch_cluster_payload(
            server.CreateOpensearchClusterDetailsInput(
                display_name="cluster-one",
                compartment_id="ocid1.compartment.oc1..compartment1",
                software_version="3.2.0",
                vcn_id="ocid1.vcn.oc1..vcn1",
                vcn_compartment_id="ocid1.compartment.oc1..network1",
                subnet_id="ocid1.subnet.oc1..subnet1",
                subnet_compartment_id="ocid1.compartment.oc1..network1",
                security_master_user_name="admin1",
                security_master_user_password_hash="pbkdf2_stretch_1000$SALT$HASH",
            )
        )

        assert payload["master_node_host_type"] == "FLEX"
        assert payload["data_node_host_type"] == "FLEX"
        assert "master_node_host_shape" not in payload
        assert "data_node_host_shape" not in payload
        assert "opendashboard_node_host_shape" not in payload

    def test_build_create_payload_defaults_flex_host_type_when_optional_shapes_are_present(
        self,
    ):
        payload = server._build_create_opensearch_cluster_payload(
            server.CreateOpensearchClusterDetailsInput(
                display_name="cluster-one",
                compartment_id="ocid1.compartment.oc1..compartment1",
                software_version="3.2.0",
                vcn_id="ocid1.vcn.oc1..vcn1",
                vcn_compartment_id="ocid1.compartment.oc1..network1",
                subnet_id="ocid1.subnet.oc1..subnet1",
                subnet_compartment_id="ocid1.compartment.oc1..network1",
                security_master_user_name="admin1",
                security_master_user_password_hash="pbkdf2_stretch_1000$SALT$HASH",
                search_node_host_shape="VM.Standard.E4.Flex",
                ml_node_host_shape="VM.Standard.E4.Flex",
            )
        )

        assert payload["search_node_host_type"] == "FLEX"
        assert payload["ml_node_host_type"] == "FLEX"

    def test_create_opensearch_cluster_rejects_invalid_host_type(self):
        with pytest.raises(ValueError, match="master_node_host_type"):
            server._build_create_opensearch_cluster_payload(
                server.CreateOpensearchClusterDetailsInput(
                    display_name="cluster-one",
                    compartment_id="ocid1.compartment.oc1..compartment1",
                    software_version="3.2.0",
                    vcn_id="ocid1.vcn.oc1..vcn1",
                    vcn_compartment_id="ocid1.compartment.oc1..network1",
                    subnet_id="ocid1.subnet.oc1..subnet1",
                    subnet_compartment_id="ocid1.compartment.oc1..network1",
                    security_master_user_name="admin1",
                    security_master_user_password_hash="pbkdf2_stretch_1000$SALT$HASH",
                    master_node_host_type="INVALID",
                )
            )

    def test_create_opensearch_cluster_rejects_invalid_ml_host_type(self):
        with pytest.raises(ValueError, match="ml_node_host_type"):
            server._build_create_opensearch_cluster_payload(
                server.CreateOpensearchClusterDetailsInput(
                    display_name="cluster-one",
                    compartment_id="ocid1.compartment.oc1..compartment1",
                    software_version="3.2.0",
                    vcn_id="ocid1.vcn.oc1..vcn1",
                    vcn_compartment_id="ocid1.compartment.oc1..network1",
                    subnet_id="ocid1.subnet.oc1..subnet1",
                    subnet_compartment_id="ocid1.compartment.oc1..network1",
                    security_master_user_name="admin1",
                    security_master_user_password_hash="pbkdf2_stretch_1000$SALT$HASH",
                    ml_node_host_type="BM",
                )
            )

    def test_create_opensearch_cluster_rejects_non_enforcing_security_mode(self):
        with pytest.raises(ValueError, match="must be `ENFORCING`"):
            server._build_create_opensearch_cluster_payload(
                server.CreateOpensearchClusterDetailsInput(
                    display_name="cluster-one",
                    compartment_id="ocid1.compartment.oc1..compartment1",
                    software_version="3.2.0",
                    vcn_id="ocid1.vcn.oc1..vcn1",
                    vcn_compartment_id="ocid1.compartment.oc1..network1",
                    subnet_id="ocid1.subnet.oc1..subnet1",
                    subnet_compartment_id="ocid1.compartment.oc1..network1",
                    security_master_user_name="admin1",
                    security_master_user_password_hash="pbkdf2_stretch_1000$SALT$HASH",
                    security_mode="DISABLED",
                )
            )

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_missing_body_has_actionable_error(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="create_opensearch_cluster_details"):
                await client.call_tool("create_opensearch_cluster", {"opc_retry_token": "retry-token"})

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_missing_required_fields_has_actionable_error(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="display_name"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                            "security_master_user_name": "admin1",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        }
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_requires_network_compartment_ids(self, mock_get_client):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="subnet_compartment_id"):
                await client.call_tool(
                    "create_opensearch_cluster",
                    {
                        "create_opensearch_cluster_details": {
                            "display_name": "cluster-one",
                            "compartment_id": "ocid1.compartment.oc1..compartment1",
                            "software_version": "3.2.0",
                            "vcn_id": "ocid1.vcn.oc1..vcn1",
                            "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                            "subnet_id": "ocid1.subnet.oc1..subnet1",
                            "security_master_user_name": "admin1",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        }
                    },
                )

        mock_get_client.assert_not_called()

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_create_opensearch_cluster_service_error_returns_clean_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.create_opensearch_cluster.side_effect = oci.exceptions.ServiceError(
            status=400,
            code="InvalidParameter",
            headers={},
            message="softwareVersion is invalid",
            request_id="request-create-error",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "create_opensearch_cluster",
                {
                    "create_opensearch_cluster_details": {
                        "display_name": "cluster-one",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "software_version": "3.2.0",
                        "vcn_id": "ocid1.vcn.oc1..vcn1",
                        "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                        "subnet_id": "ocid1.subnet.oc1..subnet1",
                        "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                        "security_master_user_name": "admin1",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                    }
                },
            )

        assert result.structured_content["status"] == 400
        assert result.structured_content["code"] == "InvalidParameter"
        assert result.structured_content["message"] == "softwareVersion is invalid"
        assert "opc_request_id" not in result.structured_content

    @pytest.mark.asyncio
    async def test_create_opensearch_cluster_schema_is_explicit(self):
        tools = await _tools_by_name()
        create_tool = tools["create_opensearch_cluster"]
        schema = create_tool.model_dump()["parameters"]
        detail_schema = _object_schema(schema, "create_opensearch_cluster_details")

        assert detail_schema["type"] == "object"
        assert "properties" in detail_schema
        assert "display_name" in detail_schema["properties"]
        assert "compartment_id" in detail_schema["properties"]
        assert "vcn_compartment_id" in detail_schema["properties"]
        assert "subnet_compartment_id" in detail_schema["properties"]
        assert "ml_node_host_shape" in detail_schema["properties"]

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_update_opensearch_cluster(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-update",
            "opc-request-id": "request-update",
        }
        mock_client.update_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "update_details": {"display_name": "cluster-one-updated"},
                },
            )

        assert result.structured_content["status"] == 202
        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-update"
        assert result.structured_content["status_check_policy"] == "single_get_work_request_then_ask_user"
        mock_client.update_opensearch_cluster.assert_called_once()
        update_payload = mock_client.update_opensearch_cluster.call_args.args[1]
        assert isinstance(update_payload, oci.opensearch.models.UpdateOpensearchClusterDetails)
        assert update_payload.display_name == "cluster-one-updated"

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_security_hash_without_security_mode(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="security_mode"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        },
                    },
                )

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_incomplete_security_master_user_pair(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="security_master_user_name"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "security_mode": "ENFORCING",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        },
                    },
                )

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_reserved_security_master_user(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="admin"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "security_mode": "ENFORCING",
                            "security_master_user_name": "admin",
                            "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                        },
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_update_opensearch_cluster_passes_complete_security_update(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-security"}
        mock_client.update_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "update_details": {
                        "security_mode": "ENFORCING",
                        "security_master_user_name": "master-user",
                        "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                    },
                },
            )

        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-security"
        update_payload = mock_client.update_opensearch_cluster.call_args.args[1]
        assert update_payload.display_name is None
        assert update_payload.security_mode == "ENFORCING"
        assert update_payload.security_master_user_name == "master-user"
        assert update_payload.security_master_user_password_hash == "pbkdf2_stretch_1000$SALT$HASH"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_update_opensearch_cluster_passes_advanced_optional_configs_without_display_name(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-update-advanced"}
        mock_client.update_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "update_details": {
                        "security_mode": "ENFORCING",
                        "security_saml_config": {
                            "is_enabled": True,
                            "idp_entity_id": "https://idp.example.com/entity",
                            "idp_metadata_content": "<EntityDescriptor />",
                            "opendashboard_url": "https://dash.example.com",
                            "admin_backend_role": "opensearch-admins",
                            "subject_key": "nameid",
                            "roles_key": "roles",
                        },
                        "backup_policy": {
                            "is_enabled": True,
                            "retention_in_days": 30,
                            "frequency_in_hours": 12,
                        },
                        "reverse_connection_endpoint_customer_ips": ["203.0.113.20"],
                        "outbound_cluster_config": {
                            "is_enabled": True,
                            "outbound_clusters": [
                                {
                                    "display_name": "remote-one",
                                    "seed_cluster_id": "ocid1.opensearchcluster.oc1..remote1",
                                    "mode": "SEARCH_ONLY",
                                    "ping_schedule": "*/5 * * * *",
                                    "is_skip_unavailable": True,
                                }
                            ],
                        },
                        "certificate_config": {
                            "cluster_certificate_mode": "OCI_CERTIFICATES_SERVICE",
                            "dashboard_certificate_mode": "OCI_CERTIFICATES_SERVICE",
                            "open_search_api_certificate_id": "ocid1.certificate.oc1..api1",
                            "open_search_dashboard_certificate_id": "ocid1.certificate.oc1..dashboard1",
                        },
                        "maintenance_details": {"notification_email_ids": ["admin@example.com"]},
                        "defined_tags": {"Operations": {"CostCenter": "42"}},
                        "freeform_tags": {"env": "qa"},
                        "security_attributes": {"oracle-zpr": {"sensitivity": "internal"}},
                    },
                },
            )

        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-update-advanced"
        update_payload = mock_client.update_opensearch_cluster.call_args.args[1]
        assert update_payload.display_name is None
        assert update_payload.software_version is None
        assert update_payload.security_mode == "ENFORCING"
        assert isinstance(
            update_payload.security_saml_config,
            oci.opensearch.models.SecuritySamlConfig,
        )
        assert update_payload.security_saml_config.admin_backend_role == "opensearch-admins"
        assert isinstance(update_payload.backup_policy, oci.opensearch.models.BackupPolicy)
        assert update_payload.backup_policy.retention_in_days == 30
        assert update_payload.reverse_connection_endpoint_customer_ips == ["203.0.113.20"]
        assert isinstance(
            update_payload.outbound_cluster_config,
            oci.opensearch.models.OutboundClusterConfig,
        )
        assert isinstance(
            update_payload.outbound_cluster_config.outbound_clusters[0],
            oci.opensearch.models.OutboundClusterSummary,
        )
        assert (
            update_payload.outbound_cluster_config.outbound_clusters[0].seed_cluster_id
            == "ocid1.opensearchcluster.oc1..remote1"
        )
        assert isinstance(update_payload.certificate_config, oci.opensearch.models.CertificateConfig)
        assert update_payload.certificate_config.cluster_certificate_mode == "OCI_CERTIFICATES_SERVICE"
        assert update_payload.certificate_config.dashboard_certificate_mode == "OCI_CERTIFICATES_SERVICE"
        assert (
            update_payload.certificate_config.open_search_dashboard_certificate_id
            == "ocid1.certificate.oc1..dashboard1"
        )
        assert isinstance(
            update_payload.maintenance_details,
            oci.opensearch.models.UpdateMaintenanceDetails,
        )
        assert update_payload.defined_tags == {"Operations": {"CostCenter": "42"}}
        assert update_payload.freeform_tags == {"env": "qa"}
        assert update_payload.security_attributes == {"oracle-zpr": {"sensitivity": "internal"}}

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_invalid_certificate_mode(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="CUSTOMER_MANAGED"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "certificate_config": {
                                "cluster_certificate_mode": "CUSTOMER_MANAGED",
                                "dashboard_certificate_mode": "CUSTOMER_MANAGED",
                                "open_search_api_certificate_id": "ocid1.certificate.oc1..api1",
                                "open_search_dashboard_certificate_id": "ocid1.certificate.oc1..dashboard1",
                            },
                        },
                    },
                )

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_byoc_mode_without_certificate_id(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="open_search_api_certificate_id"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "certificate_config": {"cluster_certificate_mode": "OCI_CERTIFICATES_SERVICE"},
                        },
                    },
                )

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_service_managed_mode_with_certificate_id(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="must be omitted"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "certificate_config": {
                                "cluster_certificate_mode": "OPENSEARCH_SERVICE",
                                "open_search_api_certificate_id": "ocid1.certificate.oc1..api1",
                            },
                        },
                    },
                )

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_saml_config_without_security_mode(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="security_mode"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "security_saml_config": {
                                "is_enabled": True,
                                "idp_entity_id": "entity-id",
                            },
                        },
                    },
                )

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_unknown_nested_saml_config_fields(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Extra inputs are not permitted"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "security_mode": "ENFORCING",
                            "security_saml_config": {
                                "is_enabled": True,
                                "unknown_field": "value",
                            },
                        },
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_update_opensearch_cluster_converts_nested_load_balancer_and_certificate_configs(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-update"}
        mock_client.update_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            await client.call_tool(
                "update_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "update_details": {
                        "load_balancer_config": {
                            "load_balancer_service_type": "LOAD_BALANCER",
                            "load_balancer_min_bandwidth_in_mbps": 10,
                            "load_balancer_max_bandwidth_in_mbps": 100,
                        },
                        "certificate_config": {
                            "cluster_certificate_mode": "OPENSEARCH_SERVICE",
                            "dashboard_certificate_mode": "OPENSEARCH_SERVICE",
                        },
                    },
                },
            )

        update_payload = mock_client.update_opensearch_cluster.call_args.args[1]
        assert isinstance(
            update_payload.load_balancer_config,
            oci.opensearch.models.LoadBalancerConfig,
        )
        assert update_payload.load_balancer_config.load_balancer_max_bandwidth_in_mbps == 100
        assert isinstance(update_payload.certificate_config, oci.opensearch.models.CertificateConfig)
        assert update_payload.certificate_config.dashboard_certificate_mode == "OPENSEARCH_SERVICE"

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_unknown_nested_load_balancer_config_fields(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Extra inputs are not permitted"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {
                            "load_balancer_config": {"is_enabled": True},
                        },
                    },
                )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_update_opensearch_cluster_accepts_software_version_without_display_name(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-update-version"}
        mock_client.update_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "update_details": {"software_version": "3.2.0"},
                },
            )

        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-update-version"
        update_payload = mock_client.update_opensearch_cluster.call_args.args[1]
        assert update_payload.display_name is None
        assert update_payload.software_version == "3.2.0"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_update_opensearch_cluster_accepts_tags_without_display_name(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-update-tags"}
        mock_client.update_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "update_details": {
                        "freeform_tags": {"env": "prod"},
                        "defined_tags": {"Operations": {"CostCenter": "42"}},
                    },
                },
            )

        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-update-tags"
        update_payload = mock_client.update_opensearch_cluster.call_args.args[1]
        assert update_payload.display_name is None
        assert update_payload.freeform_tags == {"env": "prod"}
        assert update_payload.defined_tags == {"Operations": {"CostCenter": "42"}}

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_update_opensearch_cluster_accepts_backup_policy_without_display_name(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {"opc-work-request-id": "ocid1.workrequest.oc1..wr-update-backup"}
        mock_client.update_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "update_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "update_details": {
                        "backup_policy": {
                            "is_enabled": True,
                            "retention_in_days": 30,
                            "frequency_in_hours": 12,
                        },
                    },
                },
            )

        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-update-backup"
        update_payload = mock_client.update_opensearch_cluster.call_args.args[1]
        assert update_payload.display_name is None
        assert isinstance(update_payload.backup_policy, oci.opensearch.models.BackupPolicy)
        assert update_payload.backup_policy.retention_in_days == 30

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_rejects_empty_update_details(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="at least one update_details field"):
                await client.call_tool(
                    "update_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "update_details": {},
                    },
                )

    @pytest.mark.asyncio
    async def test_update_opensearch_cluster_schema_is_explicit(self):
        tools = await _tools_by_name()
        update_tool = tools["update_opensearch_cluster"]
        schema = update_tool.model_dump()["parameters"]
        detail_schema = _object_schema(schema, "update_details")

        assert detail_schema["type"] == "object"
        assert "display_name" in detail_schema["properties"]
        assert "software_version" in detail_schema["properties"]
        assert "security_mode" in detail_schema["properties"]
        assert "security_master_user_name" in detail_schema["properties"]
        assert "security_master_user_password_hash" in detail_schema["properties"]
        assert "security_saml_config" in detail_schema["properties"]
        assert "outbound_cluster_config" in detail_schema["properties"]
        assert "reverse_connection_endpoint_customer_ips" in detail_schema["properties"]
        assert "certificate_config" in detail_schema["properties"]
        assert "display_name" not in detail_schema.get("required", [])

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_delete_opensearch_cluster(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-delete",
            "opc-request-id": "request-delete",
        }
        mock_client.delete_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "delete_opensearch_cluster",
                {"opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1"},
            )

        assert result.structured_content["status"] == 202
        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-delete"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_resize_opensearch_cluster_vertical(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-resize-v",
            "opc-request-id": "request-resize-v",
        }
        mock_client.resize_opensearch_cluster_vertical.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "resize_opensearch_cluster_vertical",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "resize_details": {"master_node_host_ocpu_count": 8},
                },
            )

        assert result.structured_content["status"] == 202
        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-resize-v"
        assert result.structured_content["opc_retry_token"].startswith("mcp-rzv-")
        assert result.structured_content["opc_retry_token_source"] == "generated"
        mock_client.resize_opensearch_cluster_vertical.assert_called_once()
        assert (
            mock_client.resize_opensearch_cluster_vertical.call_args.kwargs["opc_retry_token"]
            == result.structured_content["opc_retry_token"]
        )
        resize_payload = mock_client.resize_opensearch_cluster_vertical.call_args.args[1]
        assert isinstance(resize_payload, oci.opensearch.models.ResizeOpensearchClusterVerticalDetails)
        assert resize_payload.master_node_host_ocpu_count == 8

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_resize_opensearch_cluster_vertical_passes_shape_fields(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-resize-v",
            "opc-request-id": "request-resize-v",
        }
        mock_client.resize_opensearch_cluster_vertical.return_value = mock_response

        async with Client(mcp) as client:
            await client.call_tool(
                "resize_opensearch_cluster_vertical",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "resize_details": {
                        "master_node_host_shape": "VM.Standard.E4.Flex",
                        "data_node_host_shape": "VM.Standard.E4.Flex",
                        "opendashboard_node_host_shape": "VM.Standard.E4.Flex",
                        "search_node_host_shape": "VM.Standard.E4.Flex",
                        "ml_node_host_shape": "VM.Standard.E4.Flex",
                    },
                },
            )

        resize_payload = mock_client.resize_opensearch_cluster_vertical.call_args.args[1]
        assert resize_payload.master_node_host_shape == "VM.Standard.E4.Flex"
        assert resize_payload.data_node_host_shape == "VM.Standard.E4.Flex"
        assert resize_payload.opendashboard_node_host_shape == "VM.Standard.E4.Flex"
        assert resize_payload.search_node_host_shape == "VM.Standard.E4.Flex"
        assert resize_payload.ml_node_host_shape == "VM.Standard.E4.Flex"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_resize_opensearch_cluster_vertical_service_error_returns_clean_payload(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.resize_opensearch_cluster_vertical.side_effect = oci.exceptions.ServiceError(
            status=400,
            code="InvalidParameter",
            headers={},
            message="shape is invalid",
            request_id="request-resize-v-error",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "resize_opensearch_cluster_vertical",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "resize_details": {"master_node_host_shape": "Invalid.Shape"},
                },
            )

        assert result.structured_content["status"] == 400
        assert result.structured_content["code"] == "InvalidParameter"
        assert result.structured_content["message"] == "shape is invalid"

    @pytest.mark.asyncio
    async def test_resize_opensearch_cluster_vertical_requires_non_empty_body(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Provide at least one resize_details field"):
                await client.call_tool(
                    "resize_opensearch_cluster_vertical",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "resize_details": {},
                    },
                )

    @pytest.mark.asyncio
    async def test_resize_opensearch_cluster_vertical_schema_is_explicit(self):
        tools = await _tools_by_name()
        resize_tool = tools["resize_opensearch_cluster_vertical"]
        schema = resize_tool.model_dump()["parameters"]
        detail_schema = _object_schema(schema, "resize_details")

        assert detail_schema["type"] == "object"
        assert "master_node_host_ocpu_count" in detail_schema["properties"]
        assert "data_node_storage_gb" in detail_schema["properties"]

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_resize_opensearch_cluster_horizontal(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-resize-h",
            "opc-request-id": "request-resize-h",
        }
        mock_client.resize_opensearch_cluster_horizontal.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "resize_opensearch_cluster_horizontal",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "resize_details": {"data_node_count": 6},
                },
            )

        assert result.structured_content["status"] == 202
        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-resize-h"
        assert result.structured_content["opc_retry_token"].startswith("mcp-rzh-")
        assert result.structured_content["opc_retry_token_source"] == "generated"
        mock_client.resize_opensearch_cluster_horizontal.assert_called_once()
        assert (
            mock_client.resize_opensearch_cluster_horizontal.call_args.kwargs["opc_retry_token"]
            == result.structured_content["opc_retry_token"]
        )
        resize_payload = mock_client.resize_opensearch_cluster_horizontal.call_args.args[1]
        assert isinstance(
            resize_payload,
            oci.opensearch.models.ResizeOpensearchClusterHorizontalDetails,
        )
        assert resize_payload.data_node_count == 6

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_resize_opensearch_cluster_horizontal_service_error_returns_clean_payload(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.resize_opensearch_cluster_horizontal.side_effect = oci.exceptions.ServiceError(
            status=409,
            code="Conflict",
            headers={},
            message="cluster is updating",
            request_id="request-resize-h-error",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "resize_opensearch_cluster_horizontal",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "resize_details": {"data_node_count": 6},
                },
            )

        assert result.structured_content["status"] == 409
        assert result.structured_content["code"] == "Conflict"
        assert result.structured_content["message"] == "cluster is updating"

    @pytest.mark.asyncio
    async def test_resize_opensearch_cluster_horizontal_requires_non_empty_body(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="Provide at least one resize_details field"):
                await client.call_tool(
                    "resize_opensearch_cluster_horizontal",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "resize_details": {},
                    },
                )

    @pytest.mark.asyncio
    async def test_resize_opensearch_cluster_horizontal_schema_is_explicit(self):
        tools = await _tools_by_name()
        resize_tool = tools["resize_opensearch_cluster_horizontal"]
        schema = resize_tool.model_dump()["parameters"]
        detail_schema = _object_schema(schema, "resize_details")

        assert detail_schema["type"] == "object"
        assert "data_node_count" in detail_schema["properties"]
        assert "search_node_count" in detail_schema["properties"]
        assert "master_node_host_shape" not in detail_schema["properties"]

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_backup_opensearch_cluster(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.status = 202
        mock_response.data = None
        mock_response.headers = {
            "opc-work-request-id": "ocid1.workrequest.oc1..wr-backup",
            "opc-request-id": "request-backup",
        }
        mock_client.backup_opensearch_cluster.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "backup_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "backup_details": {
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "display_name": "backup-1",
                    },
                },
            )

        assert result.structured_content["status"] == 202
        assert result.structured_content["opc_work_request_id"] == "ocid1.workrequest.oc1..wr-backup"
        assert result.structured_content["opc_retry_token"].startswith("mcp-backup-")
        assert result.structured_content["opc_retry_token_source"] == "generated"
        mock_client.backup_opensearch_cluster.assert_called_once()
        assert (
            mock_client.backup_opensearch_cluster.call_args.kwargs["opc_retry_token"]
            == result.structured_content["opc_retry_token"]
        )
        backup_payload = mock_client.backup_opensearch_cluster.call_args.args[1]
        assert isinstance(backup_payload, oci.opensearch.models.BackupOpensearchClusterDetails)
        assert backup_payload.compartment_id == "ocid1.compartment.oc1..compartment1"
        assert backup_payload.display_name == "backup-1"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_backup_opensearch_cluster_service_error_returns_clean_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.backup_opensearch_cluster.side_effect = oci.exceptions.ServiceError(
            status=409,
            code="Conflict",
            headers={},
            message="cluster is updating",
            request_id="request-backup-error",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "backup_opensearch_cluster",
                {
                    "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "backup_details": {
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "display_name": "backup-1",
                    },
                },
            )

        assert result.structured_content["status"] == 409
        assert result.structured_content["code"] == "Conflict"
        assert result.structured_content["message"] == "cluster is updating"

    @pytest.mark.asyncio
    async def test_backup_opensearch_cluster_missing_required_fields_has_actionable_error(
        self,
    ):
        async with Client(mcp) as client:
            with pytest.raises(Exception, match="compartment_id"):
                await client.call_tool(
                    "backup_opensearch_cluster",
                    {
                        "opensearch_cluster_id": "ocid1.opensearchcluster.oc1..cluster1",
                        "backup_details": {"display_name": "backup-1"},
                    },
                )

    @pytest.mark.asyncio
    async def test_backup_opensearch_cluster_schema_is_explicit(self):
        tools = await _tools_by_name()
        backup_tool = tools["backup_opensearch_cluster"]
        schema = backup_tool.model_dump()["parameters"]
        detail_schema = _object_schema(schema, "backup_details")

        assert detail_schema["type"] == "object"
        assert "compartment_id" in detail_schema["properties"]
        assert "display_name" in detail_schema["properties"]

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_work_requests(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = type(
            "WorkRequestCollection",
            (),
            {
                "items": [
                    {
                        "id": "ocid1.workrequest.oc1..wr1",
                        "operation_type": "UPDATE_OPENSEARCH_CLUSTER",
                        "compartment_id": "ocid1.compartment.oc1..compartment1",
                        "status": "SUCCEEDED",
                        "resources": [],
                    }
                ]
            },
        )()
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_work_requests.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_work_requests",
                {"compartment_id": "ocid1.compartment.oc1..compartment1"},
            )

        payload = result.structured_content["items"]
        assert result.structured_content["count"] == 1
        assert len(payload) == 1
        assert payload[0]["id"] == "ocid1.workrequest.oc1..wr1"
        mock_client.list_work_requests.assert_called_once_with("ocid1.compartment.oc1..compartment1")

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_work_requests_normalizes_dict_items_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = {"items": [{"id": "ocid1.workrequest.oc1..wr1"}]}
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_work_requests.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_work_requests",
                {"compartment_id": "ocid1.compartment.oc1..compartment1"},
            )

        assert result.structured_content == {
            "items": [{"id": "ocid1.workrequest.oc1..wr1"}],
            "count": 1,
        }

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_work_requests_with_explicit_optional_parameters(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = type("WorkRequestCollection", (), {"items": []})()
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_work_requests.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_work_requests",
                {
                    "compartment_id": "ocid1.compartment.oc1..compartment1",
                    "work_request_id": "ocid1.workrequest.oc1..wr1",
                    "source_resource_id": "ocid1.opensearchcluster.oc1..cluster1",
                    "limit": 1000,
                    "opc_request_id": "req-list-work-requests",
                },
            )

        assert result.structured_content == {"items": [], "count": 0}
        assert result.content
        mock_client.list_work_requests.assert_called_once_with(
            "ocid1.compartment.oc1..compartment1",
            work_request_id="ocid1.workrequest.oc1..wr1",
            source_resource_id="ocid1.opensearchcluster.oc1..cluster1",
            opc_request_id="req-list-work-requests",
            limit=1000,
        )

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_list_work_requests_service_error_returns_clean_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_work_requests.side_effect = oci.exceptions.ServiceError(
            status=401,
            code="NotAuthenticated",
            headers={"opc-request-id": "request-list-work-requests-error"},
            message="The required information to complete authentication was not provided.",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "list_work_requests",
                {
                    "compartment_id": "ocid1.compartment.oc1..compartment1",
                    "limit": 1000,
                },
            )

        assert result.structured_content["status"] == 401
        assert result.structured_content["code"] == "NotAuthenticated"
        assert "authentication" in result.structured_content["message"]
        assert result.structured_content["opc_request_id"] == "request-list-work-requests-error"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_get_work_request(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = oci.opensearch.models.WorkRequest(
            id="ocid1.workrequest.oc1..wr1",
            operation_type="UPDATE_OPENSEARCH_CLUSTER",
            compartment_id="ocid1.compartment.oc1..compartment1",
            status="SUCCEEDED",
            resources=[],
        )
        mock_client.get_work_request.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_work_request",
                {"work_request_id": "ocid1.workrequest.oc1..wr1"},
            )

        assert result.structured_content["id"] == "ocid1.workrequest.oc1..wr1"

    @pytest.mark.asyncio
    @patch("oracle.oci_opensearch_mcp_server.server.get_opensearch_cluster_client")
    async def test_get_work_request_service_error_returns_clean_payload(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_work_request.side_effect = oci.exceptions.ServiceError(
            status=404,
            code="NotAuthorizedOrNotFound",
            headers={"opc-request-id": "request-get-work-request-error"},
            message="Work request not found.",
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_work_request",
                {"work_request_id": "ocid1.workrequest.oc1..missing"},
            )

        assert result.structured_content["status"] == 404
        assert result.structured_content["code"] == "NotAuthorizedOrNotFound"
        assert result.structured_content["message"] == "Work request not found."
        assert result.structured_content["opc_request_id"] == "request-get-work-request-error"


class TestServer:
    def test_server_instructions_discourage_continuous_polling(self):
        assert "get_work_request at most once" in server.mcp.instructions
        assert "instead of polling continuously" in server.mcp.instructions

    @pytest.mark.parametrize(
        "mock_env",
        [
            {"ORACLE_MCP_HOST": "127.0.0.1", "ORACLE_MCP_PORT": "8888"},
            {"ORACLE_MCP_HOST": "127.0.0.1"},
            {"ORACLE_MCP_PORT": "8888"},
        ],
    )
    @patch("oracle.oci_opensearch_mcp_server.server.mcp.run")
    @patch("oracle.oci_opensearch_mcp_server.server.os.getenv")
    def test_main_rejects_http_transport_env(self, mock_getenv, mock_mcp_run, mock_env):
        mock_getenv.side_effect = lambda key: mock_env.get(key)

        with pytest.raises(RuntimeError, match="supports stdio transport only"):
            server.main()

        mock_mcp_run.assert_not_called()

    @patch("oracle.oci_opensearch_mcp_server.server.mcp.run")
    @patch("oracle.oci_opensearch_mcp_server.server.os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        server.main()

        mock_mcp_run.assert_called_once_with()


class TestRuntimeGuides:
    def test_runtime_guides_are_available(self):
        assert "SDK-backed MVP" in get_script_content(OPENSEARCH_API_GUIDE)
        assert "Work Request Guide" in get_script_content(WORK_REQUEST_GUIDE)
        assert "Tool Surface Summary" in get_script_content(TOOL_SURFACE_SUMMARY)

    def test_runtime_guides_include_shape_workflow(self):
        api_guide = get_script_content(OPENSEARCH_API_GUIDE)
        work_request_guide = get_script_content(WORK_REQUEST_GUIDE)
        tool_summary = get_script_content(TOOL_SURFACE_SUMMARY)

        assert "Shape selection workflow" in api_guide
        assert "list_opensearch_cluster_shapes" in api_guide
        assert "capacity" in work_request_guide.lower()
        assert "do not poll continuously" in api_guide
        assert "get_work_request` once" in work_request_guide
        assert "list_opensearch_cluster_shapes" in tool_summary
