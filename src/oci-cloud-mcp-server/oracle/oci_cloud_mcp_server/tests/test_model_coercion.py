"""Tests for coercing complex OCI model params and kwarg renaming."""

import asyncio
import oci

from oracle.oci_cloud_mcp_server.tests.sdk_fixtures import install_catalog

from fastmcp import Client
from oracle.oci_cloud_mcp_server.server import mcp


class TestModelCoercion:
    def test_create_operation_coerces_model_and_renames_key(self, monkeypatch):
        # fake OCI-like response
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-789"}

        CreateVcnDetails = oci.core.models.CreateVcnDetails

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
                        "cidr_block": create_vcn_details.cidr_block,
                        "display_name": create_vcn_details.display_name,
                    }
                )

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient},
                        models={"oci.fake.models.CreateVcnDetails": CreateVcnDetails})
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server._get_config_and_signer", lambda: ({}, object()))

        # note: We intentionally pass "vcn_details" (missing the "create_")
        # the server should rename it to "create_vcn_details" and coerce dict to model.
        payload = {
            "client_fqn": "oci.fake.FakeClient",
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

        assert result["client"] == "oci.fake.FakeClient"
        assert result["operation"] == "create_vcn"
        # original params echoed back
        assert "vcn_details" in result["params"]
        # data should come from FakeResponse and be serialized to dict
        assert result["data"]["ok"] is True
        assert result["data"]["cidr_block"] == "10.0.0.0/16"
        assert result["data"]["display_name"] == "my-vcn"
