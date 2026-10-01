"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class OperationResult(BaseModel):
    """Stable envelope returned by OCI Speech tools."""

    operation: str
    data: Any = None
    status: int | None = None
    opc_request_id: str | None = None
    etag: str | None = None
    next_page: str | None = None
    count: int | None = None
    notes: list[str] = Field(default_factory=list)


class EntityInput(BaseModel):
    value: str = Field(min_length=1, max_length=500)
    sounds_like: list[str] = Field(default_factory=list, max_length=255)
    audio_object_names: list[str] = Field(default_factory=list, max_length=1024)
    weight: int | None = Field(default=None, ge=1, le=100)


class EntityListInput(BaseModel):
    alias: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description=(
            "Optional alias for a populated entity list, or the alias of an "
            "existing reusable entity customization when entities is empty."
        ),
    )
    customization_id: str | None = Field(
        default=None,
        description=(
            "OCID of an existing reusable entity customization. Use only when "
            "entities is empty."
        ),
    )
    entity_type: str = Field(min_length=1, max_length=64)
    entities: list[EntityInput] = Field(default_factory=list, max_length=1024)

    @model_validator(mode="after")
    def inline_entities_or_reference(self):
        if self.entities:
            if self.customization_id is not None:
                raise ValueError(
                    "A populated entity list cannot also reference customization_id."
                )
            return self
        if (self.alias is None) == (self.customization_id is None):
            raise ValueError(
                "An entity list without entities must reference exactly one of "
                "alias or customization_id."
            )
        return self


class InlineCustomizationInput(BaseModel):
    entity_lists: list[EntityListInput] = Field(min_length=1, max_length=100)
    reference_examples: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def reference_examples_match_entity_types(self):
        if not self.reference_examples:
            if any(not entity_list.entities for entity_list in self.entity_lists):
                raise ValueError(
                    "Existing customization references require reference_examples."
                )
            return self
        entity_types = {item.entity_type.casefold() for item in self.entity_lists}
        placeholders = {
            value.casefold()
            for example in self.reference_examples
            for value in re.findall(r"<([A-Za-z][A-Za-z0-9_-]*)>", example)
        }
        unknown = sorted(placeholders - entity_types)
        if unknown:
            raise ValueError(
                "Reference-example placeholders must match an entity_type; unknown: "
                + ", ".join(unknown)
            )
        return self


class ObjectStorageCustomizationInput(BaseModel):
    entity_type: str = Field(min_length=1, max_length=64)
    namespace_name: str = Field(min_length=1)
    bucket_name: str = Field(min_length=1)
    object_names: list[str] = Field(min_length=1, max_length=1024)


class CustomizationDatasetInput(BaseModel):
    inline: InlineCustomizationInput | None = None
    object_storage: ObjectStorageCustomizationInput | None = None

    @model_validator(mode="after")
    def exactly_one_dataset(self):
        if (self.inline is None) == (self.object_storage is None):
            raise ValueError("Provide exactly one of inline or object_storage.")
        return self


TranscriptionLifecycle = Literal[
    "ACCEPTED",
    "IN_PROGRESS",
    "SUCCEEDED",
    "FAILED",
    "CANCELING",
    "CANCELED",
]

TaskLifecycle = Literal[
    "ACCEPTED",
    "IN_PROGRESS",
    "SUCCEEDED",
    "FAILED",
    "CANCELED",
]

CustomizationLifecycle = Literal[
    "CREATING", "ACTIVE", "UPDATING", "DELETING", "DELETED", "FAILED"
]

AudioFormat = Literal["MP3", "PCM", "OGG", "JSON"]
SpeechModel = Literal["TTS_1_STANDARD", "TTS_2_NATURAL"]
TextType = Literal["TEXT", "SSML"]
EventType = Literal[
    "com.oraclecloud.aiservicespeech.createtranscriptionjob",
    "com.oraclecloud.aiservicespeech.updatetranscriptionjob",
    "com.oraclecloud.aiservicespeech.completedtranscriptionjob",
    "com.oraclecloud.aiservicespeech.failedtranscriptionjob",
]
