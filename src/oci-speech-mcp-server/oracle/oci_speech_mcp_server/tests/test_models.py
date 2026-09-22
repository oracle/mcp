"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest
from pydantic import ValidationError

from oracle.oci_speech_mcp_server.models import (
    CustomizationDatasetInput,
    EntityInput,
    EntityListInput,
    InlineCustomizationInput,
    ObjectStorageCustomizationInput,
    OperationResult,
)


def test_operation_result_defaults():
    result = OperationResult(operation="test")
    assert result.notes == []
    assert result.data is None


def test_customization_dataset_requires_exactly_one_variant():
    inline = InlineCustomizationInput(
        entity_lists=[
            EntityListInput(
                alias="products",
                entity_type="product",
                entities=[EntityInput(value="Oracle")],
            )
        ]
    )
    storage = ObjectStorageCustomizationInput(
        entity_type="product",
        namespace_name="namespace",
        bucket_name="bucket",
        object_names=["dataset.json"],
    )
    assert CustomizationDatasetInput(inline=inline).inline is inline
    assert CustomizationDatasetInput(object_storage=storage).object_storage is storage
    with pytest.raises(ValidationError, match="exactly one"):
        CustomizationDatasetInput()
    with pytest.raises(ValidationError, match="exactly one"):
        CustomizationDatasetInput(inline=inline, object_storage=storage)


def test_entity_list_reuse_and_reference_example_validation():
    referenced = EntityListInput(
        entity_type="person",
        customization_id="ocid1.aispeechcustomization.example",
    )
    inline = InlineCustomizationInput(
        entity_lists=[referenced],
        reference_examples=["Welcome <PERSON>"],
    )
    assert inline.entity_lists[0].entities == []

    alias_reference = EntityListInput(entity_type="person", alias="people-active")
    assert alias_reference.customization_id is None

    with pytest.raises(ValidationError, match="exactly one"):
        EntityListInput(entity_type="person")
    with pytest.raises(ValidationError, match="cannot also reference"):
        EntityListInput(
            entity_type="person",
            customization_id="ocid1.aispeechcustomization.example",
            entities=[EntityInput(value="Alice")],
        )
    with pytest.raises(ValidationError, match="require reference_examples"):
        InlineCustomizationInput(entity_lists=[referenced])
    with pytest.raises(ValidationError, match="unknown"):
        InlineCustomizationInput(
            entity_lists=[
                EntityListInput(
                    entity_type="person",
                    entities=[EntityInput(value="Alice")],
                )
            ],
            reference_examples=["Take <MEDICATION>"],
        )
