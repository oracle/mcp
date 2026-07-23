"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from oracle.oci_document_understanding_mcp_server.models import (
    ClassificationOptions,
    ClassificationRequest,
    DocumentSource,
    ExtractionOptions,
    ExtractionRequest,
)
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci.provider import create_provider
from oracle.oci_document_understanding_mcp_server.oci.stub_provider import StubOciDocumentUnderstandingProvider


def _config() -> OciDocumentUnderstandingConfig:
    return OciDocumentUnderstandingConfig(
        runtime_mode="stub",
        region="us-phoenix-1",
        endpoint=None,
        auth_mode="none",
        default_compartment_id=None,
        config_file_path=None,
        profile="DEFAULT",
    )


def test_create_provider_uses_stub_for_stub_mode() -> None:
    assert isinstance(create_provider(_config()), StubOciDocumentUnderstandingProvider)


def test_stub_provider_returns_extraction_and_classification_payloads() -> None:
    provider = StubOciDocumentUnderstandingProvider(_config())
    source = DocumentSource(source_type="INLINE_BASE64", document="SGVsbG8=", mime_type="application/pdf")

    extraction = provider.extract(
        ExtractionRequest(
            document_source=source,
            features=["TEXT", "KEY_VALUE", "TABLE", "ELEMENT"],
            options=ExtractionOptions(language="en", include_confidence=True),
        )
    )
    classification = provider.classify(
        ClassificationRequest(
            document_source=source,
            options=ClassificationOptions(language="en", confidence_threshold=0.2),
            document_type_hint="INVOICE",
        )
    )

    assert extraction.payload["provider"] == "stub"
    assert extraction.payload["text"]
    assert extraction.payload["keyValues"]
    assert extraction.payload["tables"]
    assert extraction.payload["elements"]
    assert classification.payload["documentType"] == "INVOICE"
    assert classification.payload["confidenceThreshold"] == 0.2
