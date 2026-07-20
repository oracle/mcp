"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from oracle.oci_document_understanding_mcp_server import __project__, __version__
from oracle.oci_document_understanding_mcp_server.handlers.classification import DocumentClassificationHandler
from oracle.oci_document_understanding_mcp_server.handlers.extraction import DocumentExtractionHandler
from oracle.oci_document_understanding_mcp_server.models import ClassificationOptions, DocumentSource, ExtractionOptions
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci.provider import OciDocumentUnderstandingProvider, create_provider
from oracle.oci_document_understanding_mcp_server.parsers.classification import ClassificationOutputParser
from oracle.oci_document_understanding_mcp_server.parsers.extraction import ExtractionOutputParser

mcp = FastMCP(name=__project__, version=__version__)

_provider: OciDocumentUnderstandingProvider | None = None
_extraction_handler: DocumentExtractionHandler | None = None
_classification_handler: DocumentClassificationHandler | None = None


def _get_provider() -> OciDocumentUnderstandingProvider:
    """Creates the configured OCI provider once for this server process."""
    global _provider
    if _provider is None:
        _provider = create_provider(OciDocumentUnderstandingConfig.from_environment())
    return _provider


def _get_extraction_handler() -> DocumentExtractionHandler:
    """Creates the document extraction handler once for this server process."""
    global _extraction_handler
    if _extraction_handler is None:
        _extraction_handler = DocumentExtractionHandler(_get_provider(), ExtractionOutputParser())
    return _extraction_handler


def _get_classification_handler() -> DocumentClassificationHandler:
    """Creates the document classification handler once for this server process."""
    global _classification_handler
    if _classification_handler is None:
        _classification_handler = DocumentClassificationHandler(_get_provider(), ClassificationOutputParser())
    return _classification_handler


def _model_dump(value: BaseModel | dict[str, Any] | FieldInfo | None) -> dict[str, Any] | None:
    """Normalizes FastMCP/Pydantic inputs into the existing handler dictionary contract."""
    if value is None or isinstance(value, FieldInfo):
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_none=True)
    return value


def _arguments(**kwargs: Any) -> dict[str, Any]:
    """Drops omitted optional tool arguments before delegating to existing handlers."""
    return {key: value for key, value in kwargs.items() if value is not None and not isinstance(value, FieldInfo)}


@mcp.tool(name="document_extract")
def document_extract(
    features: list[str] = Field(..., description="Document extraction features to run: TEXT, KEY_VALUE, TABLE, or ELEMENT."),
    document_source: DocumentSource | None = Field(
        None,
        description="Structured document source. Use INLINE_BASE64 for inline content or OBJECT_STORAGE for an OCI Object Storage object.",
    ),
    document: str | None = Field(None, description="Base64-encoded document content for backward-compatible inline input."),
    mime_type: str | None = Field(None, description="MIME type for backward-compatible inline input, for example application/pdf."),
    options: ExtractionOptions | None = Field(None, description="Optional extraction settings such as language and confidence output."),
) -> dict[str, Any]:
    """Extract text, key-value pairs, tables, and document elements from a document."""
    return _get_extraction_handler().handle(
        _arguments(
            document_source=_model_dump(document_source),
            document=document,
            mime_type=mime_type,
            features=features,
            options=_model_dump(options),
        )
    )


@mcp.tool(name="document_classify")
def document_classify(
    document_source: DocumentSource | None = Field(
        None,
        description="Structured document source. Use INLINE_BASE64 for inline content or OBJECT_STORAGE for an OCI Object Storage object.",
    ),
    document: str | None = Field(None, description="Base64-encoded document content for backward-compatible inline input."),
    mime_type: str | None = Field(None, description="MIME type for backward-compatible inline input, for example application/pdf."),
    options: ClassificationOptions | None = Field(None, description="Optional classification settings such as language and confidence threshold."),
    document_type_hint: str | None = Field(None, description="Optional hint to guide classification, for example INVOICE or RECEIPT."),
) -> dict[str, Any]:
    """Classify a document and return candidate document classes with confidence."""
    return _get_classification_handler().handle(
        _arguments(
            document_source=_model_dump(document_source),
            document=document,
            mime_type=mime_type,
            options=_model_dump(options),
            document_type_hint=document_type_hint,
        )
    )


def main() -> None:
    """Run the MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
