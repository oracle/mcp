from types import ModuleType, SimpleNamespace

import oci
import pytest
from fastmcp import Client

import oracle.oci_cloud_mcp_server.server as server_mod
from oracle.oci_cloud_mcp_server.server import (
    _build_param_error_hints,
    _candidate_model_class_names,
    _coerce_primitive_value,
    _coerce_value_to_type,
    _describe_operation,
    _discover_client_classes,
    _extract_expected_kwargs_from_source,
    _extract_paginated_items,
    _import_client,
    _resolve_model_class_from_type_name,
    _resolve_polymorphic_model_class,
    _score_discovery_match,
    _score_query_match,
    _serialize_oci_data,
    _summarize_serialized_data,
    _supports_pagination,
    _validate_client_fqn,
    mcp,
)


class TestValidationAndFormattingHelpers:
    def test_validate_client_fqn_rejects_invalid_values(self):
        with pytest.raises(ValueError, match="non-empty"):
            _validate_client_fqn("")
        with pytest.raises(ValueError, match="fully-qualified"):
            _validate_client_fqn("oci")
        with pytest.raises(ValueError, match="oci."):
            _validate_client_fqn("fake.module.Client")
        with pytest.raises(ValueError, match="ending in 'Client'"):
            _validate_client_fqn("oci.core.models.Instance", require_client_class=True)

    def test_candidate_model_class_names_covers_update_and_config_suffixes(self):
        assert _candidate_model_class_names("update_vcn", "vcn_details") == [
            "UpdateVcnDetails",
            "VcnDetails",
        ]
        assert _candidate_model_class_names("create_thing", "shape_config") == ["ShapeConfig"]

    def test_score_query_match_handles_blank_and_no_match(self):
        assert _score_query_match("   ", "anything") == 1
        assert _score_query_match("nope", "something else") == 0

    def test_score_query_match_ignores_generic_tokens_and_requires_multiple_hits(self):
        assert _score_query_match(
            "list all OCI regions",
            "oci.identity.IdentityClient",
            "list_regions",
            "Lists all the regions offered by Oracle Cloud Infrastructure.",
        ) > 0
        assert (
            _score_query_match(
                "list all OCI regions",
                "oci.core.ComputeClient",
                "list_instances",
                "Lists compute instances in a compartment.",
            )
            == 0
        )

    def test_score_discovery_match_prefers_exact_operation_name(self):
        exact_match = _score_discovery_match(
            "launch instance",
            "oci.core.ComputeClient",
            "launch_instance",
            "Creates a new instance in the specified compartment and availability domain.",
        )
        related_match = _score_discovery_match(
            "launch instance",
            "oci.core.ComputeClient",
            "list_instances",
            "Lists the compute instances in a compartment.",
        )

        assert exact_match > related_match

    def test_score_discovery_match_prefers_compute_shapes_for_ambiguous_list_shapes(self):
        compute_score = _score_discovery_match(
            "list shapes",
            "oci.core.ComputeClient",
            "list_shapes",
            "Lists the shapes that can be used to launch an instance within the specified compartment.",
        )
        rover_score = _score_discovery_match(
            "list shapes",
            "oci.rover.ShapeClient",
            "list_shapes",
            "Returns a list of Shapes.",
        )

        assert compute_score > rover_score

class TestDiscoveryAndImportHelpers:
    def test_discover_client_classes_covers_skip_paths(self, monkeypatch):
        class GoodClient:
            __module__ = "oci.good.compute_client"

        class WrongModuleClient:
            __module__ = "oci.somewhere_else"

        good_module = ModuleType("oci.good.compute_client")
        good_module.GoodClient = GoodClient
        good_module.WrongModuleClient = WrongModuleClient
        good_parent = ModuleType("oci.good")
        good_parent.GoodClient = GoodClient

        class ModuleInfo:
            def __init__(self, name):
                self.name = name

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.pkgutil.walk_packages",
            lambda path, prefix="oci.": [
                ModuleInfo("oci._private.secret_client"),
                ModuleInfo("oci.not_a_client"),
                ModuleInfo("oci.bad_client"),
                ModuleInfo("oci.good.compute_client"),
            ],
        )

        def fake_import(name):
            if name == "oci.bad_client":
                raise ImportError("boom")
            if name == "oci.good.compute_client":
                return good_module
            if name == "oci.good":
                return good_parent
            raise ImportError(name)

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", fake_import)

        _discover_client_classes.cache_clear()
        try:
            discovered = _discover_client_classes()
        finally:
            _discover_client_classes.cache_clear()

        assert discovered == [("oci.good.GoodClient", GoodClient)]

    def test_import_client_falls_back_when_signature_introspection_fails(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, **kwargs):
                self.config = config
                self.kwargs = kwargs

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({"region": "us-phoenix-1"}, object()),
        )

        real_signature = server_mod.inspect.signature

        def fake_signature(obj):
            if obj is FakeClient.__init__:
                raise TypeError("no signature")
            return real_signature(obj)

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.signature", fake_signature)

        client = _import_client("oci.fake.FakeClient")

        assert client.config == {"region": "us-phoenix-1"}
        assert "signer" in client.kwargs


class TestTypeAndModelHelpers:
    def test_resolve_polymorphic_model_class_covers_success_and_error(self):
        class ChildModel:
            pass

        class BaseModel:
            attribute_map = {"resource_type": "resourceType"}

            @staticmethod
            def get_subtype(payload):
                return "ChildModel" if payload.get("resourceType") == "child" else "BaseModel"

        class FailingModel:
            @staticmethod
            def get_subtype(payload):  # noqa: ARG004
                raise RuntimeError("bad subtype")

        models_module = SimpleNamespace(ChildModel=ChildModel)

        assert (
            _resolve_polymorphic_model_class(BaseModel, {"resource_type": "child"}, models_module)
            is ChildModel
        )
        assert _resolve_polymorphic_model_class(FailingModel, {"x": 1}, models_module) is FailingModel

    def test_coerce_primitive_value_covers_false_invalid_float_and_integral_float(self):
        assert _coerce_primitive_value(3.0, "int") == 3
        assert _coerce_primitive_value("not-a-float", "float") == "not-a-float"
        assert _coerce_primitive_value("no", "bool") is False

    def test_resolve_model_class_from_type_name_covers_fqn_and_failure(self):
        assert _resolve_model_class_from_type_name("datetime.datetime", None).__name__ == "datetime"
        assert _resolve_model_class_from_type_name("missing.module.Type", None) is None
        assert _resolve_model_class_from_type_name("", None) is None

    def test_coerce_value_to_type_covers_dict_and_model_paths(self, monkeypatch):
        class FakeModel:
            pass

        models_module = SimpleNamespace(FakeModel=FakeModel)

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._construct_model_from_mapping",
            lambda value, models_module, candidates: {
                "value": value,
                "candidates": candidates,
                "models_module": models_module,
            },
        )

        assert _coerce_value_to_type({"a": "1"}, "dict(str, int)", None) == {"a": 1}
        assert _coerce_value_to_type(["true", "false"], "list[bool]", None) == [True, False]
        assert _coerce_value_to_type(
            {"x": 1},
            "FakeModel",
            models_module,
        ) == {
            "value": {"x": 1},
            "candidates": ["FakeModel"],
            "models_module": models_module,
        }

    def test_extract_expected_kwargs_from_source_returns_none_on_regex_error(self, monkeypatch):
        def method():
            expected_kwargs = ["page"]  # noqa: F841
            return None

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.re.search", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("bad regex")))
        assert _extract_expected_kwargs_from_source(method) is None


class TestDescriptionAndSerializationHelpers:
    def test_describe_operation_covers_missing_operation_non_callable_and_doc_failure(self, monkeypatch):
        class FakeClient:
            thing = 123

            def list_things(self, compartment_id, opc_retry_token=None):  # noqa: ARG002
                """List things."""
                return None

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )

        with pytest.raises(AttributeError, match="Similar operations"):
            _describe_operation("oci.fake.FakeClient", "list_thingz")

        with pytest.raises(AttributeError, match="not callable"):
            _describe_operation("oci.fake.FakeClient", "thing")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.getdoc", lambda obj: (_ for _ in ()).throw(RuntimeError("doc fail")))
        desc = _describe_operation("oci.fake.FakeClient", "list_things")
        assert desc["summary"] == ""
        assert desc["request_models"] == []

    def test_extract_paginated_items_covers_all_shapes(self):
        dns_items = oci.dns.models.RecordCollection(items=[{"domain": "a.example"}])
        object_items = oci.object_storage.models.ListObjects(objects=[{"name": "x"}], prefixes=["p/"])
        custom_items = SimpleNamespace(items=[1, 2, 3])
        no_items = SimpleNamespace(name="plain-object")

        assert _extract_paginated_items(dns_items)[1] == "dns"
        assert _extract_paginated_items(object_items)[1] == "object_storage"
        assert _extract_paginated_items([1, 2, 3])[0] == [1, 2, 3]
        assert _extract_paginated_items(custom_items)[0] == [1, 2, 3]
        assert _extract_paginated_items(no_items)[0] is no_items

    def test_summarize_and_serialize_helpers_cover_scalar_and_fallback_paths(self, monkeypatch):
        summary = _summarize_serialized_data([{"a": 1}, {"b": 2}], 1)
        assert summary["kind"] == "list"
        assert summary["sample_truncated"] is True
        assert _summarize_serialized_data("x", 2) == {"kind": "str", "value": "x"}

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.oci.util.to_dict", lambda obj: (_ for _ in ()).throw(RuntimeError("no dict")))

        class Weird:
            def __str__(self):
                return "weird"

        assert _serialize_oci_data(Weird()) == "weird"

    def test_build_param_error_hints_includes_kwargs_and_aliases(self):
        def create_vcn(create_vcn_details, **kwargs):  # noqa: ARG001
            expected_kwargs = ["page", "limit"]
            return expected_kwargs

        hints = _build_param_error_hints(
            create_vcn,
            "create_vcn",
            {"vcn_details": {"cidr_block": "10.0.0.0/16"}},
            "got an unexpected keyword argument 'foo'",
        )

        assert hints["invalid_param"] == "foo"
        assert hints["expected_params"] == ["create_vcn_details"]
        assert hints["accepted_kwargs"] == ["limit", "page"]
        assert hints["parameter_aliases"] == [{"from": "vcn_details", "to": "create_vcn_details"}]


class TestPaginationHelperBranches:
    def test_supports_pagination_false_when_signature_introspection_blows_up(self, monkeypatch):
        def get_widget(widget_id):  # noqa: ARG001
            return None

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.signature", lambda obj: (_ for _ in ()).throw(RuntimeError("bad sig")))
        assert _supports_pagination(get_widget, "get_widget") is False

    def test_supports_pagination_ignores_docstrings_that_only_mention_limits(self):
        def create_widget(name, **kwargs):  # noqa: ARG001
            """Create a widget.

            The service enforces a limit of 10 widgets per compartment.
            """
            return None

        assert _supports_pagination(create_widget, "create_widget") is False

    def test_call_with_pagination_covers_dns_and_object_storage_paths(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data, has_next_page=False, next_page=None):
                self.data = data
                self.has_next_page = has_next_page
                self.next_page = next_page
                self.headers = {"opc-request-id": "req-1"}

        dns_response = FakeResponse(
            oci.dns.models.RecordCollection(items=[{"domain": "a.example"}]),
            has_next_page=False,
        )
        object_response = FakeResponse(
            oci.object_storage.models.ListObjects(
                objects=[{"name": "one"}],
                prefixes=["prefix/"],
                next_start_with=None,
            ),
            has_next_page=False,
        )

        calls = []

        def fake_retrying_call(method, **kwargs):
            calls.append(kwargs)
            if method.__name__ == "get_rr_set":
                return dns_response
            return object_response

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.retry.DEFAULT_RETRY_STRATEGY.make_retrying_call",
            fake_retrying_call,
        )

        def get_rr_set(page=None, limit=None):  # noqa: ARG001
            return None

        def list_objects(start=None, limit=None):  # noqa: ARG001
            return None

        dns_data, dns_req, dns_more = server_mod._call_with_pagination_if_applicable(
            get_rr_set,
            {},
            "get_rr_set",
            max_results=1,
        )
        obj_data, obj_req, obj_more = server_mod._call_with_pagination_if_applicable(
            list_objects,
            {},
            "list_objects",
            max_results=1,
        )

        assert isinstance(dns_data, oci.dns.models.RecordCollection)
        assert dns_req == "req-1"
        assert dns_more is False
        assert isinstance(obj_data, oci.object_storage.models.ListObjects)
        assert obj_data.prefixes == ["prefix/"]
        assert obj_req == "req-1"
        assert obj_more is False
        assert calls == [{}, {}]

    def test_call_with_pagination_skips_recheck_when_flag_is_false(self):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-direct"}

        def list_things():
            return FakeResponse(["a", "b"])

        data, opc, has_more = server_mod._call_with_pagination_if_applicable(
            list_things,
            {},
            "list_things",
            uses_pagination=False,
        )

        assert data == ["a", "b"]
        assert opc == "req-direct"
        assert has_more is False


class TestToolValidationBranches:
    @pytest.mark.asyncio
    async def test_translate_tools_are_not_exposed(self):
        tools = await mcp.get_tools()
        assert "translate_oci_sdk_call" not in tools
        assert "translate_oci_sdk_procedure" not in tools

    @pytest.mark.asyncio
    async def test_find_oci_api_validates_limit_and_query(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception):
                await client.call_tool("find_oci_api", {"query": "list", "limit": 0})
            with pytest.raises(Exception):
                await client.call_tool("find_oci_api", {"query": "   "})

    @pytest.mark.asyncio
    async def test_find_oci_api_client_filter_path_and_include_params(self, monkeypatch):
        class FakeClient:
            def list_instances(self, compartment_id):  # noqa: ARG002
                """List instances."""
                return None

            def get_instance(self, instance_id):  # noqa: ARG002
                """Get instance."""
                return None

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "find_oci_api",
                    {
                        "query": "list instances",
                        "client_fqn": "oci.fake.FakeClient",
                        "include_params": True,
                    },
                )
            ).data

        assert res["client_filter"] == "oci.fake.FakeClient"
        assert res["matches"][0]["operation"] == "list_instances"
        assert "params" in res["matches"][0]

    @pytest.mark.asyncio
    async def test_describe_invoke_and_list_tools_validate_positive_limits(self):
        async with Client(mcp) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "describe_oci_operation",
                    {"client_fqn": "oci.core.ComputeClient", "operation": "list_instances", "max_model_fields": 0},
                )
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {"client_fqn": "oci.core.ComputeClient", "operation": "list_instances", "max_results": 0},
                )
            ).data
            assert res["error"] == "max_results must be >= 1"
            with pytest.raises(Exception):
                await client.call_tool(
                    "list_client_operations",
                    {"client_fqn": "oci.core.ComputeClient", "limit": 0},
                )
            with pytest.raises(Exception):
                await client.call_tool("list_oci_clients", {"limit": 0})

    @pytest.mark.asyncio
    async def test_invoke_oci_api_validates_fields_input(self):
        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.core.ComputeClient",
                        "operation": "list_instances",
                        "fields": ["id", ""],
                    },
                )
            ).data

            assert res["error"] == "fields must contain only non-empty strings"

            with pytest.raises(Exception):
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.core.ComputeClient",
                        "operation": "list_instances",
                        "fields": "id,display_name",
                    },
                )
