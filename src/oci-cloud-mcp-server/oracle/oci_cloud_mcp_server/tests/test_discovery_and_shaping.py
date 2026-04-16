from types import ModuleType, SimpleNamespace

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
import oracle.oci_cloud_mcp_server.server as server_mod
from oracle.oci_cloud_mcp_server.server import mcp


def _fake_tool_response(data, request_id):
    return SimpleNamespace(data=data, headers={"opc-request-id": request_id})


def _patch_fake_invoke_client(monkeypatch, client_cls, *, pager_response=None):
    monkeypatch.setattr(
        "oracle.oci_cloud_mcp_server.server.import_module",
        lambda name: SimpleNamespace(FakeClient=client_cls),
    )
    monkeypatch.setattr(
        "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
        lambda: ({}, object()),
    )
    if pager_response is not None:
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results",
            lambda method, **kwargs: pager_response,
        )


class TestDiscoveryTools:
    def test_discover_client_classes_skips_internal_and_base_clients(self, monkeypatch):
        class ComputeClient:
            __module__ = "oci.core.compute_client"

        class BaseClient:
            __module__ = "oci.base_client"

        class PyJWKClient:
            __module__ = "oci._vendor.jwt.foo_client"

        compute_client_module = ModuleType("oci.core.compute_client")
        compute_client_module.ComputeClient = ComputeClient
        core_module = ModuleType("oci.core")
        core_module.ComputeClient = ComputeClient
        base_client_module = ModuleType("oci.base_client")
        base_client_module.BaseClient = BaseClient
        oci_module = ModuleType("oci")
        oci_module.BaseClient = BaseClient
        vendor_client_module = ModuleType("oci._vendor.jwt.foo_client")
        vendor_client_module.PyJWKClient = PyJWKClient
        vendor_parent_module = ModuleType("oci._vendor.jwt")
        vendor_parent_module.PyJWKClient = PyJWKClient

        fake_modules = {
            "oci.core.compute_client": compute_client_module,
            "oci.core": core_module,
            "oci.base_client": base_client_module,
            "oci": oci_module,
            "oci._vendor.jwt.foo_client": vendor_client_module,
            "oci._vendor.jwt": vendor_parent_module,
        }

        class ModuleInfo:
            def __init__(self, name):
                self.name = name

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.pkgutil.walk_packages",
            lambda path, prefix="oci.": [
                ModuleInfo("oci.base_client"),
                ModuleInfo("oci._vendor.jwt.foo_client"),
                ModuleInfo("oci.core.compute_client"),
            ],
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: fake_modules[name],
        )

        server_mod._discover_client_classes.cache_clear()
        try:
            discovered = server_mod._discover_client_classes()
        finally:
            server_mod._discover_client_classes.cache_clear()

        assert discovered == [("oci.core.ComputeClient", ComputeClient)]

    @pytest.mark.asyncio
    async def test_find_oci_api_returns_ranked_matches(self, monkeypatch):
        class ComputeClient:
            def list_instances(self, compartment_id):  # noqa: ARG002
                """List compute instances."""
                return None

        class NetworkClient:
            def list_vcns(self, compartment_id):  # noqa: ARG002
                """List virtual cloud networks."""
                return None

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._discover_client_classes",
            lambda: [
                ("oci.core.ComputeClient", ComputeClient),
                ("oci.core.VirtualNetworkClient", NetworkClient),
            ],
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "find_oci_api",
                    {"query": "list instances", "limit": 5},
                )
            ).data

        assert res["total_matches"] >= 1
        assert res["matches"][0]["client_fqn"] == "oci.core.ComputeClient"
        assert res["matches"][0]["operation"] == "list_instances"

    @pytest.mark.asyncio
    async def test_find_oci_api_prefers_compute_list_shapes_for_ambiguous_shapes_query(self, monkeypatch):
        class ComputeClient:
            def list_shapes(self, compartment_id):  # noqa: ARG002
                """Lists the shapes that can be used to launch an instance within the specified compartment."""
                return None

        class ShapeClient:
            def list_shapes(self, compartment_id):  # noqa: ARG002
                """Returns a list of Shapes."""
                return None

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._discover_client_classes",
            lambda: [
                ("oci.rover.ShapeClient", ShapeClient),
                ("oci.core.ComputeClient", ComputeClient),
            ],
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "find_oci_api",
                    {"query": "list shapes", "limit": 3},
                )
            ).data

        assert res["matches"][0]["client_fqn"] == "oci.core.ComputeClient"
        assert res["matches"][0]["operation"] == "list_shapes"
        assert any(match["client_fqn"] == "oci.rover.ShapeClient" for match in res["matches"])

    @pytest.mark.asyncio
    async def test_describe_oci_operation_returns_model_hints(self, monkeypatch):
        class CreateVcnDetails:
            swagger_types = {
                "cidr_block": "str",
                "compartment_id": "str",
                "display_name": "str",
            }

        class VirtualNetworkClient:
            def create_vcn(self, create_vcn_details, opc_retry_token=None, **kwargs):  # noqa: ARG002
                """Create a VCN."""
                return None

        def fake_import(name):
            if name == "oci.fake":
                return SimpleNamespace(VirtualNetworkClient=VirtualNetworkClient)
            if name == "oci.fake.models":
                return SimpleNamespace(CreateVcnDetails=CreateVcnDetails)
            raise ImportError(name)

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", fake_import)

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "describe_oci_operation",
                    {
                        "client_fqn": "oci.fake.VirtualNetworkClient",
                        "operation": "create_vcn",
                    },
                )
            ).data

        assert res["summary"] == "Create a VCN."
        assert res["supports_pagination"] is False
        assert [p["name"] for p in res["required_params"]] == ["create_vcn_details"]
        assert res["parameter_aliases"] == [{"from": "vcn_details", "to": "create_vcn_details"}]
        assert res["request_models"][0]["model"]["name"] == "CreateVcnDetails"
        assert "cidr_block" in res["request_models"][0]["model"]["fields"]

    @pytest.mark.asyncio
    async def test_list_client_operations_supports_query_limit_and_compact_mode(self, monkeypatch):
        class FakeClient:
            def create_thing(self, create_thing_details):  # noqa: ARG002
                """Create a thing."""
                return None

            def get_thing(self, thing_id):  # noqa: ARG002
                """Get a thing."""
                return None

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "list_client_operations",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "query": "create",
                        "limit": 1,
                        "include_params": False,
                    },
                )
            ).data

        assert res["returned_operations"] == 1
        assert res["operations"][0]["name"] == "create_thing"
        assert "params" not in res["operations"][0]

    @pytest.mark.asyncio
    async def test_list_oci_clients_returns_discovered_clients(self, monkeypatch):
        class ComputeClient:
            pass

        class IdentityClient:
            pass

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._discover_client_classes",
            lambda: [
                ("oci.core.ComputeClient", ComputeClient),
                ("oci.identity.IdentityClient", IdentityClient),
            ],
        )

        async with Client(mcp) as client:
            res = (await client.call_tool("list_oci_clients", {})).data

        assert res == {
            "count": 2,
            "clients": [
                {
                    "client_fqn": "oci.core.ComputeClient",
                    "module": "oci.core",
                    "class": "ComputeClient",
                },
                {
                    "client_fqn": "oci.identity.IdentityClient",
                    "module": "oci.identity",
                    "class": "IdentityClient",
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_tool_rejects_non_oci_client_fqn(self):
        async with Client(mcp) as client:
            with pytest.raises(ToolError, match="OCI SDK client under the 'oci\\.' namespace"):
                await client.call_tool(
                    "list_client_operations",
                    {"client_fqn": "fake.module.ComputeClient"},
                )


class TestInvokeShaping:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_bounded_pagination_uses_service_default_page_size(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data, request_id, next_page=None):
                self.data = data
                self.headers = {"opc-request-id": request_id}
                if next_page is not None:
                    self.headers["opc-next-page"] = next_page
                self.next_page = next_page

            @property
            def has_next_page(self):
                return self.next_page is not None

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_things(self, compartment_id, limit=None, page=None):  # noqa: ARG002
                captured["calls"].append({"compartment_id": compartment_id, "limit": limit, "page": page})
                if page is None:
                    return FakeResponse([{"name": "a"}, {"name": "b"}], "req-222", next_page="page-2")
                return FakeResponse([{"name": "c"}, {"name": "d"}], "req-223", next_page="page-3")

        captured = {"calls": [], "retry_calls": []}

        def fake_retrying_call(method, **kwargs):
            captured["retry_calls"].append(dict(kwargs))
            return method(**kwargs)

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.retry.DEFAULT_RETRY_STRATEGY.make_retrying_call",
            fake_retrying_call,
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "list_things",
                        "params": {"compartment_id": "ocid1.compartment.oc1..example"},
                        "max_results": 2,
                        "result_mode": "full",
                    },
                )
            ).data

        assert captured["calls"] == [
            {
                "compartment_id": "ocid1.compartment.oc1..example",
                "limit": None,
                "page": None,
            }
        ]
        assert captured["retry_calls"] == [
            {
                "compartment_id": "ocid1.compartment.oc1..example",
            }
        ]
        assert res["data"] == [{"name": "a"}, {"name": "b"}]
        assert res["result_meta"]["pagination_used"] is True
        assert res["result_meta"]["max_results"] == 2
        assert res["result_meta"]["returned_items"] == 2
        assert res["result_meta"]["truncated"] is True
        assert "total_items" not in res["result_meta"]

    @pytest.mark.asyncio
    async def test_invoke_oci_api_bounded_pagination_respects_explicit_limit(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data, request_id, next_page=None):
                self.data = data
                self.headers = {"opc-request-id": request_id}
                if next_page is not None:
                    self.headers["opc-next-page"] = next_page
                self.next_page = next_page

            @property
            def has_next_page(self):
                return self.next_page is not None

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_things(self, compartment_id, limit=None, page=None):  # noqa: ARG002
                captured["limits"].append(limit)
                if page is None:
                    return FakeResponse([{"name": "a"}, {"name": "b"}], "req-224", next_page="page-2")
                return FakeResponse([{"name": "c"}], "req-225")

        captured = {"limits": [], "retry_calls": []}

        def fake_retrying_call(method, **kwargs):
            captured["retry_calls"].append(dict(kwargs))
            return method(**kwargs)

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.retry.DEFAULT_RETRY_STRATEGY.make_retrying_call",
            fake_retrying_call,
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "list_things",
                        "params": {
                            "compartment_id": "ocid1.compartment.oc1..example",
                            "limit": 2,
                        },
                        "max_results": 3,
                        "result_mode": "full",
                    },
                )
            ).data

        assert captured["limits"] == [2, 1]
        assert captured["retry_calls"] == [
            {
                "compartment_id": "ocid1.compartment.oc1..example",
                "limit": 2,
            },
            {
                "compartment_id": "ocid1.compartment.oc1..example",
                "limit": 1,
                "page": "page-2",
            },
        ]
        assert res["data"] == [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        assert res["result_meta"]["returned_items"] == 3
        assert res["result_meta"]["total_items"] == 3
        assert res["result_meta"]["truncated"] is False

    @pytest.mark.asyncio
    async def test_invoke_oci_api_summary_mode_returns_compact_shape(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "req-333"}

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, thing_id):  # noqa: ARG002
                return FakeResponse(
                    {
                        "id": "thing-1",
                        "display_name": "demo",
                        "details": {"state": "ACTIVE", "shape": "VM.Standard.E5.Flex"},
                        "items": [{"name": "alpha"}, {"name": "beta"}],
                    }
                )

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
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "get_thing",
                        "params": {"thing_id": "thing-1"},
                        "result_mode": "summary",
                    },
                )
            ).data

        assert res["result_meta"]["result_mode"] == "summary"
        assert res["data"]["kind"] == "object"
        assert "items" in res["data"]["sample"]
        assert res["data"]["sample"]["items"]["kind"] == "list"

    @pytest.mark.asyncio
    async def test_invoke_oci_api_auto_mode_defaults_list_results_to_summary(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_things(self, compartment_id):  # noqa: ARG002
                return _fake_tool_response([{"id": "a"}, {"id": "b"}], "req-333b")

        _patch_fake_invoke_client(monkeypatch, FakeClient, pager_response=_fake_tool_response([{"id": "a"}, {"id": "b"}], "req-333b"))

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "list_things",
                        "params": {"compartment_id": "ocid1.compartment.oc1..example"},
                    },
                )
            ).data

        assert res["result_meta"]["result_mode"] == "summary"
        assert res["data"]["kind"] == "list"

    @pytest.mark.asyncio
    async def test_invoke_oci_api_fields_projection_returns_only_requested_top_level_fields(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, thing_id):  # noqa: ARG002
                return _fake_tool_response(
                    {
                        "id": "thing-1",
                        "display_name": "demo",
                        "lifecycle_state": "ACTIVE",
                        "shape": "VM.Standard.A1.Flex",
                    },
                    "req-334",
                )

        _patch_fake_invoke_client(monkeypatch, FakeClient)

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "get_thing",
                        "params": {"thing_id": "thing-1"},
                        "fields": ["id", "display_name", "lifecycle_state"],
                    },
                )
            ).data

        assert res["data"] == {
            "id": "thing-1",
            "display_name": "demo",
            "lifecycle_state": "ACTIVE",
        }
        assert res["result_meta"]["fields"] == ["id", "display_name", "lifecycle_state"]

    @pytest.mark.asyncio
    async def test_invoke_oci_api_fields_projection_reports_unmatched_fields(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, thing_id):  # noqa: ARG002
                return _fake_tool_response(
                    {
                        "id": "thing-1",
                        "display_name": "demo",
                        "lifecycle_state": "ACTIVE",
                        "shape": "VM.Standard.A1.Flex",
                    },
                    "req-334b",
                )

        _patch_fake_invoke_client(monkeypatch, FakeClient)

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "get_thing",
                        "params": {"thing_id": "thing-1"},
                        "fields": ["id", "display_name", "displayName"],
                    },
                )
            ).data

        assert res["data"] == {
            "id": "thing-1",
            "display_name": "demo",
        }
        assert res["result_meta"]["fields"] == ["id", "display_name"]
        assert res["result_meta"]["unmatched_fields"] == ["displayName"]

    @pytest.mark.asyncio
    async def test_invoke_oci_api_summary_mode_respects_fields_projection(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def list_things(self, compartment_id):  # noqa: ARG002
                return _fake_tool_response(
                    [
                        {"id": "thing-1", "display_name": "alpha", "shape": "A1"},
                        {"id": "thing-2", "display_name": "beta", "shape": "E5"},
                    ],
                    "req-335",
                )

        _patch_fake_invoke_client(
            monkeypatch,
            FakeClient,
            pager_response=_fake_tool_response(
                [
                    {"id": "thing-1", "display_name": "alpha", "shape": "A1"},
                    {"id": "thing-2", "display_name": "beta", "shape": "E5"},
                ],
                "req-335",
            ),
        )

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "list_things",
                        "params": {"compartment_id": "ocid1.compartment.oc1..example"},
                        "fields": ["id", "display_name"],
                        "result_mode": "summary",
                    },
                )
            ).data

        assert res["result_meta"]["result_mode"] == "summary"
        assert res["result_meta"]["fields"] == ["id", "display_name"]
        assert res["data"]["kind"] == "list"
        assert res["data"]["sample"][0] == {"id": "thing-1", "display_name": "alpha"}
        assert res["data"]["sample_item_keys"] == ["display_name", "id"]

    @pytest.mark.asyncio
    async def test_invoke_oci_api_fields_projection_errors_when_no_fields_match(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, thing_id):  # noqa: ARG002
                return _fake_tool_response({"id": "thing-1", "display_name": "demo"}, "req-335b")

        _patch_fake_invoke_client(monkeypatch, FakeClient)

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "get_thing",
                        "params": {"thing_id": "thing-1"},
                        "fields": ["displayName"],
                    },
                )
            ).data

        assert "error" in res
        assert "None of the requested fields matched" in res["error"]

    @pytest.mark.asyncio
    async def test_invoke_oci_api_errors_include_repair_hints(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, compartment_id):
                """Get a thing."""
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
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "get_thing",
                        "params": {"compartment": "ocid1.compartment.oc1..example"},
                    },
                )
            ).data

        assert "error" in res
        assert res["invalid_param"] == "compartment"
        assert "compartment_id" in res["parameter_suggestions"]
        assert res["expected_params"] == ["compartment_id"]
        assert res["operation_help"]["signature"].startswith("get_thing(")

    @pytest.mark.asyncio
    async def test_invoke_oci_api_coerces_top_level_docstring_types(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {}

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_thing(self, compartment_id, retry_count=None):  # noqa: ARG002
                """
                Get a thing.

                :param str compartment_id: The compartment OCID.
                :param int retry_count: Optional retry count.
                """
                return FakeResponse({"retry_count": retry_count})

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
                        "client_fqn": "oci.fake.FakeClient",
                        "operation": "get_thing",
                        "params": {
                            "compartment_id": "ocid1.compartment.oc1..example",
                            "retry_count": "3",
                        },
                    },
                )
            ).data

        assert res["data"]["retry_count"] == 3


class TestModelTypeCoercion:
    def test_construct_model_coerces_swagger_primitives(self, monkeypatch):
        class MyModel:
            swagger_types = {
                "ocpus": "int",
                "is_enabled": "bool",
                "tags": "list[str]",
            }

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(MyModel=MyModel)

        from oracle.oci_cloud_mcp_server.server import _construct_model_from_mapping
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(_oci.util, "from_dict", lambda cls, data: cls(**data), raising=False)

        inst = _construct_model_from_mapping(
            {
                "__model": "MyModel",
                "ocpus": "2",
                "is_enabled": "true",
                "tags": [1, "blue"],
            },
            fake_models,
            [],
        )

        assert inst._data["ocpus"] == 2
        assert inst._data["is_enabled"] is True
        assert inst._data["tags"] == ["1", "blue"]
