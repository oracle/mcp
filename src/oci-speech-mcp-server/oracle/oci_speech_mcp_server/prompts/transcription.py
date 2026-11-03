"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP


def transcribe_local_audio_prompt(local_path: str) -> str:
    return f"""Transcribe the local audio file `{local_path}` using OCI Speech.
First read `speech://guides/local-files`, `speech://guides/transcription`, and
`speech://guides/service-limits`.
Confirm the target compartment and Object Storage bucket are explicit. Use the
end-to-end local-file tool, wait for success, and report the job OCID, lifecycle
state, uploaded object, and downloaded output paths. If the user states that the
audio has multiple speakers, enable diarization and use a known 2–16 speaker
count; if speaker context is missing, ask rather than guessing. Do not expose
audio bytes in the conversation and do not delete the uploaded input
automatically."""


def manage_transcription_job_prompt(job_id: str) -> str:
    return f"""Help manage OCI Speech transcription job `{job_id}`.
Retrieve its current state before proposing a mutation. Use the narrowest job or
task operation needed, preserve ETags when supplied, and summarize the resulting
lifecycle state and request ID."""


def troubleshoot_speech_job_prompt(job_id: str) -> str:
    return f"""Troubleshoot OCI Speech transcription job `{job_id}`.
Retrieve the job and all tasks, distinguish service lifecycle failures from local
download or IAM problems, inspect output locations without reading unrelated
objects, and give the smallest corrective action. Include OCI request IDs but do
not reveal credential material or full SDK request bodies."""


def register_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        name="transcribe_local_audio",
        description="Safely transcribe a local media file end to end.",
    )(transcribe_local_audio_prompt)
    mcp.prompt(
        name="manage_transcription_job",
        description="Inspect and safely manage a transcription job.",
    )(manage_transcription_job_prompt)
    mcp.prompt(
        name="troubleshoot_speech_job",
        description="Diagnose a transcription job and its tasks.",
    )(troubleshoot_speech_job_prompt)
