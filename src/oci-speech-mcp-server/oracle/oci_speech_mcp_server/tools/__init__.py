"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

from . import customization, notifications, transcription, tts


def register_tools(mcp: FastMCP) -> None:
    transcription.register_tools(mcp)
    customization.register_tools(mcp)
    tts.register_tools(mcp)
    notifications.register_tools(mcp)
