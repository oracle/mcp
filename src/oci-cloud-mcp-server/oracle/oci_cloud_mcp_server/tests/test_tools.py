"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import importlib.metadata
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastmcp import Client
from oracle.oci_cloud_mcp_server import __project__
from oracle.oci_cloud_mcp_server.server import mcp

__version__ = importlib.metadata.version(__project__)
user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
USER_AGENT = f"{user_agent_name}/{__version__}"


class TestCloudSdkTools:
    @pytest.mark.asyncio
    async def test_list_client_operations_with_fake_client(self):
        # build a fake client class with a couple of methods
        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            def get_thing(self, id):
                return id

            def _hidden(self):
                return None

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import:
            mock_import.return_value = fake_module

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "list_client_operations",
                        {"client_fqn": "x.y.FakeClient"},
                    )
                ).data
                ops = (
                    result.get("operations", result)
                    if isinstance(result, dict)
                    else result or []
                )

                # only public callable functions should be listed
                names = [
                    op["name"] if isinstance(op, dict) else getattr(op, "name", None)
                    for op in ops
                ]
                names = [n for n in names if n]
                assert "get_thing" in names
                assert "_hidden" not in names

    @pytest.mark.asyncio
    async def test_invoke_oci_api_non_list_success(self):
        # fake OCI-like response
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-123"}

        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            def get_thing(self, id):
                return FakeResponse({"id": id, "value": "ok"})

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with patch(
            "oracle.oci_cloud_mcp_server.server.import_module"
        ) as mock_import, patch(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer"
        ) as mock_cfg:
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_thing",
                            "params": {"id": "abc"},
                        },
                    )
                ).data

                assert result["client"] == "x.y.FakeClient"
                assert result["operation"] == "get_thing"
                assert result["params"] == {"id": "abc"}
                assert result["opc_request_id"] == "req-123"
                assert result["data"] == {"id": "abc", "value": "ok"}

    @pytest.mark.asyncio
    async def test_invoke_oci_api_list_uses_paginator(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-456"}

        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            # existence of a list_* method is enough; paginator will be patched
            def list_things(self, compartment_id):
                return FakeResponse([{"name": "x"}])

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with patch(
            "oracle.oci_cloud_mcp_server.server.import_module"
        ) as mock_import, patch(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer"
        ) as mock_cfg, patch(
            "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results"
        ) as mock_pager:
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())
            mock_pager.return_value = FakeResponse(
                [{"name": "a"}, {"name": "b"}, {"name": "c"}]
            )

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "list_things",
                            "params": {"compartment_id": "ocid1.compartment..xyz"},
                        },
                    )
                ).data

                assert result["client"] == "x.y.FakeClient"
                assert result["operation"] == "list_things"
                assert isinstance(result["data"], list)
                assert len(result["data"]) == 3
