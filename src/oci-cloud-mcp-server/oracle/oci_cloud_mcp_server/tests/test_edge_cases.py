from types import SimpleNamespace

import oci
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from oracle.oci_cloud_mcp_server import server
from oracle.oci_cloud_mcp_server.sdk_catalog import SdkResolutionError
from oracle.oci_cloud_mcp_server.tests.sdk_fixtures import install_catalog
from oracle.oci_cloud_mcp_server.server import (
    _call_with_pagination_if_applicable,
    _coerce_params_to_oci_models,
    _construct_model_from_mapping,
    _import_client,
    _resolve_model_class,
    _serialize_oci_data,
    _supports_pagination,
    mcp,
)


def fixture_model(name, fields, *, fails=False):
    def init(self, **kwargs):
        if fails:
            raise RuntimeError("ctor fail")
        self.kw = self._data = dict(kwargs)
    return type(name, (), {"__init__": init, "swagger_types": fields})


async def invoke_fixture(monkeypatch, client_class, operation, params=None):
    identity = f"oci.fake.{client_class.__name__}"
    install_catalog(monkeypatch, clients={identity: client_class})
    monkeypatch.setattr(server, "_get_config_and_signer", lambda: ({}, object()))
    async with Client(mcp) as client:
        payload = {"client_fqn": identity, "operation": operation}
        if params is not None:
            payload["params"] = params
        return (await client.call_tool("invoke_oci_api", payload)).data


class TestCandidateSwaggerFilter:
    def test_candidate_ctor_receives_only_declared_fields(self, monkeypatch):
        MyDetails = fixture_model("MyDetails", {"a": "int"})
        install_catalog(monkeypatch, models={"oci.core.models.MyDetails": MyDetails})
        inst = _construct_model_from_mapping({"a": 1, "b": 2}, "oci.core", ["MyDetails"])
        assert isinstance(inst, MyDetails)
        assert inst.kw == {"a": 1}

class TestCoerceTopLevelConfigSuffix:
    def test_top_level_config_suffix_constructs_model(self, monkeypatch):
        ShapeConfig = fixture_model("ShapeConfig", {"x": "int"})
        install_catalog(monkeypatch, models={"oci.core.models.ShapeConfig": ShapeConfig})
        out = _coerce_params_to_oci_models("oci.core.ComputeClient", "op", {"shape_config": {"x": 1}})
        assert isinstance(out["shape_config"], ShapeConfig)
        assert out["shape_config"].kw == {"x": 1}

class TestInvokePreNormalize:
    @pytest.mark.asyncio
    async def test_invoke_pre_normalizes_create_details_before_coerce(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass
            def create_vcn(self, create_vcn_details):
                return SimpleNamespace(data={"ok": True, "k": create_vcn_details["k"]},
                                       headers={"opc-request-id": "pre-norm-1"})
        result = await invoke_fixture(monkeypatch, FakeClient, "create_vcn", {"vcn_details": {"k": 42}})
        assert result["opc_request_id"] == "pre-norm-1"
        assert result["data"] == {"ok": True, "k": 42}

class TestListClientOperationsLoadErrorTool:
    @pytest.mark.asyncio
    async def test_approved_class_load_failure_is_a_tool_error(self, monkeypatch):
        def fail(entry):
            raise SdkResolutionError("cataloged class unavailable")
        monkeypatch.setattr(server._catalog, "load_client", fail)
        async with Client(mcp) as client:
            with pytest.raises(ToolError, match="cataloged class unavailable"):
                await client.call_tool("list_client_operations", {"client_fqn": "oci.core.ComputeClient"})

class TestInvokePlainListReturn:
    @pytest.mark.asyncio
    async def test_invoke_returns_plain_list_not_response(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass
            def get_list(self):
                return [10, 20, 30]
        result = await invoke_fixture(monkeypatch, FakeClient, "get_list")
        assert result["opc_request_id"] is None
        assert result["data"] == [10, 20, 30]

class TestConstructFqnValidation:
    def test_construct_model_from_fqn_rejects_non_oci_namespace(self):
        with pytest.raises(SdkResolutionError, match="cataloged"):
            _construct_model_from_mapping({"__class_fqn": "mymod9.Kiwi", "a": 7}, None, [])

class TestConstructModelFqnAttrNotClass:
    def test_non_model_export_is_rejected(self):
        with pytest.raises(SdkResolutionError, match="cataloged"):
            _construct_model_from_mapping({"__model_fqn": "oci.core.ComputeClient", "a": 1}, None, [])

class TestConstructModelSimpleNameNotClass:
    def test_explicit_unknown_short_name_is_rejected(self):
        with pytest.raises(SdkResolutionError, match="cataloged"):
            _construct_model_from_mapping({"__model": "NotAModel", "a": 1}, "oci.core", [])

class TestListClientOperationsGetdocRaises:
    @pytest.mark.asyncio
    async def test_getdoc_raises_summary_empty(self, monkeypatch):
        class KlassClient:
            def foo(self, a):
                """Doc first line."""
                return 1
        install_catalog(monkeypatch, clients={"oci.fake.KlassClient": KlassClient})
        original = server.inspect.getdoc
        def getdoc(obj):
            if obj is KlassClient.foo:
                raise RuntimeError("doc boom")
            return original(obj)
        monkeypatch.setattr(server.inspect, "getdoc", getdoc)
        async with Client(mcp) as client:
            result = (await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.KlassClient"})).data
        assert result["operations"][0]["name"] == "foo"
        assert result["operations"][0]["summary"] == ""

class TestConstructExplicitClassKey:
    def test_construct_model_with_class_key_uses_approved_constructor(self, monkeypatch):
        Foo = fixture_model("Foo", {"a": "int"})
        install_catalog(monkeypatch, models={"oci.core.models.Foo": Foo})
        first = _construct_model_from_mapping({"__class": "Foo", "a": 1}, "oci.core", [])
        second = _construct_model_from_mapping({"__class": "Foo", "a": 2}, "oci.core", [])
        assert isinstance(first, Foo) and isinstance(second, Foo)
        assert first.kw == {"a": 1}
        assert second.kw == {"a": 2}

class TestCreateUpdateCandidateClasses:
    @pytest.mark.parametrize("operation,name,value", [
        ("create_vcn", "CreateVcnDetails", 1), ("update_vcn", "UpdateVcnDetails", 2),
    ])
    def test_candidate_class_used_and_key_renamed(self, monkeypatch, operation, name, value):
        model = fixture_model(name, {"a": "int"})
        install_catalog(monkeypatch, models={f"oci.core.models.{name}": model})
        out = _coerce_params_to_oci_models("oci.core.ComputeClient", operation, {"vcn_details": {"a": value}})
        key = f"{operation}_details"
        assert key in out and "vcn_details" not in out
        assert isinstance(out[key], model)
        assert out[key].kw == {"a": value}

class TestListElementClassFqn:
    def test_list_item_with_non_oci_class_fqn_is_rejected(self):
        with pytest.raises(SdkResolutionError, match="cataloged"):
            _coerce_params_to_oci_models("oci.core.ComputeClient", "op", {
                "items": [{"__class_fqn": "mymod4.Bar", "z": 9}, {"plain": True}],
            })

class TestListPassThroughNonDict:
    def test_list_of_scalars_passthrough(self):
        out = _coerce_params_to_oci_models("oci.core.ComputeClient", "op", {"items": [1, 2, 3]})
        assert out["items"] == [1, 2, 3]

class TestFqnConstructor:
    def test_construct_model_from_fqn_uses_approved_constructor(self, monkeypatch):
        Apple = fixture_model("Apple", {"a": "int"})
        install_catalog(monkeypatch, models={"oci.core.models.Apple": Apple})
        inst = _construct_model_from_mapping({"__model_fqn": "oci.core.models.Apple", "a": 10}, None, [])
        assert isinstance(inst, Apple)
        assert inst.kw == {"a": 10}

class TestPreAliasCreatePath:
    def test_pre_alias_in_call_with_pagination_succeeds_without_fallback(self):
        # method expects create_vcn_details but we pass vcn_details;
        # pre-aliasing in _call_with_pagination_if_applicable should handle it.
        class Resp:
            def __init__(self, data):
                self.data = data
                self.headers = {}

        def create_vcn(create_vcn_details):  # noqa: ARG001
            return Resp({"ok": True})

        data, opc, has_more = _call_with_pagination_if_applicable(
            create_vcn,
            {"vcn_details": {"x": 1}},
            "create_vcn",
        )
        assert data == {"ok": True}
        assert opc is None
        assert has_more is False

class TestListClientOpsHiddenOnly:
    @pytest.mark.asyncio
    async def test_class_with_only_hidden_methods_returns_empty(self, monkeypatch):
        class KlassClient:
            def _private(self):
                return 1
        install_catalog(monkeypatch, clients={"oci.fake.KlassClient": KlassClient})
        async with Client(mcp) as client:
            result = (await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.KlassClient"})).data
        assert result == {"client": "oci.fake.KlassClient", "operations": []}

class TestResolveModelClassSuccess:
    def test_resolve_model_class_returns_approved_class(self, monkeypatch):
        ModelX = fixture_model("ModelX", {})
        install_catalog(monkeypatch, models={"oci.core.models.ModelX": ModelX})
        assert _resolve_model_class("oci.core", "ModelX") is ModelX

class TestDeclaredNestedType:
    def test_nested_schema_selects_the_approved_model(self, monkeypatch):
        InstanceDetails = fixture_model("InstanceDetails", {"shape_config": "InstanceShapeConfig"})
        InstanceShapeConfig = fixture_model("InstanceShapeConfig", {"ocpus": "int"})
        install_catalog(monkeypatch, models={
            "oci.core.models.InstanceDetails": InstanceDetails,
            "oci.core.models.InstanceShapeConfig": InstanceShapeConfig,
        })
        out = _coerce_params_to_oci_models("oci.core.ComputeClient", "launch_instance", {
            "instance_details": {"shape_config": {"ocpus": 1}},
        })
        inst = out["instance_details"]
        assert isinstance(inst, InstanceDetails)
        assert isinstance(inst.kw["shape_config"], InstanceShapeConfig)
        assert inst.kw["shape_config"].kw["ocpus"] == 1

class TestDunderMainExecution:
    def test_running_module_as_main_calls_mcp_run(self, monkeypatch):
        # patch FastMCP.run to a no-op to safely execute __main__ guard
        import runpy
        import sys

        from fastmcp import FastMCP

        called = {"args": None, "kwargs": None}

        def fake_run(self, *args, **kwargs):
            called["args"] = args
            called["kwargs"] = kwargs

        monkeypatch.setattr(FastMCP, "run", fake_run, raising=False)
        # force default branch in main (no HTTP host/port)
        monkeypatch.delenv("ORACLE_MCP_HOST", raising=False)
        monkeypatch.delenv("ORACLE_MCP_PORT", raising=False)

        # remove pre-imported module to avoid runpy RuntimeWarning
        monkeypatch.delitem(sys.modules, "oracle.oci_cloud_mcp_server.server", raising=False)

        runpy.run_module("oracle.oci_cloud_mcp_server.server", run_name="__main__", alter_sys=True)
        assert called["args"] == ()
        assert called["kwargs"] == {}

class TestExplicitModelConstructorFailure:
    def test_explicit_model_constructor_failure_propagates(self, monkeypatch):
        BoomModel = fixture_model("BoomModel", {"a": "int"}, fails=True)
        install_catalog(monkeypatch, models={"oci.core.models.BoomModel": BoomModel})
        with pytest.raises(RuntimeError, match="ctor fail"):
            _construct_model_from_mapping({"__model": "BoomModel", "a": 1}, "oci.core", [])

class TestCandidateConstructorFailure:
    def test_candidate_constructor_failure_does_not_become_raw_success(self, monkeypatch):
        Candidate = fixture_model("Candidate", {"x": "int"}, fails=True)
        install_catalog(monkeypatch, models={"oci.core.models.Candidate": Candidate})
        with pytest.raises(RuntimeError, match="ctor fail"):
            _construct_model_from_mapping({"x": 1}, "oci.core", ["Candidate"])

class TestSourceDetailsSuffixCoercion:
    def test_source_details_suffix_constructs(self, monkeypatch):
        SourceDetails = fixture_model("SourceDetails", {"a": "int"})
        install_catalog(monkeypatch, models={"oci.core.models.SourceDetails": SourceDetails})
        out = _coerce_params_to_oci_models("oci.core.ComputeClient", "op", {"source_details": {"a": 1}})
        assert isinstance(out["source_details"], SourceDetails)
        assert out["source_details"].kw == {"a": 1}

class TestListItemWithModelNameHint:
    def test_list_items_with_model_hint_constructs(self, monkeypatch):
        Foo = fixture_model("Foo", {"a": "int"})
        install_catalog(monkeypatch, models={"oci.core.models.Foo": Foo})
        out = _coerce_params_to_oci_models("oci.core.ComputeClient", "op", {
            "items": [{"__model": "Foo", "a": 5}, {"b": 6}],
        })
        assert isinstance(out["items"][0], Foo)
        assert out["items"][0].kw == {"a": 5}
        assert out["items"][1] == {"b": 6}

class TestFinalAliasingNonDict:
    def test_alias_renames_non_dict_value(self):
        out = _coerce_params_to_oci_models("oci.core.ComputeClient", "create_vcn", {"vcn_details": [1, 2]})
        assert "create_vcn_details" in out and "vcn_details" not in out
        assert out["create_vcn_details"] == [1, 2]

class TestInvokeTupleSerialization:
    @pytest.mark.asyncio
    async def test_invoke_serializes_tuple_data_to_list(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass
            def get_tuple(self):
                return SimpleNamespace(data=(1, 2, 3), headers={})
        result = await invoke_fixture(monkeypatch, FakeClient, "get_tuple", {})
        assert result["data"] == [1, 2, 3]

class TestSerializeToDictReturnsNonJsonable:
    def test_serialize_when_to_dict_returns_non_jsonable_object(self, monkeypatch):
        # if oci.util.to_dict returns a non-JSON-serializable object, ensure fallback to str
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        class P:
            pass

        # force to_dict to return a plain instance which is not JSON serializable
        monkeypatch.setattr(_oci.util, "to_dict", lambda data: P(), raising=False)
        out = _serialize_oci_data(object())
        import json as _json

        # should be a string that can be dumped to JSON
        _json.dumps(out)
        assert isinstance(out, str)
        assert "P" in out

class TestInvokeGenericException:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_handles_generic_exception(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass
            def get_crash(self):
                raise RuntimeError("boom")
        result = await invoke_fixture(monkeypatch, FakeClient, "get_crash", {})
        assert "boom" in result["error"]

class TestListPaginatorHeadersMissing:
    def test_list_headers_object_without_get(self):
        # ensure list_* branch handles headers object without 'get'
        class Resp:
            def __init__(self, data):
                self.data = data
                self.headers = object()  # lacks .get

        def list_things():
            return Resp([1, 2])

        data, opc, has_more = _call_with_pagination_if_applicable(list_things, {}, "list_things")
        assert data == [1, 2]
        assert opc is None
        assert has_more is False

class TestImportClientBadCtor:
    def test_approved_client_constructor_invalid_signature_raises(self, monkeypatch):
        class BadClient:
            def __init__(self):
                pass
        monkeypatch.setattr(server, "_get_config_and_signer", lambda: ({}, object()))
        with pytest.raises(TypeError):
            _import_client(BadClient)

class TestInvokeDefaultParams:
    @pytest.mark.asyncio
    async def test_invoke_with_params_omitted_defaults_to_empty(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass
            def get_plain(self):
                return {"ok": True}
        result = await invoke_fixture(monkeypatch, FakeClient, "get_plain")
        assert result["data"] == {"ok": True}
        assert result["params"] == {}

class TestConstructModelFieldFilter:
    def test_short_hint_constructor_receives_declared_fields(self, monkeypatch):
        MyModel2 = fixture_model("MyModel2", {"a": "int"})
        install_catalog(monkeypatch, models={"oci.core.models.MyModel2": MyModel2})
        inst = _construct_model_from_mapping({"__model": "MyModel2", "a": 1, "b": 2}, "oci.core", [])
        assert isinstance(inst, MyModel2)
        assert inst.kw == {"a": 1}

class TestInvokeNonListHeadersNoGet:
    @pytest.mark.asyncio
    async def test_non_list_response_headers_missing_get(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass
            def get(self):
                return SimpleNamespace(data={"ok": True}, headers=object())
        result = await invoke_fixture(monkeypatch, FakeClient, "get")
        assert result["opc_request_id"] is None
        assert result["data"] == {"ok": True}

class TestFqnConstructorFailure:
    def test_fqn_constructor_failure_propagates(self, monkeypatch):
        Boom = fixture_model("Boom", {"a": "int"}, fails=True)
        install_catalog(monkeypatch, models={"oci.core.models.Boom": Boom})
        with pytest.raises(RuntimeError, match="ctor fail"):
            _construct_model_from_mapping({"__model_fqn": "oci.core.models.Boom", "a": 1}, None, [])

class TestListClientOperationsIgnoreNewHelpers:
    @pytest.mark.asyncio
    async def test_runtime_helper_cannot_expand_catalog_operations(self, monkeypatch):
        class KlassClient:
            def foo(self):
                return 1
        install_catalog(monkeypatch, clients={"oci.fake.KlassClient": KlassClient})
        monkeypatch.setattr(KlassClient, "extra_helper", lambda self: 2, raising=False)
        async with Client(mcp) as client:
            result = (await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.KlassClient"})).data
        assert [operation["name"] for operation in result["operations"]] == ["foo"]

class TestSupportsPaginationHeuristics:
    def test_supports_pagination_list_prefix_without_contract_false(self):
        def list_things():
            pass

        assert _supports_pagination(list_things, "list_things") is False

    def test_supports_pagination_summarize_prefix_without_contract_false(self):
        def summarize_metrics():
            pass

        assert _supports_pagination(summarize_metrics, "summarize_metrics") is False

    def test_supports_pagination_signature_page_limit_true(self):
        def get_zone_records(zone_name, page=None, limit=None):  # noqa: ARG001
            pass

        assert _supports_pagination(get_zone_records, "get_zone_records") is True

    def test_supports_pagination_default_false(self):
        def get_config(id):  # noqa: ARG001
            pass

        assert _supports_pagination(get_config, "get_config") is False

    def test_supports_pagination_expected_kwargs_in_source_true(self):
        # simulate SDK-generated expected_kwargs captured in source for **kwargs-only method
        def get_zone_records(**kwargs):  # noqa: ARG001
            expected_kwargs = ["if_none_match", "limit", "page"]  # noqa: F841
            return None

        assert _supports_pagination(get_zone_records, "get_zone_records") is True

    def test_supports_pagination_docstring_mentions_page_limit_false(self):
        def get_zone_records(**kwargs):  # noqa: ARG001
            """
            Retrieve zone records.

            :param str page: pagination token
            :param int limit: maximum number of items to return
            """
            return None

        assert _supports_pagination(get_zone_records, "get_zone_records") is False
