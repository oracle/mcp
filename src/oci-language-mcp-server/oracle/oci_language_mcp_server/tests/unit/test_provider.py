# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from types import SimpleNamespace

import oci
import pytest

from oracle.oci_language_mcp_server.config import LanguageMcpSettings
from oracle.oci_language_mcp_server.models import REQUEST_MODELS
from oracle.oci_language_mcp_server.provider import OciLanguageProvider


class FakeLanguageClient:
    def __init__(self) -> None:
        self.operation = None
        self.kwargs = None

    def __getattr__(self, operation):
        def call(**kwargs):
            self.operation = operation
            self.kwargs = kwargs
            return SimpleNamespace(data={"documents": [], "errors": []})

        return call


@pytest.mark.parametrize(
    ("tool", "provider_method", "arguments", "sdk_operation", "details_argument"),
    [
        (
            "detect_dominant_language",
            "detect_dominant_language",
            {"documents": [{"key": "one", "text": "hello"}]},
            "batch_detect_dominant_language",
            "batch_detect_dominant_language_details",
        ),
        (
            "detect_language_text_classification",
            "classify_text",
            {"documents": [{"key": "one", "text": "news"}]},
            "batch_detect_language_text_classification",
            "batch_detect_language_text_classification_details",
        ),
        (
            "detect_language_entities",
            "detect_entities",
            {"documents": [{"key": "one", "text": "Jane"}]},
            "batch_detect_language_entities",
            "batch_detect_language_entities_details",
        ),
        (
            "detect_language_key_phrases",
            "extract_key_phrases",
            {"documents": [{"key": "one", "text": "important phrase"}]},
            "batch_detect_language_key_phrases",
            "batch_detect_language_key_phrases_details",
        ),
        (
            "detect_language_sentiments",
            "analyze_sentiment",
            {"documents": [{"key": "one", "text": "Great service"}]},
            "batch_detect_language_sentiments",
            "batch_detect_language_sentiments_details",
        ),
        (
            "detect_language_pii_entities",
            "detect_pii_entities",
            {"documents": [{"key": "one", "text": "jane@example.com"}]},
            "batch_detect_language_pii_entities",
            "batch_detect_language_pii_entities_details",
        ),
        (
            "translate_language_text",
            "translate_text",
            {
                "documents": [{"key": "one", "text": "hello"}],
                "target_language_code": "fr",
            },
            "batch_language_translation",
            "batch_language_translation_details",
        ),
    ],
)
def test_provider_calls_only_fixed_pretrained_operation(
    monkeypatch, tool, provider_method, arguments, sdk_operation, details_argument
) -> None:
    provider = OciLanguageProvider(LanguageMcpSettings())
    client = FakeLanguageClient()
    monkeypatch.setattr(provider, "_client", lambda **_kwargs: client)
    request = REQUEST_MODELS[tool].model_validate(arguments)

    getattr(provider, provider_method)(
        request,
        compartment_id="ocid1.compartment.oc1..example",
        opc_request_id="CLIENT_REQ",
    )

    assert client.operation == sdk_operation
    details = client.kwargs[details_argument]
    assert details.compartment_id == "ocid1.compartment.oc1..example"
    assert details.endpoint_id is None
    assert details.alias is None
    assert client.kwargs["opc_request_id"] == "CLIENT_REQ"
    assert isinstance(client.kwargs["retry_strategy"], oci.retry.NoneRetryStrategy)


def test_provider_maps_dominant_language_and_translation_options(monkeypatch) -> None:
    provider = OciLanguageProvider(LanguageMcpSettings())
    client = FakeLanguageClient()
    monkeypatch.setattr(provider, "_client", lambda **_kwargs: client)
    dominant = REQUEST_MODELS["detect_dominant_language"].model_validate(
        {
            "documents": [{"key": "one", "text": "hello"}],
            "should_ignore_transliteration": True,
            "chars_to_consider": 0,
        }
    )
    provider.detect_dominant_language(
        dominant, compartment_id="compartment", opc_request_id="REQ"
    )
    details = client.kwargs["batch_detect_dominant_language_details"]
    assert details.should_ignore_transliteration is True
    assert details.chars_to_consider == 0

    translation = REQUEST_MODELS["translate_language_text"].model_validate(
        {
            "documents": [{"key": "one", "text": "hello"}],
            "target_language_code": "fr",
            "no_translate": ["OCI"],
        }
    )
    provider.translate_text(
        translation, compartment_id="compartment", opc_request_id="REQ"
    )
    details = client.kwargs["batch_language_translation_details"]
    assert details.documents[0].language_code == "auto"
    assert details.target_language_code == "fr"
    assert details.no_translate == ["OCI"]


def test_provider_maps_optional_sentiment_levels(monkeypatch) -> None:
    provider = OciLanguageProvider(LanguageMcpSettings())
    client = FakeLanguageClient()
    monkeypatch.setattr(provider, "_client", lambda **_kwargs: client)

    document_only = REQUEST_MODELS["detect_language_sentiments"].model_validate(
        {"documents": [{"key": "one", "text": "Great service"}]}
    )
    provider.analyze_sentiment(
        document_only, compartment_id="compartment", opc_request_id="REQ"
    )
    assert "level" not in client.kwargs

    detailed = REQUEST_MODELS["detect_language_sentiments"].model_validate(
        {
            "documents": [{"key": "one", "text": "Great food and slow service"}],
            "levels": ["ASPECT", "SENTENCE"],
        }
    )
    provider.analyze_sentiment(
        detailed, compartment_id="compartment", opc_request_id="REQ"
    )
    assert client.kwargs["level"] == ["ASPECT", "SENTENCE"]


def test_provider_maps_all_pii_modes() -> None:
    request = REQUEST_MODELS["detect_language_pii_entities"].model_validate(
        {
            "documents": [{"key": "one", "text": "Jane"}],
            "masking": {
                "PERSON": {"mode": "REPLACE", "replace_with": "[NAME]"},
                "ADDRESS": {"mode": "REMOVE"},
                "DATE_TIME": {"mode": "RELEXIFY"},
                "EMAIL": {"mode": "MASK"},
            },
        }
    )
    mapped = OciLanguageProvider._masking(request)
    assert isinstance(mapped["PERSON"], oci.ai_language.models.PiiEntityReplace)
    assert isinstance(mapped["ADDRESS"], oci.ai_language.models.PiiEntityRemove)
    assert isinstance(mapped["DATE_TIME"], oci.ai_language.models.PiiEntityRelexify)
    assert isinstance(mapped["EMAIL"], oci.ai_language.models.PiiEntityMask)


@pytest.mark.parametrize("auth_mode", ["session", "instance_principal", "resource_principal"])
def test_provider_sets_safe_client_configuration_for_each_auth_mode(
    monkeypatch, capsys, auth_mode
) -> None:
    captured: dict[str, object] = {}
    sentinel_payload = "SENTINEL_REQUEST_TEXT"
    sentinel_authorization = "SENTINEL_AUTHORIZATION"

    class CapturingLanguageClient:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)
            if kwargs["config"].get("log_requests"):
                print(sentinel_payload)
                print(sentinel_authorization, file=__import__("sys").stderr)

    monkeypatch.setattr(
        "oracle.oci_language_mcp_server.provider.build_auth_context",
        lambda *_args, **_kwargs: SimpleNamespace(
            mode=auth_mode,
            region="us-phoenix-1",
            config={"region": "us-phoenix-1"},
            signer=None,
        ),
    )
    monkeypatch.setattr(
        oci.ai_language,
        "AIServiceLanguageClient",
        CapturingLanguageClient,
    )

    OciLanguageProvider(LanguageMcpSettings(oci_auth_mode=auth_mode))._client(region=None)

    assert captured["config"]["additional_user_agent"] == "oci-language-mcp/0.1.0"
    assert captured["config"]["log_requests"] is False
    output = capsys.readouterr()
    assert sentinel_payload not in output.out + output.err
    assert sentinel_authorization not in output.out + output.err
