"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP


def synthesize_narration_prompt(text: str) -> str:
    return f"""Create narrated speech for this text: `{text}`.
Read `speech://guides/text-to-speech`, list compatible voices if no voice was
chosen, and read `speech://guides/ssml` when the user wants customized delivery.
Then synthesize to a contained local output file. Confirm model, voice, language,
text type, sample rate, output format, and final path. Never place the audio
payload directly in the conversation."""


def customize_tts_with_ssml_prompt(text: str, goal: str) -> str:
    return f"""Customize this text for OCI Speech TTS:

`{text}`

Delivery goal: `{goal}`

Read `speech://guides/ssml` and `speech://guides/service-limits`. Preserve the
meaning and wording unless the user explicitly requests an editorial change.
Use only OCI-supported tags, escape XML characters, and wrap the result in one
`<speak>` root. Ask for pronunciation intent instead of inventing IPA. Confirm
that a selected en-US voice supports SSML and avoid `<prosody>` with a natural
voice. Show the proposed SSML and briefly explain each insertion before calling
`synthesize_speech` with `text_type=SSML`. Keep the full marked-up request within
10,000 characters."""


def register_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        name="synthesize_narration",
        description="Choose a voice and synthesize narrated audio.",
    )(synthesize_narration_prompt)
    mcp.prompt(
        name="customize_tts_with_ssml",
        description=(
            "Turn supplied text and delivery goals into supported OCI Speech SSML."
        ),
    )(customize_tts_with_ssml_prompt)
