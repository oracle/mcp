"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import Mock, patch

import oci
import pytest
from fastmcp import Client

from oracle.oci_cloud_mcp_server import server


@pytest.mark.parametrize("fqn", ["oci.core.ComputeClient", "oci.core.compute_client.ComputeClient"])
def test_client_aliases_resolve_to_the_sdk_export(fqn):
    assert server._get_client_class(fqn) is oci.core.ComputeClient


@pytest.mark.parametrize("fqn", [
    "oci.base_client.BaseClient",
    "oci.core.compute_client.BaseClient",
    "oci.core.not_a_client.ComputeClient",
    "oci.core.ComputeClientCompositeOperations",
    "oci._vendor.fake.FakeClient",
    "oci.not_a_service.FakeClient",
    "subprocess.Popen",
])
def test_unexported_client_names_are_rejected_without_importing_the_requested_path(fqn):
    _ = oci.core.ComputeClient  # Load the trusted service before watching imports.
    with patch("importlib.import_module") as importer, pytest.raises(ValueError):
        server._get_client_class(fqn)
    importer.assert_not_called()


@pytest.mark.parametrize("fqn", [
    "oci.core.models.CreateVcnDetails", "oci.core.models.create_vcn_details.CreateVcnDetails",
])
def test_model_aliases_resolve_without_model_construction(fqn):
    cls = oci.core.models.CreateVcnDetails
    with patch.object(cls, "__init__", side_effect=AssertionError("constructed model")) as constructor:
        assert server._resolve_model_class_from_fqn(fqn) is cls
    constructor.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("fqn", ["oci.base_client.BaseClient", "oci._vendor.fake.FakeClient"])
async def test_rejected_client_is_not_resolved_again_for_error_hints(monkeypatch, fqn):
    credentials = Mock(side_effect=AssertionError("loaded credentials"))
    monkeypatch.setattr(server, "_get_config_and_signer", credentials)
    with patch.object(server, "_get_client_class", wraps=server._get_client_class) as resolver:
        async with Client(server.mcp) as client:
            result = (await client.call_tool("invoke_oci_api", {
                "client_fqn": fqn, "operation": "call_api",
            })).data
    assert "Unknown OCI SDK service" in result["error"]
    assert resolver.call_count == 1
    credentials.assert_not_called()


@pytest.mark.asyncio
async def test_parameter_error_hints_reuse_the_validated_sdk_method(monkeypatch):
    class ExecutionClient:
        def get_instance(self, instance_id):
            raise AssertionError("method must fail argument binding before execution")

    lookups_before_execution = []

    def construct(fqn):
        lookups_before_execution.append(resolver.call_count)
        return ExecutionClient()

    monkeypatch.setattr(server, "_import_client", construct)
    with patch.object(server, "_get_client_class", wraps=server._get_client_class) as resolver:
        async with Client(server.mcp) as client:
            result = (await client.call_tool("invoke_oci_api", {
                "client_fqn": "oci.core.ComputeClient", "operation": "get_instance",
            })).data
    assert result["expected_params"] == ["instance_id"]
    assert lookups_before_execution == [resolver.call_count]


@pytest.mark.parametrize("fqn", [
    "oci.core.models.not_a_model.CreateVcnDetails",
    "oci.core.models.core_type_mapping",
    "oci._vendor.models.FakeModel",
    "subprocess.Popen",
])
def test_unexported_model_names_are_rejected_without_imports(fqn):
    _ = oci.core.models
    with patch("importlib.import_module") as importer, pytest.raises(ValueError):
        server._resolve_model_class_from_fqn(fqn)
    importer.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["not_an_operation", "__init__", "call_api"])
async def test_invalid_operation_is_rejected_before_authentication_or_construction(monkeypatch, operation):
    credentials = Mock(side_effect=AssertionError("loaded credentials"))
    monkeypatch.setattr(server, "_get_config_and_signer", credentials)
    with patch.object(oci.core.ComputeClient, "__init__") as constructor, \
            patch.object(server, "_get_client_class", wraps=server._get_client_class) as resolver:
        async with Client(server.mcp) as client:
            result = (await client.call_tool("invoke_oci_api", {
                "client_fqn": "oci.core.ComputeClient", "operation": operation,
            })).data
    assert "not found or is not public" in result["error"]
    assert resolver.call_count == 1  # The error path must not resolve the input again.
    credentials.assert_not_called()
    constructor.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_hint", [
    {"__model_fqn": "subprocess.Popen"},
    {"__model": "NotAnOciModel"},
    {"__class": 42},
    {"__model": "CreateVcnDetails", "__class": "CreateSubnetDetails"},
])
async def test_all_model_hints_are_validated_before_any_constructor(monkeypatch, bad_hint):
    credentials = Mock(side_effect=AssertionError("loaded credentials"))
    monkeypatch.setattr(server, "_get_config_and_signer", credentials)
    with patch.object(oci.core.ComputeClient, "__init__") as client_constructor, \
            patch.object(oci.core.models.CreateVcnDetails, "__init__") as model_constructor:
        async with Client(server.mcp) as client:
            result = (await client.call_tool("invoke_oci_api", {
                "client_fqn": "oci.core.ComputeClient", "operation": "get_instance",
                "params": {
                    "first": {"__model": "CreateVcnDetails"},
                    "later": {"nested": [bad_hint]},
                },
            })).data
    assert "model" in result["error"].lower()
    credentials.assert_not_called()
    client_constructor.assert_not_called()
    model_constructor.assert_not_called()


def test_cross_service_model_hint_uses_its_own_nested_model_exports():
    models = oci.container_instances.models
    result = server._construct_model_from_mapping({
        "__model_fqn": "oci.container_instances.models.CreateContainerInstanceDetails",
        "__model": "CreateContainerInstanceDetails",
        "shape_config": {"__model": "CreateContainerInstanceShapeConfigDetails", "ocpus": 2},
    }, oci.core.models, [])
    assert isinstance(result, models.CreateContainerInstanceDetails)
    assert isinstance(result.shape_config, models.CreateContainerInstanceShapeConfigDetails)
    assert result.shape_config.ocpus == 2


def test_sdk_polymorphic_model_conversion_is_preserved():
    result = server._construct_model_from_mapping({
        "__model": "LaunchInstanceDetails",
        "source_details": {"source_type": "image", "image_id": "example-image"},
    }, oci.core.models, [])
    assert isinstance(result.source_details, oci.core.models.InstanceSourceViaImageDetails)
    assert result.source_details.image_id == "example-image"
