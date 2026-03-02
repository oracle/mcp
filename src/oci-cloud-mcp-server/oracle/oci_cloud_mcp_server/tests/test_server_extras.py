"""
Additional tests to increase coverage for cloud MCP server helpers and edge cases.
Copyright (c) 2026, Oracle
Licensed under the UPL v1.0 https://oss.oracle.com/licenses/upl
"""

from types import SimpleNamespace
from unittest.mock import mock_open, patch

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_cloud_mcp_server.server import (
    _ADDITIONAL_UA,
    _align_params_to_signature,
    _coerce_params_to_oci_models,
    _get_config_and_signer,
    _import_client,
    _import_models_module_from_client_fqn,
    _serialize_oci_data,
    list_client_operations,
    main,
    mcp,
)


class TestGetConfigAndSigner:
    def test_uses_security_token_signer_when_token_exists(self):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/path/to/token",
        }

        with (
            patch("oracle.oci_cloud_mcp_server.server.oci.config.from_file") as m_from,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file") as m_loadkey,
            patch("oracle.oci_cloud_mcp_server.server.oci.auth.signers.SecurityTokenSigner") as m_sts,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.Signer") as m_signer,
            patch("oracle.oci_cloud_mcp_server.server.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="TOKEN123")),
        ):
            m_from.return_value = dict(cfg)  # function mutates to add UA
            m_loadkey.return_value = object()
            sentinel_signer = object()
            m_sts.return_value = sentinel_signer

            out_cfg, signer = _get_config_and_signer()

            assert out_cfg["additional_user_agent"] == _ADDITIONAL_UA
            assert signer is sentinel_signer
            # should not fall back to API key signer when token path exists
            m_signer.assert_not_called()

    def test_falls_back_to_api_key_signer_when_no_token(self):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/path/to/token",
        }

        with (
            patch("oracle.oci_cloud_mcp_server.server.oci.config.from_file") as m_from,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file") as m_loadkey,
            patch("oracle.oci_cloud_mcp_server.server.oci.auth.signers.SecurityTokenSigner") as m_sts,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.Signer") as m_signer,
            patch("oracle.oci_cloud_mcp_server.server.os.path.exists", return_value=False),
        ):
            m_from.return_value = dict(cfg)
            m_loadkey.return_value = object()
            sentinel_signer = object()
            m_signer.return_value = sentinel_signer

            out_cfg, signer = _get_config_and_signer()

            assert out_cfg["additional_user_agent"] == _ADDITIONAL_UA
            assert signer is sentinel_signer
            # no token path - STS should not be used
            m_sts.assert_not_called()


class TestImportClientAndModels:
    def test_import_client_requires_dotted_fqn(self):
        with pytest.raises(ValueError):
            _import_client("InvalidFQNWithoutDot")

    def test_import_client_raises_when_attr_not_class(self):
        with patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import:
            m_import.return_value = SimpleNamespace(Fake=123)  # not a class
            with pytest.raises(ValueError):
                _import_client("x.y.Fake")

    def test_import_models_module_from_client_fqn_returns_none_on_failure(self):
        def import_side_effect(name):
            if name == "x.y.models":
                raise ImportError("no models")
            return object()

        with patch(
            "oracle.oci_cloud_mcp_server.server.import_module",
            side_effect=import_side_effect,
        ):
            mod = _import_models_module_from_client_fqn("x.y.FakeClient")
            assert mod is None


class TestAlignParamsSignature:
    def test_align_params_to_signature_remaps_create_details(self):
        def create_vcn(create_vcn_details):  # noqa: ARG001
            return None

        aligned = _align_params_to_signature(create_vcn, "create_vcn", {"vcn_details": {"x": 1}})
        assert "create_vcn_details" in aligned
        assert "vcn_details" not in aligned


class TestSerializeFallback:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_serializes_unjsonable_objects_to_str(self):
        class Weird:
            pass

        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "weird-1"}

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_weird(self, id):  # noqa: ARG002
                return FakeResponse(Weird())

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_import.return_value = fake_module
            m_cfg.return_value = ({}, object())

            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_weird",
                            "params": {"id": "abc"},
                        },
                    )
                ).data

            # should serialize to a string representation
            assert isinstance(res["data"], str)
            assert "Weird" in res["data"]

    def test_serialize_direct_non_jsonable(self):
        class X: ...

        s = _serialize_oci_data(X())
        assert isinstance(s, str)
        assert "X" in s


class TestListClientOperationsErrors:
    @pytest.mark.asyncio
    async def test_list_client_operations_raises_on_not_class(self):
        with patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import:
            m_import.return_value = SimpleNamespace(NotAClass=42)
            async with Client(mcp) as client:
                with pytest.raises(ToolError):
                    await client.call_tool("list_client_operations", {"client_fqn": "x.y.NotAClass"})


class TestModelCoercionAdvanced:
    def test_nested_parent_prefix_model_resolution(self):
        # create a fake models module with nested types:
        class InstanceShapeConfigDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        class InstanceDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(
            InstanceDetails=InstanceDetails,
            InstanceShapeConfigDetails=InstanceShapeConfigDetails,
        )

        with patch("oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn") as m_models:
            m_models.return_value = fake_models

            coerced = _coerce_params_to_oci_models(
                "x.y.FakeClient",
                "launch_instance",  # non-create op to keep key as 'instance_details'
                {
                    "instance_details": {
                        "display_name": "demo",
                        "shape_config": {"ocpus": 2, "memory_in_gbs": 16},
                    }
                },
            )
            inst = coerced["instance_details"]
            assert isinstance(inst, InstanceDetails)
            assert isinstance(inst._data["shape_config"], InstanceShapeConfigDetails)
            assert inst._data["shape_config"]._data["ocpus"] == 2
            assert inst._data["shape_config"]._data["memory_in_gbs"] == 16

    def test_construct_model_with_explicit_name_and_swagger_filter(self):
        # fake models module where the class has swagger_types filtering unknown keys
        class MyModel:
            swagger_types = {"a": "int"}

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(MyModel=MyModel)

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping

        inst = _construct_model_from_mapping(
            {"__model": "MyModel", "a": 1, "b": 2},
            fake_models,
            [],
        )
        assert isinstance(inst, MyModel)
        assert inst._data == {"a": 1}  # 'b' filtered by swagger_types


class TestMainEntrypoint:
    def test_main_runs_http_with_env(self, monkeypatch):
        called = {}

        def fake_run(*args, **kwargs):
            called["args"] = args
            called["kwargs"] = kwargs

        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "9999")

        with patch("oracle.oci_cloud_mcp_server.server.mcp.run", side_effect=fake_run):
            main()

        assert called["kwargs"] == {
            "transport": "http",
            "host": "127.0.0.1",
            "port": 9999,
        }
        assert called["args"] == ()

    def test_main_runs_default_without_env(self, monkeypatch):
        called = {}

        def fake_run(*args, **kwargs):
            called["args"] = args
            called["kwargs"] = kwargs

        monkeypatch.delenv("ORACLE_MCP_HOST", raising=False)
        monkeypatch.delenv("ORACLE_MCP_PORT", raising=False)

        with patch("oracle.oci_cloud_mcp_server.server.mcp.run", side_effect=fake_run):
            main()

        # called with no arguments
        assert called["args"] == ()
        assert called["kwargs"] == {}


# keep an example end-to-end happy path not already covered:
# ensure import_client works end-to-end instantiation
class TestImportClientInstantiation:
    def test_import_client_instantiates_with_config_and_signer(self):
        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_import.return_value = fake_module
            m_cfg.return_value = ({"k": "v"}, object())
            inst = _import_client("x.y.FakeClient")
            assert isinstance(inst, FakeClient)


class TestInvokeErrors:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_operation_not_found_returns_error(self):
        class FakeClient:
            def __init__(self, config, signer):
                pass

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_import.return_value = fake_module
            m_cfg.return_value = ({}, object())

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

        assert res["client"] == "x.y.FakeClient"
        assert res["operation"] == "does_not_exist"
        assert "error" in res
        assert "not found" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_invoke_oci_api_attribute_not_callable_returns_error(self):
        class FakeClient:
            def __init__(self, config, signer):
                pass

            get_thing = 123  # not callable

        fake_module = SimpleNamespace(FakeClient=FakeClient)

        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_import.return_value = fake_module
            m_cfg.return_value = ({}, object())

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

        assert res["client"] == "x.y.FakeClient"
        assert res["operation"] == "get_thing"
        assert "error" in res
        assert "not callable" in res["error"].lower()


class TestGetConfigAndSignerErrors:
    def test_private_key_failure_raises(self):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/path/to/token",
        }

        with (
            patch("oracle.oci_cloud_mcp_server.server.oci.config.from_file") as m_from,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file",
                side_effect=Exception("bad key"),
            ),
        ):
            m_from.return_value = dict(cfg)
            with pytest.raises(Exception):
                _get_config_and_signer()


class TestSignerFallbackOnStsFailure:
    def test_token_present_but_sts_raises_falls_back_to_api_key(self):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/path/to/token",
        }
        with (
            patch("oracle.oci_cloud_mcp_server.server.oci.config.from_file") as m_from,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file") as m_loadkey,
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.auth.signers.SecurityTokenSigner",
                side_effect=Exception("boom"),
            ),
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.Signer") as m_signer,
            patch("oracle.oci_cloud_mcp_server.server.os.path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="TOKEN123")),
        ):
            m_from.return_value = dict(cfg)
            m_loadkey.return_value = object()
            sentinel_signer = object()
            m_signer.return_value = sentinel_signer

            out_cfg, signer = _get_config_and_signer()
            assert out_cfg["additional_user_agent"] == _ADDITIONAL_UA
            assert signer is sentinel_signer


class TestParamCoercionAndAlignmentExtras:
    def test_create_alias_rename_in_coerce_params(self):
        # when operation is create_*, vcn_details should be renamed to create_vcn_details
        with patch(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            return_value=None,
        ):
            out = _coerce_params_to_oci_models("x.y.Fake", "create_vcn", {"vcn_details": {"x": 1}})
            assert "create_vcn_details" in out
            assert "vcn_details" not in out

    def test_align_params_no_dst_in_signature_no_change(self):
        def create_vcn(vcn_details):  # noqa: ARG001
            return None

        aligned = _align_params_to_signature(create_vcn, "create_vcn", {"vcn_details": 1})
        assert "vcn_details" in aligned
        assert "create_vcn_details" not in aligned


class TestCallWithPaginationFallback:
    def test_typeerror_unexpected_kw_triggers_fallback(self):
        class FakeResponse:
            def __init__(self):
                self.data = {"ok": True}
                self.headers = {}

        def create_vcn(create_vcn_details):  # noqa: ARG001
            return FakeResponse()

        data, opc = __import__(
            "oracle.oci_cloud_mcp_server.server",
            fromlist=["_call_with_pagination_if_applicable"],
        )._call_with_pagination_if_applicable(create_vcn, {"vcn_details": {}}, "create_vcn")
        assert data == {"ok": True}
        assert opc is None


class TestConstructModelFQN:
    def test_construct_model_from_fqn(self):
        import sys as _sys
        from types import ModuleType

        mod = ModuleType("mymod")

        class Banana:
            def __init__(self, **kwargs):
                self.kwargs = dict(kwargs)

        setattr(mod, "Banana", Banana)
        _sys.modules["mymod"] = mod

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping

        inst = _construct_model_from_mapping({"__model_fqn": "mymod.Banana", "a": 1}, None, [])
        assert isinstance(inst, Banana)
        assert inst.kwargs["a"] == 1


class TestListAndCandidates:
    def test_list_items_model_hint_and_passthrough(self):
        class MyModel:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(MyModel=MyModel)
        with patch("oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn") as m_models:
            m_models.return_value = fake_models
            out = _coerce_params_to_oci_models(
                "x.y.Fake",
                "op",
                {"items": [{"__model": "MyModel", "a": 1}, {"a": 2}]},
            )
            assert isinstance(out["items"][0], MyModel)
            assert out["items"][0].kw["a"] == 1
            assert out["items"][1] == {"a": 2}

    def test_candidate_from_param_name(self):
        class SourceDetails:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(SourceDetails=SourceDetails)
        with patch("oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn") as m_models:
            m_models.return_value = fake_models
            out = _coerce_params_to_oci_models("x.y.Fake", "op", {"source_details": {"foo": "bar"}})
            assert isinstance(out["source_details"], SourceDetails)
            assert out["source_details"].kw["foo"] == "bar"


class TestSnakeToCamel:
    def test_snake_to_camel(self):
        from oracle.oci_cloud_mcp_server.server import _snake_to_camel

        assert _snake_to_camel("source_details") == "SourceDetails"


class TestSerializeNested:
    def test_serialize_recurses_for_nested_non_jsonable(self):
        class Y:
            def __repr__(self):
                return "Y()"

        nested = {"a": [Y(), (Y(), {"z": Y()})]}
        out = _serialize_oci_data(nested)
        # expect recursion into list/tuple/dict and stringify Y()
        assert isinstance(out, dict)
        assert isinstance(out["a"], list)
        assert isinstance(out["a"][1], list) or isinstance(out["a"][1], tuple)
        flat = _serialize_oci_data(nested)
        # it must be JSON-serializable
        import json as _json

        _json.dumps(flat)


class TestImportModelsAndResolve:
    def test_import_models_success(self, monkeypatch):
        # ensure success path returns the mocked models module
        fake_models = SimpleNamespace()

        def fake_import(name):
            assert name == "x.y.models"
            return fake_models

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", fake_import)
        from oracle.oci_cloud_mcp_server.server import (
            _import_models_module_from_client_fqn,
        )

        mod = _import_models_module_from_client_fqn("x.y.Client")
        assert mod is fake_models

    def test_resolve_model_class_missing_returns_none(self):
        from oracle.oci_cloud_mcp_server.server import _resolve_model_class

        assert _resolve_model_class(SimpleNamespace(), "Nope") is None


class TestInvokePlainReturnNoHeaders:
    @pytest.mark.asyncio
    async def test_invoke_returns_plain_mapping_without_headers(self):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_plain(self, id):  # noqa: ARG002
                # return a plain dict (no .data or .headers)
                return {"ok": True}

        fake_module = SimpleNamespace(FakeClient=FakeClient)
        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_import.return_value = fake_module
            m_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_plain",
                            "params": {"id": "1"},
                        },
                    )
                ).data
        assert res["data"] == {"ok": True}
        assert res["opc_request_id"] is None


class TestInvokeImportFailure:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_import_error_surfaces_as_error_payload(self):
        with (
            patch(
                "oracle.oci_cloud_mcp_server.server.import_module",
                side_effect=ImportError("boom"),
            ),
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.Nope",
                            "operation": "get_thing",
                            "params": {},
                        },
                    )
                ).data
                assert "error" in res
                assert "boom" in res["error"]


class TestSignerTokenReadFailure:
    def test_token_file_exists_but_open_fails_falls_back(self):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/path/to/token",
        }
        with (
            patch("oracle.oci_cloud_mcp_server.server.oci.config.from_file") as m_from,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file") as m_loadkey,
            patch("oracle.oci_cloud_mcp_server.server.os.path.exists", return_value=True),
            patch("oracle.oci_cloud_mcp_server.server.oci.auth.signers.SecurityTokenSigner") as m_sts,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.Signer") as m_signer,
            patch("builtins.open", side_effect=Exception("io")),
        ):
            m_from.return_value = dict(cfg)
            m_loadkey.return_value = object()
            sentinel_signer = object()
            m_signer.return_value = sentinel_signer

            out_cfg, signer = _get_config_and_signer()
            assert out_cfg["additional_user_agent"] == _ADDITIONAL_UA
            assert signer is sentinel_signer
            m_sts.assert_not_called()


class TestAlignParamsSignatureRaises:
    def test_align_params_signature_exception_returns_original(self, monkeypatch):
        def fn(x):  # noqa: ARG001
            pass

        def _raise_sig(*args, **kwargs):
            raise Exception("boom")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.signature", _raise_sig)
        aligned = _align_params_to_signature(fn, "create_something", {"something_details": 1})
        # should return params unchanged when inspect.signature fails
        assert aligned == {"something_details": 1}


class TestCallWithPaginationTypeErrorNoAlias:
    def test_typeerror_without_unexpected_kw_is_reraised(self):
        from oracle.oci_cloud_mcp_server.server import (
            _call_with_pagination_if_applicable,
        )

        def bad_fn(**kwargs):  # noqa: ARG001
            raise TypeError("other type error")

        with pytest.raises(TypeError):
            _call_with_pagination_if_applicable(bad_fn, {"foo": 1}, "create_thing")


class TestListClientOperationsDirect:
    @pytest.mark.asyncio
    async def test_direct_success_and_signature_error_path(self, monkeypatch):
        # create a fake module with a Python-defined class and function to inspect
        class Klass:
            def foo(self, a, b):  # noqa: ARG002
                """Doc first line."""
                return 1

            def _hidden(self):
                pass

        fake_module = SimpleNamespace(Klass=Klass)

        # first run with normal behavior
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_module)
        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})).data
        assert isinstance(res, dict)
        assert "operations" in res
        names = [op["name"] for op in res["operations"]]
        assert "foo" in names
        assert "_hidden" not in names

        # now force inspect.signature to raise to cover the exception path
        def sig_raises(_):
            raise Exception("sig boom")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.signature", sig_raises)
        async with Client(mcp) as client:
            res2 = (await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})).data
        # should still succeed with empty/summary fallback
        assert isinstance(res2, dict)
        assert "operations" in res2


class TestConstructModelFallback:
    def test_construct_model_returns_mapping_when_no_candidates(self):
        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping

        mapping = {"x": 1}
        out = _construct_model_from_mapping(mapping, None, [])
        assert out is mapping


class TestCallWithPaginationHeadersError:
    def test_headers_get_raises_results_in_none_opc_id(self):
        from oracle.oci_cloud_mcp_server.server import (
            _call_with_pagination_if_applicable,
        )

        class Resp:
            def __init__(self):
                self.data = {"val": 1}

                class H:
                    def get(self, *args, **kwargs):
                        raise AttributeError("nope")

                self.headers = H()

        def fn_ok():
            return Resp()

        data, opc = _call_with_pagination_if_applicable(lambda: fn_ok(), {}, "get_thing")
        assert data == {"val": 1}
        assert opc is None


class TestInvokeTypeErrorNonUnexpected:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_typeerror_without_unexpected_kw_returns_error(self):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, id):  # noqa: ARG002
                raise TypeError("some other error")

        fake_module = SimpleNamespace(FakeClient=FakeClient)
        with (
            patch("oracle.oci_cloud_mcp_server.server.import_module") as m_import,
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_import.return_value = fake_module
            m_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "x.y.FakeClient",
                            "operation": "get_thing",
                            "params": {"id": "1"},
                        },
                    )
                ).data
                assert "error" in res
                assert "some other error" in res["error"]


class TestCoerceUpdateAlias:
    def test_update_alias_rename_in_coerce_params(self):
        # when operation is update_*, xxx_details should be renamed to update_xxx_details
        with patch(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            return_value=None,
        ):
            out = _coerce_params_to_oci_models("x.y.Fake", "update_vcn", {"vcn_details": {"x": 1}})
            assert "update_vcn_details" in out
            assert "vcn_details" not in out


class TestListClientOperationsErrorsDirect:
    def test_invalid_fqn_raises(self):
        # missing dot in FQN should raise
        with pytest.raises(Exception):
            list_client_operations("InvalidFqn")

    def test_not_class_raises_direct(self, monkeypatch):
        fake_module = SimpleNamespace(NotAClass=42)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_module)
        with pytest.raises(Exception):
            list_client_operations("x.y.NotAClass")


class TestSignerApiKeyFailure:
    def test_api_key_signer_failure_raises(self):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/path/to/token",
        }
        with (
            patch("oracle.oci_cloud_mcp_server.server.oci.config.from_file") as m_from,
            patch("oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file") as m_loadkey,
            patch("oracle.oci_cloud_mcp_server.server.os.path.exists", return_value=False),
            patch(
                "oracle.oci_cloud_mcp_server.server.oci.signer.Signer",
                side_effect=Exception("signer-fail"),
            ),
        ):
            m_from.return_value = dict(cfg)
            m_loadkey.return_value = object()
            with pytest.raises(Exception):
                _get_config_and_signer()


class TestListClientOperationsDetails:
    @pytest.mark.asyncio
    async def test_operation_entries_have_expected_fields(self, monkeypatch):
        class Klass:
            def foo(self, a, b=1):  # noqa: ARG002
                """Doc first line."""
                return 1

        fake_module = SimpleNamespace(Klass=Klass)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_module)
        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})).data
        ops = res["operations"]
        assert isinstance(ops, list) and ops
        entry = next(o for o in ops if o["name"] == "foo")
        assert "summary" in entry and "Doc first line." in entry["summary"]
        assert "params" in entry and "(" in entry["params"] and ")" in entry["params"]


class TestFromDictSuccess:
    def test_construct_model_from_class_name_from_dict_success(self, monkeypatch):
        # ensure oci.util.from_dict success path is exercised for __model (simple class name)
        class MyModel:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(MyModel=MyModel)

        # inject a from_dict into oci.util that calls the constructor
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(_oci.util, "from_dict", lambda cls, data: cls(**data), raising=False)

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping

        inst = _construct_model_from_mapping({"__model": "MyModel", "a": 1}, fake_models, [])
        assert isinstance(inst, MyModel)
        assert inst._data == {"a": 1}

    def test_construct_model_from_candidate_from_dict_success(self, monkeypatch):
        # ensure success path for candidate classnames (derived from param name)
        class VcnDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(VcnDetails=VcnDetails)

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(_oci.util, "from_dict", lambda cls, data: cls(**data), raising=False)

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping

        inst = _construct_model_from_mapping({"a": 2}, fake_models, ["VcnDetails"])
        assert isinstance(inst, VcnDetails)
        assert inst._data == {"a": 2}

    def test_construct_model_from_fqn_from_dict_success(self, monkeypatch):
        # ensure success path for __model_fqn using from_dict
        import sys as _sys
        from types import ModuleType

        mod = ModuleType("mymod2")

        class Pear:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        setattr(mod, "Pear", Pear)
        _sys.modules["mymod2"] = mod

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(_oci.util, "from_dict", lambda cls, data: cls(**data), raising=False)

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping

        inst = _construct_model_from_mapping({"__model_fqn": "mymod2.Pear", "a": 3}, None, [])
        assert isinstance(inst, Pear)
        assert inst.kw == {"a": 3}


class TestPaginationListPath:
    def test_list_operation_uses_paginator_direct(self, monkeypatch):
        # exercise list_* branch in _call_with_pagination_if_applicable directly
        class Resp:
            def __init__(self, data):
                self.data = data
                self.headers = {}

        def fake_pager(method, **kwargs):  # noqa: ARG001
            return Resp([{"n": 1}, {"n": 2}])

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results",
            fake_pager,
        )

        from oracle.oci_cloud_mcp_server.server import (
            _call_with_pagination_if_applicable,
        )

        def list_things(compartment_id=None):  # noqa: ARG001
            return Resp([{"n": 9}])

        data, opc = _call_with_pagination_if_applicable(
            list_things, {"compartment_id": "ocid1"}, "list_things"
        )
        assert isinstance(data, list) and len(data) == 2
        assert opc is None


class TestListOpcRequestIdPropagation:
    @pytest.mark.asyncio
    async def test_invoke_list_opc_request_id_included(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-list-123"}

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_things(self, compartment_id):  # noqa: ARG002
                return FakeResponse([{"x": 1}])

        # return our fake client and a paginator result with headers
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results",
            lambda method, **kwargs: FakeResponse([{"a": 1}, {"a": 2}]),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "x.y.FakeClient",
                        "operation": "list_things",
                        "params": {"compartment_id": "ocid1.compartment..zzz"},
                    },
                )
            ).data

        assert res["opc_request_id"] == "req-list-123"
        assert isinstance(res["data"], list) and len(res["data"]) == 2


class TestCoerceParamsCornerCases:
    def test_empty_params_returns_empty(self):
        out = _coerce_params_to_oci_models("x.y.Fake", "op", {})
        assert out == {}

    def test_configuration_suffix_constructs(self, monkeypatch):
        class SourceConfiguration:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(SourceConfiguration=SourceConfiguration)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        out = _coerce_params_to_oci_models("x.y.Fake", "op", {"source_configuration": {"a": 1}})
        assert isinstance(out["source_configuration"], SourceConfiguration)
        assert out["source_configuration"].kw["a"] == 1


class TestConstructModelClassFqn:
    def test_construct_model_from_class_fqn_key(self, monkeypatch):
        import sys as _sys
        from types import ModuleType

        mod = ModuleType("mymod3")

        class Grape:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        setattr(mod, "Grape", Grape)
        _sys.modules["mymod3"] = mod

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping

        inst = _construct_model_from_mapping({"__class_fqn": "mymod3.Grape", "v": 7}, None, [])
        assert isinstance(inst, Grape)
        assert inst.kw == {"v": 7}


class TestListClientOperationsNoDoc:
    @pytest.mark.asyncio
    async def test_no_docstring_summary_empty(self, monkeypatch):
        class Klass:
            def foo(self):  # no docstring
                return 1

        fake_module = SimpleNamespace(Klass=Klass)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_module)
        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})).data
        ops = res["operations"]
        entry = next(o for o in ops if o["name"] == "foo")
        assert entry["summary"] == ""


class TestAlignParamsUpdateSignature:
    def test_update_remap_when_signature_requires(self):
        def update_vcn(update_vcn_details):  # noqa: ARG001
            return None

        aligned = _align_params_to_signature(update_vcn, "update_vcn", {"vcn_details": {"x": 1}})
        assert "update_vcn_details" in aligned
        assert "vcn_details" not in aligned


class TestCoerceParamsBothKeysProvided:
    def test_no_double_rename_when_dst_already_present(self):
        out = _coerce_params_to_oci_models(
            "x.y.Fake",
            "create_vcn",
            {"vcn_details": {"x": 1}, "create_vcn_details": {"y": 2}},
        )
        # since destination already present, source key should remain untouched
        assert "create_vcn_details" in out and "vcn_details" in out
        assert out["create_vcn_details"] == {"y": 2}


class TestListClientOperationsInvalidFqnTool:
    @pytest.mark.asyncio
    async def test_invalid_fqn_tool_error(self):
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("list_client_operations", {"client_fqn": "InvalidFqn"})


class TestSerializeTuple:
    def test_tuple_converted_to_jsonable_list(self):
        out = _serialize_oci_data((1, 2, 3))
        # ensure it's JSON-serializable
        import json as _json

        _json.dumps(out)
        # and preserves element order/content
        assert list(out) == [1, 2, 3]


class TestInvokeLastChanceAlias:
    @pytest.mark.asyncio
    async def test_last_chance_alias_in_invoke_oci_api(self, monkeypatch):
        # force final_params to contain 'vcn_details' and ensure the TypeError path
        # in _call_with_pagination_if_applicable triggers the last-chance aliasing.
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "alias-123"}

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            # expects create_vcn_details; passing vcn_details should raise a TypeError
            def create_vcn(self, create_vcn_details):  # noqa: ARG001
                return FakeResponse({"ok": True})

        # provide FakeClient
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        # basic config/signer
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )
        # force coerce step to return the wrong kw name (vcn_details)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._coerce_params_to_oci_models",
            lambda fqn, op, params: {"vcn_details": {"a": 1}},
        )
        # prevent alignment from renaming to create_vcn_details so the TypeError occurs
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._align_params_to_signature",
            lambda method, op, params: dict(params),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "x.y.FakeClient",
                        "operation": "create_vcn",
                        "params": {"vcn_details": {"ignored": True}},
                    },
                )
            ).data

        # should have succeeded via last-chance alias path with opc id propagated
        assert res["opc_request_id"] == "alias-123"
        assert res["data"] == {"ok": True}


class TestSerializeToDictFailure:
    def test_oci_to_dict_raises_falls_back_to_str(self, monkeypatch):
        # patch oci.util.to_dict to raise to exercise fallback
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def raising_to_dict(obj):
            raise Exception("no to_dict")

        monkeypatch.setattr(_oci.util, "to_dict", raising_to_dict, raising=False)

        class Z:
            pass

        s = _serialize_oci_data(Z())
        assert isinstance(s, str)
        assert "Z" in s


class TestInvokeUnexpectedKwOther:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_unexpected_kw_non_matching_raises_error(self, monkeypatch):
        # if TypeError occurs with unexpected kw that does not match expected alias, error should surface
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, id):  # noqa: ARG002
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
                        "operation": "get_thing",
                        # wrong kw 'uuid' should produce an error
                        "params": {"uuid": "x"},
                    },
                )
            ).data

        assert "error" in res
        assert "unexpected keyword" in res["error"]


class TestConstructModelCtorSwaggerFilter:
    def test_from_dict_failure_filters_unknown_and_uses_ctor(self, monkeypatch):
        # ensure that when from_dict fails, constructor path is used
        # and unknown keys are filtered via swagger_types
        class MyModel:
            swagger_types = {"a": "int"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(MyModel=MyModel)

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def raising_from_dict(cls, data):  # noqa: ARG001
            raise Exception("from_dict fail")

        monkeypatch.setattr(_oci.util, "from_dict", raising_from_dict, raising=False)

        inst = _construct_model_from_mapping({"__model": "MyModel", "a": 1, "b": 2}, fake_models, [])
        assert isinstance(inst, MyModel)
        # 'b' should be filtered out because it's not in swagger_types
        assert inst.kw == {"a": 1}
