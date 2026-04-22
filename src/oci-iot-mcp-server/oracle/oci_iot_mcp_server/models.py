"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import oci
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


def _resource_name(model: Any) -> str | None:
    return getattr(model, "name", getattr(model, "display_name", None))


def _created_at(model: Any) -> datetime | None:
    return getattr(model, "created_at", getattr(model, "time_created", None))


def _last_updated(model: Any) -> datetime | None:
    return getattr(model, "last_updated", getattr(model, "time_updated", None))


def _freeform_tags(model: Any) -> dict[str, Any] | None:
    return getattr(model, "freeform_tags", None)


def _defined_tags(model: Any) -> dict[str, dict[str, Any]] | None:
    return getattr(model, "defined_tags", None)


def _normalize_nested_oci_value(value: Any) -> Any:
    return oci.util.to_dict(value)


class DigitalTwinAdapterModel(BaseModel):
    id: str = Field(..., description="The digital twin adapter identifier")
    name: str | None = Field(None, description="The name of the digital twin adapter")
    description: str | None = Field(None, description="Description of the digital twin adapter")
    lifecycle_state: str | None = Field(None, description="Lifecycle state of the digital twin adapter")
    created_at: datetime | None = Field(None, description="Creation timestamp of the digital twin adapter")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the digital twin adapter")
    digital_twin_model_id: str | None = Field(None, description="The linked digital twin model identifier")
    digital_twin_model_spec_uri: str | None = Field(
        None,
        description="URI to the digital twin model specification",
    )
    inbound_envelope: Any | None = Field(None, description="Inbound envelope metadata")
    inbound_routes: list[Any] | None = Field(None, description="Inbound route definitions")
    freeform_tags: dict[str, Any] | None = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type, or scope",
    )
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, description="Defined tags for this resource")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a DigitalTwinAdapterModel from an OCI digital twin adapter object."""
        return cls(
            id=getattr(model, "id"),
            name=_resource_name(model),
            description=getattr(model, "description", None),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
            digital_twin_model_id=getattr(model, "digital_twin_model_id", None),
            digital_twin_model_spec_uri=getattr(model, "digital_twin_model_spec_uri", None),
            inbound_envelope=_normalize_nested_oci_value(getattr(model, "inbound_envelope", None)),
            inbound_routes=_normalize_nested_oci_value(getattr(model, "inbound_routes", None)),
            freeform_tags=_freeform_tags(model),
            defined_tags=_defined_tags(model),
        )


class DigitalTwinModelModel(BaseModel):
    id: str = Field(..., description="The digital twin model identifier")
    name: str | None = Field(None, description="The name of the digital twin model")
    description: str | None = Field(None, description="Description of the digital twin model")
    lifecycle_state: str | None = Field(None, description="Lifecycle state of the digital twin model")
    created_at: datetime | None = Field(None, description="Creation timestamp of the digital twin model")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the digital twin model")
    freeform_tags: dict[str, Any] | None = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type, or scope",
    )
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, description="Defined tags for this resource")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a DigitalTwinModelModel from an OCI digital twin model object."""
        return cls(
            id=getattr(model, "id"),
            name=_resource_name(model),
            description=getattr(model, "description", None),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
            freeform_tags=_freeform_tags(model),
            defined_tags=_defined_tags(model),
        )


class DigitalTwinModelSummaryModel(BaseModel):
    id: str = Field(..., description="The digital twin model identifier")
    name: str | None = Field(None, description="The name of the digital twin model")
    description: str | None = Field(None, description="Description of the digital twin model")
    lifecycle_state: str | None = Field(None, description="Lifecycle state of the digital twin model")
    created_at: datetime | None = Field(None, description="Creation timestamp of the digital twin model")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the digital twin model")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a DigitalTwinModelSummaryModel from an OCI DigitalTwinModelSummary object."""
        return cls(
            id=getattr(model, "id"),
            name=_resource_name(model),
            description=getattr(model, "description", None),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
        )


class DigitalTwinInstanceModel(BaseModel):
    id: str = Field(..., description="The digital twin instance identifier")
    name: str | None = Field(None, description="The name of the digital twin instance")
    description: str | None = Field(None, description="Description of the digital twin instance")
    lifecycle_state: str | None = Field(None, description="Lifecycle state of the digital twin instance")
    created_at: datetime | None = Field(None, description="Creation timestamp of the digital twin instance")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the digital twin instance")
    iot_domain_id: str | None = Field(None, description="The linked IoT domain identifier")
    digital_twin_adapter_id: str | None = Field(None, description="The linked digital twin adapter identifier")
    freeform_tags: dict[str, Any] | None = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type, or scope",
    )
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, description="Defined tags for this resource")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a DigitalTwinInstanceModel from an OCI digital twin instance object."""
        return cls(
            id=getattr(model, "id"),
            name=_resource_name(model),
            description=getattr(model, "description", None),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
            iot_domain_id=getattr(model, "iot_domain_id", None),
            digital_twin_adapter_id=getattr(model, "digital_twin_adapter_id", None),
            freeform_tags=_freeform_tags(model),
            defined_tags=_defined_tags(model),
        )


class DigitalTwinRelationshipModel(BaseModel):
    id: str = Field(..., description="The digital twin relationship identifier")
    name: str | None = Field(None, description="The name of the digital twin relationship")
    description: str | None = Field(None, description="Description of the digital twin relationship")
    lifecycle_state: str | None = Field(None, description="Lifecycle state of the digital twin relationship")
    created_at: datetime | None = Field(None, description="Creation timestamp of the digital twin relationship")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the digital twin relationship")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a DigitalTwinRelationshipModel from an OCI digital twin relationship object."""
        return cls(
            id=getattr(model, "id"),
            name=_resource_name(model),
            description=getattr(model, "description", None),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
        )


class IoTDomainModel(BaseModel):
    id: str = Field(..., description="The IoT domain identifier")
    name: str | None = Field(None, description="The name of the IoT domain")
    description: str | None = Field(None, description="Description of the IoT domain")
    compartment_id: str | None = Field(None, description="Compartment containing the IoT domain")
    iot_domain_group_id: str | None = Field(None, description="The containing IoT domain group identifier")
    lifecycle_state: str | None = Field(None, description="Lifecycle state of the IoT domain")
    created_at: datetime | None = Field(None, description="Creation timestamp of the IoT domain")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the IoT domain")
    device_host: str | None = Field(None, description="The IoT device host for the domain")
    db_allowed_identity_domain_host: str | None = Field(
        None,
        description="The identity domain host used for data-plane token minting",
    )
    freeform_tags: dict[str, Any] | None = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type, or scope",
    )
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, description="Defined tags for this resource")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create an IoTDomainModel from an OCI IotDomainSummary object."""
        return cls(
            id=getattr(model, "id"),
            name=_resource_name(model),
            description=getattr(model, "description", None),
            compartment_id=getattr(model, "compartment_id", None),
            iot_domain_group_id=getattr(model, "iot_domain_group_id", None),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
            device_host=getattr(model, "device_host", None),
            db_allowed_identity_domain_host=getattr(model, "db_allowed_identity_domain_host", None),
            freeform_tags=_freeform_tags(model),
            defined_tags=_defined_tags(model),
        )


class IoTDomainGroupModel(BaseModel):
    id: str = Field(..., description="The IoT domain group identifier")
    name: str | None = Field(None, description="The name of the IoT domain group")
    description: str | None = Field(None, description="Description of the IoT domain group")
    compartment_id: str | None = Field(None, description="Compartment containing the IoT domain group")
    lifecycle_state: str | None = Field(None, description="Lifecycle state of the IoT domain group")
    created_at: datetime | None = Field(None, description="Creation timestamp of the IoT domain group")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the IoT domain group")
    data_host: str | None = Field(None, description="The IoT data host for the domain group")
    db_token_scope: str | None = Field(None, description="The direct database token scope")
    freeform_tags: dict[str, Any] | None = Field(
        None,
        description="Simple key-value pair that is applied without any predefined name, type, or scope",
    )
    defined_tags: dict[str, dict[str, Any]] | None = Field(None, description="Defined tags for this resource")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create an IoTDomainGroupModel from an OCI IotDomainGroupSummary object."""
        return cls(
            id=getattr(model, "id"),
            name=_resource_name(model),
            description=getattr(model, "description", None),
            compartment_id=getattr(model, "compartment_id", None),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
            data_host=getattr(model, "data_host", None),
            db_token_scope=getattr(model, "db_token_scope", None),
            freeform_tags=_freeform_tags(model),
            defined_tags=_defined_tags(model),
        )


class WorkRequestModel(BaseModel):
    id: str = Field(..., description="The work request identifier")
    status: str | None = Field(None, description="Status of the work request")
    compartment_id: str | None = Field(None, description="Compartment containing the work request")
    created_at: datetime | None = Field(None, description="Creation timestamp of the work request")
    last_updated: datetime | None = Field(None, description="Last update timestamp of the work request")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a WorkRequestModel from an OCI work request object."""
        return cls(
            id=getattr(model, "id"),
            status=getattr(model, "status", getattr(model, "lifecycle_state", None)),
            compartment_id=getattr(model, "compartment_id", None),
            created_at=_created_at(model),
            last_updated=_last_updated(model),
        )


class ErrorModel(BaseModel):
    code: str | None = Field(None, description="Error code")
    message: str = Field(..., description="Error message")
    timestamp: datetime | None = Field(None, description="Timestamp of the error")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create an ErrorModel from an OCI work request error object."""
        if isinstance(model, str):
            return cls(message=model)
        return cls(
            code=getattr(model, "code", None),
            message=getattr(model, "message", str(model)),
            timestamp=getattr(model, "timestamp", getattr(model, "time_stamp", None)),
        )


class LogModel(BaseModel):
    level: str | None = Field(None, description="Log level")
    message: str = Field(..., description="Log message")
    timestamp: datetime | None = Field(None, description="Timestamp of the log entry")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a LogModel from an OCI work request log entry object."""
        if isinstance(model, str):
            return cls(message=model)
        return cls(
            level=getattr(model, "level", None),
            message=getattr(model, "message", str(model)),
            timestamp=getattr(model, "timestamp", getattr(model, "time_stamp", None)),
        )


class CompartmentModel(BaseModel):
    id: str = Field(..., description="The compartment identifier")
    name: Optional[str] = Field(None, description="The name of the compartment")
    description: Optional[str] = Field(None, description="Description of the compartment")
    parent_id: Optional[str] = Field(None, description="The parent compartment identifier")
    lifecycle_state: Optional[str] = Field(None, description="Lifecycle state of the compartment")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp of the compartment")

    @classmethod
    def from_oci_model(cls, model: Any):
        """Create a CompartmentModel from an OCI compartment object."""
        return cls(
            id=getattr(model, "id"),
            name=getattr(model, "name", getattr(model, "display_name", None)),
            description=getattr(model, "description", None),
            parent_id=getattr(model, "compartment_id", getattr(model, "parent_id", None)),
            lifecycle_state=getattr(model, "lifecycle_state", None),
            created_at=getattr(model, "time_created", getattr(model, "created_at", None)),
        )
