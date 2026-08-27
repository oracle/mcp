"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

TRANSCRIPTION_GUIDE = """# Transcription workflows

Use `transcribe_local_file` for the simplest end-to-end workflow: validate a
local media file, upload it to Object Storage, submit a job, optionally wait,
and download outputs. Uploaded inputs are deliberately retained; delete them
through your normal Object Storage lifecycle or governance process.

Use `create_transcription_job` when audio is already in Object Storage. A job
can reference up to 100 object names. Oracle models default to `ORACLE` and the
`GENERIC` domain. Whisper model names accepted by your tenancy can also be
provided; use language `auto` where supported. Diarization supports 2–16
speakers. SRT is the supported additional transcription format.

## Diarization decision

- If the user says the audio has multiple speakers—or describes a meeting,
  interview, panel, call, or other multi-person recording—set
  `diarization_enabled=true`.
- If a speaker count from 2 through 16 is known, set `number_of_speakers` too.
  If multiple speakers are known but the exact count is not, enable diarization
  and leave the count unset.
- If the user says the audio is single-speaker, leave diarization disabled.
- If speaker context is absent, ask the user instead of guessing. These MCP tools
  inspect file path, suffix, and size, but do not listen to or pre-analyze the
  audio to detect speakers.

Diarization assigns speaker labels; it does not establish people's identities.
Overlapping speakers and poor input quality can still reduce accuracy. Both the
Oracle ASR and OCI Whisper models support diarization.

Jobs progress through ACCEPTED, IN_PROGRESS, SUCCEEDED, FAILED, CANCELING, and
CANCELED. Job metadata is retained by the service for 90 days. Inspect task
outputs with `list_transcription_tasks`, and download them with
`download_transcription_results`.
"""

LOCAL_FILES_GUIDE = """# Local-file safety

The server will not read a local path unless `OCI_SPEECH_INPUT_ROOT` is set.
The resolved file must stay inside that root, be a regular supported media file,
and be no larger than 2 GiB. Credential and operating-system secret directories
are blocked even if a broad input root would otherwise include them.

Output names must be relative. Resolved outputs remain inside
`OCI_SPEECH_OUTPUT_ROOT`, and existing files are not replaced unless the caller
explicitly sets `overwrite=true`. Object names are reduced to safe basenames
before download.
"""


def transcription_guide() -> str:
    return TRANSCRIPTION_GUIDE


def local_files_guide() -> str:
    return LOCAL_FILES_GUIDE


def register_resources(mcp: FastMCP) -> None:
    mcp.resource(
        "speech://guides/transcription",
        description="OCI Speech transcription job and task workflow guidance.",
    )(transcription_guide)
    mcp.resource(
        "speech://guides/local-files",
        description="Safety rules for local transcription inputs and downloaded outputs.",
    )(local_files_guide)

