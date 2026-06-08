"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, create_autospec, mock_open, patch

import oci
import pytest
from fastmcp import Client
import oracle.oci_limits_mcp_server.server as server
from oracle.oci_limits_mcp_server.server import mcp
from oracle.oci_limits_mcp_server import utils


class TestLimitsTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_list_services(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [
            oci.limits.models.ServiceSummary(name="service1", description="Service 1")
        ]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_services.return_value = mock_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_services",
                    {
                        "compartment_id": "ocid1.compartment.oc1..xxxx",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "service1"

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_list_limit_definitions(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [
            oci.limits.models.LimitDefinitionSummary(
                name="limit1", service_name="service1", description="Limit 1"
            )
        ]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_definitions.return_value = mock_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_limit_definitions",
                    {
                        "compartment_id": "ocid1.compartment.oc1..xxxx",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "limit1"

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_list_limit_value(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [
            oci.limits.models.LimitValueSummary(
                name="limit_value1", scope_type="GLOBAL", value=10
            )
        ]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_values.return_value = mock_response

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "list_limit_value",
                    {
                        "compartment_id": "ocid1.compartment.oc1..xxxx",
                        "service_name": "service1",
                        "name": "limit_value1",
                        "scope_type": "GLOBAL",
                    },
                )
            ).structured_content["result"]

            assert len(result) == 1
            assert result[0]["name"] == "limit_value1"

    def test_provide_availability_domains_redirects_to_identity_server(self):
        result = server.provide_availability_domains_for_limits(
            "ocid1.tenancy.oc1..xxxx"
        )

        assert result == [
            {
                "message": (
                    "Call oracle-identity-mcp-server.list_availability_domains with tenancy_id=the tenancy OCID. "
                    "Then pass one of the returned AD names to get_resource_availability when scopeType is AD."
                ),
                "redirect": {
                    "server": "oracle.oci-identity-mcp-server",
                    "tool": "list_availability_domains",
                    "args": {"tenancy_id": "ocid1.tenancy.oc1..xxxx"},
                },
            }
        ]

    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    def test_list_services_propagates_pagination_errors(self, mock_get_client):
        mock_get_client.return_value = MagicMock()

        with patch(
            "oracle.oci_limits_mcp_server.server.list_services_with_pagination",
            side_effect=RuntimeError("service list failed"),
        ):
            with pytest.raises(RuntimeError, match="service list failed"):
                server.list_services("ocid1.compartment.oc1..xxxx")

    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    def test_list_limit_definitions_propagates_pagination_errors(self, mock_get_client):
        mock_get_client.return_value = MagicMock()

        with patch(
            "oracle.oci_limits_mcp_server.server.list_limit_definitions_with_pagination",
            side_effect=RuntimeError("definition list failed"),
        ):
            with pytest.raises(RuntimeError, match="definition list failed"):
                server.list_limit_definitions("ocid1.compartment.oc1..xxxx")

    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    def test_list_limit_value_propagates_pagination_errors(self, mock_get_client):
        mock_get_client.return_value = MagicMock()

        with patch(
            "oracle.oci_limits_mcp_server.server.list_limit_values_with_pagination",
            side_effect=RuntimeError("value list failed"),
        ):
            with pytest.raises(RuntimeError, match="value list failed"):
                server.list_limit_value(
                    compartment_id="ocid1.compartment.oc1..xxxx",
                    service_name="service1",
                    name="limit_value1",
                    scope_type="GLOBAL",
                )


class TestGetClient:
    def test_get_oci_client_kwargs_without_signer_uses_circuit_breaker_env(
        self, monkeypatch
    ):
        monkeypatch.setenv("OCI_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "2")
        monkeypatch.setenv("OCI_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "5")

        kwargs = server._get_oci_client_kwargs()

        assert "signer" not in kwargs
        assert isinstance(
            kwargs["circuit_breaker_strategy"],
            oci.circuit_breaker.CircuitBreakerStrategy,
        )
        assert callable(kwargs["circuit_breaker_callback"])
        kwargs["circuit_breaker_callback"](RuntimeError("circuit open"))

    @patch("oracle.oci_limits_mcp_server.server.oci.limits.LimitsClient")
    @patch("oracle.oci_limits_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_limits_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch(
        "oracle.oci_limits_mcp_server.server.open",
        new_callable=mock_open,
        read_data="SECURITY_TOKEN",
    )
    @patch("oracle.oci_limits_mcp_server.server.oci.config.from_file")
    @patch("oracle.oci_limits_mcp_server.server.os.getenv")
    def test_get_limits_client_passes_circuit_breaker(
        self,
        mock_getenv,
        mock_from_file,
        mock_open_file,
        mock_load_private_key,
        mock_security_token_signer,
        mock_client,
    ):
        mock_getenv.side_effect = lambda k, default=None: (
            "MYPROFILE" if k == "OCI_CONFIG_PROFILE" else default
        )
        config = {"key_file": "/key.pem", "security_token_file": "/token"}
        mock_from_file.return_value = config
        private_key_obj = object()
        mock_load_private_key.return_value = private_key_obj

        result = server.get_limits_client()

        mock_open_file.assert_called_once_with("/token", "r")
        mock_security_token_signer.assert_called_once_with("SECURITY_TOKEN", private_key_obj)
        args, kwargs = mock_client.call_args
        assert args[0] is config
        assert kwargs["signer"] is mock_security_token_signer.return_value
        assert isinstance(kwargs["circuit_breaker_strategy"], oci.circuit_breaker.CircuitBreakerStrategy)
        assert callable(kwargs["circuit_breaker_callback"])
        assert result is mock_client.return_value

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_get_resource_availability_ad_scope(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_limit_definition = create_autospec(
            oci.limits.models.LimitDefinitionSummary
        )
        mock_limit_definition.is_resource_availability_supported = True
        mock_limit_definition.scope_type = "AD"

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [mock_limit_definition]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_definitions.return_value = mock_response

        # Simulate that the tool returns a redirect/hint to identity server for AD lists
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_resource_availability",
                {
                    "service_name": "service1",
                    "limit_name": "limit1",
                    "compartment_id": "ocid1.compartment.oc1..xxxx",
                },
            )

            result_obj = result.structured_content["result"]
            assert isinstance(result_obj, list)
            assert "redirect" in result_obj[0] or "message" in result_obj[0]
            assert "identity" in result_obj[0].get(
                "message", ""
            ) or "list_availability_domains" in str(result_obj[0])

            # Optionally check that the redirect/hint is well-formed
            if "redirect" in result_obj[0]:
                redirect = result_obj[0]["redirect"]
                assert redirect["server"].endswith("identity-mcp-server")
                assert redirect["tool"] == "list_availability_domains"

    @pytest.mark.asyncio
    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    async def test_get_resource_availability_non_ad_scope(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_limit_definition = create_autospec(
            oci.limits.models.LimitDefinitionSummary
        )
        mock_limit_definition.is_resource_availability_supported = True
        mock_limit_definition.scope_type = "REGION"

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = [mock_limit_definition]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_limit_definitions.return_value = mock_response

        mock_response = create_autospec(oci.response.Response)
        mock_response.data = oci.limits.models.ResourceAvailability(
            used=10, available=100
        )
        mock_client.get_resource_availability.return_value = mock_response

        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_resource_availability",
                {
                    "service_name": "service1",
                    "limit_name": "limit1",
                    "compartment_id": "ocid1.compartment.oc1..xxxx",
                },
            )

            assert len(result.structured_content["result"]) == 1
            assert result.structured_content["result"][0]["used"] == 10
            assert result.structured_content["result"][0]["available"] == 100

    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    def test_get_resource_availability_returns_not_found_message(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.list_limit_definitions.return_value = SimpleNamespace(
            data=[],
            has_next_page=False,
            next_page=None,
        )

        result = server.get_resource_availability(
            service_name="service1",
            limit_name="missing_limit",
            compartment_id="ocid1.compartment.oc1..xxxx",
        )

        assert result == [
            {"message": "Limit 'missing_limit' not found for service 'service1'"}
        ]

    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    def test_get_resource_availability_returns_unsupported_message(
        self, mock_get_client
    ):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_limit_definitions.return_value = SimpleNamespace(
            data=[
                SimpleNamespace(
                    is_resource_availability_supported=False,
                    scope_type="REGION",
                )
            ],
            has_next_page=False,
            next_page=None,
        )

        result = server.get_resource_availability(
            service_name="service1",
            limit_name="unsupported_limit",
            compartment_id="ocid1.compartment.oc1..xxxx",
        )

        assert result == [
            {
                "message": (
                    "Resource availability not supported for limit 'unsupported_limit'. "
                    "Consider calling list_limit_value to get the limit value."
                )
            }
        ]

    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    def test_get_resource_availability_ad_scope_with_domain(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_limit_definitions.return_value = SimpleNamespace(
            data=[
                SimpleNamespace(
                    is_resource_availability_supported=True,
                    scope_type="AD",
                )
            ],
            has_next_page=False,
            next_page=None,
        )
        mock_client.get_resource_availability.return_value = SimpleNamespace(
            data=oci.limits.models.ResourceAvailability(
                used=3,
                available=7,
                fractional_usage=3.5,
                fractional_availability=7.5,
                effective_quota_value=10,
            )
        )

        result = server.get_resource_availability(
            service_name="service1",
            limit_name="ad_limit",
            compartment_id="ocid1.compartment.oc1..xxxx",
            availability_domain="US-ASHBURN-AD-1",
            subscription_id="ocid1.subscription.oc1..xxxx",
        )

        assert result == [
            {
                "availabilityDomain": "US-ASHBURN-AD-1",
                "resourceAvailability": {
                    "used": 3,
                    "available": 7,
                    "fractionalUsage": 3.5,
                    "fractionalAvailability": 7.5,
                    "effectiveQuotaValue": 10,
                },
            }
        ]
        mock_client.get_resource_availability.assert_called_once_with(
            service_name="service1",
            limit_name="ad_limit",
            compartment_id="ocid1.compartment.oc1..xxxx",
            availability_domain="US-ASHBURN-AD-1",
            subscription_id="ocid1.subscription.oc1..xxxx",
        )

    @patch("oracle.oci_limits_mcp_server.server.get_limits_client")
    def test_get_resource_availability_propagates_errors(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.list_limit_definitions.side_effect = RuntimeError(
            "availability failed"
        )

        with pytest.raises(RuntimeError, match="availability failed"):
            server.get_resource_availability(
                service_name="service1",
                limit_name="limit1",
                compartment_id="ocid1.compartment.oc1..xxxx",
            )

    def test_get_identity_client_points_callers_to_identity_server(self):
        with pytest.raises(NotImplementedError, match="oracle-identity-mcp-server"):
            server.get_identity_client()

    def test_main_runs_mcp_server(self):
        with patch.object(server.mcp, "run") as mock_run:
            server.main()

        mock_run.assert_called_once_with()


class TestPaginationHelpers:
    def test_list_services_collects_all_pages(self):
        first = SimpleNamespace(name="service1")
        second = SimpleNamespace(name="service2")
        mock_client = MagicMock()
        mock_client.list_services.side_effect = [
            SimpleNamespace(data=[first], has_next_page=True, next_page="page-2"),
            SimpleNamespace(data=[second], has_next_page=False, next_page=None),
        ]

        result = utils.list_services_with_pagination(
            mock_client,
            compartment_id="ocid1.compartment.oc1..xxxx",
            sort_by="description",
            sort_order="DESC",
            limit=50,
            subscription_id="ocid1.subscription.oc1..xxxx",
        )

        assert result == [first, second]
        assert mock_client.list_services.call_args_list[0].kwargs["page"] is None
        assert mock_client.list_services.call_args_list[1].kwargs["page"] == "page-2"

    def test_list_limit_definitions_stops_after_requested_page(self):
        definition = SimpleNamespace(name="limit1")
        mock_client = MagicMock()
        mock_client.list_limit_definitions.return_value = SimpleNamespace(
            data=[definition],
            has_next_page=True,
            next_page="unused-next-page",
        )

        result = utils.list_limit_definitions_with_pagination(
            mock_client,
            compartment_id="ocid1.compartment.oc1..xxxx",
            service_name="service1",
            name="limit1",
            page="requested-page",
        )

        assert result == [definition]
        mock_client.list_limit_definitions.assert_called_once()
        assert (
            mock_client.list_limit_definitions.call_args.kwargs["page"]
            == "requested-page"
        )

    def test_list_limit_values_treats_empty_page_data_as_empty_list(self):
        mock_client = MagicMock()
        mock_client.list_limit_values.return_value = SimpleNamespace(
            data=None,
            has_next_page=False,
            next_page=None,
        )

        result = utils.list_limit_values_with_pagination(
            mock_client,
            compartment_id="ocid1.compartment.oc1..xxxx",
            service_name="service1",
            scope_type="GLOBAL",
            name="limit1",
        )

        assert result == []

    def test_list_services_reraises_client_errors(self):
        mock_client = MagicMock()
        mock_client.list_services.side_effect = RuntimeError("services unavailable")

        with pytest.raises(RuntimeError, match="services unavailable"):
            utils.list_services_with_pagination(
                mock_client,
                compartment_id="ocid1.compartment.oc1..xxxx",
            )

    def test_list_limit_definitions_reraises_client_errors(self):
        mock_client = MagicMock()
        mock_client.list_limit_definitions.side_effect = RuntimeError(
            "definitions unavailable"
        )

        with pytest.raises(RuntimeError, match="definitions unavailable"):
            utils.list_limit_definitions_with_pagination(
                mock_client,
                compartment_id="ocid1.compartment.oc1..xxxx",
            )

    def test_list_limit_values_reraises_client_errors(self):
        mock_client = MagicMock()
        mock_client.list_limit_values.side_effect = RuntimeError("values unavailable")

        with pytest.raises(RuntimeError, match="values unavailable"):
            utils.list_limit_values_with_pagination(
                mock_client,
                compartment_id="ocid1.compartment.oc1..xxxx",
                service_name="service1",
                scope_type="GLOBAL",
            )
