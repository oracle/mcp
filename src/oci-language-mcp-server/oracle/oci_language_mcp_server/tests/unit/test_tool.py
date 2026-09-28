# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

from __future__ import annotations

from fastmcp import Client, FastMCP

from oracle.oci_language_mcp_server.constants import TOOL_NAMES
from oracle.oci_language_mcp_server.middleware import ArgumentSanitizationMiddleware
from oracle.oci_language_mcp_server.models import DetectDominantLanguageResult, ResultSummary
from oracle.oci_language_mcp_server.tools import TOOL_TITLES, register_tools


class FakeLanguageService:
    def __init__(self, *, failed: bool = False) -> None:
        self.request = None
        self.tool = None
        self.failed = failed
        self.tool_timeout_seconds = 40.0

    async def execute(self, tool, request):
        self.tool = tool
        self.request = request
        return DetectDominantLanguageResult(
            status="failed" if self.failed else "succeeded",
            text="Language detection failed." if self.failed else "Language detection succeeded.",
            request_id="MCP",
            client_opc_request_id="CLIENT",
            oci_request_id="CLIENT/OCI",
            documents=(
                []
                if self.failed
                else [
                    {
                        "key": request.documents[0].key,
                        "languages": [{"name": "English", "code": "en", "score": 1}],
                    }
                ]
            ),
            errors=(
                [{"code": "UPSTREAM_UNAVAILABLE", "message": "Unavailable"}]
                if self.failed
                else []
            ),
            summary=ResultSummary(
                submitted=1,
                succeeded=0 if self.failed else 1,
                failed=1 if self.failed else 0,
                items_found=0 if self.failed else 1,
            ),
        )


async def test_tool_returns_text_structured_content_and_error_semantics() -> None:
    service = FakeLanguageService()
    server = FastMCP("test")
    register_tools(server, service, ("detect_dominant_language",))
    async with Client(server) as client:
        tools = await client.list_tools()
        result = await client.call_tool(
            "detect_dominant_language",
            {"documents": [{"key": "one", "text": "hello"}]},
        )
    assert tools[0].outputSchema is not None
    assert tools[0].title == TOOL_TITLES["detect_dominant_language"]
    assert result.content[0].text == "Language detection succeeded."
    assert result.structured_content["oci_request_id"] == "CLIENT/OCI"
    assert result.is_error is False

    failed_server = FastMCP("test")
    register_tools(
        failed_server, FakeLanguageService(failed=True), ("detect_dominant_language",)
    )
    async with Client(failed_server) as client:
        failed = await client.call_tool(
            "detect_dominant_language",
            {"documents": [{"key": "one", "text": "hello"}]},
            raise_on_error=False,
        )
    assert failed.is_error is True


async def test_validation_and_unknown_arguments_are_sanitized() -> None:
    service = FakeLanguageService()
    server = FastMCP("test", middleware=[ArgumentSanitizationMiddleware()])
    register_tools(server, service, ("detect_dominant_language",))
    async with Client(server) as client:
        result = await client.call_tool(
            "detect_dominant_language",
            {
                "documents": [{"key": "bad key", "text": "sensitive input"}],
                "endpoint_id": "not-allowed",
            },
            raise_on_error=False,
        )
    assert result.is_error is True
    assert result.structured_content["errors"][0]["code"] == "INVALID_REQUEST"
    assert "sensitive input" not in str(result)
    assert result.content[0].text.startswith("Language detection failed.")
    assert "detect_dominant_language" not in result.content[0].text
    assert service.request is None


def test_catalog_has_exact_public_tools() -> None:
    assert TOOL_NAMES == (
        "detect_dominant_language",
        "detect_language_text_classification",
        "detect_language_entities",
        "detect_language_key_phrases",
        "detect_language_sentiments",
        "detect_language_pii_entities",
        "translate_language_text",
    )
    assert tuple(TOOL_TITLES) == TOOL_NAMES
