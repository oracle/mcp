# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""MCP middleware with payload-safe request telemetry."""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.tool import ToolResult
from mcp import types as mt

from .constants import TOOL_ARGUMENTS

logger = structlog.get_logger(component="mcp_middleware")
_CLIENT_META_KEYS = frozenset({"task_progress"})


class ArgumentSanitizationMiddleware(Middleware):
    """Remove known client metadata that is not part of the tool contract."""

    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        arguments: dict[str, Any] | None = context.message.arguments
        if arguments:
            stripped = _CLIENT_META_KEYS.intersection(arguments)
            for key in stripped:
                del arguments[key]
            if stripped:
                await logger.adebug(
                    "client_metadata_removed",
                    tool=context.message.name,
                    keys=sorted(stripped),
                )
            allowed = TOOL_ARGUMENTS.get(context.message.name, frozenset())
            unknown = set(arguments).difference(allowed)
            if unknown:
                for key in unknown:
                    del arguments[key]
                # Preserve only the fact that unknown fields existed. Never copy or log
                # attacker-controlled field names or values.
                arguments["_invalid_fields"] = True
        return await call_next(context)


class SafeTelemetryMiddleware(Middleware):
    """Log method, outcome, correlation id, and duration without arguments."""

    async def on_request(
        self,
        context: MiddlewareContext[mt.Request],
        call_next: CallNext[mt.Request, object],
    ) -> object:
        correlation_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        started = time.perf_counter()
        status = "ok"
        try:
            result = await call_next(context)
            if isinstance(result, ToolResult) and result.structured_content:
                tool_status = result.structured_content.get("status")
                if tool_status == "failed":
                    status = "error"
                elif tool_status == "partial":
                    status = "partial"
            return result
        except Exception:
            status = "error"
            raise
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            await logger.ainfo(
                "mcp_request_completed",
                method=context.method,
                status=status,
                duration_ms=round(duration_ms, 2),
            )
            structlog.contextvars.clear_contextvars()
