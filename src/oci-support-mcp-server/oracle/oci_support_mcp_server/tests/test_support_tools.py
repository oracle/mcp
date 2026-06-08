"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import oci
import oracle.oci_support_mcp_server.server as server
import pytest
from fastmcp import Client
from oracle.oci_support_mcp_server.models import (
    CreateIncident,
    Incident,
    IncidentResourceType,
    IncidentSummary,
    ValidationResponse,
)
from oracle.oci_support_mcp_server.server import mcp


def _response(data, *, has_next_page=False, next_page=None):
    return SimpleNamespace(data=data, has_next_page=has_next_page, next_page=next_page)


def _raise(error):
    raise error


class TestSupportTools:
    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_list_incidents(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        # Simulate OCI response with sample IncidentSummary data
        mock_summary = IncidentSummary(key="INC1", compartment_id="test_compartment")
        mock_response.data = [mock_summary]
        mock_response.has_next_page = False
        mock_response.next_page = None
        mock_client.list_incidents.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_incidents", {"compartment_id": "test_compartment"}
            )
            result = call_tool_result.structured_content["result"]
            assert isinstance(result, list)
            assert result[0]["key"] == "INC1"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_get_incident(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_incident = Incident(key="INC1", ticket={"severity": "SEV1"})
        mock_response.data = mock_incident
        mock_client.get_incident.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "get_incident",
                {"incident_key": "INC1", "compartment_id": "test_compartment"},
            )
            result = call_tool_result.structured_content
            assert result["key"] == "INC1"
            assert result["ticket"]["severity"] == "SEV1"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_create_incident(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_incident = Incident(key="INC1", ticket={"severity": "SEV2"})
        mock_response.data = mock_incident
        mock_client.create_incident.return_value = mock_response

        create_incident_details = CreateIncident(compartment_id="test_compartment")
        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "create_incident", {"create_incident_details": create_incident_details}
            )
            result = call_tool_result.structured_content
            assert result["key"] == "INC1"
            assert result["ticket"]["severity"] == "SEV2"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_list_incident_resource_types(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_res_type = IncidentResourceType(resource_type_key="RT1", name="ResType1")
        # Use model_dump to ensure dict serialization, matching FastMCP output
        mock_response.data = [mock_res_type.model_dump(exclude_none=True)]
        mock_client.list_incident_resource_types.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool(
                "list_incident_resource_types",
                {"problem_type": "TECH", "compartment_id": "test_compartment"},
            )
            result = call_tool_result.structured_content
            assert isinstance(
                result, dict
            ), f"Expected a dict, got {type(result)}: {result}"
            entries = result.get("result")
            assert isinstance(entries, list), f"'result' is not a list: {entries}"
            assert (
                entries
            ), f"list_incident_resource_types returned empty list: {entries}"
            assert entries[0]["resource_type_key"] == "RT1"
            assert entries[0]["name"] == "ResType1"

    @pytest.mark.asyncio
    @patch("oracle.oci_support_mcp_server.server.get_cims_client")
    async def test_validate_user(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_response = MagicMock()
        mock_validation = ValidationResponse(is_valid_user=True)
        mock_response.data = mock_validation
        mock_client.validate_user.return_value = mock_response

        async with Client(mcp) as client:
            call_tool_result = await client.call_tool("validate_user", {})
            result = call_tool_result.structured_content
            assert "is_valid_user" in result
            assert result["is_valid_user"]


def test_http_signer_requires_region(monkeypatch):
    monkeypatch.setattr(server, "get_access_token", lambda: MagicMock(token="token"))
    monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
    monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
    monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
    monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

    with pytest.raises(RuntimeError, match="OCI_REGION"):
        server._get_http_config_and_signer()


def test_http_config_and_cims_client_auth_paths(monkeypatch):
    for key in (
        "ORACLE_MCP_HOST",
        "ORACLE_MCP_PORT",
        "IDCS_DOMAIN",
        "IDCS_CLIENT_ID",
        "IDCS_CLIENT_SECRET",
        "OCI_REGION",
    ):
        monkeypatch.delenv(key, raising=False)

    assert server._get_http_config_and_signer() == (None, None)

    monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
    monkeypatch.setattr(server, "get_access_token", lambda: None)
    with pytest.raises(RuntimeError, match="access token"):
        server._get_http_config_and_signer()

    monkeypatch.setattr(server, "get_access_token", lambda: MagicMock(token="token"))
    with pytest.raises(RuntimeError, match="IDCS authentication"):
        server._get_http_config_and_signer()

    monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
    monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
    monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
    with pytest.raises(RuntimeError, match="OCI_REGION"):
        server._get_http_config_and_signer()

    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    token_exchange_signer = MagicMock(return_value="http-signer")
    monkeypatch.setattr(
        server.oci.auth.signers, "TokenExchangeSigner", token_exchange_signer
    )
    config, signer = server._get_http_config_and_signer()
    assert config == {
        "region": "us-ashburn-1",
        "additional_user_agent": f"oci_support_mcp_server/{server.__version__}",
    }
    assert signer == "http-signer"

    incident_client = MagicMock(return_value="incident-client")
    monkeypatch.setattr(server.oci.cims, "IncidentClient", incident_client)
    monkeypatch.setattr(
        server, "_get_http_config_and_signer", lambda: (config, signer)
    )
    assert server.get_cims_client() == "incident-client"
    incident_client.assert_called_once_with(config, signer=signer)

    incident_client.reset_mock()
    monkeypatch.setattr(server, "_get_http_config_and_signer", lambda: (None, None))
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "PROFILE")
    monkeypatch.setattr(
        server.oci.config, "from_file", MagicMock(return_value={"region": "home"})
    )
    assert server.get_cims_client() == "incident-client"
    assert incident_client.call_args.args[0]["additional_user_agent"] == (
        f"oci_support/{server.__version__}"
    )
    server.oci.config.from_file.assert_called_once_with(profile_name="PROFILE")


def test_support_tools_forward_optional_kwargs_and_paginate(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr(server, "get_cims_client", lambda: mock_client)

    mock_client.list_incidents.side_effect = [
        _response(
            [
                {
                    "key": "INC1",
                    "compartment_id": "compartment",
                    "ticket": {"severity": "SEV1"},
                }
            ],
            has_next_page=True,
            next_page="page-2",
        ),
        _response(
            [
                {
                    "key": "INC2",
                    "compartment_id": "compartment",
                    "ticket": {"severity": "SEV2"},
                }
            ]
        ),
    ]
    incidents = server.list_incidents(
        compartment_id="compartment",
        ocid="user",
        limit=2,
        sort_by="severity",
        sort_order="DESC",
        lifecycle_state="ACTIVE",
        page="page-1",
        opc_request_id="opc",
        homeregion="us-ashburn-1",
        problem_type="TECH",
        bearertokentype="jwt",
        bearertoken="bearer",
        idtoken="id",
        domainid="domain",
        allow_control_chars=True,
        retry_strategy="default",
    )

    assert [incident["key"] for incident in incidents] == ["INC1", "INC2"]
    assert mock_client.list_incidents.call_args_list[0].kwargs["retry_strategy"] is (
        oci.retry.DEFAULT_RETRY_STRATEGY
    )
    assert mock_client.list_incidents.call_args_list[0].kwargs["page"] == "page-1"
    assert mock_client.list_incidents.call_args_list[1].kwargs["page"] == "page-2"

    mock_client.get_incident.return_value = _response(
        {
            "key": "INC1",
            "compartment_id": "compartment",
            "ticket": {"severity": "SEV1"},
        }
    )
    incident = server.get_incident(
        incident_key="INC1",
        compartment_id="compartment",
        opc_request_id="opc",
        ocid="user",
        homeregion="us-ashburn-1",
        problemtype="TECH",
        bearertokentype="jwt",
        bearertoken="bearer",
        idtoken="id",
        domainid="domain",
        allow_control_chars=True,
        retry_strategy="none",
    )
    assert incident.key == "INC1"
    assert mock_client.get_incident.call_args.kwargs["retry_strategy"] is (
        oci.retry.NoneRetryStrategy
    )

    mock_client.create_incident.return_value = _response(
        {"key": "INC3", "ticket": {"severity": "HIGH"}}
    )
    create_details = CreateIncident(
        compartment_id="compartment",
        ticket={"severity": "HIGH"},
    )
    created = server.create_incident(
        create_incident_details=create_details,
        opc_request_id="opc",
        ocid="user",
        homeregion="us-ashburn-1",
        bearertokentype="jwt",
        bearertoken="bearer",
        idtoken="id",
        domainid="domain",
        allow_control_chars=True,
        retry_strategy="default",
    )
    assert created.key == "INC3"
    create_kwargs = mock_client.create_incident.call_args.kwargs
    assert create_kwargs["create_incident_details"].compartment_id == "compartment"
    assert create_kwargs["retry_strategy"] is oci.retry.DEFAULT_RETRY_STRATEGY

    mock_client.list_incident_resource_types.return_value = _response(
        [{"resource_type_key": "rt", "name": "Resource"}]
    )
    resource_types = server.list_incident_resource_types(
        problem_type="TECH",
        compartment_id="compartment",
        opc_request_id="opc",
        limit=10,
        page="page",
        sort_by="dateUpdated",
        sort_order="ASC",
        name="Resource",
        ocid="user",
        homeregion="us-ashburn-1",
        domainid="domain",
        allow_control_chars=True,
        retry_strategy="none",
    )
    assert resource_types[0].resource_type_key == "rt"
    assert mock_client.list_incident_resource_types.call_args.kwargs[
        "retry_strategy"
    ] is oci.retry.NoneRetryStrategy

    mock_client.validate_user.return_value = _response(
        {
            "is_valid_user": True,
            "write_permitted_user_group_infos": [
                {"user_group_id": "group", "user_group_name": "Group"}
            ],
        }
    )
    validation = server.validate_user(
        opc_request_id="opc",
        problem_type="TECH",
        ocid="user",
        homeregion="us-ashburn-1",
        bearertokentype="jwt",
        bearertoken="bearer",
        idtoken="id",
        domainid="domain",
        allow_control_chars=True,
        retry_strategy="default",
    )
    assert validation.is_valid_user is True
    assert mock_client.validate_user.call_args.kwargs["retry_strategy"] is (
        oci.retry.DEFAULT_RETRY_STRATEGY
    )


def test_support_tools_default_empty_models_and_error_paths(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr(server, "get_cims_client", lambda: mock_client)

    mock_client.get_incident.return_value = _response(None)
    assert server.get_incident("INC1", "compartment").key is None

    mock_client.create_incident.return_value = _response(None)
    assert server.create_incident(CreateIncident(compartment_id="compartment")).key is None

    mock_client.validate_user.return_value = _response(None)
    assert server.validate_user().is_valid_user is None

    error_cases = [
        (
            server.list_incidents,
            {"compartment_id": "compartment"},
            "list_incidents",
        ),
        (
            server.get_incident,
            {"incident_key": "INC1", "compartment_id": "compartment"},
            "get_incident",
        ),
        (
            server.create_incident,
            {"create_incident_details": CreateIncident(compartment_id="compartment")},
            "create_incident",
        ),
        (
            server.list_incident_resource_types,
            {"problem_type": "TECH", "compartment_id": "compartment"},
            "list_incident_resource_types",
        ),
        (server.validate_user, {}, "validate_user"),
    ]
    for tool, kwargs, method_name in error_cases:
        getattr(mock_client, method_name).side_effect = RuntimeError(
            f"{method_name} failed"
        )
        with pytest.raises(RuntimeError, match=f"{method_name} failed"):
            tool(**kwargs)
        getattr(mock_client, method_name).side_effect = None


def test_list_incidents_limit_and_retry_none(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr(server, "get_cims_client", lambda: mock_client)

    mock_client.list_incidents.return_value = _response(
        [
            {"key": "INC1", "compartment_id": "compartment"},
            {"key": "INC2", "compartment_id": "compartment"},
        ],
        has_next_page=True,
        next_page="unused",
    )

    incidents = server.list_incidents(
        compartment_id="compartment",
        limit=1,
        retry_strategy="none",
    )

    assert incidents == [{"key": "INC1", "compartment_id": "compartment"}]
    assert mock_client.list_incidents.call_args.kwargs["retry_strategy"] is (
        oci.retry.NoneRetryStrategy
    )


def test_main_with_host_and_port(monkeypatch):
    monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
    monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
    monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
    monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("IDCS_AUDIENCE", "mcp-audience")
    monkeypatch.setenv("ORACLE_MCP_BASE_URL", "http://127.0.0.1:8888")

    with (
        patch("oracle.oci_support_mcp_server.server.OCIProvider", return_value=object()) as mock_provider,
        patch("oracle.oci_support_mcp_server.server.mcp.run") as mock_run,
    ):
        server.main()

    mock_provider.assert_called_once_with(
        config_url="https://idcs.example.com/.well-known/openid-configuration",
        client_id="client-id",
        client_secret="client-secret",
        audience="mcp-audience",
        required_scopes=f"openid profile email oci_mcp.{server.__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
        base_url="http://127.0.0.1:8888",
    )
    mock_run.assert_called_once_with(transport="http", host="127.0.0.1", port=8888)


def test_main_without_host_or_missing_http_config(monkeypatch):
    monkeypatch.delenv("ORACLE_MCP_HOST", raising=False)
    monkeypatch.delenv("ORACLE_MCP_PORT", raising=False)
    with patch("oracle.oci_support_mcp_server.server.mcp.run") as mock_run:
        server.main()
    mock_run.assert_called_once_with()

    monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
    monkeypatch.delenv("IDCS_DOMAIN", raising=False)
    monkeypatch.delenv("IDCS_CLIENT_ID", raising=False)
    monkeypatch.delenv("IDCS_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("IDCS_AUDIENCE", raising=False)
    monkeypatch.delenv("ORACLE_MCP_BASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="HTTP transport requires"):
        server.main()
