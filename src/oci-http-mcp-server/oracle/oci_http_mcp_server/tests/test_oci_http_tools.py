"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import mock_open, patch

import pytest
import requests
from fastmcp import Client

from oracle.oci_http_mcp_server.server import (
    USER_AGENT,
    _build_request_url,
    _decode_response_body,
    _get_config_and_signer,
    _merge_user_agent,
    _prepare_request_body,
    _resolve_verify_ssl,
    mcp,
)


class FakeResponse:
    def __init__(self, *, status_code=200, headers=None, json_body=None, text="", reason="OK"):
        self.status_code = status_code
        self.headers = headers or {}
        self._json_body = json_body
        self.text = text
        self.reason = reason
        self.ok = 200 <= status_code < 400
        if json_body is None:
            self.content = text.encode("utf-8")
        else:
            self.content = b'{"ok":true}'

    def json(self):
        if self._json_body is None:
            raise ValueError("No JSON body")
        return self._json_body


class TestOciHttpServer:
    @pytest.mark.asyncio
    async def test_get_oci_http_request_guide(self):
        async with Client(mcp) as client:
            result = (await client.read_resource("resource://oci-http-request-guide"))[0].text

        assert "invoke_oci_http_api" in result
        assert "opc-next-page" in result

    @pytest.mark.asyncio
    @patch("oracle.oci_http_mcp_server.server.requests.request")
    @patch("oracle.oci_http_mcp_server.server.oci.regions.endpoint_for")
    @patch("oracle.oci_http_mcp_server.server._get_config_and_signer")
    async def test_invoke_oci_http_api_with_service_and_path(
        self, mock_get_config_and_signer, mock_endpoint_for, mock_request
    ):
        mock_get_config_and_signer.return_value = ({"region": "us-phoenix-1"}, object())
        mock_endpoint_for.return_value = "https://iaas.us-phoenix-1.oraclecloud.com"
        mock_request.return_value = FakeResponse(
            headers={
                "Content-Type": "application/json",
                "opc-request-id": "req-123",
            },
            json_body={"items": [{"id": "ocid1.instance.oc1..example"}]},
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "invoke_oci_http_api",
                    {
                        "method": "get",
                        "service": "iaas",
                        "path": "/20160918/instances",
                        "query": {"compartmentId": "ocid1.compartment.oc1..example"},
                    },
                )
            ).data

        assert result["method"] == "GET"
        assert result["status_code"] == 200
        assert result["opc_request_id"] == "req-123"
        assert result["data"] == {"items": [{"id": "ocid1.instance.oc1..example"}]}

        mock_endpoint_for.assert_called_once_with("iaas", region="us-phoenix-1")
        mock_request.assert_called_once()
        request_kwargs = mock_request.call_args.kwargs
        assert request_kwargs["method"] == "GET"
        assert request_kwargs["url"] == "https://iaas.us-phoenix-1.oraclecloud.com/20160918/instances"
        assert request_kwargs["params"] == {"compartmentId": "ocid1.compartment.oc1..example"}
        assert request_kwargs["headers"]["User-Agent"] == USER_AGENT
        assert request_kwargs["verify"] is True
        assert request_kwargs["timeout"] == 30

    @pytest.mark.asyncio
    @patch("oracle.oci_http_mcp_server.server.requests.request")
    @patch("oracle.oci_http_mcp_server.server._get_config_and_signer")
    async def test_invoke_oci_http_api_with_explicit_url_and_json_body(
        self, mock_get_config_and_signer, mock_request
    ):
        mock_get_config_and_signer.return_value = ({"region": "us-phoenix-1"}, object())
        mock_request.return_value = FakeResponse(
            headers={"Content-Type": "application/json"},
            json_body={"id": "ocid1.vcn.oc1..example"},
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "invoke_oci_http_api",
                    {
                        "method": "POST",
                        "url": "https://iaas.us-phoenix-1.oraclecloud.com/20160918/vcns",
                        "body": {
                            "cidrBlock": "10.0.0.0/16",
                            "compartmentId": "ocid1.compartment.oc1..example",
                        },
                    },
                )
            ).data

        assert result["data"] == {"id": "ocid1.vcn.oc1..example"}
        request_kwargs = mock_request.call_args.kwargs
        assert request_kwargs["url"] == "https://iaas.us-phoenix-1.oraclecloud.com/20160918/vcns"
        assert request_kwargs["json"] == {
            "cidrBlock": "10.0.0.0/16",
            "compartmentId": "ocid1.compartment.oc1..example",
        }
        assert request_kwargs["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    @patch("oracle.oci_http_mcp_server.server.requests.request")
    @patch("oracle.oci_http_mcp_server.server._get_config_and_signer")
    async def test_invoke_oci_http_api_with_raw_body_and_existing_user_agent(
        self, mock_get_config_and_signer, mock_request
    ):
        mock_get_config_and_signer.return_value = ({"region": "us-phoenix-1"}, object())
        mock_request.return_value = FakeResponse(
            headers={"Content-Type": "application/json"},
            json_body={"status": "accepted"},
        )

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "invoke_oci_http_api",
                    {
                        "method": "POST",
                        "path": "https://identity.us-phoenix-1.oraclecloud.com/20160918/tagNamespaces",
                        "body": "raw-body",
                        "headers": {"user-agent": "custom-agent", "Content-Type": "text/plain"},
                    },
                )
            ).data

        assert result["data"] == {"status": "accepted"}
        request_kwargs = mock_request.call_args.kwargs
        assert request_kwargs["url"] == (
            "https://identity.us-phoenix-1.oraclecloud.com/20160918/tagNamespaces"
        )
        assert request_kwargs["data"] == "raw-body"
        assert request_kwargs["headers"]["user-agent"] == f"custom-agent {USER_AGENT}"

    @pytest.mark.asyncio
    @patch("oracle.oci_http_mcp_server.server.requests.request")
    @patch("oracle.oci_http_mcp_server.server._get_config_and_signer")
    async def test_invoke_oci_http_api_respects_ssl_override_and_text_response(
        self, mock_get_config_and_signer, mock_request
    ):
        mock_get_config_and_signer.return_value = ({"region": "us-phoenix-1"}, object())
        mock_request.return_value = FakeResponse(
            headers={"Content-Type": "text/plain"},
            text="plain text response",
        )

        with patch.dict("os.environ", {"OCI_HTTP_VERIFY_SSL": "false"}):
            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_http_api",
                        {
                            "method": "GET",
                            "url": "https://identity.us-phoenix-1.oraclecloud.com/20160918/tenancies/x",
                        },
                    )
                ).data

        assert result["data"] == "plain text response"
        assert mock_request.call_args.kwargs["verify"] is False

    @pytest.mark.asyncio
    @patch("oracle.oci_http_mcp_server.server.requests.request")
    @patch("oracle.oci_http_mcp_server.server._get_config_and_signer")
    async def test_invoke_oci_http_api_returns_request_errors(
        self, mock_get_config_and_signer, mock_request
    ):
        mock_get_config_and_signer.return_value = ({"region": "us-phoenix-1"}, object())
        mock_request.side_effect = requests.Timeout("timed out")

        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "invoke_oci_http_api",
                    {
                        "method": "GET",
                        "url": "https://iaas.us-phoenix-1.oraclecloud.com/20160918/instances",
                    },
                )
            ).data

        assert result["ok"] is False
        assert result["error_type"] == "Timeout"
        assert "timed out" in result["error"]


class TestSignerSetup:
    @patch("oracle.oci_http_mcp_server.server.oci.auth.signers.SecurityTokenSigner")
    @patch("oracle.oci_http_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch("oracle.oci_http_mcp_server.server.os.path.exists")
    @patch("oracle.oci_http_mcp_server.server.oci.config.from_file")
    def test_get_config_and_signer_prefers_security_token(
        self,
        mock_from_file,
        mock_exists,
        mock_load_private_key,
        mock_security_token_signer,
    ):
        mock_from_file.return_value = {
            "key_file": "/tmp/key.pem",
            "pass_phrase": "secret",
            "security_token_file": "/tmp/token",
            "tenancy": "tenancy",
            "user": "user",
            "fingerprint": "fingerprint",
            "region": "us-phoenix-1",
        }
        mock_exists.return_value = True
        mock_load_private_key.return_value = "private-key"
        mock_security_token_signer.return_value = "security-signer"

        with patch("builtins.open", mock_open(read_data="token-value")):
            config, signer = _get_config_and_signer()

        assert signer == "security-signer"
        assert config["additional_user_agent"] == USER_AGENT
        mock_load_private_key.assert_called_once_with("/tmp/key.pem", "secret")
        mock_security_token_signer.assert_called_once_with("token-value", "private-key")

    @patch("oracle.oci_http_mcp_server.server.oci.signer.Signer")
    @patch("oracle.oci_http_mcp_server.server.oci.signer.load_private_key_from_file")
    @patch("oracle.oci_http_mcp_server.server.os.path.exists")
    @patch("oracle.oci_http_mcp_server.server.oci.config.from_file")
    def test_get_config_and_signer_falls_back_to_api_key_signer(
        self,
        mock_from_file,
        mock_exists,
        mock_load_private_key,
        mock_signer,
    ):
        mock_from_file.return_value = {
            "key_file": "/tmp/key.pem",
            "pass_phrase": "secret",
            "tenancy": "tenancy",
            "user": "user",
            "fingerprint": "fingerprint",
            "region": "us-phoenix-1",
        }
        mock_exists.return_value = False
        mock_load_private_key.return_value = "private-key"
        mock_signer.return_value = "api-signer"

        _, signer = _get_config_and_signer()

        assert signer == "api-signer"
        mock_signer.assert_called_once_with(
            tenancy="tenancy",
            user="user",
            fingerprint="fingerprint",
            private_key_file_location="/tmp/key.pem",
            pass_phrase="secret",
        )


class TestHelpers:
    def test_merge_user_agent_appends_when_present(self):
        merged = _merge_user_agent({"user-agent": "custom-agent"})

        assert merged["user-agent"] == f"custom-agent {USER_AGENT}"

    def test_prepare_request_body_serializes_scalar_values(self):
        headers, json_body, data_body = _prepare_request_body(7, {"X-Test": "1"})

        assert headers["Content-Type"] == "application/json"
        assert json_body is None
        assert data_body == "7"

    def test_resolve_verify_ssl_prefers_explicit_value(self):
        assert _resolve_verify_ssl(False) is False

    def test_build_request_url_accepts_full_path_url(self):
        url = _build_request_url(
            path="https://example.com/path",
            service=None,
            region=None,
            endpoint=None,
            url=None,
            default_region=None,
        )

        assert url == "https://example.com/path"

    def test_build_request_url_uses_explicit_endpoint(self):
        url = _build_request_url(
            path="/20160918/instances",
            service=None,
            region=None,
            endpoint="https://iaas.us-phoenix-1.oraclecloud.com",
            url=None,
            default_region=None,
        )

        assert url == "https://iaas.us-phoenix-1.oraclecloud.com/20160918/instances"

    def test_build_request_url_requires_path(self):
        with pytest.raises(ValueError, match="path is required"):
            _build_request_url(
                path=None,
                service="iaas",
                region="us-phoenix-1",
                endpoint=None,
                url=None,
                default_region=None,
            )

    def test_build_request_url_requires_service_without_endpoint(self):
        with pytest.raises(ValueError, match="service is required"):
            _build_request_url(
                path="/20160918/instances",
                service=None,
                region="us-phoenix-1",
                endpoint=None,
                url=None,
                default_region=None,
            )

    def test_build_request_url_requires_region_when_missing_everywhere(self):
        with pytest.raises(ValueError, match="region is required"):
            _build_request_url(
                path="/20160918/instances",
                service="iaas",
                region=None,
                endpoint=None,
                url=None,
                default_region=None,
            )

    def test_decode_response_body_returns_none_for_empty_content(self):
        response = FakeResponse(headers={"Content-Type": "application/json"}, json_body=None, text="")
        response.content = b""

        assert _decode_response_body(response) is None


class TestMain:
    @patch("oracle.oci_http_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_with_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_env = {
            "ORACLE_MCP_HOST": "127.0.0.1",
            "ORACLE_MCP_PORT": "8181",
        }
        mock_getenv.side_effect = lambda key: mock_env.get(key)

        import oracle.oci_http_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with(transport="http", host="127.0.0.1", port=8181)

    @patch("oracle.oci_http_mcp_server.server.mcp.run")
    @patch("os.getenv")
    def test_main_without_host_and_port(self, mock_getenv, mock_mcp_run):
        mock_getenv.return_value = None

        import oracle.oci_http_mcp_server.server as server

        server.main()
        mock_mcp_run.assert_called_once_with()
