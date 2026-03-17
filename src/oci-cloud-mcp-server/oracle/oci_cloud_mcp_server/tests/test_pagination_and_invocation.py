from types import SimpleNamespace

import pytest
from fastmcp import Client
from oracle.oci_cloud_mcp_server.server import (
    _call_with_pagination_if_applicable,
    _import_client,
    _supports_pagination,
    mcp,
)


class TestSupportsPaginationAllowlistIntrospectionFailure:
    def test_allowlist_true_when_signature_introspection_fails(self, monkeypatch):
        # force inspect.signature to raise to exercise exception path

        def boom_sig(obj):
            raise Exception("no sig")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.signature", boom_sig)

        def fn(**kwargs):  # noqa: ARG001
            """
            Retrieve records.

            :param str page: pagination token
            :param int limit: max items
            """
            return None

        # operation is on known allowlist ("get_rr_set")
        assert _supports_pagination(fn, "get_rr_set") is True


class TestInvokeErrorPaths:
    @pytest.mark.asyncio
    async def test_missing_operation_returns_error_in_payload(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

        # patch module import and config/signer bootstrap
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "x.y.FakeClient",
                        "operation": "does_not_exist",
                        "params": {},
                    },
                )
            ).data

        assert "error" in res
        assert "not found" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_attribute_present_but_not_callable_returns_error(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                self.get_thing = 123  # not callable

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "x.y.FakeClient",
                        "operation": "get_thing",
                        "params": {},
                    },
                )
            ).data

        assert "error" in res
        assert "not callable" in res["error"].lower()


class TestImportClientHappyPath:
    def test_import_client_constructs_instance_with_signer(self, monkeypatch):
        constructed = {"called": False, "args": None, "kwargs": None}

        class GoodClient:
            def __init__(self, config, signer=None, **kwargs):
                constructed["called"] = True
                constructed["args"] = (config,)
                constructed["kwargs"] = {"signer": signer, **kwargs}

        # module with GoodClient
        fake_mod = SimpleNamespace(GoodClient=GoodClient)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_mod)
        # basic config/signer
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({"x": 1}, object()),
        )

        inst = _import_client("x.y.GoodClient")
        assert isinstance(inst, GoodClient)
        assert constructed["called"] is True
        assert constructed["args"][0] == {"x": 1}
        assert "signer" in constructed["kwargs"]


# Removed tests for DNS-style '**kwargs + records' pagination heuristic.
# The server no longer treats var-kw only methods with names like '*records'
# as implicitly paginated without explicit page/limit or documented kwargs.


class TestPaginatorHeadersWithGet:
    def test_paginator_headers_with_get_yields_request_id(self, monkeypatch):
        class Resp:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-123"}

        def fake_pager(method, **kwargs):  # noqa: ARG001
            return Resp([1, 2, 3])

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results",
            fake_pager,
        )

        def list_things():
            return Resp([9])

        data, opc = _call_with_pagination_if_applicable(list_things, {}, "list_things")
        assert data == [1, 2, 3]
        assert opc == "req-123"


class TestCallWithPaginationTypeErrorFallback:
    def test_typeerror_fallback_moves_src_to_dst(self):
        # when both 'vcn_details' (src) and 'create_vcn_details' (dst) are present,
        # Python raises a TypeError for the unexpected 'vcn_details' kw. The helper
        # should catch this and retry with only the dst kw.
        class Resp:
            def __init__(self, data):
                self.data = data
                self.headers = {}

        def create_vcn(create_vcn_details):  # noqa: ARG001
            return Resp({"ok": True})

        # include both src and dst to force the TypeError path first, then fallback retry
        data, opc = _call_with_pagination_if_applicable(
            create_vcn,
            {"vcn_details": {"x": 1}, "create_vcn_details": {"x": 1}},
            "create_vcn",
        )
        assert data == {"ok": True}
        assert opc is None


class TestSupportsPaginationAdditional:
    def test_known_allowlist_variant_get_rr_set_true(self):
        def fn(zone_name_or_id, domain, rtype, page=None, limit=None, **kwargs):  # noqa: ARG001
            return None

        assert _supports_pagination(fn, "get_rr_set") is True

    def test_docstring_getdoc_raises_fallback_false(self, monkeypatch):
        def get_widget(widget_id):  # noqa: ARG001
            """A simple getter with no pagination."""
            return None

        # cause the internal docstring inspection helper to encounter an exception
        def boom(obj):
            raise Exception("doc error")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.getdoc", boom)

        # no list_/summarize_ prefix, no page/limit, no **kwargs DNS-like name -> False
        assert _supports_pagination(get_widget, "get_widget") is False


class TestInvokeTypeErrorPropagation:
    @pytest.mark.asyncio
    async def test_invoke_typeerror_falls_through_and_errors(self, monkeypatch):
        # create_vcn expects an unexpected kw ('create_vcn_details'), which triggers TypeError.
        # _call_with_pagination_if_applicable won't alias because the error kw is not the src,
        # so the TypeError bubbles to invoke_oci_api where the last-chance alias block is skipped
        # (src not present) and the tool returns an error payload.
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def create_vcn(self, foo):  # noqa: ARG002
                return {"ok": True}

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "x.y.FakeClient",
                        "operation": "create_vcn",
                        "params": {"vcn_details": {"x": 1}},
                    },
                )
            ).data

        assert "error" in res
        assert "unexpected keyword" in res["error"].lower()
