"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Protocol

from oracle.oci_document_understanding_mcp_server.models import ClassificationRequest, ExtractionRequest, RawOciDocumentResult
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig


class OciDocumentUnderstandingProvider(Protocol):
    """Provider contract implemented by stub and OCI SDK-backed providers."""

    def extract(self, request: ExtractionRequest) -> RawOciDocumentResult:
        """Submits an extraction request and returns raw provider output."""

    def classify(self, request: ClassificationRequest) -> RawOciDocumentResult:
        """Submits a classification request and returns raw provider output."""


def create_provider(config: OciDocumentUnderstandingConfig) -> OciDocumentUnderstandingProvider:
    """Chooses the provider implementation for the configured runtime mode."""
    if config.runtime_mode == "stub":
        from oracle.oci_document_understanding_mcp_server.oci.stub_provider import StubOciDocumentUnderstandingProvider

        return StubOciDocumentUnderstandingProvider(config)

    from oracle.oci_document_understanding_mcp_server.oci.sdk_provider import OciSdkDocumentUnderstandingProvider

    return OciSdkDocumentUnderstandingProvider(config)

