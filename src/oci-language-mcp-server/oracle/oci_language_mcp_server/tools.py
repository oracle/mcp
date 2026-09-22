# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""Registration of the public OCI Language MCP tools."""

from __future__ import annotations

import uuid
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.tools.function_tool import FunctionTool
from fastmcp.tools.tool import ToolResult
from mcp.types import CallToolResult, ContentBlock, TextContent
from pydantic import ValidationError

from .constants import TOOL_ARGUMENTS
from .models import REQUEST_MODELS, RESULT_MODELS, BaseToolResult, tool_input_schema
from .parser import failure_result
from .service import LanguageService

TOOL_DESCRIPTIONS = {
    "detect_dominant_language": (
        "Detect the dominant language of 1-100 plain-text documents using OCI Language. "
        "Use before language-specific analysis or when the source language is unknown."
    ),
    "detect_language_text_classification": (
        "Classify 1-100 English documents into OCI Language content categories and return "
        "labels with confidence scores."
    ),
    "detect_language_entities": (
        "Detect named entities in 1-100 English or Spanish documents and return their "
        "type, location, text, and confidence."
    ),
    "detect_language_key_phrases": (
        "Extract important phrases from 1-100 English or Spanish documents and return "
        "each phrase with its confidence."
    ),
    "detect_language_sentiments": (
        "Analyze sentiment in 1-100 English or Spanish documents. Document sentiment is "
        "always returned; optionally request ASPECT, SENTENCE, or both detailed levels."
    ),
    "detect_language_pii_entities": (
        "Detect PII in 1-100 English documents, optionally applying MASK, REPLACE, REMOVE, "
        "or RELEXIFY rules. Transformed results omit original detected values by default; "
        "configured exclusions deliberately leave matching values unchanged."
    ),
    "translate_language_text": (
        "Translate 1-100 documents with OCI Language. Specify a target language and either "
        "a source language per document or auto detection."
    ),
}

TOOL_TITLES = {
    "detect_dominant_language": "Detect Dominant Language",
    "detect_language_text_classification": "Classify Language Text",
    "detect_language_entities": "Detect Language Entities",
    "detect_language_key_phrases": "Detect Language Key Phrases",
    "detect_language_sentiments": "Detect Language Sentiments",
    "detect_language_pii_entities": "Detect Language PII Entities",
    "translate_language_text": "Translate Language Text",
}


class LanguageMcpToolResult(ToolResult):
    is_error: bool = False

    def __init__(
        self,
        *,
        content: list[ContentBlock],
        structured_content: dict[str, Any],
        is_error: bool,
    ) -> None:
        super().__init__(content=content, structured_content=structured_content)
        object.__setattr__(self, "is_error", is_error)

    def to_mcp_result(self) -> CallToolResult:
        return CallToolResult(
            content=self.content,
            structuredContent=self.structured_content,
            isError=self.is_error,
        )


def register_tools(
    mcp_server: FastMCP, service: LanguageService, enabled_tools: tuple[str, ...]
) -> None:
    for tool in enabled_tools:
        _register_tool(mcp_server, service, tool)


def _register_tool(mcp_server: FastMCP, service: LanguageService, tool_name: str) -> None:
    async def invoke(
        ctx: Context,
        documents: Any = None,
        compartment_id: Any = None,
        options: Any = None,
        should_ignore_transliteration: Any = None,
        chars_to_consider: Any = None,
        levels: Any = None,
        masking: Any = None,
        target_language_code: Any = None,
        no_translate: Any = None,
        _invalid_fields: bool = False,
    ) -> ToolResult:
        del ctx
        supplied = {
            "documents": documents,
            "compartment_id": compartment_id,
            "options": options,
            "should_ignore_transliteration": should_ignore_transliteration,
            "chars_to_consider": chars_to_consider,
            "levels": levels,
            "masking": masking,
            "target_language_code": target_language_code,
            "no_translate": no_translate,
        }
        arguments = {
            name: value
            for name, value in supplied.items()
            if name in TOOL_ARGUMENTS[tool_name] and value is not None
        }
        if _invalid_fields:
            arguments["invalid_fields"] = True
        request_type = REQUEST_MODELS[tool_name]
        try:
            request = request_type.model_validate(arguments)
        except ValidationError:
            submitted = len(documents) if isinstance(documents, list) else 0
            result = failure_result(
                tool=tool_name,
                request_id=uuid.uuid4().hex,
                client_opc_request_id=None,
                submitted=submitted,
                code="INVALID_REQUEST",
                message=(
                    f"The {TOOL_TITLES[tool_name].lower()} request is invalid. "
                    "Check the tool schema and retry."
                ),
                retryable=False,
            )
        else:
            result = await service.execute(tool_name, request)
        return _mcp_result(result)

    invoke.__name__ = tool_name
    tool = FunctionTool.from_function(
        invoke,
        name=tool_name,
        title=TOOL_TITLES[tool_name],
        description=TOOL_DESCRIPTIONS[tool_name],
        output_schema=RESULT_MODELS[tool_name].model_json_schema(),
        timeout=service.tool_timeout_seconds,
    )
    tool = tool.model_copy(update={"parameters": tool_input_schema(tool_name)})
    mcp_server.add_tool(tool)


def _mcp_result(result: BaseToolResult) -> LanguageMcpToolResult:
    return LanguageMcpToolResult(
        content=[TextContent(type="text", text=result.text)],
        structured_content=result.model_dump(mode="json", exclude_none=True),
        is_error=result.status == "failed",
    )
