"""OCI Managed Kafka API wrapper for all control plane operations.

This module wraps the OCI Python SDK's ``KafkaClusterClient``
(``oci.managed_kafka``) to manage OCI Streaming with Apache Kafka
clusters, configurations, superusers, and work requests.

The client is lazily initialized to avoid import errors when the
OCI SDK is not installed or ``~/.oci/config`` is not present.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_OCI_SDK_NOT_CONFIGURED = "OCI SDK not configured"


# -------------------------------------------------------------------------
# Private serializers
# -------------------------------------------------------------------------


def _serialize_cluster(cluster: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": cluster.id,
        "display_name": cluster.display_name,
        "compartment_id": cluster.compartment_id,
        "lifecycle_state": cluster.lifecycle_state,
        "kafka_version": cluster.kafka_version,
        "cluster_type": cluster.cluster_type,
        "coordination_type": cluster.coordination_type,
        "time_created": str(cluster.time_created),
        "time_updated": str(cluster.time_updated),
    }
    if cluster.broker_shape:
        result["broker_shape"] = {
            "node_count": cluster.broker_shape.node_count,
            "ocpu_count": cluster.broker_shape.ocpu_count,
            "storage_size_in_gbs": cluster.broker_shape.storage_size_in_gbs,
        }
    if cluster.kafka_bootstrap_urls:
        result["bootstrap_urls"] = [
            {"name": url.name, "url": url.url} for url in cluster.kafka_bootstrap_urls
        ]
    if getattr(cluster, "cluster_config_id", None):
        result["cluster_config_id"] = cluster.cluster_config_id
    if getattr(cluster, "cluster_config_version", None):
        result["cluster_config_version"] = cluster.cluster_config_version
    if cluster.freeform_tags:
        result["freeform_tags"] = cluster.freeform_tags
    if cluster.defined_tags:
        result["defined_tags"] = cluster.defined_tags
    return result


def _serialize_cluster_summary(item: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": item.id,
        "display_name": item.display_name,
        "lifecycle_state": item.lifecycle_state,
        "compartment_id": item.compartment_id,
        "kafka_version": item.kafka_version,
        "cluster_type": item.cluster_type,
        "time_created": str(item.time_created),
    }
    if item.broker_shape:
        result["broker_shape"] = {
            "node_count": item.broker_shape.node_count,
            "ocpu_count": item.broker_shape.ocpu_count,
            "storage_size_in_gbs": item.broker_shape.storage_size_in_gbs,
        }
    return result


def _serialize_cluster_config(config: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": config.id,
        "display_name": config.display_name,
        "compartment_id": config.compartment_id,
        "lifecycle_state": config.lifecycle_state,
        "time_created": str(config.time_created),
        "time_updated": str(config.time_updated),
    }
    if getattr(config, "latest_config", None):
        result["latest_version"] = _serialize_config_version(config.latest_config)
    if getattr(config, "freeform_tags", None):
        result["freeform_tags"] = config.freeform_tags
    return result


def _serialize_cluster_config_summary(item: Any) -> dict[str, Any]:
    return {
        "id": item.id,
        "display_name": item.display_name,
        "compartment_id": item.compartment_id,
        "lifecycle_state": item.lifecycle_state,
        "time_created": str(item.time_created),
    }


def _serialize_config_version(version: Any) -> dict[str, Any]:
    return {
        "version_number": version.version_number,
        "kafka_cluster_config_id": version.kafka_cluster_config_id,
        "lifecycle_state": version.lifecycle_state,
        "time_created": str(version.time_created),
    }


def _serialize_work_request(wr: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": wr.id,
        "operation_type": wr.operation_type,
        "status": wr.status,
        "compartment_id": wr.compartment_id,
        "percent_complete": wr.percent_complete,
        "time_accepted": str(wr.time_accepted),
    }
    if wr.time_started:
        result["time_started"] = str(wr.time_started)
    if wr.time_finished:
        result["time_finished"] = str(wr.time_finished)
    if getattr(wr, "resources", None):
        result["resources"] = [
            {"resource_type": r.resource_type, "resource_id": r.resource_id} for r in wr.resources
        ]
    return result


class OciKafkaClient:
    """Wrapper for OCI Managed Kafka control plane operations.

    Uses ``oci.managed_kafka.KafkaClusterClient`` to manage
    OCI Kafka clusters (``ocid1.kafkacluster.*``), cluster
    configurations, config versions, superusers, work requests,
    and available node shapes.
    """

    def __init__(self, config_file: str = "~/.oci/config", profile: str = "DEFAULT") -> None:
        self._config_file = config_file
        self._profile = profile
        self._client = None
        self._oci_config: dict[str, Any] | None = None

    def _load_oci_config(self) -> dict[str, Any] | None:
        """Load and cache the OCI config dict from ~/.oci/config."""
        if self._oci_config is None:
            try:
                import oci

                self._oci_config = oci.config.from_file(self._config_file, self._profile)
            except Exception as e:
                logger.warning("OCI SDK not configured: %s. OCI operations will be unavailable.", e)
                return None
        return self._oci_config

    def _get_client(self) -> Any:
        """Lazily initialize the OCI Managed Kafka KafkaClusterClient."""
        if self._client is None:
            config = self._load_oci_config()
            if config is None:
                return None
            try:
                from oci.managed_kafka import KafkaClusterClient

                self._client = KafkaClusterClient(config)
            except Exception as e:
                logger.warning("Failed to create KafkaClusterClient: %s", e)
                return None
        return self._client

    def get_tenancy_id(self) -> str | None:
        """Get the tenancy OCID from the loaded OCI config."""
        self._load_oci_config()
        if self._oci_config is not None:
            return self._oci_config.get("tenancy")
        return None

    # -------------------------------------------------------------------------
    # Cluster operations
    # -------------------------------------------------------------------------

    def get_kafka_cluster(self, kafka_cluster_id: str) -> dict[str, Any]:
        """Get detailed metadata for a Kafka cluster."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.get_kafka_cluster(kafka_cluster_id=kafka_cluster_id)
            return _serialize_cluster(response.data)
        except Exception as e:
            return {"error": f"Failed to get Kafka cluster: {e}"}

    def list_kafka_clusters(self, compartment_id: str) -> dict[str, Any]:
        """List all OCI Managed Kafka clusters in a compartment."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.list_kafka_clusters(compartment_id=compartment_id)
            clusters = [_serialize_cluster_summary(item) for item in response.data.items]
            return {"cluster_count": len(clusters), "clusters": clusters}
        except Exception as e:
            return {"error": f"Failed to list Kafka clusters: {e}"}

    def create_kafka_cluster(
        self,
        display_name: str,
        compartment_id: str,
        subnet_id: str,
        broker_count: int = 3,
        kafka_version: str = "3.6.0",
        cluster_type: str = "PRODUCTION",
        ocpu_count: int = 2,
        storage_size_in_gbs: int = 50,
        cluster_config_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new OCI Managed Kafka cluster (async — returns work request)."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            from oci.managed_kafka.models import BrokerShape, CreateKafkaClusterDetails, SubnetSet

            details = CreateKafkaClusterDetails(
                display_name=display_name,
                compartment_id=compartment_id,
                kafka_version=kafka_version,
                cluster_type=cluster_type,
                access_subnets=[SubnetSet(subnet_id=subnet_id)],
                broker_shape=BrokerShape(
                    node_count=broker_count,
                    ocpu_count=ocpu_count,
                    storage_size_in_gbs=storage_size_in_gbs,
                ),
                cluster_config_id=cluster_config_id,
            )
            response = client.create_kafka_cluster(create_kafka_cluster_details=details)
            return _serialize_work_request(response.data)
        except Exception as e:
            return {"error": f"Failed to create Kafka cluster: {e}"}

    def update_kafka_cluster(
        self,
        kafka_cluster_id: str,
        display_name: str | None = None,
        cluster_config_id: str | None = None,
        cluster_config_version: int | None = None,
        freeform_tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Update a cluster's display name, tags, or configuration (async)."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            from oci.managed_kafka.models import UpdateKafkaClusterDetails

            details = UpdateKafkaClusterDetails(
                display_name=display_name,
                cluster_config_id=cluster_config_id,
                cluster_config_version=cluster_config_version,
                freeform_tags=freeform_tags,
            )
            response = client.update_kafka_cluster(
                kafka_cluster_id=kafka_cluster_id,
                update_kafka_cluster_details=details,
            )
            return _serialize_work_request(response.data)
        except Exception as e:
            return {"error": f"Failed to update Kafka cluster: {e}"}

    def delete_kafka_cluster(self, kafka_cluster_id: str) -> dict[str, Any]:
        """Delete a Kafka cluster (async — returns work request)."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.delete_kafka_cluster(kafka_cluster_id=kafka_cluster_id)
            return _serialize_work_request(response.data)
        except Exception as e:
            return {"error": f"Failed to delete Kafka cluster: {e}"}

    def change_kafka_cluster_compartment(
        self, kafka_cluster_id: str, compartment_id: str
    ) -> dict[str, Any]:
        """Move a Kafka cluster to a different OCI compartment."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            from oci.managed_kafka.models import ChangeKafkaClusterCompartmentDetails

            details = ChangeKafkaClusterCompartmentDetails(compartment_id=compartment_id)
            client.change_kafka_cluster_compartment(
                kafka_cluster_id=kafka_cluster_id,
                change_kafka_cluster_compartment_details=details,
            )
            return {
                "status": "compartment_change_accepted",
                "kafka_cluster_id": kafka_cluster_id,
                "target_compartment_id": compartment_id,
            }
        except Exception as e:
            return {"error": f"Failed to change cluster compartment: {e}"}

    # -------------------------------------------------------------------------
    # Superuser operations
    # -------------------------------------------------------------------------

    def enable_superuser(
        self, kafka_cluster_id: str, duration_in_hours: int | None = None
    ) -> dict[str, Any]:
        """Enable the superuser for a Kafka cluster (async)."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            from oci.managed_kafka.models import EnableSuperuserDetails

            details = EnableSuperuserDetails(duration_in_hours=duration_in_hours)
            response = client.enable_superuser(
                kafka_cluster_id=kafka_cluster_id,
                enable_superuser_details=details,
            )
            return _serialize_work_request(response.data)
        except Exception as e:
            return {"error": f"Failed to enable superuser: {e}"}

    def disable_superuser(self, kafka_cluster_id: str) -> dict[str, Any]:
        """Disable the superuser for a Kafka cluster (async)."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.disable_superuser(kafka_cluster_id=kafka_cluster_id)
            return _serialize_work_request(response.data)
        except Exception as e:
            return {"error": f"Failed to disable superuser: {e}"}

    # -------------------------------------------------------------------------
    # Cluster configuration operations
    # -------------------------------------------------------------------------

    def create_kafka_cluster_config(
        self,
        display_name: str,
        compartment_id: str,
        freeform_tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a new cluster configuration object."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            from oci.managed_kafka.models import CreateKafkaClusterConfigDetails

            details = CreateKafkaClusterConfigDetails(
                display_name=display_name,
                compartment_id=compartment_id,
                freeform_tags=freeform_tags,
            )
            response = client.create_kafka_cluster_config(
                create_kafka_cluster_config_details=details
            )
            return _serialize_cluster_config(response.data)
        except Exception as e:
            return {"error": f"Failed to create cluster config: {e}"}

    def get_kafka_cluster_config(self, kafka_cluster_config_id: str) -> dict[str, Any]:
        """Get a cluster configuration by ID."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.get_kafka_cluster_config(
                kafka_cluster_config_id=kafka_cluster_config_id
            )
            return _serialize_cluster_config(response.data)
        except Exception as e:
            return {"error": f"Failed to get cluster config: {e}"}

    def list_kafka_cluster_configs(self, compartment_id: str) -> dict[str, Any]:
        """List all cluster configurations in a compartment."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.list_kafka_cluster_configs(compartment_id=compartment_id)
            configs = [_serialize_cluster_config_summary(item) for item in response.data.items]
            return {"config_count": len(configs), "configs": configs}
        except Exception as e:
            return {"error": f"Failed to list cluster configs: {e}"}

    def update_kafka_cluster_config(
        self,
        kafka_cluster_config_id: str,
        display_name: str | None = None,
        freeform_tags: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Update a cluster configuration's display name or tags (async)."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            from oci.managed_kafka.models import UpdateKafkaClusterConfigDetails

            details = UpdateKafkaClusterConfigDetails(
                display_name=display_name,
                freeform_tags=freeform_tags,
            )
            response = client.update_kafka_cluster_config(
                kafka_cluster_config_id=kafka_cluster_config_id,
                update_kafka_cluster_config_details=details,
            )
            return _serialize_work_request(response.data)
        except Exception as e:
            return {"error": f"Failed to update cluster config: {e}"}

    def delete_kafka_cluster_config(self, kafka_cluster_config_id: str) -> dict[str, Any]:
        """Delete a cluster configuration."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            client.delete_kafka_cluster_config(kafka_cluster_config_id=kafka_cluster_config_id)
            return {"status": "deleted", "kafka_cluster_config_id": kafka_cluster_config_id}
        except Exception as e:
            return {"error": f"Failed to delete cluster config: {e}"}

    def change_kafka_cluster_config_compartment(
        self, kafka_cluster_config_id: str, compartment_id: str
    ) -> dict[str, Any]:
        """Move a cluster configuration to a different compartment."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            from oci.managed_kafka.models import ChangeKafkaClusterConfigCompartmentDetails

            details = ChangeKafkaClusterConfigCompartmentDetails(compartment_id=compartment_id)
            client.change_kafka_cluster_config_compartment(
                kafka_cluster_config_id=kafka_cluster_config_id,
                change_kafka_cluster_config_compartment_details=details,
            )
            return {
                "status": "compartment_change_accepted",
                "kafka_cluster_config_id": kafka_cluster_config_id,
                "target_compartment_id": compartment_id,
            }
        except Exception as e:
            return {"error": f"Failed to change config compartment: {e}"}

    # -------------------------------------------------------------------------
    # Configuration version operations
    # -------------------------------------------------------------------------

    def get_kafka_cluster_config_version(
        self, kafka_cluster_config_id: str, version_number: int
    ) -> dict[str, Any]:
        """Get a specific version of a cluster configuration."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.get_kafka_cluster_config_version(
                kafka_cluster_config_id=kafka_cluster_config_id,
                version_number=version_number,
            )
            return _serialize_config_version(response.data)
        except Exception as e:
            return {"error": f"Failed to get config version: {e}"}

    def list_kafka_cluster_config_versions(self, kafka_cluster_config_id: str) -> dict[str, Any]:
        """List all versions of a cluster configuration."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.list_kafka_cluster_config_versions(
                kafka_cluster_config_id=kafka_cluster_config_id
            )
            versions = [_serialize_config_version(v) for v in response.data.items]
            return {"version_count": len(versions), "versions": versions}
        except Exception as e:
            return {"error": f"Failed to list config versions: {e}"}

    def delete_kafka_cluster_config_version(
        self, kafka_cluster_config_id: str, version_number: int
    ) -> dict[str, Any]:
        """Delete a specific version of a cluster configuration."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            client.delete_kafka_cluster_config_version(
                kafka_cluster_config_id=kafka_cluster_config_id,
                version_number=version_number,
            )
            return {
                "status": "deleted",
                "kafka_cluster_config_id": kafka_cluster_config_id,
                "version_number": version_number,
            }
        except Exception as e:
            return {"error": f"Failed to delete config version: {e}"}

    # -------------------------------------------------------------------------
    # Work request operations
    # -------------------------------------------------------------------------

    def get_work_request(self, work_request_id: str) -> dict[str, Any]:
        """Get the status and details of an asynchronous work request."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.get_work_request(work_request_id=work_request_id)
            return _serialize_work_request(response.data)
        except Exception as e:
            return {"error": f"Failed to get work request: {e}"}

    def list_work_requests(
        self,
        compartment_id: str | None = None,
        resource_id: str | None = None,
    ) -> dict[str, Any]:
        """List work requests filtered by compartment or resource."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            kwargs: dict[str, Any] = {}
            if compartment_id:
                kwargs["compartment_id"] = compartment_id
            if resource_id:
                kwargs["resource_id"] = resource_id
            response = client.list_work_requests(**kwargs)
            items = []
            for wr in response.data.items:
                items.append(
                    {
                        "id": wr.id,
                        "operation_type": wr.operation_type,
                        "status": wr.status,
                        "compartment_id": wr.compartment_id,
                        "percent_complete": wr.percent_complete,
                        "time_accepted": str(wr.time_accepted),
                        "time_started": str(wr.time_started) if wr.time_started else None,
                        "time_finished": str(wr.time_finished) if wr.time_finished else None,
                    }
                )
            return {"work_request_count": len(items), "work_requests": items}
        except Exception as e:
            return {"error": f"Failed to list work requests: {e}"}

    def cancel_work_request(self, work_request_id: str) -> dict[str, Any]:
        """Cancel an in-progress work request."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            client.cancel_work_request(work_request_id=work_request_id)
            return {"status": "cancellation_requested", "work_request_id": work_request_id}
        except Exception as e:
            return {"error": f"Failed to cancel work request: {e}"}

    def get_work_request_errors(self, work_request_id: str) -> dict[str, Any]:
        """Get error details from a failed work request."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.list_work_request_errors(work_request_id=work_request_id)
            errors = [{"code": e.code, "message": e.message} for e in response.data.items]
            return {"error_count": len(errors), "errors": errors}
        except Exception as e:
            return {"error": f"Failed to get work request errors: {e}"}

    def get_work_request_logs(self, work_request_id: str) -> dict[str, Any]:
        """Get log entries from a work request."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            response = client.list_work_request_logs(work_request_id=work_request_id)
            logs = [
                {"timestamp": str(entry.timestamp), "message": entry.message}
                for entry in response.data.items
            ]
            return {"log_count": len(logs), "logs": logs}
        except Exception as e:
            return {"error": f"Failed to get work request logs: {e}"}

    # -------------------------------------------------------------------------
    # Node shapes
    # -------------------------------------------------------------------------

    def list_node_shapes(self, compartment_id: str | None = None) -> dict[str, Any]:
        """List available broker node shapes for cluster provisioning."""
        client = self._get_client()
        if client is None:
            return {"error": _OCI_SDK_NOT_CONFIGURED}
        try:
            kwargs: dict[str, Any] = {}
            if compartment_id:
                kwargs["compartment_id"] = compartment_id
            response = client.list_node_shapes(**kwargs)
            shapes = [
                {
                    "name": s.name,
                    "ocpu_count": s.ocpu_count,
                    "memory_in_gbs": s.memory_in_gbs,
                }
                for s in response.data.items
            ]
            return {"shape_count": len(shapes), "shapes": shapes}
        except Exception as e:
            return {"error": f"Failed to list node shapes: {e}"}
