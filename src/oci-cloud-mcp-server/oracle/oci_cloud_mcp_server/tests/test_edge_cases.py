from types import SimpleNamespace

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from oracle.oci_cloud_mcp_server.server import (
    _align_params_to_signature,
    _call_with_pagination_if_applicable,
    _coerce_params_to_oci_models,
    _construct_model_from_mapping,
    _import_client,
    _resolve_model_class,
    _serialize_oci_data,
    _supports_pagination,
    _to_model_attribute_map_keys,
    mcp,
)


class TestCandidateSwaggerFilter:
    def test_candidate_ctor_with_swagger_filter_on_from_dict_failure(self, monkeypatch):
        # candidate class with swagger_types to filter unknown keys
        class MyDetails:
            swagger_types = {"a": "int"}

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(MyDetails=MyDetails)

        # force from_dict to raise so ctor path is used with swagger filtering
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def raising_from_dict(cls, data):  # noqa: ARG001
            raise Exception("from_dict fail")

        monkeypatch.setattr(_oci.util, "from_dict", raising_from_dict, raising=False)

        inst = _construct_model_from_mapping({"a": 1, "b": 2}, fake_models, ["MyDetails"])
        assert isinstance(inst, MyDetails)
        assert inst._data == {"a": 1}

    def test_candidate_ctor_works_without_from_dict_symbol(self, monkeypatch):
        class MyDetails:
            def __init__(self, **kwargs):
                self.swagger_types = {"a": "int"}
                self.attribute_map = {"a": "a"}
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(MyDetails=MyDetails)
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util,
            "from_dict",
            lambda cls, data: (_ for _ in ()).throw(Exception("unexpected")),  # noqa: ARG005
            raising=False,
        )

        inst = _construct_model_from_mapping(
            {"a": 1, "b": 2}, fake_models, ["MyDetails"]
        )
        assert isinstance(inst, MyDetails)
        assert inst._data == {"a": 1}


class TestCoerceTopLevelConfigSuffix:
    def test_top_level_config_suffix_constructs_model(self, monkeypatch):
        class ShapeConfig:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(ShapeConfig=ShapeConfig)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "op",
            {"shape_config": {"x": 1}},
        )
        assert isinstance(out["shape_config"], ShapeConfig)
        assert out["shape_config"].kw == {"x": 1}


class TestInvokePreNormalize:
    @pytest.mark.asyncio
    async def test_invoke_pre_normalizes_create_details_before_coerce(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {"opc-request-id": "pre-norm-1"}

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def create_vcn(self, create_vcn_details):  # noqa: ARG001
                return FakeResponse({"ok": True, "k": create_vcn_details.get("k")})

        # patch import_module to provide FakeClient
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(FakeClient=FakeClient),
        )
        # avoid models module
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: None,
        )
        # basic config/signer
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )

        from oracle.oci_cloud_mcp_server.server import mcp

        async with Client(mcp) as client:
            res = (
                await client.call_tool(
                    "invoke_oci_api",
                    {
                        "client_fqn": "x.y.FakeClient",
                        "operation": "create_vcn",
                        "params": {"vcn_details": {"k": 42}},
                    },
                )
            ).data

        assert res["opc_request_id"] == "pre-norm-1"
        assert res["data"]["ok"] is True
        assert res["data"]["k"] == 42


class TestNestedSnakeCaseNormalization:
    def test_model_attribute_map_normalizes_nested_snake_case(self):
        class PortRange:
            swagger_types = {"min": "int", "max": "int"}
            attribute_map = {"min": "min", "max": "max"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        class TcpOptions:
            swagger_types = {"destination_port_range": "PortRange"}
            attribute_map = {"destination_port_range": "destinationPortRange"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        class IngressSecurityRule:
            swagger_types = {
                "protocol": "str",
                "source": "str",
                "source_type": "str",
                "tcp_options": "TcpOptions",
            }
            attribute_map = {
                "protocol": "protocol",
                "source": "source",
                "source_type": "sourceType",
                "tcp_options": "tcpOptions",
            }

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        class UpdateSecurityListDetails:
            swagger_types = {"ingress_security_rules": "list[IngressSecurityRule]"}
            attribute_map = {"ingress_security_rules": "ingressSecurityRules"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(
            PortRange=PortRange,
            TcpOptions=TcpOptions,
            IngressSecurityRule=IngressSecurityRule,
            UpdateSecurityListDetails=UpdateSecurityListDetails,
        )

        out = _to_model_attribute_map_keys(
            {
                "ingress_security_rules": [
                    {
                        "protocol": "6",
                        "source": "0.0.0.0/0",
                        "source_type": "CIDR_BLOCK",
                        "tcp_options": {
                            "destination_port_range": {"min": 22, "max": 22}
                        },
                    }
                ]
            },
            UpdateSecurityListDetails,
            fake_models,
        )

        assert "ingressSecurityRules" in out
        rule = out["ingressSecurityRules"][0]
        assert "sourceType" in rule
        assert "tcpOptions" in rule
        assert "destinationPortRange" in rule["tcpOptions"]

    def test_model_attribute_map_normalizes_route_rule_network_entity_id(self):
        class RouteRule:
            swagger_types = {
                "destination": "str",
                "destination_type": "str",
                "network_entity_id": "str",
            }
            attribute_map = {
                "destination": "destination",
                "destination_type": "destinationType",
                "network_entity_id": "networkEntityId",
            }

        class UpdateRouteTableDetails:
            swagger_types = {"route_rules": "list[RouteRule]"}
            attribute_map = {"route_rules": "routeRules"}

        fake_models = SimpleNamespace(
            RouteRule=RouteRule, UpdateRouteTableDetails=UpdateRouteTableDetails
        )

        out = _to_model_attribute_map_keys(
            {
                "route_rules": [
                    {
                        "destination": "0.0.0.0/0",
                        "destination_type": "CIDR_BLOCK",
                        "network_entity_id": "ocid1.internetgateway.oc1..example",
                    }
                ]
            },
            UpdateRouteTableDetails,
            fake_models,
        )

        assert "routeRules" in out
        rr = out["routeRules"][0]
        assert rr["destinationType"] == "CIDR_BLOCK"
        assert rr["networkEntityId"] == "ocid1.internetgateway.oc1..example"

    def test_model_attribute_map_normalizes_launch_instance_source_details(self):
        class InstanceSourceViaImageDetails:
            swagger_types = {"source_type": "str", "image_id": "str"}
            attribute_map = {"source_type": "sourceType", "image_id": "imageId"}

        class LaunchInstanceShapeConfigDetails:
            swagger_types = {"ocpus": "float", "memory_in_gbs": "float"}
            attribute_map = {"ocpus": "ocpus", "memory_in_gbs": "memoryInGBs"}

        class CreateVnicDetails:
            swagger_types = {"subnet_id": "str", "assign_public_ip": "bool"}
            attribute_map = {"subnet_id": "subnetId", "assign_public_ip": "assignPublicIp"}

        class LaunchInstanceDetails:
            swagger_types = {
                "availability_domain": "str",
                "compartment_id": "str",
                "shape": "str",
                "shape_config": "LaunchInstanceShapeConfigDetails",
                "source_details": "InstanceSourceViaImageDetails",
                "create_vnic_details": "CreateVnicDetails",
            }
            attribute_map = {
                "availability_domain": "availabilityDomain",
                "compartment_id": "compartmentId",
                "shape": "shape",
                "shape_config": "shapeConfig",
                "source_details": "sourceDetails",
                "create_vnic_details": "createVnicDetails",
            }

        fake_models = SimpleNamespace(
            LaunchInstanceDetails=LaunchInstanceDetails,
            InstanceSourceViaImageDetails=InstanceSourceViaImageDetails,
            LaunchInstanceShapeConfigDetails=LaunchInstanceShapeConfigDetails,
            CreateVnicDetails=CreateVnicDetails,
        )

        out = _to_model_attribute_map_keys(
            {
                "availability_domain": "AD-1",
                "compartment_id": "ocid1.compartment.oc1..example",
                "shape": "VM.Standard.A1.Flex",
                "shape_config": {"ocpus": 1.0, "memory_in_gbs": 6.0},
                "source_details": {
                    "source_type": "image",
                    "image_id": "ocid1.image.oc1..example",
                },
                "create_vnic_details": {
                    "subnet_id": "ocid1.subnet.oc1..example",
                    "assign_public_ip": True,
                },
            },
            LaunchInstanceDetails,
            fake_models,
        )

        assert out["availabilityDomain"] == "AD-1"
        assert out["compartmentId"] == "ocid1.compartment.oc1..example"
        assert out["shapeConfig"]["memoryInGBs"] == 6.0
        assert out["sourceDetails"]["sourceType"] == "image"
        assert out["sourceDetails"]["imageId"] == "ocid1.image.oc1..example"
        assert out["createVnicDetails"]["assignPublicIp"] is True

    def test_model_attribute_map_uses_source_details_discriminator(self):
        class InstanceSourceDetails:
            swagger_types = {"source_type": "str"}
            attribute_map = {"source_type": "sourceType"}

        class InstanceSourceViaImageDetails:
            swagger_types = {"source_type": "str", "image_id": "str"}
            attribute_map = {"source_type": "sourceType", "image_id": "imageId"}

        class LaunchInstanceDetails:
            swagger_types = {"source_details": "InstanceSourceDetails"}
            attribute_map = {"source_details": "sourceDetails"}

        fake_models = SimpleNamespace(
            InstanceSourceDetails=InstanceSourceDetails,
            InstanceSourceViaImageDetails=InstanceSourceViaImageDetails,
            LaunchInstanceDetails=LaunchInstanceDetails,
        )

        out = _to_model_attribute_map_keys(
            {
                "source_details": {
                    "source_type": "image",
                    "image_id": "ocid1.image.oc1..example",
                }
            },
            LaunchInstanceDetails,
            fake_models,
        )

        assert out["sourceDetails"]["sourceType"] == "image"
        assert out["sourceDetails"]["imageId"] == "ocid1.image.oc1..example"


class TestListClientOperationsImportErrorTool:
    @pytest.mark.asyncio
    async def test_list_client_operations_import_error(self, monkeypatch):
        # import_module throws ImportError to exercise tool error path
        def boom(name):
            raise ImportError("fail")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", boom)

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})


class TestInvokePlainListReturn:
    @pytest.mark.asyncio
    async def test_invoke_returns_plain_list_not_response(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_list(self):
                # return a plain list, not an oci.response.Response
                return [10, 20, 30]

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
                    {"client_fqn": "x.y.FakeClient", "operation": "get_list"},
                )
            ).data

        assert res["opc_request_id"] is None
        assert res["data"] == [10, 20, 30]


class TestConstructFqnSuccess:
    def test_construct_model_from_fqn_success_via_from_dict(self, monkeypatch):
        import sys as _sys
        from types import ModuleType

        # create a module with a class and ensure from_dict returns instance
        mod = ModuleType("mymod9")

        class Kiwi:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        setattr(mod, "Kiwi", Kiwi)
        _sys.modules["mymod9"] = mod

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        # make from_dict call the constructor successfully
        monkeypatch.setattr(_oci.util, "from_dict", lambda cls, data: cls(**data), raising=False)

        inst = _construct_model_from_mapping({"__class_fqn": "mymod9.Kiwi", "a": 7}, None, [])
        assert isinstance(inst, Kiwi)
        assert inst.kw == {"a": 7}


class TestConstructModelFqnAttrNotClass:
    def test_fqn_points_to_non_class_returns_mapping(self, monkeypatch):
        import sys as _sys
        from types import ModuleType

        mod = ModuleType("mymod8")
        # attribute exists but is not a class
        setattr(mod, "Const", 42)
        _sys.modules["mymod8"] = mod

        mapping = {"__model_fqn": "mymod8.Const", "a": 1}
        out = _construct_model_from_mapping(mapping, None, [])
        assert out is mapping


class TestConstructModelSimpleNameNotClass:
    def test_simple_name_resolves_to_non_class_returns_mapping(self):
        class models:
            Foo = 123  # not a class

        mapping = {"__model": "Foo", "a": 1}
        out = _construct_model_from_mapping(mapping, models, [])
        assert out is mapping


class TestListClientOperationsGetdocRaises:
    @pytest.mark.asyncio
    async def test_getdoc_raises_summary_empty(self, monkeypatch):
        class Klass:
            def foo(self, a):  # noqa: ARG002
                """Doc first line."""
                return 1

        fake_module = SimpleNamespace(Klass=Klass)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_module)

        # force inspect.getdoc to raise to hit exception path for summary extraction
        import inspect as _inspect

        orig_getdoc = _inspect.getdoc

        def boom_getdoc(obj):
            if obj is Klass.foo:
                raise Exception("doc boom")
            return orig_getdoc(obj)

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.getdoc", boom_getdoc)

        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})).data

        ops = res["operations"]
        entry = next(o for o in ops if o["name"] == "foo")
        assert entry["summary"] == ""


class TestConstructExplicitClassKey:
    def test_construct_model_with___class_key_uses_from_dict_then_ctor(self, monkeypatch):
        class Foo:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(Foo=Foo)

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        # first let from_dict succeed
        monkeypatch.setattr(_oci.util, "from_dict", lambda cls, data: cls(**data), raising=False)

        inst1 = _construct_model_from_mapping({"__class": "Foo", "a": 1}, fake_models, [])
        assert isinstance(inst1, Foo)
        assert inst1._data == {"a": 1}

        # then force from_dict to fail and check ctor fallback
        def raising_from_dict(cls, data):  # noqa: ARG001
            raise Exception("nope")

        monkeypatch.setattr(_oci.util, "from_dict", raising_from_dict, raising=False)
        inst2 = _construct_model_from_mapping({"__class": "Foo", "a": 2}, fake_models, [])
        assert isinstance(inst2, Foo)
        assert inst2._data == {"a": 2}


class TestCreateUpdateCandidateClasses:
    def test_create_candidate_class_used_and_key_renamed(self, monkeypatch):
        class CreateVcnDetails:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(CreateVcnDetails=CreateVcnDetails)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "create_vcn",
            {"vcn_details": {"a": 1}},
        )
        assert "create_vcn_details" in out and "vcn_details" not in out
        assert isinstance(out["create_vcn_details"], CreateVcnDetails)
        assert out["create_vcn_details"].kw == {"a": 1}

    def test_update_candidate_class_used_and_key_renamed(self, monkeypatch):
        class UpdateVcnDetails:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(UpdateVcnDetails=UpdateVcnDetails)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "update_vcn",
            {"vcn_details": {"a": 2}},
        )
        assert "update_vcn_details" in out and "vcn_details" not in out
        assert isinstance(out["update_vcn_details"], UpdateVcnDetails)
        assert out["update_vcn_details"].kw == {"a": 2}

    def test_method_hint_prefers_create_model_over_generic(self, monkeypatch):
        class VcnDetails:
            def __init__(self, **kwargs):
                raise Exception("generic should not be selected")

        class CreateVcnDetails:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(
            VcnDetails=VcnDetails,
            CreateVcnDetails=CreateVcnDetails,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )

        def create_vcn(create_vcn_details):  # noqa: ARG001
            return None

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "create_vcn",
            {"vcn_details": {"a": 1}},
            method=create_vcn,
        )
        assert isinstance(out["create_vcn_details"], CreateVcnDetails)
        assert out["create_vcn_details"].kw == {"a": 1}


class TestSchemaDrivenCoercion:
    def test_update_route_table_uses_instance_level_model_schema(self, monkeypatch):
        class RouteRule:
            def __init__(self, **kwargs):
                self.swagger_types = {
                    "destination": "str",
                    "destination_type": "str",
                    "network_entity_id": "str",
                }
                self.attribute_map = {
                    "destination": "destination",
                    "destination_type": "destinationType",
                    "network_entity_id": "networkEntityId",
                }
                self.kw = dict(kwargs)

        class UpdateRouteTableDetails:
            def __init__(self, **kwargs):
                self.swagger_types = {"route_rules": "list[RouteRule]"}
                self.attribute_map = {"route_rules": "routeRules"}
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(
            RouteRule=RouteRule,
            UpdateRouteTableDetails=UpdateRouteTableDetails,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "update_route_table",
            {
                "update_route_table_details": {
                    "route_rules": [
                        {
                            "destination": "0.0.0.0/0",
                            "destination_type": "CIDR_BLOCK",
                            "network_entity_id": "ocid1.internetgateway.oc1..example",
                        }
                    ]
                }
            },
        )
        details = out["update_route_table_details"]
        assert isinstance(details, UpdateRouteTableDetails)
        rr = details.kw["route_rules"][0]
        if isinstance(rr, dict):
            assert rr["destination_type"] == "CIDR_BLOCK"
            assert rr["network_entity_id"] == "ocid1.internetgateway.oc1..example"
        else:
            assert isinstance(rr, RouteRule)
            assert rr.kw["destination_type"] == "CIDR_BLOCK"
            assert rr.kw["network_entity_id"] == "ocid1.internetgateway.oc1..example"

    def test_update_route_table_with_real_sdk_models(self, monkeypatch):
        from oci.core import models as core_models

        # OCI SDK 2.160.0 stores swagger_types/attribute_map on instances.
        assert not hasattr(core_models.UpdateRouteTableDetails, "swagger_types")

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: core_models,
        )

        out = _coerce_params_to_oci_models(
            "oci.core.VirtualNetworkClient",
            "update_route_table",
            {
                "update_route_table_details": {
                    "route_rules": [
                        {
                            "destination": "0.0.0.0/0",
                            "destination_type": "CIDR_BLOCK",
                            "network_entity_id": "ocid1.internetgateway.oc1..example",
                        }
                    ]
                }
            },
        )
        details = out["update_route_table_details"]
        assert isinstance(details, core_models.UpdateRouteTableDetails)
        rr = details.route_rules[0]
        rr_neid = rr["network_entity_id"] if isinstance(rr, dict) else rr.network_entity_id
        assert rr_neid == "ocid1.internetgateway.oc1..example"

    def test_launch_instance_with_real_sdk_models_builds_typed_source_details(
        self, monkeypatch
    ):
        from oci.core import models as core_models

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: core_models,
        )

        out = _coerce_params_to_oci_models(
            "oci.core.ComputeClient",
            "launch_instance",
            {
                "launch_instance_details": {
                    "availability_domain": "AD-1",
                    "compartment_id": "ocid1.compartment.oc1..example",
                    "shape": "VM.Standard.A1.Flex",
                    "shape_config": {"ocpus": 1, "memory_in_gbs": 6},
                    "source_details": {
                        "source_type": "image",
                        "image_id": "ocid1.image.oc1..example",
                    },
                    "create_vnic_details": {
                        "subnet_id": "ocid1.subnet.oc1..example",
                        "assign_public_ip": True,
                    },
                }
            },
        )

        details = out["launch_instance_details"]
        assert isinstance(details, core_models.LaunchInstanceDetails)
        assert isinstance(details.shape_config, core_models.LaunchInstanceShapeConfigDetails)
        assert isinstance(details.create_vnic_details, core_models.CreateVnicDetails)
        assert isinstance(
            details.source_details, core_models.InstanceSourceViaImageDetails
        )
        assert details.source_details.source_type == "image"

    def test_update_route_table_plain_snake_case_coerces_nested_route_rules(
        self, monkeypatch
    ):
        class RouteRule:
            swagger_types = {
                "destination": "str",
                "destination_type": "str",
                "network_entity_id": "str",
            }
            attribute_map = {
                "destination": "destination",
                "destination_type": "destinationType",
                "network_entity_id": "networkEntityId",
            }

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        class UpdateRouteTableDetails:
            swagger_types = {"route_rules": "list[RouteRule]"}
            attribute_map = {"route_rules": "routeRules"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(
            RouteRule=RouteRule,
            UpdateRouteTableDetails=UpdateRouteTableDetails,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util, "from_dict", lambda cls, data: cls(**data), raising=False
        )

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "update_route_table",
            {
                "update_route_table_details": {
                    "route_rules": [
                        {
                            "destination": "0.0.0.0/0",
                            "destination_type": "CIDR_BLOCK",
                            "network_entity_id": "ocid1.internetgateway.oc1..example",
                        }
                    ]
                }
            },
        )
        details = out["update_route_table_details"]
        assert isinstance(details, UpdateRouteTableDetails)
        rr = details.kw["route_rules"][0]
        if isinstance(rr, dict):
            assert rr["destination_type"] == "CIDR_BLOCK"
            assert rr["network_entity_id"] == "ocid1.internetgateway.oc1..example"
        else:
            assert isinstance(rr, RouteRule)
            assert rr.kw["destination_type"] == "CIDR_BLOCK"
            assert rr.kw["network_entity_id"] == "ocid1.internetgateway.oc1..example"

    def test_launch_instance_plain_snake_case_no_explicit_model_hints(self, monkeypatch):
        class LaunchInstanceShapeConfigDetails:
            swagger_types = {"ocpus": "float", "memory_in_gbs": "float"}
            attribute_map = {"ocpus": "ocpus", "memory_in_gbs": "memoryInGBs"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        class InstanceSourceViaImageDetails:
            swagger_types = {"source_type": "str", "image_id": "str"}
            attribute_map = {"source_type": "sourceType", "image_id": "imageId"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        class CreateVnicDetails:
            swagger_types = {"subnet_id": "str", "assign_public_ip": "bool"}
            attribute_map = {"subnet_id": "subnetId", "assign_public_ip": "assignPublicIp"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        class LaunchInstanceDetails:
            swagger_types = {
                "availability_domain": "str",
                "compartment_id": "str",
                "shape": "str",
                "shape_config": "LaunchInstanceShapeConfigDetails",
                "source_details": "InstanceSourceDetails",
                "create_vnic_details": "CreateVnicDetails",
                "metadata": "dict(str, str)",
            }
            attribute_map = {
                "availability_domain": "availabilityDomain",
                "compartment_id": "compartmentId",
                "shape": "shape",
                "shape_config": "shapeConfig",
                "source_details": "sourceDetails",
                "create_vnic_details": "createVnicDetails",
                "metadata": "metadata",
            }

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(
            LaunchInstanceDetails=LaunchInstanceDetails,
            LaunchInstanceShapeConfigDetails=LaunchInstanceShapeConfigDetails,
            InstanceSourceViaImageDetails=InstanceSourceViaImageDetails,
            CreateVnicDetails=CreateVnicDetails,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util, "from_dict", lambda cls, data: cls(**data), raising=False
        )

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "launch_instance",
            {
                "launch_instance_details": {
                    "availability_domain": "AD-1",
                    "compartment_id": "ocid1.compartment.oc1..example",
                    "shape": "VM.Standard.A1.Flex",
                    "shape_config": {"ocpus": 1, "memory_in_gbs": 6},
                    "source_details": {
                        "source_type": "image",
                        "image_id": "ocid1.image.oc1..example",
                    },
                    "create_vnic_details": {
                        "subnet_id": "ocid1.subnet.oc1..example",
                        "assign_public_ip": True,
                    },
                    "metadata": {"ssh_authorized_keys": "ssh-rsa AAA..."},
                }
            },
        )

        details = out["launch_instance_details"]
        assert isinstance(details, LaunchInstanceDetails)
        shape_cfg = details.kw["shape_config"]
        src = details.kw["source_details"]
        vnic = details.kw["create_vnic_details"]

        shape_mem = (
            shape_cfg["memory_in_gbs"]
            if isinstance(shape_cfg, dict)
            else shape_cfg.kw["memory_in_gbs"]
        )
        src_type = src["source_type"] if isinstance(src, dict) else src.kw["source_type"]
        src_img = src["image_id"] if isinstance(src, dict) else src.kw["image_id"]
        assign_public = (
            vnic["assign_public_ip"] if isinstance(vnic, dict) else vnic.kw["assign_public_ip"]
        )

        assert shape_mem == 6
        assert src_type == "image"
        assert src_img == "ocid1.image.oc1..example"
        assert assign_public is True
        if not isinstance(src, dict):
            assert isinstance(src, InstanceSourceViaImageDetails)


class TestListElementClassFqn:
    def test_list_item_with_class_fqn_constructs(self, monkeypatch):
        import sys as _sys
        from types import ModuleType

        mod = ModuleType("mymod4")

        class Bar:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        setattr(mod, "Bar", Bar)
        _sys.modules["mymod4"] = mod

        # models module not needed for FQN-based construction
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: None,
        )

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "op",
            {"items": [{"__class_fqn": "mymod4.Bar", "z": 9}, {"plain": True}]},
        )
        assert isinstance(out["items"][0], Bar)
        assert out["items"][0].kw == {"z": 9}
        assert out["items"][1] == {"plain": True}


class TestListPassThroughNonDict:
    def test_list_of_scalars_passthrough(self):
        out = _coerce_params_to_oci_models("x.y.Client", "op", {"items": [1, 2, 3]})
        assert out["items"] == [1, 2, 3]


class TestSignatureAlignment:
    def test_align_maps_single_unknown_id_to_single_expected_id(self):
        def delete_internet_gateway(ig_id, **kwargs):  # noqa: ARG001
            return None

        out = _align_params_to_signature(
            delete_internet_gateway,
            "delete_internet_gateway",
            {"internet_gateway_id": "ocid1.internetgateway.oc1..example"},
        )
        assert "ig_id" in out
        assert out["ig_id"] == "ocid1.internetgateway.oc1..example"
        assert "internet_gateway_id" not in out


class TestFqnCtorFallback:
    def test_construct_model_from_fqn_from_dict_failure_uses_ctor(self, monkeypatch):
        # module and class available by FQN
        import sys as _sys
        from types import ModuleType

        mod = ModuleType("mymod5")

        class Apple:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        setattr(mod, "Apple", Apple)
        _sys.modules["mymod5"] = mod

        # force from_dict to fail so ctor is used
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def raising_from_dict(cls, data):  # noqa: ARG001
            raise Exception("from_dict fail")

        monkeypatch.setattr(_oci.util, "from_dict", raising_from_dict, raising=False)

        inst = _construct_model_from_mapping({"__model_fqn": "mymod5.Apple", "a": 10}, None, [])
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

        data, opc = _call_with_pagination_if_applicable(
            create_vcn,
            {"vcn_details": {"x": 1}},
            "create_vcn",
        )
        assert data == {"ok": True}
        assert opc is None


class TestListClientOpsHiddenOnly:
    @pytest.mark.asyncio
    async def test_class_with_only_hidden_methods_returns_empty(self, monkeypatch):
        class Klass:
            def _private(self):
                return 1

        fake_module = SimpleNamespace(Klass=Klass)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_module)
        async with Client(mcp) as client:
            res = (await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})).data
        assert res == {"operations": []}


class TestResolveModelClassSuccess:
    def test_resolve_model_class_returns_class(self):
        class MM:
            pass

        MM.ModelX = type("ModelX", (), {})
        cls = _resolve_model_class(MM, "ModelX")
        assert cls.__name__ == "ModelX"


class TestParentPrefixAlt:
    def test_parent_prefix_prefers_non_details_variant_when_available(self, monkeypatch):
        # ensure when only 'InstanceShapeConfig' exists (no '...Details'),
        # nested coercion picks it using the parent prefix hint path.
        class InstanceDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        class InstanceShapeConfig:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(
            InstanceDetails=InstanceDetails,
            InstanceShapeConfig=InstanceShapeConfig,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        out = _coerce_params_to_oci_models(
            "x.y.Fake",
            "launch_instance",
            {"instance_details": {"shape_config": {"ocpus": 1}}},
        )
        inst = out["instance_details"]
        assert isinstance(inst, InstanceDetails)
        assert isinstance(inst._data["shape_config"], InstanceShapeConfig)
        assert inst._data["shape_config"]._data["ocpus"] == 1

    def test_parent_prefix_preferred_over_generic_nested_candidate(
        self, monkeypatch
    ):
        class LaunchInstanceDetails:
            swagger_types = {"shape_config": "LaunchInstanceShapeConfigDetails"}
            attribute_map = {"shape_config": "shapeConfig"}

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        class ShapeConfig:
            def __init__(self, **kwargs):
                raise Exception("generic should not be used")

        class LaunchInstanceShapeConfigDetails:
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(
            LaunchInstanceDetails=LaunchInstanceDetails,
            ShapeConfig=ShapeConfig,
            LaunchInstanceShapeConfigDetails=LaunchInstanceShapeConfigDetails,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util, "from_dict", lambda cls, data: cls(**data), raising=False
        )

        out = _coerce_params_to_oci_models(
            "x.y.Fake",
            "launch_instance",
            {"launch_instance_details": {"shape_config": {"ocpus": 1}}},
        )
        inst = out["launch_instance_details"]
        assert isinstance(inst, LaunchInstanceDetails)
        shape_cfg = inst._data["shape_config"]
        if isinstance(shape_cfg, dict):
            assert shape_cfg["ocpus"] == 1
        else:
            assert isinstance(shape_cfg, LaunchInstanceShapeConfigDetails)
            assert shape_cfg._data["ocpus"] == 1

    def test_parent_prefix_avoids_generic_shape_config_in_construct_with_class(
        self, monkeypatch
    ):
        class LaunchInstanceDetails:
            swagger_types = {"shape_config": "LaunchInstanceShapeConfigDetails"}
            attribute_map = {"shape_config": "shapeConfig"}

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        class ShapeConfig:
            # Generic class that accepts kwargs; prior behavior could select this,
            # leading to malformed launch payloads for real SDK requests.
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        class LaunchInstanceShapeConfigDetails:
            swagger_types = {"ocpus": "float"}
            attribute_map = {"ocpus": "ocpus"}

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(
            LaunchInstanceDetails=LaunchInstanceDetails,
            ShapeConfig=ShapeConfig,
            LaunchInstanceShapeConfigDetails=LaunchInstanceShapeConfigDetails,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        from oracle.oci_cloud_mcp_server.server import _construct_model_with_class
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util, "from_dict", lambda cls, data: cls(**data), raising=False
        )

        inst = _construct_model_with_class(
            {"shape_config": {"ocpus": 1}},
            LaunchInstanceDetails,
            fake_models,
        )
        assert isinstance(inst, LaunchInstanceDetails)
        shape_cfg = inst._data["shape_config"]
        assert isinstance(shape_cfg, LaunchInstanceShapeConfigDetails)
        assert shape_cfg._data["ocpus"] == 1

    def test_source_details_stays_mapping_for_parent_discriminator_path(
        self, monkeypatch
    ):
        class LaunchInstanceDetails:
            swagger_types = {"source_details": "InstanceSourceDetails"}
            attribute_map = {"source_details": "sourceDetails"}

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        class SourceDetails:
            # intentionally wrong candidate; this should not be chosen for source_details
            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(
            LaunchInstanceDetails=LaunchInstanceDetails,
            SourceDetails=SourceDetails,
        )

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util, "from_dict", lambda cls, data: cls(**data), raising=False
        )

        out = _coerce_params_to_oci_models(
            "x.y.Fake",
            "launch_instance",
            {
                "launch_instance_details": {
                    "source_details": {
                        "source_type": "image",
                        "image_id": "ocid1.image.oc1..example",
                    }
                }
            },
        )
        inst = out["launch_instance_details"]
        assert isinstance(inst, LaunchInstanceDetails)
        src = (
            inst._data["sourceDetails"]
            if "sourceDetails" in inst._data
            else inst._data["source_details"]
        )
        assert isinstance(src, dict)
        assert src["source_type"] == "image"
        assert src["image_id"] == "ocid1.image.oc1..example"

    def test_construct_model_with_class_keeps_camelcase_keys_via_normalization(
        self, monkeypatch
    ):
        class CreateSubnetDetails:
            swagger_types = {
                "compartment_id": "str",
                "vcn_id": "str",
                "dns_label": "str",
                "prohibit_public_ip_on_vnic": "bool",
            }
            attribute_map = {
                "compartment_id": "compartmentId",
                "vcn_id": "vcnId",
                "dns_label": "dnsLabel",
                "prohibit_public_ip_on_vnic": "prohibitPublicIpOnVnic",
            }

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(CreateSubnetDetails=CreateSubnetDetails)
        from oracle.oci_cloud_mcp_server.server import _construct_model_with_class
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util, "from_dict", lambda cls, data: cls(**data), raising=False
        )

        inst = _construct_model_with_class(
            {
                "compartment_id": "ocid1.compartment.oc1..x",
                "vcnId": "ocid1.vcn.oc1..x",
                "dnsLabel": "edge1",
                "prohibitPublicIpOnVnic": False,
            },
            CreateSubnetDetails,
            fake_models,
        )
        assert isinstance(inst, CreateSubnetDetails)
        assert inst._data["compartment_id"] == "ocid1.compartment.oc1..x"
        assert inst._data["vcn_id"] == "ocid1.vcn.oc1..x"
        assert inst._data["dns_label"] == "edge1"
        assert inst._data["prohibit_public_ip_on_vnic"] is False

    def test_create_subnet_alias_with_mixed_key_styles_coerces_model(self, monkeypatch):
        class CreateSubnetDetails:
            swagger_types = {
                "compartment_id": "str",
                "vcn_id": "str",
                "cidr_block": "str",
                "display_name": "str",
                "dns_label": "str",
                "prohibit_public_ip_on_vnic": "bool",
            }
            attribute_map = {
                "compartment_id": "compartmentId",
                "vcn_id": "vcnId",
                "cidr_block": "cidrBlock",
                "display_name": "displayName",
                "dns_label": "dnsLabel",
                "prohibit_public_ip_on_vnic": "prohibitPublicIpOnVnic",
            }

            def __init__(self, **kwargs):
                self._data = dict(kwargs)

        fake_models = SimpleNamespace(CreateSubnetDetails=CreateSubnetDetails)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        monkeypatch.setattr(
            _oci.util, "from_dict", lambda cls, data: cls(**data), raising=False
        )

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "create_subnet",
            {
                "subnet_details": {
                    "compartment_id": "ocid1.compartment.oc1..x",
                    "vcnId": "ocid1.vcn.oc1..x",
                    "cidr_block": "10.0.1.0/24",
                    "display_name": "edge-subnet",
                    "dnsLabel": "edge1",
                    "prohibitPublicIpOnVnic": False,
                }
            },
        )

        details = out["create_subnet_details"]
        assert isinstance(details, CreateSubnetDetails)
        assert details._data["compartment_id"] == "ocid1.compartment.oc1..x"
        assert details._data["vcn_id"] == "ocid1.vcn.oc1..x"
        assert details._data["cidr_block"] == "10.0.1.0/24"
        assert details._data["display_name"] == "edge-subnet"
        assert details._data["dns_label"] == "edge1"
        assert details._data["prohibit_public_ip_on_vnic"] is False


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


class TestExplicitModelCtorRaisesFallsBack:
    def test_explicit_model_ctor_and_from_dict_fail_returns_mapping(self, monkeypatch):
        # fake models module with a class whose ctor raises
        class BoomModel:
            swagger_types = {"a": "int"}

            def __init__(self, **kwargs):
                raise Exception("ctor boom")

        fake_models = SimpleNamespace(BoomModel=BoomModel)

        # force from_dict to raise as well to hit nested except path
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def raising_from_dict(cls, data):  # noqa: ARG001
            raise Exception("from_dict boom")

        monkeypatch.setattr(_oci.util, "from_dict", raising_from_dict, raising=False)

        mapping = {"__model": "BoomModel", "a": 1}
        out = _construct_model_from_mapping(mapping, fake_models, [])
        # should fall back to original mapping when both from_dict and ctor fail
        assert out is mapping


class TestCandidateCtorRaisesContinueAndFallback:
    def test_candidate_ctor_and_from_dict_fail_continue_and_return_mapping(self, monkeypatch):
        class Candidate:
            def __init__(self, **kwargs):
                raise Exception("ctor fail")

        fake_models = SimpleNamespace(Candidate=Candidate)

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def raising_from_dict(cls, data):  # noqa: ARG001
            raise Exception("from_dict fail")

        monkeypatch.setattr(_oci.util, "from_dict", raising_from_dict, raising=False)

        mapping = {"x": 1}
        out = _construct_model_from_mapping(mapping, fake_models, ["Candidate"])
        assert out is mapping


class TestSourceDetailsSuffixCoercion:
    def test_source_details_suffix_constructs(self, monkeypatch):
        class SourceDetails:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(SourceDetails=SourceDetails)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )
        out = _coerce_params_to_oci_models("x.y.Client", "op", {"source_details": {"a": 1}})
        assert isinstance(out["source_details"], SourceDetails)
        assert out["source_details"].kw == {"a": 1}


class TestListItemWithModelNameHint:
    def test_list_items_with_model_hint_constructs(self, monkeypatch):
        class Foo:
            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(Foo=Foo)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: fake_models,
        )

        out = _coerce_params_to_oci_models(
            "x.y.Client",
            "op",
            {"items": [{"__model": "Foo", "a": 5}, {"b": 6}]},
        )
        assert isinstance(out["items"][0], Foo)
        assert out["items"][0].kw == {"a": 5}
        # second element without a hint should pass through unchanged
        assert out["items"][1] == {"b": 6}


class TestFinalAliasingNonDict:
    def test_final_alias_block_renames_non_dict_value(self, monkeypatch):
        # ensure the final aliasing block in _coerce_params_to_oci_models triggers
        # when value is non-dict (loop won't rename, so tail alias should).
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._import_models_module_from_client_fqn",
            lambda fqn: None,
        )
        out = _coerce_params_to_oci_models("x.y.Client", "create_vcn", {"vcn_details": [1, 2]})
        assert "create_vcn_details" in out and "vcn_details" not in out
        assert out["create_vcn_details"] == [1, 2]


class TestInvokeTupleSerialization:
    @pytest.mark.asyncio
    async def test_invoke_serializes_tuple_data_to_list(self, monkeypatch):
        class FakeResponse:
            def __init__(self, data):
                self.data = data
                self.headers = {}

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_tuple(self):  # noqa: ARG002
                return FakeResponse((1, 2, 3))

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
                        "operation": "get_tuple",
                        "params": {},
                    },
                )
            ).data

        assert res["data"] == [1, 2, 3]


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

    def test_serialize_model_when_to_dict_returns_original_model(self, monkeypatch):
        from oracle.oci_cloud_mcp_server.server import oci as _oci

        class M:
            def __init__(self):
                self.swagger_types = {"a": "str"}
                self.attribute_map = {"a": "a"}
                self.a = "x"

        monkeypatch.setattr(_oci.util, "to_dict", lambda data: data, raising=False)
        out = _serialize_oci_data(M())
        assert out == {"a": "x"}


class TestInvokeGenericException:
    @pytest.mark.asyncio
    async def test_invoke_oci_api_handles_generic_exception(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_crash(self):
                raise RuntimeError("boom")

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
                        "operation": "get_crash",
                        "params": {},
                    },
                )
            ).data

        assert "error" in res
        assert "boom" in res["error"]


class TestListPaginatorHeadersMissing:
    def test_list_headers_object_without_get(self, monkeypatch):
        # ensure list_* branch handles headers object without 'get'
        class Resp:
            def __init__(self, data):
                self.data = data
                self.headers = object()  # lacks .get

        def fake_pager(method, **kwargs):  # noqa: ARG001
            return Resp([1, 2])

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.pagination.list_call_get_all_results",
            fake_pager,
        )

        def list_things():
            return Resp([9])

        data, opc = _call_with_pagination_if_applicable(list_things, {}, "list_things")
        assert data == [1, 2]
        assert opc is None


class TestImportClientBadCtor:
    def test_import_client_ctor_invalid_signature_raises(self, monkeypatch):
        # __init__ without 'signer' kw should cause TypeError in _import_client
        class BadClient:
            def __init__(self):  # no signer kw
                pass

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.import_module",
            lambda name: SimpleNamespace(BadClient=BadClient),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._get_config_and_signer",
            lambda: ({}, object()),
        )

        with pytest.raises(TypeError):
            _import_client("x.y.BadClient")


class TestInvokeDefaultParams:
    @pytest.mark.asyncio
    async def test_invoke_with_params_omitted_defaults_to_empty(self, monkeypatch):
        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get_plain(self):
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
                    {"client_fqn": "x.y.FakeClient", "operation": "get_plain"},
                )
            ).data

        assert res["data"] == {"ok": True}
        # ensure the tool defaulted params to {} and echoed that shape
        assert res["params"] == {}


class TestConstructModelFilteredFromDictSuccess:
    def test_from_dict_success_after_swagger_filter(self, monkeypatch):
        class MyModel2:
            swagger_types = {"a": "int"}

            def __init__(self, **kwargs):
                self.kw = dict(kwargs)

        fake_models = SimpleNamespace(MyModel2=MyModel2)

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        # from_dict should receive filtered data (without 'b')
        monkeypatch.setattr(_oci.util, "from_dict", lambda cls, data: cls(**data), raising=False)

        inst = _construct_model_from_mapping({"__model": "MyModel2", "a": 1, "b": 2}, fake_models, [])
        assert isinstance(inst, MyModel2)
        assert inst.kw == {"a": 1}


class TestInvokeNonListHeadersNoGet:
    @pytest.mark.asyncio
    async def test_non_list_response_headers_missing_get(self, monkeypatch):
        class FakeResp:
            def __init__(self, data):
                self.data = data
                self.headers = object()  # lacks .get

        class FakeClient:
            def __init__(self, config, signer):  # noqa: ARG002
                pass

            def get(self):
                return FakeResp({"ok": True})

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
                    {"client_fqn": "x.y.FakeClient", "operation": "get"},
                )
            ).data

        assert res["opc_request_id"] is None
        assert res["data"] == {"ok": True}


class TestFqnCtorBothFail:
    def test_fqn_from_dict_and_ctor_fail_returns_mapping(self, monkeypatch):
        # valid module/class path where both from_dict and ctor raise; should fall back to mapping.
        import sys as _sys
        from types import ModuleType

        mod = ModuleType("mymod7")

        class Boom:
            def __init__(self, **kwargs):
                raise Exception("ctor fail")

        setattr(mod, "Boom", Boom)
        _sys.modules["mymod7"] = mod

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def raising_from_dict(cls, data):  # noqa: ARG001
            raise Exception("from_dict fail")

        monkeypatch.setattr(_oci.util, "from_dict", raising_from_dict, raising=False)

        mapping = {"__model_fqn": "mymod7.Boom", "a": 1}
        out = _construct_model_from_mapping(mapping, None, [])
        assert out is mapping


class TestListClientOperationsScanError:
    @pytest.mark.asyncio
    async def test_member_scan_error_raises_tool_error(self, monkeypatch):
        # force inspect.getmembers to raise inside list_client_operations try block.
        class Klass:
            def foo(self):
                return 1

        fake_module = SimpleNamespace(Klass=Klass)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_module)

        def boom(*args, **kwargs):
            raise Exception("scan boom")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.inspect.getmembers", boom)

        async with Client(mcp) as client:
            with pytest.raises(ToolError):
                await client.call_tool("list_client_operations", {"client_fqn": "x.y.Klass"})


class TestSupportsPaginationHeuristics:
    def test_supports_pagination_list_prefix_true(self):
        def list_things():
            pass

        assert _supports_pagination(list_things, "list_things") is True

    def test_supports_pagination_summarize_prefix_true(self):
        def summarize_metrics():
            pass

        assert _supports_pagination(summarize_metrics, "summarize_metrics") is True

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

    def test_supports_pagination_docstring_mentions_page_limit_true(self):
        def get_zone_records(**kwargs):  # noqa: ARG001
            """
            Retrieve zone records.

            :param str page: pagination token
            :param int limit: maximum number of items to return
            """
            return None

        assert _supports_pagination(get_zone_records, "list_zone_records") is True

    def test_supports_pagination_docstring_only_false_for_create(self):
        def create_vcn(**kwargs):  # noqa: ARG001
            """
            Create VCN.

            :param str page: mentioned in docs but not applicable
            :param int limit: mentioned in docs but not applicable
            """
            return None

        assert _supports_pagination(create_vcn, "create_vcn") is False


class TestPaginationFallback:
    def test_paginator_failure_falls_back_to_direct_call(self, monkeypatch):
        class FakeResponse:
            def __init__(self):
                self.data = {"ok": True}
                self.headers = {"opc-request-id": "fallback-1"}

        def list_stuff(**kwargs):  # noqa: ARG001
            return FakeResponse()

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def boom(*args, **kwargs):  # noqa: ARG001
            raise AttributeError("object has no attribute items")

        monkeypatch.setattr(
            _oci.pagination, "list_call_get_all_results", boom, raising=False
        )

        data, opc = _call_with_pagination_if_applicable(list_stuff, {}, "list_stuff")
        assert data == {"ok": True}
        assert opc == "fallback-1"

    def test_paginator_failure_falls_back_for_create_operation(self, monkeypatch):
        class FakeResponse:
            def __init__(self):
                self.data = {"id": "ocid1.vcn.oc1..example"}
                self.headers = {"opc-request-id": "fallback-create-1"}

        def create_vcn(**kwargs):  # noqa: ARG001
            return FakeResponse()

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def boom(*args, **kwargs):  # noqa: ARG001
            raise AttributeError("'Vcn' object has no attribute 'items'")

        monkeypatch.setattr(
            _oci.pagination, "list_call_get_all_results", boom, raising=False
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._supports_pagination",
            lambda method, op: True,  # noqa: ARG005
        )

        data, opc = _call_with_pagination_if_applicable(create_vcn, {}, "create_vcn")
        assert data["id"] == "ocid1.vcn.oc1..example"
        assert opc == "fallback-create-1"

    def test_create_operation_never_uses_paginator_heuristics(self, monkeypatch):
        calls = {"paginator": 0}

        class FakeResponse:
            def __init__(self):
                self.data = {"id": "ocid1.vcn.oc1..example"}
                self.headers = {"opc-request-id": "non-paged-create-1"}

        def create_vcn(**kwargs):  # noqa: ARG001
            return FakeResponse()

        from oracle.oci_cloud_mcp_server.server import oci as _oci

        def paginator(*args, **kwargs):  # noqa: ARG001
            calls["paginator"] += 1
            raise AssertionError("paginator should not be used for create operations")

        monkeypatch.setattr(
            _oci.pagination, "list_call_get_all_results", paginator, raising=False
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._extract_expected_kwargs_from_source",
            lambda method: {"page", "limit"},  # noqa: ARG005
        )

        data, opc = _call_with_pagination_if_applicable(create_vcn, {}, "create_vcn")
        assert data["id"] == "ocid1.vcn.oc1..example"
        assert opc == "non-paged-create-1"
        assert calls["paginator"] == 0
