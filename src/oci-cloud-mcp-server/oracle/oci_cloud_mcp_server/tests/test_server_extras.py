"""
Additional tests to increase coverage for cloud MCP server helpers and edge cases.
Copyright (c) 2026, Oracle
Licensed under the UPL v1.0 https://oss.oracle.com/licenses/upl
"""

from types import SimpleNamespace
from unittest.mock import patch

import oci
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_cloud_mcp_server.tests.sdk_fixtures import install_catalog
from oracle.oci_cloud_mcp_server import server as cloud_server
from oracle.oci_cloud_mcp_server.server import (
    _ADDITIONAL_UA,
    _align_params_to_signature,
    _coerce_params_to_oci_models,
    _describe_model_class,
    _get_config_and_signer,
    _get_client_class,
    _import_client,
    _import_models_module_from_client_fqn,
    _serialize_oci_data,
    list_client_operations,
    main,
    mcp,
)


class _CoercionClient:
    pass


def _install_models(monkeypatch, models, schemas=None):
    return install_catalog(
        monkeypatch, clients={"oci.fake.FakeClient": _CoercionClient},
        models={f"oci.fake.models.{name}": cls for name, cls in models.items()},
        schemas={f"oci.fake.models.{name}": fields for name, fields in (schemas or {}).items()},
    )


class TestImportClientAndModels:
    def test_import_client_requires_dotted_fqn(self):
        with pytest.raises(ValueError, match="catalog"):
            _get_client_class("InvalidFQNWithoutDot")

    def test_import_client_raises_when_attr_not_class(self):
        with pytest.raises(ValueError, match="catalog"):
            _get_client_class("oci.fake.Fake")

    def test_model_context_rejects_uncataloged_client(self):
        with pytest.raises(ValueError, match="catalog"):
            _import_models_module_from_client_fqn("oci.fake.FakeClient")

    def test_client_aliases_share_recorded_model_service(self):
        assert _import_models_module_from_client_fqn("oci.core.ComputeClient") == "oci.core"
        assert _import_models_module_from_client_fqn("oci.core.compute_client.ComputeClient") == "oci.core"

    def test_import_models_module_from_real_client_uses_service_models(self):
        assert _import_models_module_from_client_fqn("oci.core.compute_client.ComputeClient") == "oci.core"


class TestAlignParamsSignature:
    def test_align_params_to_signature_remaps_create_details(self):
        def create_vcn(create_vcn_details):  # noqa: ARG001
            return None

        aligned = _align_params_to_signature(create_vcn, "create_vcn", {"vcn_details": {"x": 1}})
        assert "create_vcn_details" in aligned
        assert "vcn_details" not in aligned


class TestSerializeFallback:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_serializes_unjsonable_objects_to_str(self, monkeypatch):
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

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})


        with (
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_cfg.return_value = ({}, object())

            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "oci.fake.FakeClient",
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
        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.NotAClient"})


class TestModelCoercionAdvanced:
    def test_nested_parent_prefix_model_resolution(self, monkeypatch):
        class InstanceShapeConfigDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)
        class InstanceDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)
        _install_models(monkeypatch, {
            "InstanceDetails": InstanceDetails, "InstanceShapeConfigDetails": InstanceShapeConfigDetails,
        }, {
            "InstanceDetails": {"display_name": "str", "shape_config": "InstanceShapeConfigDetails"},
            "InstanceShapeConfigDetails": {"ocpus": "int", "memory_in_gbs": "int"},
        })
        inst = _coerce_params_to_oci_models("oci.fake.FakeClient", "launch_instance", {
            "instance_details": {"display_name": "demo", "shape_config": {"ocpus": 2, "memory_in_gbs": 16}},
        })["instance_details"]
        assert isinstance(inst, InstanceDetails)
        assert isinstance(inst._data["shape_config"], InstanceShapeConfigDetails)
        assert inst._data["shape_config"]._data == {"ocpus": 2, "memory_in_gbs": 16}

    def test_real_oci_model_resolution_for_launch_instance_details(self):
        from oci.core import models

        coerced = _coerce_params_to_oci_models(
            "oci.core.compute_client.ComputeClient",
            "launch_instance",
            {
                "launch_instance_details": {
                    "availability_domain": "AD-1",
                    "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
                    "shape": "VM.Standard.E2.1.Micro",
                    "source_details": {
                        "source_type": "image",
                        "image_id": "ocid1.image.oc1..exampleuniqueID",
                    },
                    "create_vnic_details": {
                        "subnet_id": "ocid1.subnet.oc1..exampleuniqueID",
                        "assign_public_ip": True,
                    },
                }
            },
        )

        details = coerced["launch_instance_details"]
        assert isinstance(details, models.LaunchInstanceDetails)
        assert isinstance(details.source_details, models.InstanceSourceViaImageDetails)
        assert details.source_details.image_id == "ocid1.image.oc1..exampleuniqueID"
        assert isinstance(details.create_vnic_details, models.CreateVnicDetails)
        assert details.create_vnic_details.subnet_id == "ocid1.subnet.oc1..exampleuniqueID"

    def test_describe_model_class_uses_real_instance_swagger_types(self):
        from oci.core import models

        desc = _describe_model_class(models.LaunchInstanceDetails, max_fields=10)
        assert desc["field_count"] > 0
        assert "availability_domain" in desc["fields"]

    def test_construct_model_with_explicit_name_and_swagger_filter(self, monkeypatch):
        class MyModel:
            swagger_types = {"a": "int"}
            def __init__(self, **kwargs):
                self._data = dict(kwargs)
        _install_models(monkeypatch, {"MyModel": MyModel})
        inst = cloud_server._construct_model_from_mapping({"__model": "MyModel", "a": 1, "b": 2}, "oci.fake", [])
        assert isinstance(inst, MyModel)
        assert inst._data == {"a": 1}


class TestMainEntrypoint:
    def test_main_runs_http_with_env(self, monkeypatch):
        called = {}
        provider = object()
        http_auth = SimpleNamespace(provider=provider)

        def fake_run(*args, **kwargs):
            called["args"] = args
            called["kwargs"] = kwargs

        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "9999")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
        monkeypatch.setenv("IDCS_AUDIENCE", "mcp-audience")
        monkeypatch.setenv("ORACLE_MCP_BASE_URL", "http://127.0.0.1:9999")
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server._http_auth", None)

        with (
            patch(
                "oracle.oci_cloud_mcp_server.server.build_idcs_http_auth",
                return_value=http_auth,
            ) as build_http_auth,
            patch("oracle.oci_cloud_mcp_server.server.mcp.run", side_effect=fake_run),
        ):
            main()
        build_http_auth.assert_called_once_with(["openid", "profile", "email", "oci_mcp.cloud.invoke"])
        assert mcp.auth is provider

        assert called["kwargs"] == {
            "transport": "http",
            "host": "127.0.0.1",
            "port": 9999,
        }
        assert called["args"] == ()

    def test_main_falls_back_for_empty_json_scope_override(self, monkeypatch):
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "9999")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
        monkeypatch.setenv("IDCS_AUDIENCE", "mcp-audience")
        monkeypatch.setenv("ORACLE_MCP_BASE_URL", "http://127.0.0.1:9999")
        monkeypatch.setenv("IDCS_REQUIRED_SCOPES", "[]")
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server._http_auth", None)
        http_auth = SimpleNamespace(provider=object())

        with (
            patch(
                "oracle.oci_cloud_mcp_server.server.build_idcs_http_auth",
                return_value=http_auth,
            ) as build_http_auth,
            patch("oracle.oci_cloud_mcp_server.server.mcp.run"),
        ):
            main()

        assert build_http_auth.call_args.args[0] == [
            "openid",
            "profile",
            "email",
            "oci_mcp.cloud.invoke",
        ]

    def test_main_fails_before_listener_when_common_http_auth_rejects_configuration(self, monkeypatch):
        def reject_http_auth(_required_scopes):
            raise ValueError("HTTP IDCS authentication requires: IDCS_CLIENT_SECRET")

        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "9999")
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server._http_auth", None)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.build_idcs_http_auth",
            reject_http_auth,
        )

        with patch("oracle.oci_cloud_mcp_server.server.mcp.run") as run:
            with pytest.raises(ValueError, match="IDCS_CLIENT_SECRET"):
                main()

        run.assert_not_called()

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
    def test_import_client_instantiates_with_config_and_signer(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                self.config = config
                self.signer = signer

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})


        with (
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_cfg.return_value = ({"k": "v"}, object())
            inst = _import_client(FakeClient)
            assert isinstance(inst, FakeClient)

    def test_import_client_passes_circuit_breaker_to_kwargs_capable_client(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, **kwargs):
                self.config = config
                self.kwargs = kwargs

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})


        with (
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            signer = object()
            m_cfg.return_value = ({"k": "v"}, signer)
            inst = _import_client(FakeClient)

        assert isinstance(inst.kwargs["circuit_breaker_strategy"], oci.circuit_breaker.CircuitBreakerStrategy)
        assert callable(inst.kwargs["circuit_breaker_callback"])
        assert inst.kwargs["signer"] is signer


class TestInvokeErrors:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_operation_not_found_returns_error(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})


        with (
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_cfg.return_value = ({}, object())

            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "oci.fake.FakeClient",
                            "operation": "does_not_exist",
                            "params": {},
                        },
                    )
                ).data

        assert res["client"] == "oci.fake.FakeClient"
        assert res["operation"] == "does_not_exist"
        assert "error" in res
        assert "catalog" in res["error"].lower()

    @pytest.mark.asyncio
    async def test_invoke_oci_api_attribute_not_callable_returns_error(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):
                pass

            get_thing = 123  # not callable

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})


        with (
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_cfg.return_value = ({}, object())

            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "oci.fake.FakeClient",
                            "operation": "get_thing",
                            "params": {},
                        },
                    )
                ).data

        assert res["client"] == "oci.fake.FakeClient"
        assert res["operation"] == "get_thing"
        assert "error" in res
        assert "catalog" in res["error"].lower()


class TestGetConfigAndSignerErrors:
    def test_common_provider_failure_is_propagated(self):
        with patch(
            "oracle.oci_cloud_mcp_server.server.build_auth_context",
            side_effect=ValueError("Unable to construct the selected signer"),
        ):
            with pytest.raises(ValueError, match="selected signer"):
                _get_config_and_signer()


class TestParamCoercionAndAlignmentExtras:
    def test_create_alias_rename_in_coerce_params(self):
        out = _coerce_params_to_oci_models("oci.identity.IdentityClient", "create_vcn", {"vcn_details": {"x": 1}})
        assert out == {"create_vcn_details": {"x": 1}}

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

        data, opc, has_more = __import__(
            "oracle.oci_cloud_mcp_server.server",
            fromlist=["_call_with_pagination_if_applicable"],
        )._call_with_pagination_if_applicable(create_vcn, {"vcn_details": {}}, "create_vcn")
        assert data == {"ok": True}
        assert opc is None
        assert has_more is False


class TestListAndCandidates:
    def test_list_items_model_hint_and_passthrough(self, monkeypatch):
        class MyModel:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)
        _install_models(monkeypatch, {"MyModel": MyModel}, {"MyModel": {"a": "int"}})
        out = _coerce_params_to_oci_models("oci.fake.FakeClient", "op", {
            "items": [{"__model": "MyModel", "a": 1}, {"a": 2}],
        })
        assert isinstance(out["items"][0], MyModel)
        assert out["items"][0].kw == {"a": 1}
        assert out["items"][1] == {"a": 2}

    def test_candidate_from_param_name(self, monkeypatch):
        class SourceDetails:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)
        _install_models(monkeypatch, {"SourceDetails": SourceDetails}, {"SourceDetails": {"foo": "str"}})
        out = _coerce_params_to_oci_models("oci.fake.FakeClient", "op", {"source_details": {"foo": "bar"}})
        assert isinstance(out["source_details"], SourceDetails)
        assert out["source_details"].kw == {"foo": "bar"}


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
    def test_model_context_uses_metadata_without_import(self, monkeypatch):
        monkeypatch.setattr(cloud_server._catalog, "load_model", lambda entry: pytest.fail("metadata lookup imported model"))
        assert _import_models_module_from_client_fqn("oci.core.ComputeClient") == "oci.core"

    def test_resolve_model_class_missing_returns_none(self):
        from oracle.oci_cloud_mcp_server.server import _resolve_model_class

        assert _resolve_model_class(SimpleNamespace(), "Nope") is None


class TestInvokePlainReturnNoHeaders:
    @pytest.mark.asyncio
    async def test_invoke_returns_plain_mapping_without_headers(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_plain(self, id):  # noqa: ARG002
                # return a plain dict (no .data or .headers)
                return {"ok": True}

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})

        with (
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "oci.fake.FakeClient",
                            "operation": "get_plain",
                            "params": {"id": "1"},
                        },
                    )
                ).data
        assert res["data"] == {"ok": True}
        assert res["opc_request_id"] is None


class TestInvokeImportFailure:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_unknown_client_rejected_before_auth(self, monkeypatch):
        monkeypatch.setattr(cloud_server, "_get_config_and_signer", lambda: pytest.fail("unknown client reached auth"))
        async with Client(mcp) as client:
            res = (await client.call_tool("invoke_oci_api", {
                "client_fqn": "oci.fake.NopeClient", "operation": "get_thing", "params": {},
            })).data
        assert "catalog" in res["error"]


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
        # Declare a test client whose public operations can be inspected.
        class KlassClient:
            def foo(self, a, b):  # noqa: ARG002
                """Doc first line."""
                return 1

            def _hidden(self):
                pass

        install_catalog(monkeypatch, clients={"oci.fake.KlassClient": KlassClient})

        # first run with normal behavior
        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.KlassClient"})).data
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
            res2 = (await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.KlassClient"})).data
        # should still succeed with empty/summary fallback
        assert isinstance(res2, dict)
        assert "operations" in res2


class TestConstructModelFallback:
    def test_construct_model_returns_mapping_when_no_candidates(self):
        mapping = {"x": 1}
        assert cloud_server._construct_model_from_mapping(mapping, None, []) == mapping


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

        data, opc, has_more = _call_with_pagination_if_applicable(lambda: fn_ok(), {}, "get_thing")
        assert data == {"val": 1}
        assert opc is None
        assert has_more is False


class TestInvokeTypeErrorNonUnexpected:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_typeerror_without_unexpected_kw_returns_error(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, id):  # noqa: ARG002
                raise TypeError("some other error")

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})

        with (
            patch("oracle.oci_cloud_mcp_server.server._get_config_and_signer") as m_cfg,
        ):
            m_cfg.return_value = ({}, object())
            async with Client(mcp) as client:
                res = (
                    await client.call_tool(
                        "invoke_oci_api",
                        {
                            "client_fqn": "oci.fake.FakeClient",
                            "operation": "get_thing",
                            "params": {"id": "1"},
                        },
                    )
                ).data
                assert "error" in res
                assert "some other error" in res["error"]


class TestCoerceUpdateAlias:
    def test_update_alias_rename_in_coerce_params(self):
        out = _coerce_params_to_oci_models("oci.identity.IdentityClient", "update_vcn", {"vcn_details": {"x": 1}})
        assert out == {"update_vcn_details": {"x": 1}}


class TestListClientOperationsErrorsDirect:
    def test_invalid_fqn_raises(self):
        # missing dot in FQN should raise
        with pytest.raises(Exception):
            list_client_operations("InvalidFqn")

    def test_not_class_raises_direct(self, monkeypatch):
        with pytest.raises(Exception):
            list_client_operations("oci.fake.NotAClient")


class TestListClientOperationsDetails:
    @pytest.mark.asyncio
    async def test_operation_entries_have_expected_fields(self, monkeypatch):
        class KlassClient:
            def foo(self, a, b=1):  # noqa: ARG002
                """Doc first line."""
                return 1

        install_catalog(monkeypatch, clients={"oci.fake.KlassClient": KlassClient})

        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.KlassClient"})).data
        ops = res["operations"]
        assert isinstance(ops, list) and ops
        entry = next(o for o in ops if o["name"] == "foo")
        assert "summary" in entry and "Doc first line." in entry["summary"]
        assert "params" in entry and "(" in entry["params"] and ")" in entry["params"]


class TestFromDictSuccess:
    def test_construct_model_from_class_name_constructor_success(self, monkeypatch):
        class MyModel:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)
        _install_models(monkeypatch, {"MyModel": MyModel}, {"MyModel": {"a": "int"}})
        inst = cloud_server._construct_model_from_mapping({"__model": "MyModel", "a": 1}, "oci.fake", [])
        assert isinstance(inst, MyModel)
        assert inst._data == {"a": 1}

    def test_construct_model_from_candidate_constructor_success(self, monkeypatch):
        class VcnDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)
        _install_models(monkeypatch, {"VcnDetails": VcnDetails}, {"VcnDetails": {"a": "int"}})
        inst = cloud_server._construct_model_from_mapping({"a": 2}, "oci.fake", ["VcnDetails"])
        assert isinstance(inst, VcnDetails)
        assert inst._data == {"a": 2}

class TestPaginationListPath:
    def test_list_operation_aggregates_directly(self):
        # Exercise the unbounded list_* pagination branch directly.
        class Resp:
            def __init__(self, data):
                self.data = data
                self.headers = {}

        from oracle.oci_cloud_mcp_server.server import (
            _call_with_pagination_if_applicable,
        )

        def list_things(compartment_id=None):  # noqa: ARG001
            return Resp([{"n": 1}, {"n": 2}])

        data, opc, has_more = _call_with_pagination_if_applicable(
            list_things, {"compartment_id": "ocid1"}, "list_things"
        )
        assert isinstance(data, list) and len(data) == 2
        assert opc is None
        assert has_more is False


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
                return FakeResponse([{"a": 1}, {"a": 2}])

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})

        # Return a fake client whose response carries the request ID.
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )
        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "list_things",
                        "params": {"compartment_id": "ocid1.compartment..zzz"},
                        "result_mode": "full",
                    },
                )
            ).data

        assert res["opc_request_id"] == "req-list-123"
        assert isinstance(res["data"], list) and len(res["data"]) == 2


class TestCoerceParamsCornerCases:
    def test_empty_params_returns_empty(self):
        assert _coerce_params_to_oci_models("oci.identity.IdentityClient", "op", {}) == {}

    def test_configuration_suffix_constructs(self, monkeypatch):
        class SourceConfiguration:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)
        _install_models(monkeypatch, {"SourceConfiguration": SourceConfiguration}, {"SourceConfiguration": {"a": "int"}})
        out = _coerce_params_to_oci_models("oci.fake.FakeClient", "op", {"source_configuration": {"a": 1}})
        assert isinstance(out["source_configuration"], SourceConfiguration)
        assert out["source_configuration"].kw == {"a": 1}


class TestListClientOperationsNoDoc:
    @pytest.mark.asyncio
    async def test_no_docstring_summary_empty(self, monkeypatch):
        class KlassClient:
            def foo(self):  # no docstring
                return 1

        install_catalog(monkeypatch, clients={"oci.fake.KlassClient": KlassClient})

        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "oci.fake.KlassClient"})).data
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
        out = _coerce_params_to_oci_models("oci.identity.IdentityClient", "create_vcn", {
            "vcn_details": {"x": 1}, "create_vcn_details": {"y": 2},
        })
        assert out == {"vcn_details": {"x": 1}, "create_vcn_details": {"y": 2}}


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

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})

        # basic config/signer
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )
        # Supply an already prepared value with the legacy keyword so execution
        # must take its last-chance alias path, independently of normalization.
        monkeypatch.setattr(
            cloud_server, "prepare_params",
            lambda *args: cloud_server.PreparedParams({"vcn_details": {"a": 1}}),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
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

        install_catalog(monkeypatch, clients={"oci.fake.FakeClient": FakeClient})

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "get_thing",
                        # wrong kw 'uuid' should produce an error
                        "params": {"uuid": "x"},
                    },
                )
            ).data

        assert "error" in res
        assert "unexpected keyword" in res["error"]


class TestConstructModelCtorSwaggerFilter:
    def test_constructor_filters_unknown_short_model_fields(self, monkeypatch):
        class MyModel:
            swagger_types = {"a": "int"}
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)
        _install_models(monkeypatch, {"MyModel": MyModel})
        inst = cloud_server._construct_model_from_mapping({"__model": "MyModel", "a": 1, "b": 2}, "oci.fake", [])
        assert isinstance(inst, MyModel)
        assert inst.kw == {"a": 1}
