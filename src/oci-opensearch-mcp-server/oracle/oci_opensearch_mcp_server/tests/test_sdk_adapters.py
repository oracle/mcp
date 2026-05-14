"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import oci

from oracle.oci_opensearch_mcp_server.sdk_adapters import (
    build_backup_opensearch_cluster_details,
    build_create_opensearch_cluster_details,
    build_resize_opensearch_cluster_horizontal_details,
    build_resize_opensearch_cluster_vertical_details,
    build_update_opensearch_cluster_details,
)


class TestSdkAdapters:
    def test_build_create_opensearch_cluster_details_converts_nested_models(self):
        payload = build_create_opensearch_cluster_details(
            {
                "display_name": "cluster-one",
                "compartment_id": "ocid1.compartment.oc1..compartment1",
                "software_version": "3.2.0",
                "master_node_host_type": "FLEX",
                "master_node_host_shape": "VM.Standard.A1.Flex",
                "vcn_id": "ocid1.vcn.oc1..vcn1",
                "vcn_compartment_id": "ocid1.compartment.oc1..network1",
                "subnet_id": "ocid1.subnet.oc1..subnet1",
                "subnet_compartment_id": "ocid1.compartment.oc1..network1",
                "security_master_user_name": "admin1",
                "security_master_user_password_hash": "pbkdf2_stretch_1000$SALT$HASH",
                "security_saml_config": {
                    "is_enabled": True,
                    "idp_entity_id": "entity-id",
                },
                "maintenance_details": {"notification_email_ids": ["admin@example.com"]},
            }
        )

        assert isinstance(payload, oci.opensearch.models.CreateOpensearchClusterDetails)
        assert payload.compartment_id == "ocid1.compartment.oc1..compartment1"
        assert payload.vcn_compartment_id == "ocid1.compartment.oc1..network1"
        assert payload.subnet_compartment_id == "ocid1.compartment.oc1..network1"
        assert isinstance(payload.security_saml_config, oci.opensearch.models.SecuritySamlConfig)
        assert isinstance(payload.maintenance_details, oci.opensearch.models.CreateMaintenanceDetails)

    def test_build_update_opensearch_cluster_details_converts_nested_models(self):
        payload = build_update_opensearch_cluster_details(
            {
                "display_name": "cluster-one-updated",
                "backup_policy": {"is_enabled": True, "retention_in_days": 7},
                "security_saml_config": {
                    "is_enabled": True,
                    "idp_entity_id": "entity-id",
                },
                "maintenance_details": {"notification_email_ids": ["admin@example.com"]},
                "load_balancer_config": {
                    "load_balancer_service_type": "LOAD_BALANCER",
                    "load_balancer_min_bandwidth_in_mbps": 10,
                    "load_balancer_max_bandwidth_in_mbps": 100,
                },
                "certificate_config": {
                    "cluster_certificate_mode": "OPENSEARCH_SERVICE",
                    "dashboard_certificate_mode": "OPENSEARCH_SERVICE",
                },
            }
        )

        assert isinstance(payload, oci.opensearch.models.UpdateOpensearchClusterDetails)
        assert payload.display_name == "cluster-one-updated"
        assert isinstance(payload.backup_policy, oci.opensearch.models.BackupPolicy)
        assert isinstance(payload.security_saml_config, oci.opensearch.models.SecuritySamlConfig)
        assert isinstance(payload.maintenance_details, oci.opensearch.models.UpdateMaintenanceDetails)
        assert "load_balancer_config" in payload.swagger_types
        assert "certificate_config" in payload.swagger_types
        assert isinstance(payload.load_balancer_config, oci.opensearch.models.LoadBalancerConfig)
        assert isinstance(payload.certificate_config, oci.opensearch.models.CertificateConfig)
        assert payload.load_balancer_config.load_balancer_min_bandwidth_in_mbps == 10
        assert payload.certificate_config.cluster_certificate_mode == "OPENSEARCH_SERVICE"

    def test_build_resize_opensearch_cluster_vertical_details(self):
        payload = build_resize_opensearch_cluster_vertical_details(
            {"master_node_host_ocpu_count": 8, "data_node_storage_gb": 100}
        )

        assert isinstance(payload, oci.opensearch.models.ResizeOpensearchClusterVerticalDetails)
        assert payload.master_node_host_ocpu_count == 8
        assert payload.data_node_storage_gb == 100

    def test_build_resize_opensearch_cluster_horizontal_details(self):
        payload = build_resize_opensearch_cluster_horizontal_details(
            {"data_node_count": 6, "search_node_count": 3}
        )

        assert isinstance(payload, oci.opensearch.models.ResizeOpensearchClusterHorizontalDetails)
        assert payload.data_node_count == 6
        assert payload.search_node_count == 3

    def test_build_backup_opensearch_cluster_details(self):
        payload = build_backup_opensearch_cluster_details(
            {
                "compartment_id": "ocid1.compartment.oc1..compartment1",
                "display_name": "backup-1",
            }
        )

        assert isinstance(payload, oci.opensearch.models.BackupOpensearchClusterDetails)
        assert payload.compartment_id == "ocid1.compartment.oc1..compartment1"
        assert payload.display_name == "backup-1"
