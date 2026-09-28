# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""OCI SDK provider for shared pretrained OCI Language operations."""

from __future__ import annotations

from typing import Any

import oci

from . import __project__, __version__
from .auth import build_auth_context
from .config import LanguageMcpSettings
from .models import (
    AnalyzeSentimentRequest,
    ClassifyTextRequest,
    DetectDominantLanguageRequest,
    DetectEntitiesRequest,
    DetectPiiEntitiesRequest,
    ExtractKeyPhrasesRequest,
    MaskRule,
    RelexifyRule,
    RemoveRule,
    ReplaceRule,
    TranslateTextRequest,
)

_user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_user_agent_name}/{__version__}"


class OciLanguageProvider:
    """Construct fixed pretrained requests without caller-controlled dispatch."""

    def __init__(self, settings: LanguageMcpSettings) -> None:
        self._settings = settings

    def detect_dominant_language(
        self, request: DetectDominantLanguageRequest, *, compartment_id: str, opc_request_id: str
    ) -> Any:
        details = oci.ai_language.models.BatchDetectDominantLanguageDetails(
            compartment_id=compartment_id,
            documents=[
                oci.ai_language.models.DominantLanguageDocument(key=item.key, text=item.text)
                for item in request.documents
            ],
            should_ignore_transliteration=request.should_ignore_transliteration,
            chars_to_consider=request.chars_to_consider,
        )
        return self._client(region=request.options.region).batch_detect_dominant_language(
            batch_detect_dominant_language_details=details,
            **self._call_options(opc_request_id),
        )

    def classify_text(
        self, request: ClassifyTextRequest, *, compartment_id: str, opc_request_id: str
    ) -> Any:
        details = oci.ai_language.models.BatchDetectLanguageTextClassificationDetails(
            compartment_id=compartment_id,
            documents=self._text_documents(request.documents),
        )
        client = self._client(region=request.options.region)
        return client.batch_detect_language_text_classification(
            batch_detect_language_text_classification_details=details,
            **self._call_options(opc_request_id),
        )

    def detect_entities(
        self, request: DetectEntitiesRequest, *, compartment_id: str, opc_request_id: str
    ) -> Any:
        details = oci.ai_language.models.BatchDetectLanguageEntitiesDetails(
            compartment_id=compartment_id,
            documents=self._text_documents(request.documents),
        )
        return self._client(region=request.options.region).batch_detect_language_entities(
            batch_detect_language_entities_details=details,
            **self._call_options(opc_request_id),
        )

    def extract_key_phrases(
        self, request: ExtractKeyPhrasesRequest, *, compartment_id: str, opc_request_id: str
    ) -> Any:
        details = oci.ai_language.models.BatchDetectLanguageKeyPhrasesDetails(
            compartment_id=compartment_id,
            documents=self._text_documents(request.documents),
        )
        return self._client(region=request.options.region).batch_detect_language_key_phrases(
            batch_detect_language_key_phrases_details=details,
            **self._call_options(opc_request_id),
        )

    def analyze_sentiment(
        self, request: AnalyzeSentimentRequest, *, compartment_id: str, opc_request_id: str
    ) -> Any:
        details = oci.ai_language.models.BatchDetectLanguageSentimentsDetails(
            compartment_id=compartment_id,
            documents=self._text_documents(request.documents),
        )
        options = self._call_options(opc_request_id)
        if request.levels:
            options["level"] = request.levels
        return self._client(region=request.options.region).batch_detect_language_sentiments(
            batch_detect_language_sentiments_details=details,
            **options,
        )

    def detect_pii_entities(
        self, request: DetectPiiEntitiesRequest, *, compartment_id: str, opc_request_id: str
    ) -> Any:
        details = oci.ai_language.models.BatchDetectLanguagePiiEntitiesDetails(
            compartment_id=compartment_id,
            documents=self._text_documents(request.documents),
            masking=self._masking(request),
            profile=oci.ai_language.models.Profile(domain="PII"),
        )
        return self._client(region=request.options.region).batch_detect_language_pii_entities(
            batch_detect_language_pii_entities_details=details,
            **self._call_options(opc_request_id),
        )

    def translate_text(
        self, request: TranslateTextRequest, *, compartment_id: str, opc_request_id: str
    ) -> Any:
        details = oci.ai_language.models.BatchLanguageTranslationDetails(
            compartment_id=compartment_id,
            documents=self._text_documents(request.documents),
            target_language_code=request.target_language_code,
            no_translate=request.no_translate or None,
        )
        return self._client(region=request.options.region).batch_language_translation(
            batch_language_translation_details=details,
            **self._call_options(opc_request_id),
        )

    @staticmethod
    def _text_documents(documents: list[Any]) -> list[Any]:
        return [
            oci.ai_language.models.TextDocument(
                key=item.key, text=item.text, language_code=item.language_code
            )
            for item in documents
        ]

    @staticmethod
    def _call_options(opc_request_id: str) -> dict[str, Any]:
        return {
            "opc_request_id": opc_request_id,
            "retry_strategy": oci.retry.NoneRetryStrategy(),
        }

    def _client(self, *, region: str | None) -> Any:
        auth = build_auth_context(self._settings, region=region)
        config = {
            **auth.config,
            "additional_user_agent": _ADDITIONAL_UA,
            "log_requests": False,
        }
        kwargs: dict[str, Any] = {
            "config": config,
            "signer": auth.signer,
            "timeout": (
                self._settings.oci_connect_timeout_seconds,
                self._settings.oci_read_timeout_seconds,
            ),
        }
        if self._settings.oci_service_endpoint:
            kwargs["service_endpoint"] = self._settings.oci_service_endpoint
        return oci.ai_language.AIServiceLanguageClient(**kwargs)

    @staticmethod
    def _masking(request: DetectPiiEntitiesRequest) -> dict[str, Any] | None:
        if request.masking is None:
            return None
        return {
            target: OciLanguageProvider._masking_rule(rule)
            for target, rule in request.masking.items()
        }

    @staticmethod
    def _masking_rule(rule: MaskRule | ReplaceRule | RemoveRule | RelexifyRule) -> Any:
        common = {
            "exclude": [
                *rule.exclude_entity_types,
                *(str(offset) for offset in rule.exclude_offsets),
            ],
            "should_detect": rule.should_detect,
        }
        if isinstance(rule, MaskRule):
            return oci.ai_language.models.PiiEntityMask(
                **common,
                masking_character=rule.masking_character,
                leave_characters_unmasked=rule.leave_characters_unmasked,
                is_unmasked_from_end=rule.is_unmasked_from_end,
            )
        if isinstance(rule, ReplaceRule):
            return oci.ai_language.models.PiiEntityReplace(
                **common, replace_with=rule.replace_with
            )
        if isinstance(rule, RemoveRule):
            return oci.ai_language.models.PiiEntityRemove(**common)
        return oci.ai_language.models.PiiEntityRelexify(**common)
