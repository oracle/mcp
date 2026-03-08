"""
Copyright (c) 2026, Oracle and/or its affiliates.
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
                ops = result.get("operations", result) if isinstance(result, dict) else result or []

                # only public callable functions should be listed
                names = [op["name"] if isinstance(op, dict) else getattr(op, "name", None) for op in ops]
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

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
        ):
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

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results"
            ) as mock_pager,
        ):
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())
            mock_pager.return_value = FakeResponse([{"name": "a"}, {"name": "b"}, {"name": "c"}])

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

    @pytest.mark.asyncio
    async def test_invoke_oci_api_dns_get_zone_records_uses_paginator(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-789"}

        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            # non-list operation name but supports pagination via page/limit params (DNS style)
            def get_zone_records(self, zone_name, page=None, limit=None):
                return FakeResponse([{"name": "first"}])

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results"
            ) as mock_pager,
        ):
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())
            mock_pager.return_value = FakeResponse(
                [{"name": "a"}, {"name": "b"}, {"name": "c"}, {"name": "d"}]
            )

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_zone_records",
                            "params": {"zone_name": "do-not-delete-me-testing-zone.example"},
                        },
                    )
                ).data

                assert result["client"] == "x.y.FakeClient"
                assert result["operation"] == "get_zone_records"
                assert isinstance(result["data"], list)
                assert len(result["data"]) == 4

    @pytest.mark.asyncio
    async def test_invoke_oci_api_summarize_prefix_uses_paginator(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-101"}

        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            # summarize_* should trigger pagination even without page/limit
            def summarize_metrics(self, compartment_id):
                return FakeResponse([{"sum": 1}])

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results"
            ) as mock_pager,
        ):
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())
            mock_pager.return_value = FakeResponse([{"sum": 10}, {"sum": 20}])

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "summarize_metrics",
                            "params": {"compartment_id": "ocid1.compartment..abc"},
                        },
                    )
                ).data

                assert result["client"] == "x.y.FakeClient"
                assert result["operation"] == "summarize_metrics"
                assert isinstance(result["data"], list)
                assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_invoke_oci_api_dns_get_rr_set_allowlist_uses_paginator(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-102"}

        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            # DNS-style op name; include page/limit in signature so pagination is detected
            def get_rr_set(self, zone_name_or_id, domain, rtype, page=None, limit=None):
                return FakeResponse([{"rr": "first"}])

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results"
            ) as mock_pager,
        ):
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())
            mock_pager.return_value = FakeResponse([{"rr": 1}, {"rr": 2}, {"rr": 3}])

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_rr_set",
                            "params": {
                                "zone_name_or_id": "do-not-delete-me-testing-zone.example",
                                "domain": "www.do-not-delete-me-testing-zone.example",
                                "rtype": "A",
                            },
                        },
                    )
                ).data

                assert result["client"] == "x.y.FakeClient"
                assert result["operation"] == "get_rr_set"
                assert isinstance(result["data"], list)
                assert len(result["data"]) == 3

    @pytest.mark.asyncio
    async def test_invoke_oci_api_non_paginated_does_not_use_paginator(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-103"}

        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            # non-list op, no page/limit params; should not paginate
            def get_config(self, id):
                return FakeResponse({"ok": True, "id": id})

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results"
            ) as mock_pager,
        ):
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_config",
                            "params": {"id": "abc"},
                        },
                    )
                ).data

                # ensure paginator was not invoked
                mock_pager.assert_not_called()
                assert result["client"] == "x.y.FakeClient"
                assert result["operation"] == "get_config"
                assert result["data"] == {"ok": True, "id": "abc"}

    @pytest.mark.asyncio
    async def test_invoke_oci_api_dns_kwargs_records_uses_paginator(self):
        # Removed: server no longer treats '**kwargs + records' name pattern as implicitly paginated.
        pass

    @pytest.mark.asyncio
    async def test_invoke_oci_api_var_kw_non_dns_does_not_use_paginator(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-105"}

        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

            # accepts **kwargs but operation name doesn't indicate records/rrset
            def get_widget(self, widget_id, **kwargs):  # noqa: ARG002
                return FakeResponse({"id": widget_id, "ok": True})

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as mock_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as mock_cfg,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results"
            ) as mock_pager,
        ):
            mock_import.return_value = fake_module
            mock_cfg.return_value = ({}, object())

            async with Client(mcp) as client:
                result = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_widget",
                            "params": {"widget_id": "w1"},
                        },
                    )
                ).data

                # ensure paginator was not invoked for **kwargs-only non-DNS-like method
                mock_pager.assert_not_called()
                assert result["client"] == "x.y.FakeClient"
                assert result["operation"] == "get_widget"
                assert result["data"] == {"id": "w1", "ok": True}
