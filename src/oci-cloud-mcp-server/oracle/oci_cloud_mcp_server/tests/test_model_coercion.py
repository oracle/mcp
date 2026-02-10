"""Tests for coercing complex OCI model params and kwarg renaming."""

import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from fastmcp import Client
from oracle.oci_cloud_mcp_server.server import mcp


class TestModelCoercion:
    def test_create_operation_coerces_model_and_renames_key(self):
        # fake OCI-like response
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-789"}

        # models module with a Create*Details class
        class CreateVcnDetails:
            def __init__(self, **kwargs):
                # emulate SDK model storing provided fields
                self._data = dict(kwargs)

        # fake client whose method expects create_vcn_details specifically
        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            def create_vcn(self, create_vcn_details):
                # ensure type is the constructed model
                assert isinstance(create_vcn_details, CreateVcnDetails)
                return FakeResponse(
                    {
                        "ok": True,
                        "cidr_block": create_vcn_details._data.get("cidr_block"),
                        "display_name": create_vcn_details._data.get("display_name"),
                    }
                )

        fake_client_module = SimpleNamespace(FakeClient=FakeClient)
        fake_models_module = SimpleNamespace(CreateVcnDetails=CreateVcnDetails)

        def import_side_effect(name):
            # return appropriate fake module depending on requested import
            if name == "x.y":
                return fake_client_module
            if name == "x.y.models":
                return fake_models_module
            raise ImportError(name)

        with (
            patch(
                "oracle.oci_cloud_mcp_server.server.import_module",
                side_effect=import_side_effect,
            ),
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
            mock_cfg.return_value = ({}, object())

            # note: We intentionally pass "vcn_details" (missing the "create_")
            # the server should rename it to "create_vcn_details" and coerce dict to model.
            payload = {
                "client_fqn": "x.y.FakeClient",
                "operation": "create_vcn",
                "params": {
                    "vcn_details": {
                        "cidr_block": "10.0.0.0/16",
                        "display_name": "my-vcn",
                    }
                },
            }

            async def run():
                async with Client(mcp) as client:
                    return (await client.call_tool("invoke_oci_api", payload)).data

            result = asyncio.run(run())
            print("TOOL RESULT:", result)

            assert result["client"] == "x.y.FakeClient"
            assert result["operation"] == "create_vcn"
            # original params echoed back
            assert "vcn_details" in result["params"]
            # data should come from FakeResponse and be serialized to dict
            assert result["data"]["ok"] is True
            assert result["data"]["cidr_block"] == "10.0.0.0/16"
            assert result["data"]["display_name"] == "my-vcn"
