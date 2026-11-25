"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from fastmcp import Client

from oracle.oci_iot_mcp_server import data_plane, server


DATA_TOOLS = [
    "list_raw_data",
    "get_raw_data",
    "list_rejected_data",
    "get_rejected_data",
    "list_snapshot_data",
    "list_historized_data",
    "get_historized_data",
    "list_raw_command_data",
    "get_raw_command_data",
]
INVALID_COMPONENTS = (
    [
        ("iot_domain_group_short_id", value)
        for value in [
            "attacker.example#",
            "attacker.example/",
            "attacker.example:443/p?",
            "user@attacker.example#",
            "group%2f",
            "group\\evil",
            "group\n",
            "",
            "-group",
        ]
    ]
    + [
        ("region", value)
        for value in ["attacker.example#", "attacker.example/", "us-phoenix-1?", "us-phoenix-1\n", "", "None"]
    ]
    + [
        ("iot_domain_short_id", value)
        for value in [
            "../other",
            "domain/other",
            "domain?query",
            "domain#fragment",
            "domain%2f",
            "",
            "domain\n",
        ]
    ]
)
INVALID_IDENTITY_HOSTS = [
    "attacker.example",
    "identity.oraclecloud.com.attacker.example",
    "idcs-example.identity.oraclecloud.com.attacker.example",
    "idcs-example.identity.oraclecloud.com@attacker.example",
    "attacker.example#idcs-example.identity.oraclecloud.com",
    "attacker.example/idcs-example.identity.oraclecloud.com",
    "https://idcs-example.identity.oraclecloud.com",
    "idcs-example.identity.oraclecloud.com/path",
    "idcs-example.identity.oraclecloud.com?query",
    "idcs-example.identity.oraclecloud.com#fragment",
    "idcs-example.identity.oraclecloud.com:8443",
    "idcs-example.identity.oraclecloud.com\n",
    "idcs-example.identity.oraclecloud.com\\evil",
    "127.0.0.1",
    "[::1]",
]


@pytest.mark.parametrize("tool_name", DATA_TOOLS)
@pytest.mark.parametrize("field,value", INVALID_COMPONENTS)
def test_data_tools_reject_invalid_endpoint_before_sending_token(monkeypatch, tool_name, field, value):
    monkeypatch.setenv("OCI_IOT_DATA_API_ACCESS_TOKEN", "example-environment-token")
    get = Mock(
        return_value=httpx.Response(
            200, json={"items": []}, request=httpx.Request("GET", "https://attacker.example")
        )
    )
    monkeypatch.setattr(server.httpx, "get", get)
    kwargs = {"iot_domain_group_short_id": "group", "iot_domain_short_id": "domain", "region": "us-phoenix-1"}
    if tool_name.startswith("get_"):
        kwargs["record_id"] = "record1"
    kwargs[field] = value

    result = getattr(server, tool_name)(**kwargs)

    get.assert_not_called()
    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_input"
    assert "example-environment-token" not in str(result)


@pytest.mark.parametrize("region", ["us-phoenix-1", "eu-frankfurt-1", "us-gov-ashburn-1"])
def test_data_url_accepts_oci_region_formats(region):
    assert server._build_iot_data_api_url("group1", "domain1", "/rawData", region) == (
        f"https://group1.data.iot.{region}.oci.oraclecloud.com/ords/domain1/rawData"
    )


@pytest.mark.parametrize("region", [None, "us-phoenix-1/", "us-phoenix-1#"])
@pytest.mark.parametrize("auth_type", ["api_key", "instance_principal"])
def test_data_tools_validate_region_from_auth_configuration(monkeypatch, region, auth_type):
    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", auth_type)
    monkeypatch.setattr(server, "_get_oci_config", lambda: {"region": region})
    monkeypatch.setattr(server, "get_default_region", lambda **kwargs: region)
    get = Mock(
        return_value=httpx.Response(
            200, json={"items": []}, request=httpx.Request("GET", "https://attacker.example")
        )
    )
    monkeypatch.setattr(server.httpx, "get", get)

    result = server.list_raw_data("group", "domain", access_token="example-token")

    get.assert_not_called()
    assert result["error"]["code"] == "invalid_input"


@pytest.mark.parametrize(
    "url",
    [
        "https://attacker.example/data",
        "http://group.data.iot.us-phoenix-1.oci.oraclecloud.com/data",
        "https://group.oci.oraclecloud.com.attacker.example/data",
        "https://user@group.oci.oraclecloud.com/data",
        "https://group.oci.oraclecloud.com:8443/data",
        "https://group.oci.oraclecloud.com\\@attacker.example/data",
        "https://group.oci.oraclecloud.com\n.attacker.example/data",
        "https://[broken/data",
    ],
)
def test_data_request_checks_final_url_before_attaching_token(monkeypatch, url):
    monkeypatch.setattr(server, "_build_iot_data_api_url", lambda **kwargs: url)
    get = Mock(
        return_value=httpx.Response(
            200, json={"items": []}, request=httpx.Request("GET", "https://attacker.example")
        )
    )
    monkeypatch.setattr(server.httpx, "get", get)

    result = server.list_raw_data("group", "domain", access_token="example-token")

    get.assert_not_called()
    assert result["error"]["code"] == "invalid_input"


@pytest.mark.asyncio
async def test_mcp_rejects_injected_host_without_http_request(monkeypatch):
    monkeypatch.setenv("OCI_IOT_DATA_API_ACCESS_TOKEN", "example-environment-token")
    get = Mock(
        return_value=httpx.Response(
            200, json={"items": []}, request=httpx.Request("GET", "https://attacker.example")
        )
    )
    monkeypatch.setattr(server.httpx, "get", get)
    async with Client(server.mcp) as client:
        result = await client.call_tool(
            "list_raw_data",
            {
                "iot_domain_group_short_id": "attacker.example#",
                "iot_domain_short_id": "domain",
                "region": "us-phoenix-1",
            },
        )
    get.assert_not_called()
    assert result.structured_content["error"]["code"] == "invalid_input"


@pytest.mark.parametrize("host", INVALID_IDENTITY_HOSTS)
def test_token_minting_rejects_untrusted_identity_host_before_sending_credentials(monkeypatch, host):
    post = Mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "example-token",
                "token_type": "Bearer",
                "expires_in": 60,
            },
            request=httpx.Request("POST", "https://attacker.example"),
        )
    )
    monkeypatch.setattr(data_plane.httpx, "post", post)
    with pytest.raises(data_plane.DataApiTokenError) as excinfo:
        data_plane.mint_data_api_token(
            domain_context={
                "domain_group_short_id": "group",
                "domain_short_id": "domain",
                "db_allowed_identity_domain_host": host,
            },
            env={
                "OCI_IOT_ORDS_CLIENT_ID": "example-client",
                "OCI_IOT_ORDS_CLIENT_SECRET": "this-is-not-the-secret",
                "OCI_IOT_ORDS_USERNAME": "example-user",
                "OCI_IOT_ORDS_PASSWORD": "example-password",
            },
            now=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )
    post.assert_not_called()
    assert excinfo.value.code == "invalid_ords_configuration"
    assert "this-is-not-the-secret" not in str(excinfo.value)
    assert "example-password" not in str(excinfo.value)


@pytest.mark.parametrize("host", INVALID_IDENTITY_HOSTS)
def test_ords_configuration_rejects_untrusted_identity_host_before_control_plane_call(monkeypatch, host):
    client = Mock()
    client.configure_iot_domain_data_access.return_value = SimpleNamespace(status=202, data={}, headers={})
    monkeypatch.setattr(server, "get_iot_client", lambda: client)
    with pytest.raises(ValueError, match="identity domain host"):
        server.configure_iot_domain_data_access(
            iot_domain_id="example-domain",
            type="ORDS",
            db_allowed_identity_domain_host=host,
        )
    client.configure_iot_domain_data_access.assert_not_called()


def test_direct_data_request_does_not_follow_redirects(monkeypatch):
    requests = []

    def transport(request):
        requests.append(request)
        return httpx.Response(307, headers={"Location": "https://attacker.example/data"})

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        monkeypatch.setattr(server.httpx, "get", client.get)
        result = server.list_raw_data("group", "domain", region="us-phoenix-1", access_token="example-token")
    assert len(requests) == 1
    assert requests[0].url.host == "group.data.iot.us-phoenix-1.oci.oraclecloud.com"
    assert result["error"]["code"] == "data_plane_http_error"


@pytest.mark.parametrize(
    "host",
    [
        "idcs-example.identity.oraclecloud.com",
        "idcs-example.identity.us-phoenix-1.oci.oraclecloud.com",
    ],
)
def test_identity_token_request_does_not_follow_redirects(monkeypatch, host):
    requests = []

    def transport(request):
        requests.append(request)
        return httpx.Response(307, headers={"Location": "https://attacker.example/token"})

    with httpx.Client(transport=httpx.MockTransport(transport)) as client:
        monkeypatch.setattr(data_plane.httpx, "post", client.post)
        with pytest.raises(data_plane.DataApiTokenError) as excinfo:
            data_plane.mint_data_api_token(
                domain_context={
                    "domain_group_short_id": "group",
                    "domain_short_id": "domain",
                    "db_allowed_identity_domain_host": host,
                },
                env={
                    "OCI_IOT_ORDS_CLIENT_ID": "example-client",
                    "OCI_IOT_ORDS_CLIENT_SECRET": "this-is-not-the-secret",
                    "OCI_IOT_ORDS_USERNAME": "example-user",
                    "OCI_IOT_ORDS_PASSWORD": "example-password",
                },
                now=lambda: datetime(2026, 1, 1, tzinfo=UTC),
            )
    assert len(requests) == 1
    assert requests[0].url.host == host
    assert requests[0].url.path == "/oauth2/v1/token"
    assert excinfo.value.details["status_code"] == 307
