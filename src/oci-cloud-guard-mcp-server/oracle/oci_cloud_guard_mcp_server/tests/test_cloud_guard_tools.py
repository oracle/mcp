"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

# noinspection PyPackageRequirements
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, create_autospec, patch

import oci
import oracle.oci_cloud_guard_mcp_server.server as server
import pytest
from fastmcp import Client


class TestResourceSearchTools:
    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_list_all_problems(self, mock_get_client):
        resource_id = "ocid.resource1"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_problems_response = create_autospec(oci.response.Response)
        mock_problems_response.data = oci.cloud_guard.models.ProblemCollection(
            items=[
                oci.cloud_guard.models.ProblemSummary(
                    id=resource_id,
                    resource_type="instance",
                    resource_id="resource1",
                    lifecycle_state="ACTIVE",
                    lifecycle_detail="OPEN",
                )
            ]
        )
        mock_client.list_problems.return_value = mock_problems_response

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "list_problems", {"compartment_id": "test_compartment"}
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["id"] == resource_id

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    @patch("oracle.oci_cloud_guard_mcp_server.server.datetime")
    async def test_list_problems_applies_optional_filters(
        self, mock_datetime, mock_get_client
    ):
        fake_now = datetime(2025, 1, 31, 12, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fake_now

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = create_autospec(oci.response.Response)
        mock_response.data = oci.cloud_guard.models.ProblemCollection(items=[])
        mock_client.list_problems.return_value = mock_response

        args = {
            "compartment_id": "ocid.compartment",
            "risk_level": "HIGH",
            "lifecycle_state": "INACTIVE",
            "detector_rule_ids": ["det-1", "det-2"],
            "time_range_days": 5,
            "limit": 5,
        }

        async with Client(server.mcp) as client:
            result = (await client.call_tool("list_problems", args)).structured_content[
                "result"
            ]

        assert result == []
        kwargs = mock_client.list_problems.call_args.kwargs
        expected_time = (fake_now - timedelta(days=5)).isoformat()
        assert kwargs["time_last_detected_greater_than_or_equal_to"] == expected_time
        assert kwargs["risk_level"] == "HIGH"
        assert kwargs["lifecycle_state"] == "INACTIVE"
        assert kwargs["detector_rule_id_list"] == ["det-1", "det-2"]
        assert kwargs["limit"] == 5

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    @patch("oracle.oci_cloud_guard_mcp_server.server.datetime")
    async def test_list_problems_omits_filters_when_none(
        self, mock_datetime, mock_get_client
    ):
        fake_now = datetime(2025, 2, 1, 12, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = fake_now

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = create_autospec(oci.response.Response)
        mock_response.data = oci.cloud_guard.models.ProblemCollection(items=[])
        mock_client.list_problems.return_value = mock_response

        async with Client(server.mcp) as client:
            await client.call_tool(
                "list_problems",
                {
                    "compartment_id": "ocid.compartment",
                    "risk_level": None,
                    "lifecycle_state": None,
                    "detector_rule_ids": None,
                    "time_range_days": None,
                },
            )

        kwargs = mock_client.list_problems.call_args.kwargs
        expected_time = (fake_now - timedelta(days=30)).isoformat()
        assert kwargs["time_last_detected_greater_than_or_equal_to"] == expected_time
        assert "risk_level" not in kwargs
        assert "lifecycle_state" not in kwargs
        assert "detector_rule_id_list" not in kwargs

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_get_problem_details(self, mock_get_client):
        problem_id = "ocid.resource1"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_problem_response = create_autospec(oci.response.Response)
        mock_get_problem_response.data = oci.cloud_guard.models.Problem(
            id=problem_id,
            resource_type="instance",
            resource_id="resource1",
            lifecycle_state="ACTIVE",
            lifecycle_detail="OPEN",
            compartment_id="test_compartment",
            region="test_region",
            impacted_resource_type="123",
            impacted_resource_name="123",
            risk_level="HIGH",
        )
        mock_client.get_problem.return_value = mock_get_problem_response

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "get_problem_details",
                    {
                        "problem_id": problem_id,
                    },
                )
            ).structured_content

            assert result["id"] == problem_id

    @pytest.mark.asyncio
    @patch(
        "oracle.oci_cloud_guard_mcp_server.server.oci.cloud_guard.models.UpdateProblemStatusDetails"
    )
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_update_problem_status_uses_sdk_model(
        self, mock_get_client, mock_update_model
    ):
        problem_id = "ocid.resource1"
        status = "RESOLVED"
        comment = "handled"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_update_model_instance = MagicMock()
        mock_update_model.return_value = mock_update_model_instance

        mock_update_problem_status_response = create_autospec(oci.response.Response)
        mock_update_problem_status_response.data = oci.cloud_guard.models.Problem(
            id=problem_id,
            lifecycle_detail=status,
            comment=comment,
        )
        mock_client.update_problem_status.return_value = (
            mock_update_problem_status_response
        )

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "update_problem_status",
                    {
                        "problem_id": problem_id,
                        "status": status,
                        "comment": comment,
                    },
                )
            ).structured_content

        mock_update_model.assert_called_once_with(status=status, comment=comment)
        mock_client.update_problem_status.assert_called_once_with(
            problem_id=problem_id,
            update_problem_status_details=mock_update_model_instance,
        )
        assert result["lifecycle_detail"] == status
        assert result["comment"] == comment

    @pytest.mark.asyncio
    @patch("oracle.mcp_common.helpers._create_oci_client")
    async def test_update_problem_status(self, mock_get_client):
        problem_id = "ocid.resource1"
        status = "OPEN"
        comment = "this is updated with ai"
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_update_problem_status_response = create_autospec(oci.response.Response)
        mock_update_problem_status_response.data = oci.cloud_guard.models.Problem(
            id=problem_id,
            resource_type="instance",
            resource_id="resource1",
            lifecycle_state="ACTIVE",
            lifecycle_detail=status,
            comment=comment,
        )
        mock_client.update_problem_status.return_value = (
            mock_update_problem_status_response
        )

        async with Client(server.mcp) as client:
            result = (
                await client.call_tool(
                    "update_problem_status",
                    {"problem_id": problem_id, "status": status, "comment": comment},
                )
            ).structured_content

            print(result)
            assert result["id"] == problem_id
            assert result["lifecycle_detail"] == status
            assert result["comment"] == comment

    @patch.object(server, "mcp")
    def test_main_uses_http_transport_when_env_configured(self, mock_mcp):
        with patch.dict(
            os.environ,
            {"ORACLE_MCP_HOST": "127.0.0.1", "ORACLE_MCP_PORT": "8080"},
            clear=False,
        ):
            server.main()

        mock_mcp.run.assert_called_once_with(
            transport="http", host="127.0.0.1", port=8080
        )

    @patch.object(server, "mcp")
    def test_main_uses_default_transport_without_env(self, mock_mcp):
        with patch.dict(os.environ, {}, clear=True):
            server.main()

        mock_mcp.run.assert_called_once_with()
