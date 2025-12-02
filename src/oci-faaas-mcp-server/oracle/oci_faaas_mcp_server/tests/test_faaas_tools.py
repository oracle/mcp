"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import sys
import types
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
    _append_items_from_response_data,
    _to_dict,
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

            assert result["fusion_environment_id"] == "env1"
            assert result["status"] == "ACTIVE"

    def test__to_dict_prefers_sdk_to_dict(self):
        obj = object()
        with patch(
            "oracle.oci_faaas_mcp_server.server.oci.util.to_dict",
            return_value={"ok": True},
        ):
            assert _to_dict(obj) == {"ok": True}

    def test__to_dict_dunder_dict_fallback(self):
        class Foo:
            def __init__(self):
                self.a = 1

        with patch(
            "oracle.oci_faaas_mcp_server.server.oci.util.to_dict",
            side_effect=Exception("boom"),
        ):
            res = _to_dict(Foo())
            assert res == {"a": 1}

    def test__to_dict_final_fallback(self):
        with patch(
            "oracle.oci_faaas_mcp_server.server.oci.util.to_dict",
            side_effect=Exception("boom"),
        ):
            assert _to_dict(42) == 42

    def test__append_items_variants_and_error(self):
        # Case: data has 'items' attribute
        class WithItems:
            def __init__(self):
                self.items = [{"id": 1}, {"id": 2}]

        acc = []
        _append_items_from_response_data(acc, WithItems())
        assert [x["id"] for x in acc] == [1, 2]

        # Case: data is a list
        acc = []
        _append_items_from_response_data(acc, [{"id": 3}])
        assert acc == [{"id": 3}]

        # Case: single object fallback (object without 'items' attribute)
        acc = []

        class Single:
            pass

        single = Single()
        with patch(
            "oracle.oci_faaas_mcp_server.server._to_dict", return_value={"id": 4}
        ):
            _append_items_from_response_data(acc, single)
        assert acc == [{"id": 4}]

        # Case: error path propagates
        acc = []
        with patch(
            "oracle.oci_faaas_mcp_server.server._to_dict", side_effect=Exception("x")
        ), pytest.raises(Exception):
            _append_items_from_response_data(acc, {"id": 5})

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
