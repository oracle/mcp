"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP


def plan_realtime_integration_prompt(goal: str) -> str:
    return f"""Plan a client-side OCI Realtime Speech integration for
`{goal}`. Read `speech://guides/realtime`, `speech://guides/customizations`, and
`speech://guides/service-limits`.
Keep the WebSocket, signer, microphone, and raw audio in the audio-producing
application. Specify the OCI region and endpoint, Oracle or Whisper model,
language, exact audio encoding, silence/punctuation settings, and any ACTIVE
customization. Design all required listener callbacks, an authentication-ready
gate, a bounded thread-safe audio queue, partial-versus-final transcript state,
acknowledgement telemetry, request-final-result shutdown, and capped reconnect
behavior. Identify which customization operations this MCP server should manage
separately, and never place credentials or raw audio in the conversation."""


def register_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        name="plan_realtime_integration",
        description="Plan a safe client-side Realtime Speech integration.",
    )(plan_realtime_integration_prompt)
