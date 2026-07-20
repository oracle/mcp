"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import sys
from types import SimpleNamespace

import pytest

from oracle.oci_document_understanding_mcp_server.models import (
    ClassificationOptions,
    ClassificationRequest,
    DocumentSource,
    ExtractionOptions,
    ExtractionRequest,
)
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci.sdk_provider import OciSdkDocumentUnderstandingProvider


class FakeClient:
    created: list[tuple[dict, object | None]] = []
    responses: list[object] = []

    def __init__(self, config: dict, signer: object | None = None) -> None:
        self.config = config
        self.signer = signer
        self.base_client = SimpleNamespace(endpoint=None, set_endpoint=lambda endpoint: setattr(self.base_client, "endpoint", endpoint))
        FakeClient.created.append((config, signer))

    def analyze_document(self, analyze_document_details: object) -> object:
        self.last_details = analyze_document_details
        return FakeClient.responses.pop(0)


class FakeModel:
    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


class FakeData:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def to_dict(self) -> dict:
        return self.payload


def _install_fake_oci(monkeypatch: pytest.MonkeyPatch, token_file: str) -> None:
    FakeClient.created.clear()
    FakeClient.responses.clear()

    class FakeSecurityTokenSigner:
        def __init__(self, token: str, private_key: object) -> None:
            self.token = token
            self.private_key = private_key

    class FakeInstanceSigner:
        pass

    def from_file(_path: str, _profile: str) -> dict:
        return {
            "region": "us-phoenix-1",
            "security_token_file": token_file,
            "key_file": "/tmp/key.pem",
        }

    fake_oci = SimpleNamespace(
        config=SimpleNamespace(from_file=from_file, DEFAULT_LOCATION="~/.oci/config"),
        signer=SimpleNamespace(load_private_key_from_file=lambda _path: object()),
        auth=SimpleNamespace(
            signers=SimpleNamespace(
                SecurityTokenSigner=FakeSecurityTokenSigner,
                InstancePrincipalsSecurityTokenSigner=FakeInstanceSigner,
            )
        ),
        ai_document=SimpleNamespace(
            AIServiceDocumentClient=FakeClient,
            models=SimpleNamespace(
                AnalyzeDocumentDetails=FakeModel,
                InlineDocumentDetails=FakeModel,
                ObjectStorageDocumentDetails=FakeModel,
                DocumentTextExtractionFeature=FakeModel,
                DocumentKeyValueExtractionFeature=FakeModel,
                DocumentTableExtractionFeature=FakeModel,
                DocumentElementsExtractionFeature=FakeModel,
                DocumentClassificationFeature=FakeModel,
            ),
        ),
    )
    monkeypatch.setitem(sys.modules, "oci", fake_oci)


def _config(auth_mode: str, *, endpoint: str | None = None, compartment: str | None = "ocid1.compartment.oc1..example") -> OciDocumentUnderstandingConfig:
    return OciDocumentUnderstandingConfig(
        runtime_mode="local",
        region="us-phoenix-1",
        endpoint=endpoint,
        auth_mode=auth_mode,
        default_compartment_id=compartment,
        config_file_path=None,
        profile="DEFAULT",
    )


@pytest.mark.parametrize("auth_mode", ["session-token", "api-key", "instance-principal"])
def test_sdk_provider_sets_additional_user_agent_for_auth_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    auth_mode: str,
) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))

    provider = OciSdkDocumentUnderstandingProvider(_config(auth_mode, endpoint="https://documents.example.com"))

    assert provider.client.base_client.endpoint == "https://documents.example.com"
    assert FakeClient.created[-1][0]["additional_user_agent"] == "oci-document-understanding-mcp/0.1.0"


def test_sdk_provider_requires_compartment_before_building_request(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    provider = OciSdkDocumentUnderstandingProvider(_config("api-key", compartment=None))
    request = ExtractionRequest(
        document_source=DocumentSource(source_type="INLINE_BASE64", document="SGVsbG8=", mime_type="application/pdf"),
        features=["TEXT"],
        options=ExtractionOptions(language=None, include_confidence=True),
    )

    with pytest.raises(RuntimeError, match="OCI_COMPARTMENT_ID"):
        provider._build_analyze_document_details(request, "extract", ["TEXT"])


def test_sdk_provider_extract_and_classify_build_oci_requests(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    FakeClient.responses.extend(
        [
            SimpleNamespace(data=FakeData({"text": "hello"}), headers={"opc-request-id": "extract-request"}),
            SimpleNamespace(data={"classifications": [{"label": "INVOICE", "confidence": 0.9}]}, headers={"Opc-Request-Id": "classify-request"}),
        ]
    )
    provider = OciSdkDocumentUnderstandingProvider(_config("api-key"))
    inline_request = ExtractionRequest(
        document_source=DocumentSource(source_type="INLINE_BASE64", document="SGVsbG8=", mime_type="application/pdf", page_range=["1"]),
        features=["TEXT", "KEY_VALUE"],
        options=ExtractionOptions(language="en", include_confidence=True),
    )

    extraction = provider.extract(inline_request)
    classification = provider.classify(
        ClassificationRequest(
            document_source=DocumentSource(source_type="OBJECT_STORAGE", namespace_name="ns", bucket_name="bucket", object_name="doc.pdf"),
            options=ClassificationOptions(language="en", confidence_threshold=0.2),
            document_type_hint="INVOICE",
        )
    )

    assert extraction.request_id == "extract-request"
    assert extraction.payload["provider"] == "oci-sdk"
    assert extraction.payload["requestConfigs"][0]["parameters"]["featureType"] == "TEXT"
    assert classification.request_id == "classify-request"
    assert classification.payload["requestConfig"]["parameters"]["documentTypeHint"] == "INVOICE"


def test_sdk_provider_helpers_cover_fallback_paths(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    provider = OciSdkDocumentUnderstandingProvider(_config("api-key"))

    assert provider._response_to_payload(SimpleNamespace(data=object()))["raw"].startswith("<object")
    assert provider._request_id(SimpleNamespace(headers={})) == "unknown"
    with pytest.raises(KeyError):
        provider._feature_model("BAD")
