"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from typing import Any, Literal
from xml.etree import ElementTree

import oci
from fastmcp import FastMCP
from pydantic import Field

from ..models import AudioFormat, OperationResult, SpeechModel, TextType
from ..utils.clients import TTS_REGION, get_clients
from ..utils.paths import safe_output_path
from ..utils.responses import page_items, raise_safe, response_header, to_dict, write_stream

SUPPORTED_SSML_TAGS = {
    "speak",
    "break",
    "s",
    "p",
    "say-as",
    "sub",
    "phoneme",
    "prosody",
    "voice",
}


def validate_ssml(text: str) -> set[str]:
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        raise ValueError(f"SSML must be well-formed XML: {error}.") from None
    root_name = root.tag.rsplit("}", 1)[-1]
    if root_name != "speak":
        raise ValueError("SSML must use <speak> as its root element.")
    tags = {
        element.tag.rsplit("}", 1)[-1]
        for element in root.iter()
        if isinstance(element.tag, str)
    }
    unsupported = sorted(tags - SUPPORTED_SSML_TAGS)
    if unsupported:
        raise ValueError(
            "Unsupported OCI Speech SSML tag(s): " + ", ".join(unsupported)
        )
    return tags


def list_voices(
    compartment_id: str,
    model_name: SpeechModel | None = None,
    language_code: str | None = None,
    display_name: str | None = None,
    max_items: int = Field(default=100, ge=1, le=1000),
) -> OperationResult:
    """List text-to-speech voices in Phoenix with a bounded response."""
    kwargs: dict[str, Any] = {"compartment_id": compartment_id}
    if model_name:
        kwargs["model_name"] = model_name
    if language_code:
        kwargs["language_code"] = language_code
    if display_name:
        kwargs["display_name"] = display_name
    try:
        response = get_clients().speech_tts.list_voices(**kwargs)
        voices = page_items(response.data)[:max_items]
        return OperationResult(
            operation="list_voices",
            data=to_dict(voices),
            status=getattr(response, "status", None),
            opc_request_id=response_header(response, "opc-request-id"),
            count=len(voices),
            notes=[f"Text-to-speech calls are routed to {TTS_REGION}."],
        )
    except Exception as error:
        raise_safe("list_voices", error)


def synthesize_speech(
    text: str = Field(
        min_length=1,
        max_length=10000,
        description="Plain text or complete SSML, including the required <speak> root.",
    ),
    compartment_id: str = Field(
        description="Compartment OCID authorized for text-to-speech."
    ),
    voice_id: str = Field(description="Voice ID returned by list_voices."),
    output_filename: str = Field(
        description="Relative path under OCI_SPEECH_OUTPUT_ROOT."
    ),
    model_name: SpeechModel = "TTS_1_STANDARD",
    language_code: str | None = None,
    text_type: TextType = "TEXT",
    output_format: AudioFormat = "MP3",
    sample_rate_in_hz: int | None = Field(default=None, ge=8000, le=48000),
    speech_mark_types: list[Literal["WORD", "SENTENCE"]] | None = None,
    overwrite: bool = False,
) -> OperationResult:
    """Synthesize text or SSML and stream it to a contained local file."""
    try:
        ssml_tags: set[str] = set()
        if text_type == "SSML":
            ssml_tags = validate_ssml(text)
            if language_code is not None and language_code != "en-US":
                raise ValueError("OCI Speech SSML is supported only for en-US voices.")
            if model_name == "TTS_2_NATURAL" and "prosody" in ssml_tags:
                raise ValueError("The <prosody> SSML tag is supported only by standard voices.")
        if model_name == "TTS_2_NATURAL":
            model_details = oci.ai_speech.models.TtsOracleTts2NaturalModelDetails(
                model_name=model_name,
                voice_id=voice_id,
                language_code=language_code,
            )
        else:
            if language_code:
                raise ValueError("language_code is only accepted by TTS_2_NATURAL.")
            model_details = oci.ai_speech.models.TtsOracleTts1StandardModelDetails(
                model_name=model_name,
                voice_id=voice_id,
            )
        if speech_mark_types and output_format != "JSON":
            raise ValueError("speech_mark_types require output_format=JSON.")
        configuration = oci.ai_speech.models.TtsOracleConfiguration(
            model_details=model_details,
            speech_settings=oci.ai_speech.models.TtsOracleSpeechSettings(
                text_type=text_type,
                sample_rate_in_hz=sample_rate_in_hz,
                output_format=output_format,
                speech_mark_types=speech_mark_types,
            ),
        )
        details = oci.ai_speech.models.SynthesizeSpeechDetails(
            text=text,
            is_stream_enabled=True,
            compartment_id=compartment_id,
            configuration=configuration,
        )
        destination = safe_output_path(output_filename, overwrite=overwrite)
        response = get_clients().speech_tts.synthesize_speech(details)
        byte_count = write_stream(response.data, destination)
        notes = []
        if text_type == "SSML":
            notes.append(
                "SSML was validated locally. Confirm the selected en-US voice supports "
                "SSML before treating the synthesis as portable."
            )
        return OperationResult(
            operation="synthesize_speech",
            data={
                "local_path": str(destination),
                "bytes": byte_count,
                "model_name": model_name,
                "voice_id": voice_id,
                "text_type": text_type,
                "output_format": output_format,
                "region": TTS_REGION,
            },
            status=getattr(response, "status", None),
            opc_request_id=response_header(response, "opc-request-id"),
            notes=notes,
        )
    except Exception as error:
        raise_safe("synthesize_speech", error)


def register_tools(mcp: FastMCP) -> None:
    for tool in (list_voices, synthesize_speech):
        mcp.tool()(tool)
