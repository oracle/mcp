"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import sys
import types
from datetime import datetime
from unittest.mock import MagicMock, create_autospec, patch

import pytest
from fastmcp import Client

# Provide a lightweight stub for 'oci' if not installed, so tests can import the server module
try:
    import oci  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    oci = types.SimpleNamespace()
    sys.modules["oci"] = oci
    oci.response = types.SimpleNamespace(Response=type("Response", (), {}))
    oci.util = types.SimpleNamespace(to_dict=lambda x: x)
    oci.config = types.SimpleNamespace(
        DEFAULT_PROFILE="DEFAULT",
        from_file=lambda profile_name=None: {"key_file": "", "security_token_file": ""},
    )
    oci.signer = types.SimpleNamespace(load_private_key_from_file=lambda path: "KEY")
    oci.auth = types.SimpleNamespace(
        signers=types.SimpleNamespace(SecurityTokenSigner=lambda token, key: object())
    )
    oci.fusion_apps = types.SimpleNamespace(
        FusionApplicationsClient=lambda config, signer=None: object()
    )

from oracle.oci_faaas_mcp_server.server import (
    get_faaas_client,
    mcp,
)


class TestFaaasTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environment_families(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            {
                "id": "family1",
                "display_name": "Family 1",
                "lifecycle_state": "ACTIVE",
            }
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_fusion_environment_families.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environment_families",
                {"compartment_id": "test_compartment"},
            )
            result = call_tool_result.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "family1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environments(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            {
                "id": "env1",
                "display_name": "Env 1",
                "lifecycle_state": "ACTIVE",
                "family_id": "family1",
            }
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_fusion_environments.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_fusion_environments",
                {
                    "compartment_id": "test_compartment",
                    "fusion_environment_family_id": "family1",
                },
            )
            result = call_tool_result.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "env1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_get_fusion_environment(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = {
            "id": "env1",
            "display_name": "Env 1",
            "lifecycle_state": "ACTIVE",
        }
        mock_client.get_fusion_environment.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_fusion_environment",
                {"fusion_environment_id": "env1"},
            )
            result = call_tool_result.structured_content

            assert isinstance(result, dict)
            assert result["id"] == "env1"
            assert result["display_name"] == "Env 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_get_fusion_environment_status(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = {
            "fusion_environment_id": "env1",
            "status": "ACTIVE",
            "time_updated": "2025-01-01T00:00:00Z",
        }
        mock_client.get_fusion_environment_status.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_fusion_environment_status",
                {"fusion_environment_id": "env1"},
            )
            result = call_tool_result.structured_content

            assert isinstance(result, dict)
            assert result["fusion_environment_id"] == "env1"
            assert result["status"] == "ACTIVE"

    def test_get_faaas_client_initializes_client(self, tmp_path):
        # Prepare temp token file
        token_file = tmp_path / "token"
        token_file.write_text("TOKEN")

        with patch(
            "oracle.oci_faaas_mcp_server.server.oci.config.from_file",
            return_value={
                "key_file": "dummy_key",
                "security_token_file": str(token_file),
            },
        ), patch(
            "oracle.oci_faaas_mcp_server.server.oci.signer.load_private_key_from_file",
            return_value="KEY",
        ), patch(
            "oracle.oci_faaas_mcp_server.server.oci.auth.signers.SecurityTokenSigner",
            return_value="SIGNER",
        ) as mock_signer, patch(
            "oracle.oci_faaas_mcp_server.server.oci.fusion_apps.FusionApplicationsClient",
            autospec=True,
        ) as mock_client_cls:
            client = get_faaas_client()
            # Returned client object comes from FusionApplicationsClient
            assert client is mock_client_cls.return_value

            # FusionApplicationsClient called with config and signer
            args, kwargs = mock_client_cls.call_args
            cfg = args[0] if args else kwargs.get("config")
            assert isinstance(cfg, dict)
            assert "additional_user_agent" in cfg
            # Signer constructed using token file contents and key
            mock_signer.assert_called_once()

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_get_fusion_environment_family_subscription_detail(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = {
            "subscriptions": [
                {
                    "id": "ocid1.subscription.oc1..exampleuniqueID",
                    "classic_subscription_id": "classic-1",
                    "service_name": "SAAS",
                    "lifecycle_state": "ACTIVE",
                    "skus": [],
                }
            ]
        }
        mock_client.get_fusion_environment_family_subscription_detail.return_value = (
            mock_get_response
        )

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_fusion_environment_family_subscription_detail",
                {
                    "fusion_environment_family_id": "ocid1.fusionenvironmentfamily.oc1..example"
                },
            )
            result = call_tool_result.structured_content

            assert "subscriptions" in result
            assert isinstance(result["subscriptions"], list)
            assert result["subscriptions"][0]["service_name"] == "SAAS"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_scheduled_activities_minimal(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = [
            {
                "id": "sa1",
                "display_name": "Activity 1",
                "run_cycle": "MONTHLY",
                "fusion_environment_id": "env1",
                "lifecycle_state": "ACCEPTED",
                "time_scheduled_start": "2025-01-01T00:00:00Z",
                "time_expected_finish": "2025-01-01T02:00:00Z",
                "scheduled_activity_phase": "MAINTENANCE",
                "scheduled_activity_association_id": "assoc1",
            }
        ]
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_scheduled_activities.return_value = mock_list_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_scheduled_activities",
                {"fusion_environment_id": "env1"},
            )
            result = call_tool_result.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "sa1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_scheduled_activities_with_filters(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_list_response = create_autospec(oci.response.Response)
        mock_list_response.data = []
        mock_list_response.has_next_page = False
        mock_list_response.next_page = None
        mock_client.list_scheduled_activities.return_value = mock_list_response

        dt_start = datetime(2025, 1, 1, 0, 0, 0)
        dt_end = datetime(2025, 1, 2, 0, 0, 0)

        async with Client(mcp) as client:
            await client.call_tool(
                "list_scheduled_activities",
                {
                    "fusion_environment_id": "env1",
                    "display_name": "ZDT",
                    "time_scheduled_start_greater_than_or_equal_to": dt_start,
                    "time_expected_finish_less_than_or_equal_to": dt_end,
                    "run_cycle": "MONTHLY",
                    "lifecycle_state": "SUCCEEDED",
                    "scheduled_activity_association_id": "assoc1",
                    "scheduled_activity_phase": "POST_MAINTENANCE",
                    "limit": 10,
                    "page": "token123",
                    "sort_order": "ASC",
                    "sort_by": "DISPLAY_NAME",
                    "opc_request_id": "req-1",
                    "allow_control_chars": True,
                    "retry_strategy": "none",
                },
            )

        # Verify mapped kwargs passed to OCI client
        _, kwargs = mock_client.list_scheduled_activities.call_args
        assert kwargs["fusion_environment_id"] == "env1"
        assert kwargs["display_name"] == "ZDT"
        assert kwargs["time_scheduled_start_greater_than_or_equal_to"] == dt_start
        assert kwargs["time_expected_finish_less_than_or_equal_to"] == dt_end
        assert kwargs["run_cycle"] == "MONTHLY"
        assert kwargs["lifecycle_state"] == "SUCCEEDED"
        assert kwargs["scheduled_activity_association_id"] == "assoc1"
        assert kwargs["scheduled_activity_phase"] == "POST_MAINTENANCE"
        assert kwargs["limit"] == 10
        assert kwargs["page"] == "token123"
        assert kwargs["sort_order"] == "ASC"
        assert kwargs["sort_by"] == "DISPLAY_NAME"
        assert kwargs["opc_request_id"] == "req-1"
        assert kwargs["allow_control_chars"] is True

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_get_scheduled_activity_minimal(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = {
            "id": "sa1",
            "display_name": "Activity 1",
            "run_cycle": "MONTHLY",
            "fusion_environment_id": "env1",
            "lifecycle_state": "ACCEPTED",
            "time_scheduled_start": "2025-01-01T00:00:00Z",
            "time_expected_finish": "2025-01-01T02:00:00Z",
            "scheduled_activity_phase": "MAINTENANCE",
            "scheduled_activity_association_id": "assoc1",
        }
        mock_client.get_scheduled_activity.return_value = mock_get_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_scheduled_activity",
                {
                    "fusion_environment_id": "env1",
                    "scheduled_activity_id": "sa1",
                },
            )
            result = call_tool_result.structured_content
            assert result["id"] == "sa1"
            assert result["display_name"] == "Activity 1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_get_scheduled_activity_with_options(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_get_response = create_autospec(oci.response.Response)
        mock_get_response.data = {"id": "sa2"}
        mock_client.get_scheduled_activity.return_value = mock_get_response

        async with Client(mcp) as client:
            await client.call_tool(
                "get_scheduled_activity",
                {
                    "fusion_environment_id": "env1",
                    "scheduled_activity_id": "sa2",
                    "opc_request_id": "req-2",
                    "allow_control_chars": True,
                    "retry_strategy": "none",
                },
            )

        _, kwargs = mock_client.get_scheduled_activity.call_args
        assert kwargs["fusion_environment_id"] == "env1"
        assert kwargs["scheduled_activity_id"] == "sa2"
        assert kwargs["opc_request_id"] == "req-2"
        assert kwargs["allow_control_chars"] is True

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_admin_users_minimal(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = [
            {
                "username": "admin1",
                "email_address": "admin1@example.com",
                "first_name": "A",
                "last_name": "One",
            }
        ]
        resp.has_next_page = False
        resp.next_page = None
        mock_client.list_admin_users.return_value = resp

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_admin_users", {"fusion_environment_id": "env1"}
            )
            result = call_res.structured_content["result"]

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["username"] == "admin1"
            assert result[0]["email_address"] == "admin1@example.com"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_admin_users_pagination(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [{"username": "admin1"}]
        resp1.has_next_page = True
        resp1.next_page = "page2"

        resp2 = create_autospec(oci.response.Response)
        resp2.data = [{"username": "admin2"}]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_client.list_admin_users.side_effect = [resp1, resp2]

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_admin_users", {"fusion_environment_id": "env1"}
            )
            result = call_res.structured_content["result"]

            assert [u["username"] for u in result] == ["admin1", "admin2"]

        # Verify pagination behavior: second call uses page token
        assert mock_client.list_admin_users.call_count == 2
        _, first_kwargs = mock_client.list_admin_users.call_args_list[0]
        _, second_kwargs = mock_client.list_admin_users.call_args_list[1]
        assert "page" not in first_kwargs or first_kwargs["page"] is None
        assert second_kwargs["page"] == "page2"
        assert second_kwargs["fusion_environment_id"] == "env1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_refresh_activities_minimal(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = [
            {
                "id": "ra1",
                "display_name": "Refresh 1",
                "lifecycle_state": "SUCCEEDED",
                "time_scheduled_start": "2025-01-01T01:00:00Z",
            }
        ]
        resp.has_next_page = False
        resp.next_page = None
        mock_client.list_refresh_activities.return_value = resp

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_refresh_activities", {"fusion_environment_id": "env1"}
            )
            result = call_res.structured_content["result"]
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "ra1"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_refresh_activities_with_filters_and_limit(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [{"id": "ra1", "display_name": "Refresh 1"}]
        resp1.has_next_page = True
        resp1.next_page = "p2"
        mock_client.list_refresh_activities.side_effect = [resp1]

        dt_start = datetime(2025, 1, 1, 0, 0, 0)
        dt_end = datetime(2025, 1, 2, 0, 0, 0)

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_refresh_activities",
                {
                    "fusion_environment_id": "env1",
                    "display_name": "Ref1",
                    "time_scheduled_start_greater_than_or_equal_to": dt_start,
                    "time_expected_finish_less_than_or_equal_to": dt_end,
                    "lifecycle_state": "SUCCEEDED",
                    "limit": 1,
                    "page": "p1",
                    "sort_order": "DESC",
                    "sort_by": "TIME_CREATED",
                    "opc_request_id": "reqX",
                },
            )
            result = call_res.structured_content["result"]
            assert len(result) == 1
            assert result[0]["id"] == "ra1"

        # With limit=1 and has_next_page True, only one SDK call should be made
        assert mock_client.list_refresh_activities.call_count == 1
        _, kwargs = mock_client.list_refresh_activities.call_args
        assert kwargs["fusion_environment_id"] == "env1"
        assert kwargs["display_name"] == "Ref1"
        assert kwargs["time_scheduled_start_greater_than_or_equal_to"] == dt_start
        assert kwargs["time_expected_finish_less_than_or_equal_to"] == dt_end
        assert kwargs["lifecycle_state"] == "SUCCEEDED"
        assert kwargs["limit"] == 1
        assert kwargs["page"] == "p1"
        assert kwargs["sort_order"] == "DESC"
        assert kwargs["sort_by"] == "TIME_CREATED"
        assert kwargs["opc_request_id"] == "reqX"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environment_families_pagination_header_fallback(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [{"id": "family1", "display_name": "Family 1"}]
        resp1.next_page = None
        # Simulate header-provided next page token
        resp1.headers = {"opc-next-page": "nxtToken"}

        resp2 = create_autospec(oci.response.Response)
        resp2.data = [{"id": "family2", "display_name": "Family 2"}]
        resp2.next_page = None
        resp2.headers = {}

        mock_client.list_fusion_environment_families.side_effect = [resp1, resp2]

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_fusion_environment_families",
                {"compartment_id": "compartmentA"},
            )
            result = call_res.structured_content["result"]

            assert [f["id"] for f in result] == ["family1", "family2"]

        # First call without page, second call with header-derived page
        assert mock_client.list_fusion_environment_families.call_count == 2
        _, first_kwargs = mock_client.list_fusion_environment_families.call_args_list[0]
        _, second_kwargs = mock_client.list_fusion_environment_families.call_args_list[
            1
        ]
        assert first_kwargs["compartment_id"] == "compartmentA"
        assert "page" not in first_kwargs or first_kwargs["page"] is None
        assert second_kwargs["page"] == "nxtToken"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environments_pagination_header_fallback(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [{"id": "env1", "display_name": "Env 1"}]
        resp1.next_page = None
        resp1.headers = {"opc-next-page": "tok2"}

        resp2 = create_autospec(oci.response.Response)
        resp2.data = [{"id": "env2", "display_name": "Env 2"}]
        resp2.next_page = None
        resp2.headers = {}

        mock_client.list_fusion_environments.side_effect = [resp1, resp2]

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_fusion_environments",
                {
                    "compartment_id": "compartmentB",
                    "fusion_environment_family_id": "fam1",
                },
            )
            result = call_res.structured_content["result"]
            assert [e["id"] for e in result] == ["env1", "env2"]

        assert mock_client.list_fusion_environments.call_count == 2
        _, first_kwargs = mock_client.list_fusion_environments.call_args_list[0]
        _, second_kwargs = mock_client.list_fusion_environments.call_args_list[1]
        assert first_kwargs["compartment_id"] == "compartmentB"
        assert first_kwargs["fusion_environment_family_id"] == "fam1"
        assert "page" not in first_kwargs or first_kwargs["page"] is None
        assert second_kwargs["page"] == "tok2"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_fusion_environments_limit_enforced(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [{"id": "env1"}]
        resp1.next_page = None
        resp1.headers = {"opc-next-page": "tok2"}  # would paginate but limit stops it

        mock_client.list_fusion_environments.side_effect = [resp1]

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_fusion_environments",
                {"compartment_id": "compartmentB", "limit": 1},
            )
            result = call_res.structured_content["result"]
            assert len(result) == 1
            assert result[0]["id"] == "env1"

        # Only one SDK call due to limit=1
        assert mock_client.list_fusion_environments.call_count == 1

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_families_handles_items_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = types.SimpleNamespace(
            items=[{"id": "familyX", "display_name": "Fam X"}]
        )
        resp.has_next_page = False
        resp.next_page = None
        mock_client.list_fusion_environment_families.return_value = resp

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_fusion_environment_families",
                {"compartment_id": "compartmentC"},
            )
            result = call_res.structured_content["result"]
            assert [f["id"] for f in result] == ["familyX"]

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_admin_users_handles_items_container(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = types.SimpleNamespace(items=[{"username": "container-admin"}])
        resp.has_next_page = False
        resp.next_page = None
        mock_client.list_admin_users.return_value = resp

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_admin_users", {"fusion_environment_id": "envC"}
            )
            result = call_res.structured_content["result"]
            assert result[0]["username"] == "container-admin"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_list_refresh_activities_paginates_and_accumulates(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp1 = create_autospec(oci.response.Response)
        resp1.data = [{"id": "ra1"}]
        resp1.has_next_page = True
        resp1.next_page = "nextPage"

        resp2 = create_autospec(oci.response.Response)
        resp2.data = [{"id": "ra2"}]
        resp2.has_next_page = False
        resp2.next_page = None

        mock_client.list_refresh_activities.side_effect = [resp1, resp2]

        async with Client(mcp) as client:
            call_res = await client.call_tool(
                "list_refresh_activities", {"fusion_environment_id": "envR"}
            )
            result = call_res.structured_content["result"]
            assert [r["id"] for r in result] == ["ra1", "ra2"]

        # Verify that the page token from the first response was used on the second call
        _, first_kwargs = mock_client.list_refresh_activities.call_args_list[0]
        _, second_kwargs = mock_client.list_refresh_activities.call_args_list[1]
        assert "page" not in first_kwargs or first_kwargs["page"] is None
        assert second_kwargs["page"] == "nextPage"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_retry_strategy_none_list_scheduled_activities(self, mock_get_client):
        # Provide a retry stub so server can set kwargs['retry_strategy']
        oci.retry = types.SimpleNamespace(NoneRetryStrategy=lambda: "NONE")  # type: ignore[attr-defined]

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = []
        resp.has_next_page = False
        resp.next_page = None
        mock_client.list_scheduled_activities.return_value = resp

        async with Client(mcp) as client:
            await client.call_tool(
                "list_scheduled_activities",
                {
                    "fusion_environment_id": "envRS",
                    "retry_strategy": "none",
                },
            )

        _, kwargs = mock_client.list_scheduled_activities.call_args
        assert kwargs["retry_strategy"] == "NONE"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_retry_strategy_none_get_scheduled_activity(self, mock_get_client):
        # Provide a retry stub so server can set kwargs['retry_strategy']
        oci.retry = types.SimpleNamespace(NoneRetryStrategy=lambda: "NONE")  # type: ignore[attr-defined]

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = {"id": "sa-retry"}
        mock_client.get_scheduled_activity.return_value = resp

        async with Client(mcp) as client:
            await client.call_tool(
                "get_scheduled_activity",
                {
                    "fusion_environment_id": "envRS",
                    "scheduled_activity_id": "sa-retry",
                    "retry_strategy": "none",
                },
            )

        _, kwargs = mock_client.get_scheduled_activity.call_args
        assert kwargs["retry_strategy"] == "NONE"
        assert kwargs["fusion_environment_id"] == "envRS"
        assert kwargs["scheduled_activity_id"] == "sa-retry"

    @pytest.mark.asyncio
    @patch("oracle.oci_faaas_mcp_server.server.get_faaas_client")
    async def test_retry_strategy_none_get_subscription_detail_with_options(
        self, mock_get_client
    ):
        # Provide a retry stub so server can set kwargs['retry_strategy']
        oci.retry = types.SimpleNamespace(NoneRetryStrategy=lambda: "NONE")  # type: ignore[attr-defined]

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        resp = create_autospec(oci.response.Response)
        resp.data = {
            "subscriptions": [{"id": "sub1", "service_name": "SAAS", "skus": []}]
        }
        mock_client.get_fusion_environment_family_subscription_detail.return_value = (
            resp
        )

        async with Client(mcp) as client:
            await client.call_tool(
                "get_fusion_environment_family_subscription_detail",
                {
                    "fusion_environment_family_id": "ocid1.fam.oc1..example",
                    "opc_request_id": "r-123",
                    "allow_control_chars": True,
                    "retry_strategy": "none",
                },
            )

        _, kwargs = (
            mock_client.get_fusion_environment_family_subscription_detail.call_args
        )
        assert kwargs["opc_request_id"] == "r-123"
        assert kwargs["allow_control_chars"] is True
        assert kwargs["retry_strategy"] == "NONE"
