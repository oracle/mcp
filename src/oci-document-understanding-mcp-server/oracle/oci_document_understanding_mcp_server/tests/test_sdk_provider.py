"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import sys
from types import SimpleNamespace

from oci import util as real_oci_util
from oci.ai_document import models as real_ai_document_models
import pytest

from oracle.oci_document_understanding_mcp_server.models import (
    ClassificationOptions,
    ClassificationRequest,
    DocumentSource,
    ExtractionOptions,
    ExtractionRequest,
)
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci import sdk_provider
from oracle.oci_document_understanding_mcp_server.oci.sdk_provider import OciSdkDocumentUnderstandingProvider


class FakeClient:
    created: list[tuple[dict, object | None]] = []
    responses: list[object] = []

    def __init__(self, config: dict, signer: object | None = None, **kwargs: object) -> None:
        self.config = config
        self.signer = signer
        self.client_kwargs = kwargs
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

    class FakeCircuitBreakerStrategy:
        pass

    def from_file(_path: str, _profile: str) -> dict:
        return {
            "region": "us-phoenix-1",
            "security_token_file": token_file,
            "key_file": "/tmp/key.pem",
        }

    def to_dict(value: object) -> object:
        return value.payload if isinstance(value, FakeData) else real_oci_util.to_dict(value)

    fake_oci = SimpleNamespace(
        config=SimpleNamespace(from_file=from_file, DEFAULT_LOCATION="~/.oci/config"),
        signer=SimpleNamespace(load_private_key_from_file=lambda _path: object()),
        util=SimpleNamespace(to_dict=to_dict),
        retry=SimpleNamespace(DEFAULT_RETRY_STRATEGY=object()),
        circuit_breaker=SimpleNamespace(CircuitBreakerStrategy=FakeCircuitBreakerStrategy),
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
    monkeypatch.setattr(
        sdk_provider,
        "build_auth_context",
        lambda: SimpleNamespace(config={"region": "us-phoenix-1"}, region="us-phoenix-1", signer=object()),
    )


def _config(*, compartment: str | None = "ocid1.compartment.oc1..example") -> OciDocumentUnderstandingConfig:
    return OciDocumentUnderstandingConfig(
        runtime_mode="oci",
        default_compartment_id=compartment,
    )


@pytest.mark.parametrize(
    ("auth_type", "auth_config", "expected_region"),
    [
        ("api_key", {"region": "eu-frankfurt-1"}, "eu-frankfurt-1"),
        ("security_token", {"region": "eu-frankfurt-1"}, "eu-frankfurt-1"),
        ("identity_domain_upst", {"region": "us-ashburn-1"}, "us-ashburn-1"),
        ("instance_principal", {"region": "uk-london-1"}, "uk-london-1"),
        ("resource_principal", {"region": "us-phoenix-1"}, "us-phoenix-1"),
        ("instance_principal_delegation", {"region": "us-chicago-1"}, "us-chicago-1"),
        ("resource_principal_delegation", {"region": "ca-toronto-1"}, "ca-toronto-1"),
        ("oke_workload_identity", {"region": "ap-mumbai-1"}, "ap-mumbai-1"),
    ],
)
def test_sdk_provider_uses_shared_auth_and_sets_user_agent_for_all_auth_contexts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    auth_type: str,
    auth_config: dict,
    expected_region: str,
) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    signer = object()
    calls = 0

    def fake_build_auth_context():
        nonlocal calls
        calls += 1
        return SimpleNamespace(auth_type=auth_type, config=auth_config, region=expected_region, signer=signer)

    monkeypatch.setattr(sdk_provider, "build_auth_context", fake_build_auth_context)

    provider = OciSdkDocumentUnderstandingProvider(_config())

    assert FakeClient.created[-1][0]["additional_user_agent"] == "oci-document-understanding-mcp/0.1.0"
    assert FakeClient.created[-1][0]["region"] == expected_region
    assert FakeClient.created[-1][1] is signer
    assert provider.client.client_kwargs["retry_strategy"] is not None
    assert provider.client.client_kwargs["circuit_breaker_strategy"] is not None
    assert callable(provider.client.client_kwargs["circuit_breaker_callback"])
    assert calls == 1


def test_sdk_provider_requires_region_from_common_auth(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    monkeypatch.setattr(
        sdk_provider,
        "build_auth_context",
        lambda: SimpleNamespace(config={}, region=None, signer=object()),
    )

    with pytest.raises(RuntimeError, match="OCI region is required"):
        OciSdkDocumentUnderstandingProvider(_config())



def test_sdk_provider_removes_confidence_when_requested(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    monkeypatch.setattr(
        sdk_provider,
        "build_auth_context",
        lambda: SimpleNamespace(config={"region": "us-phoenix-1"}, region="us-phoenix-1", signer=object()),
    )
    FakeClient.responses.append(
        SimpleNamespace(
            data=FakeData({"keyValues": [{"key": "invoice", "confidence": 0.98, "nested": {"confidence": 0.9}}]}),
            headers={"opc-request-id": "extract-request"},
        )
    )
    provider = OciSdkDocumentUnderstandingProvider(_config())

    result = provider.extract(
        ExtractionRequest(
            document_source=DocumentSource(source_type="INLINE_BASE64", document="SGVsbG8=", mime_type="application/pdf"),
            features=["KEY_VALUE"],
            options=ExtractionOptions(language=None, include_confidence=False),
        )
    )

    assert result.payload["keyValues"] == [{"key": "invoice", "nested": {}}]


def test_sdk_provider_serializes_real_oci_sdk_result_model(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    FakeClient.responses.append(
        SimpleNamespace(
            data=real_ai_document_models.AnalyzeDocumentResult(
                pages=[real_ai_document_models.Page(page_number=1, lines=[real_ai_document_models.Line(text="hello", confidence=0.9)])]
            ),
            headers={"opc-request-id": "extract-request"},
        )
    )
    provider = OciSdkDocumentUnderstandingProvider(_config())

    result = provider.extract(
        ExtractionRequest(
            document_source=DocumentSource(source_type="INLINE_BASE64", document="SGVsbG8=", mime_type="application/pdf"),
            features=["TEXT"],
            options=ExtractionOptions(language=None, include_confidence=True),
        )
    )

    assert result.payload["pages"][0]["lines"][0]["text"] == "hello"


def test_sdk_provider_requires_compartment_before_building_request(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    token_file = tmp_path / "token"
    token_file.write_text("token", encoding="utf-8")
    _install_fake_oci(monkeypatch, str(token_file))
    provider = OciSdkDocumentUnderstandingProvider(_config(compartment=None))
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
    provider = OciSdkDocumentUnderstandingProvider(_config())
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
    provider = OciSdkDocumentUnderstandingProvider(_config())

    assert provider._response_to_payload(SimpleNamespace(data=object()))["raw"].startswith("<object")
    assert provider._request_id(SimpleNamespace(headers={})) == "unknown"
    with pytest.raises(KeyError):
        provider._feature_model("BAD")
