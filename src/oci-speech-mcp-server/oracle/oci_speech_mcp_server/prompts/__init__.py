"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

from . import administration, customization, notifications, realtime, transcription, tts
from .administration import plan_speech_policies_prompt
from .customization import build_speech_customization_prompt
from .notifications import setup_job_notifications_prompt
from .realtime import plan_realtime_integration_prompt
from .transcription import (
    manage_transcription_job_prompt,
    transcribe_local_audio_prompt,
    troubleshoot_speech_job_prompt,
)
from .tts import customize_tts_with_ssml_prompt, synthesize_narration_prompt

def register_prompts(mcp: FastMCP) -> None:
    transcription.register_prompts(mcp)
    customization.register_prompts(mcp)
    tts.register_prompts(mcp)
    administration.register_prompts(mcp)
    notifications.register_prompts(mcp)
    realtime.register_prompts(mcp)


__all__ = [
    "build_speech_customization_prompt",
    "customize_tts_with_ssml_prompt",
    "manage_transcription_job_prompt",
    "plan_realtime_integration_prompt",
    "plan_speech_policies_prompt",
    "register_prompts",
    "setup_job_notifications_prompt",
    "synthesize_narration_prompt",
    "transcribe_local_audio_prompt",
    "troubleshoot_speech_job_prompt",
]
