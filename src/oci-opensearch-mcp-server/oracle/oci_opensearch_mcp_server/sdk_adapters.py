"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

import oci


def _build_security_saml_config(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("security_saml_config"), dict):
        payload["security_saml_config"] = oci.opensearch.models.SecuritySamlConfig(
            **payload["security_saml_config"]
        )
    return payload


def _build_backup_policy(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("backup_policy"), dict):
        payload["backup_policy"] = oci.opensearch.models.BackupPolicy(**payload["backup_policy"])
    return payload


def _build_outbound_cluster_config(payload: dict[str, Any]) -> dict[str, Any]:
    outbound_cluster_config = payload.get("outbound_cluster_config")
    if isinstance(outbound_cluster_config, dict):
        outbound_clusters = outbound_cluster_config.get("outbound_clusters")
        if isinstance(outbound_clusters, list):
            outbound_cluster_config["outbound_clusters"] = [
                oci.opensearch.models.OutboundClusterSummary(**cluster)
                if isinstance(cluster, dict)
                else cluster
                for cluster in outbound_clusters
            ]
        payload["outbound_cluster_config"] = oci.opensearch.models.OutboundClusterConfig(
            **outbound_cluster_config
        )
    return payload


def _build_create_maintenance_details(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("maintenance_details"), dict):
        payload["maintenance_details"] = oci.opensearch.models.CreateMaintenanceDetails(
            **payload["maintenance_details"]
        )
    return payload


def _build_update_maintenance_details(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("maintenance_details"), dict):
        payload["maintenance_details"] = oci.opensearch.models.UpdateMaintenanceDetails(
            **payload["maintenance_details"]
        )
    return payload


def _build_load_balancer_config(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("load_balancer_config"), dict):
        load_balancer_model = getattr(oci.opensearch.models, "LoadBalancerConfig", None)
        if load_balancer_model is not None:
            payload["load_balancer_config"] = load_balancer_model(**payload["load_balancer_config"])
    return payload


def _build_certificate_config(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("certificate_config"), dict):
        certificate_model = getattr(oci.opensearch.models, "CertificateConfig", None)
        if certificate_model is not None:
            payload["certificate_config"] = certificate_model(**payload["certificate_config"])
    return payload


def build_create_opensearch_cluster_details(
    create_payload: dict[str, Any],
) -> oci.opensearch.models.CreateOpensearchClusterDetails:
    payload = dict(create_payload)
    payload = _build_security_saml_config(payload)
    payload = _build_backup_policy(payload)
    payload = _build_outbound_cluster_config(payload)
    payload = _build_create_maintenance_details(payload)
    payload = _build_load_balancer_config(payload)
    payload = _build_certificate_config(payload)
    return oci.opensearch.models.CreateOpensearchClusterDetails(**payload)


def build_update_opensearch_cluster_details(
    update_payload: dict[str, Any],
) -> oci.opensearch.models.UpdateOpensearchClusterDetails:
    payload = dict(update_payload)
    payload = _build_security_saml_config(payload)
    payload = _build_backup_policy(payload)
    payload = _build_outbound_cluster_config(payload)
    payload = _build_update_maintenance_details(payload)
    payload = _build_load_balancer_config(payload)
    payload = _build_certificate_config(payload)
    supported_keys = set(oci.opensearch.models.UpdateOpensearchClusterDetails().swagger_types.keys())
    payload = {key: value for key, value in payload.items() if key in supported_keys}
    return oci.opensearch.models.UpdateOpensearchClusterDetails(**payload)


def build_backup_opensearch_cluster_details(
    backup_payload: dict[str, Any],
) -> oci.opensearch.models.BackupOpensearchClusterDetails:
    return oci.opensearch.models.BackupOpensearchClusterDetails(**backup_payload)


def build_resize_opensearch_cluster_vertical_details(
    resize_payload: dict[str, Any],
) -> oci.opensearch.models.ResizeOpensearchClusterVerticalDetails:
    return oci.opensearch.models.ResizeOpensearchClusterVerticalDetails(**resize_payload)


def build_resize_opensearch_cluster_horizontal_details(
    resize_payload: dict[str, Any],
) -> oci.opensearch.models.ResizeOpensearchClusterHorizontalDetails:
    return oci.opensearch.models.ResizeOpensearchClusterHorizontalDetails(**resize_payload)
