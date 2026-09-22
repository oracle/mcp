"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

from . import administration, customization, notifications, realtime, transcription, tts
from .administration import (
    index_guide,
    policies_guide,
    prerequisites_guide,
    service_limits_guide,
)
from .customization import customizations_guide
from .notifications import notifications_guide
from .realtime import realtime_guide
from .transcription import local_files_guide, transcription_guide
from .tts import ssml_guide, text_to_speech_guide

def register_resources(mcp: FastMCP) -> None:
    administration.register_resources(mcp)
    transcription.register_resources(mcp)
    customization.register_resources(mcp)
    tts.register_resources(mcp)
    notifications.register_resources(mcp)
    realtime.register_resources(mcp)


__all__ = [
    "customizations_guide",
    "index_guide",
    "local_files_guide",
    "notifications_guide",
    "policies_guide",
    "prerequisites_guide",
    "realtime_guide",
    "register_resources",
    "service_limits_guide",
    "ssml_guide",
    "text_to_speech_guide",
    "transcription_guide",
]
