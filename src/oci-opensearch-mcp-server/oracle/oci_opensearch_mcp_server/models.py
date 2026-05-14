"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

HOST_TYPE_FLEX = "FLEX"
HOST_TYPE_BM = "BM"
SECURITY_MODE_ENFORCING = "ENFORCING"
SHAPE_CATALOG_GUIDANCE = "Use a value returned by `list_opensearch_cluster_shapes`."

HOST_TYPE_ALLOWED_VALUES: tuple[str, ...] = (HOST_TYPE_FLEX, HOST_TYPE_BM)
HOST_TYPE_FLEX_ONLY_ALLOWED_VALUES: tuple[str, ...] = (HOST_TYPE_FLEX,)

CREATE_CLUSTER_MINIMAL_DETAILS_EXAMPLE: dict[str, Any] = {
    "display_name": "my-opensearch-cluster",
    "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
    "software_version": "3.2.0",
    "vcn_id": "ocid1.vcn.oc1..exampleuniqueID",
    "vcn_compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
    "subnet_id": "ocid1.subnet.oc1..exampleuniqueID",
    "subnet_compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
    "security_master_user_name": "admin1",
    "security_master_user_password_hash": "pbkdf2_stretch_1000$...",
}

CREATE_CLUSTER_NON_SHAPE_DEFAULT_DETAILS: dict[str, Any] = {
    "master_node_count": 1,
    "master_node_host_type": HOST_TYPE_FLEX,
    "master_node_host_ocpu_count": 2,
    "master_node_host_memory_gb": 20,
    "data_node_count": 1,
    "data_node_host_type": HOST_TYPE_FLEX,
    "data_node_host_ocpu_count": 4,
    "data_node_host_memory_gb": 20,
    "data_node_storage_gb": 50,
    "opendashboard_node_count": 1,
    "opendashboard_node_host_ocpu_count": 2,
    "opendashboard_node_host_memory_gb": 16,
}

CREATE_CLUSTER_MINIMAL_EXAMPLE = json.dumps(
    {"create_opensearch_cluster_details": CREATE_CLUSTER_MINIMAL_DETAILS_EXAMPLE},
    separators=(", ", ": "),
)

BACKUP_CLUSTER_MINIMAL_DETAILS_EXAMPLE: dict[str, Any] = {
    "compartment_id": "ocid1.compartment.oc1..exampleuniqueID",
    "display_name": "my-opensearch-backup",
}

BACKUP_CLUSTER_MINIMAL_EXAMPLE = json.dumps(
    {"backup_details": BACKUP_CLUSTER_MINIMAL_DETAILS_EXAMPLE},
    separators=(", ", ": "),
)

CREATE_CLUSTER_REQUIRED_FIELDS: tuple[str, ...] = (
    "display_name",
    "compartment_id",
    "software_version",
    "vcn_id",
    "vcn_compartment_id",
    "subnet_id",
    "subnet_compartment_id",
    "security_master_user_name",
    "security_master_user_password_hash",
)


class CreateOpensearchClusterDetailsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = Field(None, description="Cluster display name.")
    compartment_id: Optional[str] = Field(None, description="Compartment OCID for the cluster.")
    software_version: Optional[str] = Field(None, description="OpenSearch software version.")
    master_node_count: Optional[int] = Field(None, description="Master node count.")
    master_node_host_type: Optional[str] = Field(None, description="Master node host type.")
    master_node_host_bare_metal_shape: Optional[str] = Field(
        None, description="Master node bare metal shape."
    )
    master_node_host_shape: Optional[str] = Field(
        None,
        description=f"Master node VM shape. {SHAPE_CATALOG_GUIDANCE}",
    )
    master_node_host_ocpu_count: Optional[int] = Field(None, description="Master node OCPU count.")
    master_node_host_memory_gb: Optional[int] = Field(None, description="Master node memory in GB.")
    data_node_count: Optional[int] = Field(None, description="Data node count.")
    data_node_host_type: Optional[str] = Field(None, description="Data node host type.")
    data_node_host_bare_metal_shape: Optional[str] = Field(None, description="Data node bare metal shape.")
    data_node_host_shape: Optional[str] = Field(
        None,
        description=f"Data node VM shape. {SHAPE_CATALOG_GUIDANCE}",
    )
    data_node_host_ocpu_count: Optional[int] = Field(None, description="Data node OCPU count.")
    data_node_host_memory_gb: Optional[int] = Field(None, description="Data node memory in GB.")
    data_node_storage_gb: Optional[int] = Field(None, description="Data node storage in GB.")
    opendashboard_node_host_shape: Optional[str] = Field(
        None,
        description=f"OpenDashboard node VM shape. {SHAPE_CATALOG_GUIDANCE}",
    )
    opendashboard_node_count: Optional[int] = Field(None, description="OpenDashboard node count.")
    opendashboard_node_host_ocpu_count: Optional[int] = Field(
        None, description="OpenDashboard node OCPU count."
    )
    opendashboard_node_host_memory_gb: Optional[int] = Field(
        None, description="OpenDashboard node memory in GB."
    )
    search_node_count: Optional[int] = Field(None, description="Search node count.")
    search_node_host_type: Optional[str] = Field(None, description="Search node host type.")
    search_node_host_shape: Optional[str] = Field(
        None,
        description=f"Search node VM shape. {SHAPE_CATALOG_GUIDANCE}",
    )
    search_node_host_ocpu_count: Optional[int] = Field(None, description="Search node OCPU count.")
    search_node_host_memory_gb: Optional[int] = Field(None, description="Search node memory in GB.")
    search_node_storage_gb: Optional[int] = Field(None, description="Search node storage in GB.")
    ml_node_count: Optional[int] = Field(None, description="ML node count.")
    ml_node_host_type: Optional[str] = Field(None, description="ML node host type.")
    ml_node_host_shape: Optional[str] = Field(
        None,
        description=f"ML node VM shape. {SHAPE_CATALOG_GUIDANCE}",
    )
    ml_node_host_ocpu_count: Optional[int] = Field(None, description="ML node OCPU count.")
    ml_node_host_memory_gb: Optional[int] = Field(None, description="ML node memory in GB.")
    ml_node_storage_gb: Optional[int] = Field(None, description="ML node storage in GB.")
    vcn_id: Optional[str] = Field(None, description="VCN OCID for cluster networking.")
    subnet_id: Optional[str] = Field(None, description="Subnet OCID for cluster networking.")
    nsg_id: Optional[str] = Field(None, description="Network security group OCID for cluster networking.")
    vcn_compartment_id: Optional[str] = Field(
        None,
        description="Compartment OCID where the VCN is located.",
    )
    subnet_compartment_id: Optional[str] = Field(
        None,
        description="Compartment OCID where the subnet is located.",
    )
    security_mode: Optional[str] = Field(None, description="Security mode. Only ENFORCING is supported.")
    security_master_user_name: Optional[str] = Field(None, description="Security admin username.")
    security_master_user_password_hash: Optional[str] = Field(
        None,
        description=(
            "Security admin password hash in OCI-compatible pbkdf2_stretch_1000 format. "
            "Generate it externally as documented by OCI before calling this tool."
        ),
    )
    security_saml_config: Optional["SecuritySamlConfigInput"] = Field(
        None, description="SAML security configuration."
    )
    backup_policy: Optional["BackupPolicyInput"] = Field(None, description="Backup policy configuration.")
    reverse_connection_endpoint_customer_ips: Optional[list[str]] = Field(
        None,
        description="Customer IPs for reverse connection endpoint.",
    )
    inbound_cluster_ids: Optional[list[str]] = Field(None, description="Inbound cluster OCIDs.")
    outbound_cluster_config: Optional["OutboundClusterConfigInput"] = Field(
        None, description="Outbound cluster configuration."
    )
    maintenance_details: Optional["CreateMaintenanceDetailsInput"] = Field(
        None, description="Maintenance settings."
    )
    load_balancer_config: Optional["LoadBalancerConfigInput"] = Field(
        None, description="Load balancer configuration."
    )
    certificate_config: Optional["CertificateConfigInput"] = Field(
        None, description="Certificate configuration."
    )
    freeform_tags: Optional[dict[str, str]] = Field(None, description="Freeform tags.")
    defined_tags: Optional[dict[str, dict[str, Any]]] = Field(None, description="Defined tags.")
    system_tags: Optional[dict[str, dict[str, Any]]] = Field(None, description="System tags.")
    security_attributes: Optional[dict[str, dict[str, Any]]] = Field(None, description="Security attributes.")


class SecuritySamlConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_enabled: Optional[bool] = Field(None, description="Whether SAML is enabled.")
    idp_metadata_content: Optional[str] = Field(None, description="Identity provider metadata XML content.")
    idp_entity_id: Optional[str] = Field(None, description="Identity provider entity ID.")
    opendashboard_url: Optional[str] = Field(None, description="OpenDashboard URL for SAML callbacks.")
    admin_backend_role: Optional[str] = Field(None, description="Admin backend role.")
    subject_key: Optional[str] = Field(None, description="SAML subject key.")
    roles_key: Optional[str] = Field(None, description="SAML roles key.")


class BackupPolicyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_enabled: Optional[bool] = Field(None, description="Whether automated backups are enabled.")
    retention_in_days: Optional[int] = Field(None, description="Backup retention in days.")
    frequency_in_hours: Optional[int] = Field(None, description="Backup frequency in hours.")


class OutboundClusterSummaryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = Field(None, description="Display name for the outbound cluster link.")
    ping_schedule: Optional[str] = Field(None, description="Ping schedule for the outbound cluster.")
    is_skip_unavailable: Optional[bool] = Field(
        None, description="Whether to skip unavailable outbound clusters."
    )
    seed_cluster_id: Optional[str] = Field(None, description="Seed cluster OCID.")
    mode: Optional[str] = Field(None, description="Outbound cluster mode.")


class OutboundClusterConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_enabled: Optional[bool] = Field(None, description="Whether outbound cluster config is enabled.")
    outbound_clusters: Optional[list[OutboundClusterSummaryInput]] = Field(
        None,
        description="Outbound cluster definitions.",
    )


class CreateMaintenanceDetailsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notification_email_ids: Optional[list[str]] = Field(
        None, description="Maintenance notification email IDs."
    )


class UpdateMaintenanceDetailsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notification_email_ids: Optional[list[str]] = Field(
        None, description="Maintenance notification email IDs."
    )


class LoadBalancerConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    load_balancer_service_type: Optional[str] = Field(None, description="Load balancer service type.")
    load_balancer_min_bandwidth_in_mbps: Optional[int] = Field(
        None,
        description="Minimum load balancer bandwidth in Mbps.",
    )
    load_balancer_max_bandwidth_in_mbps: Optional[int] = Field(
        None,
        description="Maximum load balancer bandwidth in Mbps.",
    )


class CertificateConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_certificate_mode: Optional[str] = Field(
        None,
        description=(
            "OpenSearch API certificate mode. Use `OCI_CERTIFICATES_SERVICE` for BYOC certificates "
            "stored in OCI Certificates service or `OPENSEARCH_SERVICE` for service-managed certificates."
        ),
    )
    dashboard_certificate_mode: Optional[str] = Field(
        None,
        description=(
            "OpenDashboard certificate mode. Use `OCI_CERTIFICATES_SERVICE` for BYOC certificates "
            "stored in OCI Certificates service or `OPENSEARCH_SERVICE` for service-managed certificates."
        ),
    )
    open_search_api_certificate_id: Optional[str] = Field(
        None,
        description="OCI certificate OCID for the OpenSearch API. Required when cluster_certificate_mode is OCI_CERTIFICATES_SERVICE.",
    )
    open_search_dashboard_certificate_id: Optional[str] = Field(
        None,
        description=(
            "OCI certificate OCID for OpenDashboard. Required when dashboard_certificate_mode is "
            "OCI_CERTIFICATES_SERVICE."
        ),
    )


class UpdateOpensearchClusterDetailsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = Field(None, description="Updated cluster display name.")
    software_version: Optional[str] = Field(None, description="Updated OpenSearch software version.")
    security_mode: Optional[str] = Field(
        None,
        description="Updated security mode. Required for any security config update.",
    )
    security_master_user_name: Optional[str] = Field(
        None,
        description=(
            "Updated security admin username. Required with `security_master_user_password_hash` "
            "when updating the local master-user password."
        ),
    )
    security_master_user_password_hash: Optional[str] = Field(
        None,
        description=(
            "Updated security admin password hash in OCI-compatible pbkdf2_stretch_1000 format. "
            "Requires `security_mode` and `security_master_user_name`."
        ),
    )
    security_saml_config: Optional[SecuritySamlConfigInput] = Field(
        None, description="Updated SAML security configuration."
    )
    backup_policy: Optional[BackupPolicyInput] = Field(
        None, description="Updated backup policy configuration."
    )
    reverse_connection_endpoint_customer_ips: Optional[list[str]] = Field(
        None,
        description="Updated customer IPs for reverse connection endpoint.",
    )
    outbound_cluster_config: Optional[OutboundClusterConfigInput] = Field(
        None,
        description="Updated outbound cluster configuration.",
    )
    maintenance_details: Optional[UpdateMaintenanceDetailsInput] = Field(
        None,
        description="Updated maintenance settings.",
    )
    load_balancer_config: Optional[LoadBalancerConfigInput] = Field(
        None, description="Updated load balancer configuration."
    )
    certificate_config: Optional[CertificateConfigInput] = Field(
        None, description="Updated certificate configuration."
    )
    security_attributes: Optional[dict[str, dict[str, Any]]] = Field(
        None,
        description="Updated security attributes.",
    )
    freeform_tags: Optional[dict[str, str]] = Field(None, description="Updated freeform tags.")
    defined_tags: Optional[dict[str, dict[str, Any]]] = Field(None, description="Updated defined tags.")


class ResizeOpensearchClusterVerticalDetailsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    master_node_host_ocpu_count: Optional[int] = Field(None, description="Updated master node OCPU count.")
    master_node_host_memory_gb: Optional[int] = Field(None, description="Updated master node memory in GB.")
    master_node_host_shape: Optional[str] = Field(
        None,
        description=f"Updated master node shape. {SHAPE_CATALOG_GUIDANCE}",
    )
    data_node_host_ocpu_count: Optional[int] = Field(None, description="Updated data node OCPU count.")
    data_node_host_memory_gb: Optional[int] = Field(None, description="Updated data node memory in GB.")
    data_node_storage_gb: Optional[int] = Field(None, description="Updated data node storage in GB.")
    data_node_host_shape: Optional[str] = Field(
        None,
        description=f"Updated data node shape. {SHAPE_CATALOG_GUIDANCE}",
    )
    opendashboard_node_host_ocpu_count: Optional[int] = Field(
        None,
        description=(
            "Updated OpenDashboard node OCPU count. Only valid after OpenDashboard nodes exist; "
            "use horizontal `opendashboard_node_count` first when current count is 0."
        ),
    )
    opendashboard_node_host_memory_gb: Optional[int] = Field(
        None,
        description=(
            "Updated OpenDashboard node memory in GB. Only valid after OpenDashboard nodes exist; "
            "use horizontal `opendashboard_node_count` first when current count is 0."
        ),
    )
    opendashboard_node_host_shape: Optional[str] = Field(
        None,
        description=(
            f"Updated OpenDashboard node shape. {SHAPE_CATALOG_GUIDANCE} "
            "Only valid after OpenDashboard nodes exist; use horizontal `opendashboard_node_count` "
            "first when current count is 0."
        ),
    )
    search_node_host_shape: Optional[str] = Field(
        None,
        description=(
            f"Updated search node shape. {SHAPE_CATALOG_GUIDANCE} "
            "When current search node count is 0, provide the full search node vertical config "
            "to create 1 search node, then use horizontal resize to scale count."
        ),
    )
    search_node_host_ocpu_count: Optional[int] = Field(
        None,
        description=(
            "Updated search node OCPU count. When current search node count is 0, provide this with "
            "search_node_host_memory_gb and search_node_storage_gb to create 1 search node, then use "
            "horizontal resize to scale count."
        ),
    )
    search_node_host_memory_gb: Optional[int] = Field(
        None,
        description=(
            "Updated search node memory in GB. When current search node count is 0, provide this with "
            "search_node_host_ocpu_count and search_node_storage_gb to create 1 search node, then use "
            "horizontal resize to scale count."
        ),
    )
    search_node_storage_gb: Optional[int] = Field(
        None,
        description=(
            "Updated search node storage in GB. When current search node count is 0, provide this with "
            "search_node_host_ocpu_count and search_node_host_memory_gb to create 1 search node, then use "
            "horizontal resize to scale count."
        ),
    )
    ml_node_host_shape: Optional[str] = Field(
        None,
        description=(
            f"Updated ML node shape. {SHAPE_CATALOG_GUIDANCE} "
            "When current ML node count is 0, provide the full ML node vertical config "
            "to create 1 ML node, then use horizontal resize to scale count."
        ),
    )
    ml_node_host_ocpu_count: Optional[int] = Field(
        None,
        description=(
            "Updated ML node OCPU count. When current ML node count is 0, provide this with "
            "ml_node_host_memory_gb and ml_node_storage_gb to create 1 ML node, then use horizontal "
            "resize to scale count."
        ),
    )
    ml_node_host_memory_gb: Optional[int] = Field(
        None,
        description=(
            "Updated ML node memory in GB. When current ML node count is 0, provide this with "
            "ml_node_host_ocpu_count and ml_node_storage_gb to create 1 ML node, then use horizontal "
            "resize to scale count."
        ),
    )
    ml_node_storage_gb: Optional[int] = Field(
        None,
        description=(
            "Updated ML node storage in GB. When current ML node count is 0, provide this with "
            "ml_node_host_ocpu_count and ml_node_host_memory_gb to create 1 ML node, then use horizontal "
            "resize to scale count."
        ),
    )
    freeform_tags: Optional[dict[str, str]] = Field(None, description="Updated freeform tags.")
    defined_tags: Optional[dict[str, dict[str, Any]]] = Field(None, description="Updated defined tags.")


class ResizeOpensearchClusterHorizontalDetailsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    master_node_count: Optional[int] = Field(None, description="Updated master node count.")
    data_node_count: Optional[int] = Field(None, description="Updated data node count.")
    opendashboard_node_count: Optional[int] = Field(
        None,
        description="Updated OpenDashboard node count. Can create OpenDashboard nodes from count 0 using service defaults.",
    )
    search_node_count: Optional[int] = Field(
        None,
        description=(
            "Updated search node count. Cannot create search nodes from count 0; use vertical search node "
            "host config first to create 1 search node, then use horizontal resize to scale count."
        ),
    )
    ml_node_count: Optional[int] = Field(
        None,
        description=(
            "Updated ML node count. Cannot create ML nodes from count 0; use vertical ML node host config "
            "first to create 1 ML node, then use horizontal resize to scale count."
        ),
    )
    freeform_tags: Optional[dict[str, str]] = Field(None, description="Updated freeform tags.")
    defined_tags: Optional[dict[str, dict[str, Any]]] = Field(None, description="Updated defined tags.")


class BackupOpensearchClusterDetailsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compartment_id: Optional[str] = Field(
        None, description="Compartment OCID where the cluster backup is located."
    )
    display_name: Optional[str] = Field(None, description="Display name for the cluster backup.")


CreateOpensearchClusterDetailsInput.model_rebuild()
