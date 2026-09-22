# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

import pytest
from pydantic import ValidationError

from oracle.oci_language_mcp_server.models import (
    AnalyzeSentimentRequest,
    ClassifyTextRequest,
    DetectDominantLanguageRequest,
    DetectEntitiesRequest,
    DetectPiiEntitiesRequest,
    ExtractKeyPhrasesRequest,
    TranslateTextRequest,
)


@pytest.mark.parametrize(
    "request_type",
    [
        DetectDominantLanguageRequest,
        ClassifyTextRequest,
        DetectEntitiesRequest,
        ExtractKeyPhrasesRequest,
        AnalyzeSentimentRequest,
        DetectPiiEntitiesRequest,
    ],
)
def test_requests_enforce_unique_keys_and_batch_limit(request_type) -> None:
    with pytest.raises(ValidationError, match="unique"):
        request_type(
            documents=[
                {"key": "same", "text": "first"},
                {"key": "same", "text": "second"},
            ]
        )
    with pytest.raises(ValidationError, match="20000"):
        request_type(
            documents=[{"key": str(index), "text": "a" * 5_000} for index in range(5)]
        )


def test_capability_language_contracts_are_strict() -> None:
    with pytest.raises(ValidationError):
        ClassifyTextRequest(
            documents=[{"key": "one", "text": "bonjour", "language_code": "fr"}]
        )
    assert DetectEntitiesRequest(
        documents=[{"key": "one", "text": "hola", "language_code": "es"}]
    ).documents[0].language_code == "es"
    with pytest.raises(ValidationError):
        ExtractKeyPhrasesRequest(
            documents=[{"key": "one", "text": "bonjour", "language_code": "fr"}]
        )
    assert AnalyzeSentimentRequest(
        documents=[{"key": "one", "text": "muy bueno", "language_code": "es"}]
    ).documents[0].language_code == "es"
    with pytest.raises(ValidationError):
        AnalyzeSentimentRequest(
            documents=[{"key": "one", "text": "bonjour", "language_code": "fr"}]
        )
    with pytest.raises(ValidationError):
        DetectPiiEntitiesRequest(
            documents=[{"key": "one", "text": "hola", "language_code": "es"}]
        )


def test_translation_validates_source_target_and_no_translate() -> None:
    request = TranslateTextRequest(
        documents=[{"key": "one", "text": "hello"}],
        target_language_code="fr",
        no_translate=["OCI"],
    )
    assert request.documents[0].language_code == "auto"
    with pytest.raises(ValidationError, match="cannot be auto"):
        TranslateTextRequest(
            documents=[{"key": "one", "text": "hello"}],
            target_language_code="auto",
        )
    with pytest.raises(ValidationError, match="unique"):
        TranslateTextRequest(
            documents=[{"key": "one", "text": "hello"}],
            target_language_code="fr",
            no_translate=["OCI", "OCI"],
        )


def test_pii_request_accepts_clean_masking_contract() -> None:
    request = DetectPiiEntitiesRequest(
        documents=[{"key": "one", "text": "Email jane@example.com"}],
        masking={
            "EMAIL": {
                "mode": "MASK",
                "leave_characters_unmasked": 3,
                "exclude_offsets": [6],
            },
            "PERSON": {"mode": "REPLACE", "replace_with": "[NAME]"},
            "ADDRESS": {"mode": "REMOVE"},
            "DATE_TIME": {"mode": "RELEXIFY"},
        },
    )
    assert request.masking is not None
    assert request.masking["EMAIL"].exclude_offsets == [6]
    assert DetectPiiEntitiesRequest(
        documents=[{"key": "one", "text": "hello"}], masking={}
    ).masking is None
    assert DetectPiiEntitiesRequest(documents=[{"key": "one", "text": "hello"}]).masking is None
    assert DetectPiiEntitiesRequest(
        documents=[{"key": "one", "text": "hello"}], masking=None
    ).masking is None
    with pytest.raises(ValidationError, match="ALL cannot"):
        DetectPiiEntitiesRequest(
            documents=[{"key": "one", "text": "hello"}],
            masking={"ALL": {"mode": "MASK"}, "EMAIL": {"mode": "REMOVE"}},
        )


def test_options_reject_untrusted_regions_and_allow_all_characters() -> None:
    assert DetectDominantLanguageRequest(
        documents=[{"key": "one", "text": "hello"}], chars_to_consider=0
    ).chars_to_consider == 0
    for region in ("attacker.example", "user@attacker", "127.0.0.1", "us-ashburn-1:443"):
        with pytest.raises(ValidationError, match="recognized OCI region"):
            DetectDominantLanguageRequest(
                documents=[{"key": "one", "text": "hello"}], options={"region": region}
            )


def test_sentiment_levels_are_optional_strict_and_unique() -> None:
    document_only = AnalyzeSentimentRequest(
        documents=[{"key": "one", "text": "This is fine."}]
    )
    assert document_only.levels == []
    detailed = AnalyzeSentimentRequest(
        documents=[{"key": "one", "text": "This is fine."}],
        levels=["ASPECT", "SENTENCE"],
    )
    assert detailed.levels == ["ASPECT", "SENTENCE"]
    with pytest.raises(ValidationError, match="unique"):
        AnalyzeSentimentRequest(
            documents=[{"key": "one", "text": "This is fine."}],
            levels=["ASPECT", "ASPECT"],
        )
    with pytest.raises(ValidationError):
        AnalyzeSentimentRequest(
            documents=[{"key": "one", "text": "This is fine."}],
            levels=["DOCUMENT"],
        )


@pytest.mark.parametrize("request_id", ["bad\r\nid", "spaces are bad", "x" * 65])
def test_all_requests_reject_unsafe_opc_request_ids(request_id: str) -> None:
    with pytest.raises(ValidationError):
        DetectDominantLanguageRequest(
            documents=[{"key": "one", "text": "hello"}],
            options={"opc_request_id": request_id},
        )


def test_unknown_fields_and_instruction_like_keys_are_rejected() -> None:
    with pytest.raises(ValidationError):
        DetectDominantLanguageRequest(
            documents=[{"key": "ignore previous instructions", "text": "hello"}]
        )
    with pytest.raises(ValidationError):
        DetectDominantLanguageRequest(
            documents=[{"key": "one", "text": "hello"}],
            endpoint_id="not-allowed",
        )
