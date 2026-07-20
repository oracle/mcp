"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import asyncio

from oracle.oci_document_understanding_mcp_server import __project__, __version__, server
from oracle.oci_document_understanding_mcp_server.models import ClassificationOptions, DocumentSource, ExtractionOptions
from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig
from oracle.oci_document_understanding_mcp_server.oci.stub_provider import StubOciDocumentUnderstandingProvider
from oracle.oci_document_understanding_mcp_server.response import failed_envelope, successful_envelope, to_text


def _stub_config() -> OciDocumentUnderstandingConfig:
    return OciDocumentUnderstandingConfig(
        runtime_mode="stub",
        region="us-phoenix-1",
        endpoint=None,
        auth_mode="none",
        default_compartment_id=None,
        config_file_path=None,
        profile="DEFAULT",
    )


def _reset_server() -> None:
    server._provider = None
    server._extraction_handler = None
    server._classification_handler = None


def test_fastmcp_server_registers_document_tools() -> None:
    tools = asyncio.run(server.mcp.list_tools())

    assert server.mcp.name == __project__
    assert server.mcp.version == __version__
    assert [tool.name for tool in tools] == ["document_extract", "document_classify"]
    assert tools[0].parameters["required"] == ["features"]
    assert "document_source" in tools[0].parameters["properties"]


def test_fastmcp_call_tool_preserves_success_response_shape(monkeypatch) -> None:
    _reset_server()
    monkeypatch.setattr(server, "create_provider", lambda config: StubOciDocumentUnderstandingProvider(config))
    monkeypatch.setattr(server.OciDocumentUnderstandingConfig, "from_environment", staticmethod(_stub_config))

    result = asyncio.run(
        server.mcp.call_tool(
            "document_extract",
            {
                "document": "SGVsbG8=",
                "mime_type": "application/pdf",
                "features": ["TEXT", "KEY_VALUE"],
                "options": {"language": "en", "include_confidence": True},
            },
        )
    )

    assert result.is_error is False
    assert result.structured_content["status"] == "Successful"
    assert result.structured_content["data"]["text"] == "Sample extracted text from OCI Document Understanding."
    assert result.structured_content["data"]["metadata"]["requestConfigs"][0]["parameters"]["languageCode"] == "en"


def test_direct_tool_functions_preserve_legacy_and_structured_inputs(monkeypatch) -> None:
    _reset_server()
    monkeypatch.setattr(server, "create_provider", lambda config: StubOciDocumentUnderstandingProvider(config))
    monkeypatch.setattr(server.OciDocumentUnderstandingConfig, "from_environment", staticmethod(_stub_config))

    extraction = server.document_extract(
        document="SGVsbG8=",
        mime_type="application/pdf",
        features=["text"],
        options=ExtractionOptions(language="en", include_confidence=True),
    )
    classification = server.document_classify(
        document_source=DocumentSource(
            source_type="OBJECT_STORAGE",
            namespace_name="ns",
            bucket_name="bucket",
            object_name="invoice.pdf",
        ),
        options=ClassificationOptions(language="en", confidence_threshold=0.2),
        document_type_hint="invoice",
    )

    assert extraction["status"] == "Successful"
    assert extraction["data"]["metadata"]["requestConfigs"][0]["parameters"]["featureType"] == "TEXT"
    assert classification["status"] == "Successful"
    assert classification["data"]["documentType"] == "INVOICE"
    assert classification["data"]["metadata"]["requestConfig"]["parameters"]["documentTypeHint"] == "INVOICE"


def test_main_runs_fastmcp_stdio(monkeypatch) -> None:
    called = {}

    def fake_run() -> None:
        called["run"] = True

    monkeypatch.setattr(server.mcp, "run", fake_run)

    server.main()

    assert called == {"run": True}


def test_response_helpers() -> None:
    success = successful_envelope("job", "doc", {"value": 1, "metadata": {"a": "b"}})
    failure = failed_envelope("bad")

    assert success["metadata"] == {"a": "b"}
    assert failure["status"] == "Failed"
    assert '"status":"Successful"' in to_text(success)
