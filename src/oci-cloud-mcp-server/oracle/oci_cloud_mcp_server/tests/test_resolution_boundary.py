"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Real SDK/catalog contracts with authentication and OCI calls isolated.
"""

from types import SimpleNamespace

from fastmcp import Client
from fastmcp.exceptions import ToolError
import oci
import pytest

from oracle.oci_cloud_mcp_server import sdk_catalog
from oracle.oci_cloud_mcp_server import server


def forbid_effects(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Resolution rejection reached imports, credentials or a constructor")
    monkeypatch.setattr(server, "_get_config_and_signer", unexpected)
    monkeypatch.setattr(sdk_catalog, "import_module", unexpected)
    return unexpected


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", [
    "invoke_oci_api", "describe_oci_operation", "list_client_operations", "find_oci_api",
])
@pytest.mark.parametrize("name", [
    "oci.injected.InjectedClient", "oci.base_client.BaseClient",
    "oci.core.ComputeClientCompositeOperations", "oci._vendor.jwt.PyJWKClient",
])
async def test_rejected_client_has_no_resolution_side_effects(monkeypatch, tool, name):
    forbid_effects(monkeypatch)
    args = {"client_fqn": name}
    if tool in {"invoke_oci_api", "describe_oci_operation"}:
        args["operation"] = "list_instances"
    if tool == "find_oci_api":
        args["query"] = "list instances"
    async with Client(server.mcp) as client:
        if tool == "invoke_oci_api":
            result = (await client.call_tool(tool, args)).data
            assert "catalog" in result["error"]
        else:
            with pytest.raises(ToolError, match="catalog"):
                await client.call_tool(tool, args)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["__init__", "_call_api", "base_client", "unknown_operation"])
async def test_operation_is_rejected_before_client_load_and_auth(monkeypatch, operation):
    forbid_effects(monkeypatch)
    async with Client(server.mcp) as client:
        result = (await client.call_tool("invoke_oci_api", {
            "client_fqn": "oci.core.ComputeClient", "operation": operation,
        })).data
    assert "catalog" in result["error"]


@pytest.mark.asyncio
@pytest.mark.parametrize("early", [{"fields": []}, {"max_results": 0}])
async def test_error_repair_never_resolves_early_rejected_input(monkeypatch, early):
    forbid_effects(monkeypatch)
    async with Client(server.mcp) as client:
        result = (await client.call_tool("invoke_oci_api", {
            "client_fqn": "oci.injected.InjectedClient", "operation": "list_instances", **early,
        })).data
    assert "error" in result


@pytest.mark.asyncio
async def test_discovery_and_description_share_catalog_without_credentials(monkeypatch):
    def unexpected():
        pytest.fail("Discovery resolved credentials")
    monkeypatch.setattr(server, "_get_config_and_signer", unexpected)
    async with Client(server.mcp) as client:
        listed = (await client.call_tool("list_oci_clients", {})).data
        assert listed["count"] == 322
        assert len({c["client_fqn"] for c in listed["clients"]}) == 322
        for name, operation in [
            ("oci.core.ComputeClient", "list_instances"),
            ("oci.identity.IdentityClient", "list_regions"),
            ("oci.object_storage.ObjectStorageClient", "list_objects"),
            ("oci.identity_domains.IdentityDomainsClient", "list_users"),
        ]:
            result = (await client.call_tool("describe_oci_operation", {
                "client_fqn": name, "operation": operation,
            })).data
            assert result["operation"] == operation
        found = (await client.call_tool("find_oci_api", {"query": "list instances"})).data
        assert found["matches"][0]["client_fqn"] == "oci.core.ComputeClient"
        for match in found["matches"]:
            entry = server._catalog.client(match["client_fqn"])
            assert match["operation"] in entry.operations


@pytest.mark.asyncio
@pytest.mark.parametrize("hint,value", [
    ("__model_fqn", "oci.injected.models.Untrusted"),
    ("__class_fqn", "oci.injected.models.Untrusted"),
    ("__model", "Untrusted"), ("__class", "Untrusted"),
])
@pytest.mark.parametrize("shape", ["root", "parent", "sibling", "list"])
async def test_rejected_model_prevents_all_constructors_and_auth(monkeypatch, hint, value, shape):
    # These are real approved classes; schema inspection must not instantiate them.
    def unexpected(*args, **kwargs):
        pytest.fail("Rejected model input reached credentials or constructors")
    monkeypatch.setattr(server, "_get_config_and_signer", unexpected)
    monkeypatch.setattr(oci.core.models.CreateVcnDetails, "__init__", unexpected)
    monkeypatch.setattr(oci.core.VirtualNetworkClient, "__init__", unexpected)
    bad = {hint: value}
    good = {"__model": "CreateVcnDetails", "compartment_id": "example-compartment"}
    if shape == "root":
        params = {"create_vcn_details": bad}
    elif shape == "parent":
        params = {"create_vcn_details": {**bad, "nested": good}}
    elif shape == "sibling":
        params = {"create_vcn_details": good, "later": bad}
    else:
        params = {"create_vcn_details": good, "later": [good, bad]}
    async with Client(server.mcp) as client:
        result = (await client.call_tool("invoke_oci_api", {
            "client_fqn": "oci.core.VirtualNetworkClient", "operation": "create_vcn", "params": params,
        })).data
    assert "catalog" in result["error"]


def test_cross_service_polymorphic_and_nested_model_preparation():
    assert hasattr(server, "prepare_params"), "Constructor-free preparation has not been implemented"
    prepared = server.prepare_params(
        server._catalog.client("oci.identity.IdentityClient"), oci.identity.IdentityClient.create_user, "create_user",
        {"create_user_details": {
            "__model_fqn": "oci.core.models.launch_instance_details.LaunchInstanceDetails",
            "compartment_id": "example-compartment", "availability_domain": "example-ad",
            "shape": "example-shape",
            "source_details": {"source_type": "image", "image_id": "example-image", "boot_volume_size_in_gbs": "50"},
        }},
    )
    params = server.materialize_params(prepared)
    model = params["create_user_details"]
    assert isinstance(model, oci.core.models.LaunchInstanceDetails)
    assert isinstance(model.source_details, oci.core.models.InstanceSourceViaImageDetails)
    assert model.source_details.boot_volume_size_in_gbs == 50


def test_polymorphic_result_must_be_an_approved_related_model(monkeypatch):
    assert hasattr(server, "prepare_params"), "Constructor-free preparation has not been implemented"
    monkeypatch.setattr(oci.core.models.InstanceSourceDetails, "get_subtype", staticmethod(lambda data: "LaunchInstanceDetails"))
    with pytest.raises(sdk_catalog.SdkResolutionError, match="subtype"):
        server.prepare_params(
            server._catalog.client("oci.core.ComputeClient"), oci.core.ComputeClient.launch_instance, "launch_instance",
            {"launch_instance_details": {"source_details": {"source_type": "image"}}},
        )


def test_short_names_remain_service_scoped_and_collections_coerce():
    assert hasattr(server, "prepare_params"), "Constructor-free preparation has not been implemented"
    first = server._catalog.model("CreateJobDetails", "oci.data_science")
    second = server._catalog.model("CreateJobDetails", "oci.resource_manager")
    assert first.identity != second.identity
    params = server.materialize_params(server.prepare_params(
        server._catalog.client("oci.core.VirtualNetworkClient"), oci.core.VirtualNetworkClient.create_vcn, "create_vcn",
        {"vcn_details": {"compartment_id": "example-compartment", "cidr_blocks": ["10.0.0.0/16"],
                         "freeform_tags": {"owner": "example-owner"}, "is_ipv6_enabled": "true"}},
    ))
    model = params["create_vcn_details"]
    assert isinstance(model, oci.core.models.CreateVcnDetails)
    assert model.is_ipv6_enabled is True
    assert model.cidr_blocks == ["10.0.0.0/16"]
    assert model.freeform_tags == {"owner": "example-owner"}


def test_typed_dictionary_list_models_and_sdk_base_fallback():
    result = server._coerce_value_to_type(
        {"sources": [{"source_type": "image", "image_id": "example-image"}, {"source_type": "unrecognized"}]},
        "dict(str,list[InstanceSourceDetails])", "oci.core",
    )
    assert isinstance(result["sources"][0], oci.core.models.InstanceSourceViaImageDetails)
    assert type(result["sources"][1]) is oci.core.models.InstanceSourceDetails


@pytest.mark.asyncio
async def test_describe_model_schema_does_not_construct_models(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Description constructed a model")
    monkeypatch.setattr(oci.core.models.CreateVcnDetails, "__init__", unexpected)
    async with Client(server.mcp) as client:
        result = (await client.call_tool("describe_oci_operation", {
            "client_fqn": "oci.core.virtual_network_client.VirtualNetworkClient", "operation": "create_vcn",
        })).data
    assert result["request_models"][0]["model"]["name"] == "CreateVcnDetails"
    assert "compartment_id" in result["request_models"][0]["model"]["fields"]


@pytest.mark.parametrize("hint", [None, "", [], 3])
def test_malformed_explicit_hints_fail_before_model_loading(monkeypatch, hint):
    monkeypatch.setattr(server._catalog, "load_model", lambda entry: pytest.fail("Loaded invalid model hint"))
    with pytest.raises(sdk_catalog.SdkResolutionError):
        server._construct_model_from_mapping({"__model_fqn": hint}, "oci.core", [])


def test_conflicting_hints_and_unknown_subtypes_cannot_fall_back(monkeypatch):
    with pytest.raises(sdk_catalog.SdkResolutionError, match="Conflicting"):
        server._construct_model_from_mapping({
            "__model_fqn": "oci.core.models.LaunchInstanceDetails", "__model": "CreateVcnDetails",
        }, "oci.core", [])
    monkeypatch.setattr(oci.core.models.InstanceSourceDetails, "get_subtype", staticmethod(lambda payload: "InjectedModel"))
    with pytest.raises(sdk_catalog.SdkResolutionError, match="catalog"):
        server._construct_model_from_mapping({"__model": "InstanceSourceDetails"}, "oci.core", [])


def test_reviewed_sdk_schema_gap_preserves_raw_values_but_not_class_resolution():
    model = server._construct_model_from_mapping({
        "__model_fqn": "oci.bds.models.CertificateServiceInfoDetails", "services": ["HDFS", "YARN"],
    }, "oci.core", [])
    assert model.services == ["HDFS", "YARN"]
    with pytest.raises(sdk_catalog.SdkResolutionError):
        server._resolve_model_class_from_fqn("oci.bds.models.Service")


def test_opaque_schema_fields_still_materialize_explicit_approved_hints():
    model = server._construct_model_from_mapping({
        "__model_fqn": "oci.bds.models.CertificateServiceInfoDetails",
        "services": [{"__model_fqn": "oci.core.models.InstanceSourceDetails", "source_type": "image", "image_id": "example-image"}],
    }, "oci.core", [])
    assert isinstance(model.services[0], oci.core.models.InstanceSourceViaImageDetails)
    assert model.services[0].image_id == "example-image"
