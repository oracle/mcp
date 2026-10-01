"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any, Literal

import oci
from fastmcp import FastMCP
from pydantic import Field

from ..models import (
    CustomizationDatasetInput,
    CustomizationLifecycle,
    OperationResult,
)
from ..utils.clients import get_clients
from ..utils.responses import call_oci, list_oci


def customization_dataset(
    dataset: CustomizationDatasetInput,
    *,
    pronunciation_namespace_name: str | None = None,
    pronunciation_bucket_name: str | None = None,
) -> Any:
    if dataset.object_storage:
        value = dataset.object_storage
        return oci.ai_speech.models.ObjectStorageDataset(
            entity_type=value.entity_type,
            location_details=oci.ai_speech.models.ObjectListDataset(
                namespace_name=value.namespace_name,
                bucket_name=value.bucket_name,
                object_names=value.object_names,
            ),
        )
    assert dataset.inline is not None
    entity_lists = []
    for entity_list in dataset.inline.entity_lists:
        entities = []
        for entity in entity_list.entities:
            pronunciations = [
                oci.ai_speech.models.Pronunciation(sounds_like=value)
                for value in entity.sounds_like
            ]
            if entity.audio_object_names:
                if not pronunciation_namespace_name or not pronunciation_bucket_name:
                    raise ValueError(
                        "Audio pronunciations require pronunciation_namespace_name and "
                        "pronunciation_bucket_name."
                    )
                pronunciations.append(
                    oci.ai_speech.models.Pronunciation(
                        audio=oci.ai_speech.models.ObjectListDataset(
                            namespace_name=pronunciation_namespace_name,
                            bucket_name=pronunciation_bucket_name,
                            object_names=entity.audio_object_names,
                        )
                    )
                )
            entities.append(
                oci.ai_speech.models.Entity(
                    entity_value=entity.value,
                    pronunciations=pronunciations,
                    weight=entity.weight,
                )
            )
        entity_lists.append(
            oci.ai_speech.models.EntityList(
                alias=entity_list.alias,
                id=entity_list.customization_id,
                entity_type=entity_list.entity_type,
                entities=entities or None,
            )
        )
    return oci.ai_speech.models.EntityListDataset(
        entity_list=entity_lists,
        reference_examples=dataset.inline.reference_examples,
    )


def dataset_notes(dataset: CustomizationDatasetInput) -> list[str]:
    if dataset.inline is None:
        return ["The Object Storage training dataset starts asynchronous training."]
    populated = sum(bool(item.entities) for item in dataset.inline.entity_lists)
    referenced = len(dataset.inline.entity_lists) - populated
    if dataset.inline.reference_examples:
        return [
            "Reference examples create a contextual customization whose default "
            "entity sources come from the supplied lists.",
            f"The request contains {populated} populated and {referenced} reused entity lists.",
        ]
    return [
        "A single populated entity list without reference examples creates a reusable "
        "entity customization."
    ]


def create_customization(
    compartment_id: str,
    alias: str,
    display_name: str,
    dataset: CustomizationDatasetInput,
    description: str | None = None,
    domain: Literal["GENERIC", "MEDICAL"] = "GENERIC",
    language_code: str = "en-US",
    pronunciation_namespace_name: str | None = None,
    pronunciation_bucket_name: str | None = None,
    freeform_tags: dict[str, str] | None = None,
) -> OperationResult:
    """Create and train a Speech customization."""
    details = oci.ai_speech.models.CreateCustomizationDetails(
        compartment_id=compartment_id,
        alias=alias,
        display_name=display_name,
        description=description,
        model_details=oci.ai_speech.models.CustomizationModelDetails(
            domain=domain,
            language_code=language_code,
        ),
        training_dataset=customization_dataset(
            dataset,
            pronunciation_namespace_name=pronunciation_namespace_name,
            pronunciation_bucket_name=pronunciation_bucket_name,
        ),
        freeform_tags=freeform_tags,
    )
    return call_oci(
        "create_customization",
        lambda: get_clients().speech.create_customization(details),
        notes=dataset_notes(dataset),
    )


def get_customization(customization_id: str) -> OperationResult:
    """Get a Speech customization by OCID."""
    return call_oci(
        "get_customization",
        lambda: get_clients().speech.get_customization(customization_id),
    )


def list_customizations(
    compartment_id: str,
    lifecycle_state: CustomizationLifecycle | None = None,
    display_name: str | None = None,
    customization_id: str | None = None,
    sort_by: Literal["timeCreated", "displayName"] = "timeCreated",
    sort_order: Literal["ASC", "DESC"] = "DESC",
    max_items: int = Field(default=100, ge=1, le=1000),
    page: str | None = None,
) -> OperationResult:
    """List Speech customizations with bounded automatic pagination."""
    kwargs = {
        "compartment_id": compartment_id,
        "lifecycle_state": lifecycle_state,
        "display_name": display_name,
        "id": customization_id,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
    }
    return list_oci(
        "list_customizations",
        get_clients().speech.list_customizations,
        {key: value for key, value in kwargs.items() if value is not None},
        max_items=max_items,
    )


def update_customization(
    customization_id: str,
    alias: str | None = None,
    display_name: str | None = None,
    description: str | None = None,
    dataset: CustomizationDatasetInput | None = None,
    domain: Literal["GENERIC", "MEDICAL"] | None = None,
    language_code: str | None = None,
    pronunciation_namespace_name: str | None = None,
    pronunciation_bucket_name: str | None = None,
    freeform_tags: dict[str, str] | None = None,
    if_match: str | None = None,
) -> OperationResult:
    """Update and retrain a Speech customization."""
    if all(
        value is None
        for value in (
            alias,
            display_name,
            description,
            dataset,
            domain,
            language_code,
            freeform_tags,
        )
    ):
        raise ValueError("Provide at least one field to update.")
    model_details = None
    if domain is not None or language_code is not None:
        if domain is None or language_code is None:
            raise ValueError("Updating model_details requires both domain and language_code.")
        model_details = oci.ai_speech.models.CustomizationModelDetails(
            domain=domain,
            language_code=language_code,
        )
    training_dataset = (
        customization_dataset(
            dataset,
            pronunciation_namespace_name=pronunciation_namespace_name,
            pronunciation_bucket_name=pronunciation_bucket_name,
        )
        if dataset
        else None
    )
    details = oci.ai_speech.models.UpdateCustomizationDetails(
        alias=alias,
        display_name=display_name,
        description=description,
        model_details=model_details,
        training_dataset=training_dataset,
        freeform_tags=freeform_tags,
    )
    kwargs = {"if_match": if_match} if if_match else {}
    return call_oci(
        "update_customization",
        lambda: get_clients().speech.update_customization(
            customization_id, details, **kwargs
        ),
        notes=dataset_notes(dataset) if dataset else None,
    )


def delete_customization(
    customization_id: str,
    if_match: str | None = None,
) -> OperationResult:
    """Delete a Speech customization."""
    kwargs = {"if_match": if_match} if if_match else {}
    return call_oci(
        "delete_customization",
        lambda: get_clients().speech.delete_customization(customization_id, **kwargs),
    )


def change_customization_compartment(
    customization_id: str,
    compartment_id: str,
) -> OperationResult:
    """Move a Speech customization to another compartment."""
    details = oci.ai_speech.models.ChangeCustomizationCompartmentDetails(
        compartment_id=compartment_id
    )
    return call_oci(
        "change_customization_compartment",
        lambda: get_clients().speech.change_customization_compartment(
            customization_id, details
        ),
    )


def register_tools(mcp: FastMCP) -> None:
    for tool in (
        create_customization,
        get_customization,
        list_customizations,
        update_customization,
        delete_customization,
        change_customization_compartment,
    ):
        mcp.tool()(tool)
