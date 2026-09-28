# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

"""PII-safe structured logging setup."""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(*, level: str, output_format: str) -> None:
    """Configure stderr logging without request or response payload rendering."""

    logging.basicConfig(
        level=getattr(logging, level),
        format="%(message)s",
        force=True,
    )
    # Dependency DEBUG records can render MCP arguments. Application telemetry remains
    # configurable, but dependency payload logging is permanently disabled.
    for logger_name in ("fastmcp", "mcp", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    processors: list[object] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    processors.append(
        structlog.processors.JSONRenderer()
        if output_format == "json"
        else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
