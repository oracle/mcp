"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from unittest.mock import MagicMock

import oci
import pytest
from oracle.oci_compute_mcp_server.models import (
    Image,
    Instance,
    InstanceAgentConfig,
    InstanceAgentFeatures,
    InstanceAvailabilityConfig,
    InstanceOptions,
    InstanceShapeConfig,
    InstanceSourceDetails,
    LaunchOptions,
    PlacementConstraintDetails,
    PlatformConfig,
    PreemptibleInstanceConfigDetails,
    Request,
    Response,
    VnicAttachment,
    map_agent_config,
    map_availability_config,
    map_image,
    map_instance,
    map_instance_agent_features,
    map_instance_options,
    map_launch_options,
    map_licensing_configs,
    map_placement_constraint_details,
    map_platform_config,
    map_preemptible_config,
    map_request,
    map_response,
    map_shape_config,
    map_source_details,
    map_vnic_attachment,
)


@pytest.mark.asyncio
async def test_map_placement_constraint_details():
    oci_pcd = MagicMock()
    oci_pcd.strategy = "anti-affinity"
    oci_pcd.details = {"key": "value"}

    result = map_placement_constraint_details(oci_pcd)
    assert isinstance(result, PlacementConstraintDetails)
    assert result.strategy == "anti-affinity"
    assert result.details == {"key": "value"}

    assert map_placement_constraint_details(None) is None


@pytest.mark.asyncio
async def test_map_launch_options():
    oci_lo = oci.core.models.LaunchOptions(
        boot_volume_type="ISCSI",
        firmware="UEFI_64",
        network_type="VFIO",
        remote_data_volume_type="PARAVIRTUALIZED",
        is_pv_encryption_in_transit_enabled=True,
        is_consistent_volume_naming_enabled=True,
    )

    result = map_launch_options(oci_lo)
    assert isinstance(result, LaunchOptions)
    assert result.boot_volume_type == "ISCSI"
    assert result.firmware == "UEFI_64"
    assert result.network_type == "VFIO"
    assert result.remote_data_volume_type == "PARAVIRTUALIZED"
    assert result.is_pv_encryption_in_transit_enabled is True
    assert result.is_consistent_volume_naming_enabled is True

    assert map_launch_options(None) is None


@pytest.mark.asyncio
async def test_map_instance_options():
    oci_io = oci.core.models.InstanceOptions(are_legacy_imds_endpoints_disabled=True)

    result = map_instance_options(oci_io)
    assert isinstance(result, InstanceOptions)
    assert result.are_legacy_imds_endpoints_disabled is True

    assert map_instance_options(None) is None


@pytest.mark.asyncio
async def test_map_availability_config():
    oci_ac = oci.core.models.InstanceAvailabilityConfig(
        is_live_migration_preferred=True,
        recovery_action="RESTORE_INSTANCE",
    )

    result = map_availability_config(oci_ac)
    assert isinstance(result, InstanceAvailabilityConfig)
    assert result.is_live_migration_preferred is True
    assert result.recovery_action == "RESTORE_INSTANCE"

    assert map_availability_config(None) is None


@pytest.mark.asyncio
async def test_map_preemptible_config():
    oci_pc = oci.core.models.PreemptibleInstanceConfigDetails(
        preemption_action={"type": "TERMINATE", "preserve_boot_volume": False}
    )

    result = map_preemptible_config(oci_pc)
    assert isinstance(result, PreemptibleInstanceConfigDetails)
    assert result.preemption_action == {
        "type": "TERMINATE",
        "preserve_boot_volume": False,
    }

    assert map_preemptible_config(None) is None


@pytest.mark.asyncio
async def test_map_shape_config():
    oci_sc = oci.core.models.InstanceShapeConfig(
        ocpus=2.0,
        memory_in_gbs=16.0,
        vcpus=4,
        baseline_ocpu_utilization="BASELINE_1_1",
        local_disks=2,
        local_disks_total_size_in_gbs=100.0,
    )

    result = map_shape_config(oci_sc)
    assert isinstance(result, InstanceShapeConfig)
    assert result.ocpus == 2.0
    assert result.memory_in_gbs == 16.0
    assert result.vcpus == 4
    assert result.baseline_ocpu_utilization == "BASELINE_1_1"
    assert result.local_disks == 2
    assert result.local_disks_total_size_in_gbs == 100.0

    assert map_shape_config(None) is None


@pytest.mark.asyncio
async def test_map_source_details():
    oci_sd = oci.core.models.InstanceSourceViaImageDetails(
        source_type="image",
        image_id="ocid1.image.oc1..example",
        boot_volume_size_in_gbs=50,
    )

    result = map_source_details(oci_sd)
    assert isinstance(result, InstanceSourceDetails)
    assert result.source_type == "image"
    assert result.image_id == "ocid1.image.oc1..example"
    assert result.boot_volume_size_in_gbs == 50

    assert map_source_details(None) is None


@pytest.mark.asyncio
async def test_map_agent_config():
    oci_acfg = oci.core.models.InstanceAgentConfig(
        is_monitoring_disabled=True,
        is_management_disabled=True,
        are_all_plugins_disabled=True,
        plugins_config=[
            {"name": "plugin1", "desired_state": "ENABLED"},
            {"name": "plugin2", "desired_state": "DISABLED"},
        ],
    )

    result = map_agent_config(oci_acfg)
    assert isinstance(result, InstanceAgentConfig)
    assert result.is_monitoring_disabled is True
    assert result.is_management_disabled is True
    assert result.are_all_plugins_disabled is True
    assert result.plugins_config == [
        {"name": "plugin1", "desired_state": "ENABLED"},
        {"name": "plugin2", "desired_state": "DISABLED"},
    ]

    assert map_agent_config(None) is None


@pytest.mark.asyncio
async def test_map_platform_config():
    oci_pc = MagicMock()
    oci_pc.type = "AMD_VM"
    oci_pc.details = {"secure_boot": True}

    result = map_platform_config(oci_pc)
    assert isinstance(result, PlatformConfig)
    assert result.type == "AMD_VM"
    assert result.details == {"secure_boot": True}

    assert map_platform_config(None) is None


@pytest.mark.asyncio
async def test_map_licensing_configs():
    oci_lcs = [
        oci.core.models.LicensingConfig(license_type="BRING_YOUR_OWN_LICENSE"),
        oci.core.models.LicensingConfig(license_type="OCI_PROVIDED"),
    ]

    result = map_licensing_configs(oci_lcs)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].license_type == "BRING_YOUR_OWN_LICENSE"
    assert result[1].license_type == "OCI_PROVIDED"

    assert map_licensing_configs(None) is None
    assert map_licensing_configs([]) is None


@pytest.mark.asyncio
async def test_map_instance():
    oci_instance = oci.core.models.Instance(
        availability_domain="AD1",
        compartment_id="ocid1.compartment..example",
        display_name="test_instance",
        id="ocid1.instance..example",
        lifecycle_state="RUNNING",
        shape="VM.Standard.E2.1",
        time_created=datetime.now(),
    )

    result = map_instance(oci_instance)
    assert isinstance(result, Instance)
    assert result.availability_domain == "AD1"
    assert result.compartment_id == "ocid1.compartment..example"
    assert result.display_name == "test_instance"
    assert result.id == "ocid1.instance..example"
    assert result.lifecycle_state == "RUNNING"
    assert result.shape == "VM.Standard.E2.1"
    assert result.time_created == oci_instance.time_created


@pytest.mark.asyncio
async def test_map_instance_agent_features():
    oci_af = oci.core.models.InstanceAgentFeatures(
        is_monitoring_supported=True,
        is_management_supported=True,
    )

    result = map_instance_agent_features(oci_af)
    assert isinstance(result, InstanceAgentFeatures)
    assert result.is_monitoring_supported is True
    assert result.is_management_supported is True

    assert map_instance_agent_features(None) is None


@pytest.mark.asyncio
async def test_map_image():
    oci_image = oci.core.models.Image(
        id="ocid1.image..example",
        display_name="Oracle Linux 8",
        operating_system="Oracle Linux",
        operating_system_version="8",
        lifecycle_state="AVAILABLE",
        time_created=datetime.now(),
    )

    result = map_image(oci_image)
    assert isinstance(result, Image)
    assert result.id == "ocid1.image..example"
    assert result.display_name == "Oracle Linux 8"
    assert result.operating_system == "Oracle Linux"
    assert result.operating_system_version == "8"
    assert result.lifecycle_state == "AVAILABLE"
    assert result.time_created == oci_image.time_created


@pytest.mark.asyncio
async def test_map_request():
    oci_req = oci.request.Request(
        method="GET",
        url="https://example.com",
        query_params={"param": "value"},
        header_params={"header": "value"},
        body=None,
        response_type="json",
        enforce_content_headers=True,
    )

    result = map_request(oci_req)
    assert isinstance(result, Request)
    assert result.method == "GET"
    assert result.url == "https://example.com"
    assert result.query_params == {"param": "value"}
    assert result.header_params == {"header": "value"}
    assert result.body is None
    assert result.response_type == "json"
    assert result.enforce_content_headers is True

    assert map_request(None) is None


@pytest.mark.asyncio
async def test_map_response():
    oci_resp = oci.response.Response(
        status=200,
        headers={"opc-request-id": "req123"},
        data={"key": "value"},
        request=oci.request.Request(
            method="GET",
            url="https://example.com",
            query_params={"param": "value"},
            header_params={"header": "value"},
            body=None,
            response_type="json",
            enforce_content_headers=True,
        ),
    )
    oci_resp.next_page = "page2"

    result = map_response(oci_resp)
    assert isinstance(result, Response)
    assert result.status == 200
    assert result.headers == {"opc-request-id": "req123"}
    assert result.data == {"key": "value"}
    assert result.next_page == "page2"

    assert map_response(None) is None


@pytest.mark.asyncio
async def test_map_vnic_attachment():
    oci_va = oci.core.models.VnicAttachment(
        availability_domain="AD1",
        compartment_id="ocid1.compartment..example",
        display_name="vnic_attach",
        id="ocid1.vnicattachment..example",
        instance_id="ocid1.instance..example",
        lifecycle_state="ATTACHED",
        nic_index=0,
        subnet_id="ocid1.subnet..example",
        vlan_id="ocid1.vlan..example",
        time_created=datetime.now(),
        vlan_tag=0,
        vnic_id="ocid1.vnic..example",
    )

    result = map_vnic_attachment(oci_va)
    assert isinstance(result, VnicAttachment)
    assert result.availability_domain == "AD1"
    assert result.compartment_id == "ocid1.compartment..example"
    assert result.display_name == "vnic_attach"
    assert result.id == "ocid1.vnicattachment..example"
    assert result.instance_id == "ocid1.instance..example"
    assert result.lifecycle_state == "ATTACHED"
    assert result.nic_index == 0
    assert result.subnet_id == "ocid1.subnet..example"
    assert result.vlan_id == "ocid1.vlan..example"
    assert result.time_created == oci_va.time_created
    assert result.vlan_tag == 0
    assert result.vnic_id == "ocid1.vnic..example"


@pytest.mark.asyncio
async def test_map_response_derives_next_page_and_request_id_from_headers():
    # Do not set next_page attribute explicitly; rely on headers derivation
    oci_resp = oci.response.Response(
        status=200,
        headers={"opc-request-id": "req-abc", "opc-next-page": "np-123"},
        data="ok",
        request=None,
    )
    result = map_response(oci_resp)
    assert isinstance(result, Response)
    assert result.request_id == "req-abc"
    assert result.next_page == "np-123"
    assert result.has_next_page is True


@pytest.mark.asyncio
async def test_map_response_data_instance_object_and_list():
    # Single instance object path
    inst = oci.core.models.Instance(id="ocid1.instance..single", display_name="one")
    oci_resp_single = oci.response.Response(status=200, headers={}, data=inst, request=None)
    mapped_single = map_response(oci_resp_single)
    assert isinstance(mapped_single, Response)
    assert isinstance(mapped_single.data, Instance)
    assert mapped_single.data.id == "ocid1.instance..single"
    assert mapped_single.data.display_name == "one"

    # List of instances path
    inst2 = oci.core.models.Instance(id="ocid1.instance..two", display_name="two")
    oci_resp_list = oci.response.Response(status=200, headers={}, data=[inst, inst2], request=None)
    mapped_list = map_response(oci_resp_list)
    assert isinstance(mapped_list.data, list)
    assert all(isinstance(x, Instance) for x in mapped_list.data)
    ids = {x.id for x in mapped_list.data}
    assert ids == {"ocid1.instance..single", "ocid1.instance..two"}


@pytest.mark.asyncio
async def test__oci_to_dict_variants(monkeypatch):
    # Import private helper
    from oracle.oci_compute_mcp_server.models import _oci_to_dict as helper

    # 1) dict passes through
    d = {"a": 1}
    assert helper(d) == d

    # 2) __dict__ fallback when oci.util.to_dict raises
    class Dummy:
        def __init__(self):
            self.x = 42
            self._private = "ignore"

    def boom(_):
        raise RuntimeError("to_dict failed")

    # Patch oci.util.to_dict to raise to exercise except path
    import oci.util

    monkeypatch.setattr(oci.util, "to_dict", boom, raising=True)

    dd = Dummy()
    out = helper(dd)
    # Should fall back to __dict__ filtered of private keys
    assert isinstance(out, dict)
    assert out.get("x") == 42
    assert "_private" not in out

    # 3) None returns None
    assert helper(None) is None

    # 4) Unsupported type returns None
    class NoDict:
        __slots__ = ()  # no __dict__

    assert helper(NoDict()) is None


@pytest.mark.asyncio
async def test_map_platform_config_with_plain_dict_input():
    pc_dict = {"type": "INTEL_VM", "secure_boot": False, "something_else": 123}
    # Passing a dict should exercise the data.get('type') branch and pop('type')
    result = map_platform_config(pc_dict)
    assert isinstance(result, PlatformConfig)
    assert result.type == "INTEL_VM"
    # 'type' should be removed from details; remaining keys preserved
    assert result.details == {"secure_boot": False, "something_else": 123}
