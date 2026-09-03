"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import time
import uuid
from pathlib import Path
from typing import Any, Literal

import oci
from fastmcp import FastMCP
from pydantic import Field

from ..models import OperationResult, TaskLifecycle, TranscriptionLifecycle
from ..utils.clients import get_clients
from ..utils.paths import safe_object_filename, safe_output_path, validate_media_input
from ..utils.responses import (
    call_oci,
    list_oci,
    page_items,
    raise_safe,
    response_header,
    safe_error_details,
    to_dict,
    write_stream,
)


def validate_transcription_options(
    model_type: str,
    whisper_prompt: str | None,
    punctuation_enabled: bool,
) -> None:
    """Reject known model-specific conflicts while allowing future model names."""
    known_model = model_type.strip().upper()
    if known_model == "ORACLE" and whisper_prompt:
        raise ValueError("whisper_prompt is supported only when model_type=WHISPER.")
    if known_model == "WHISPER" and not punctuation_enabled:
        raise ValueError("punctuation_enabled must be true when model_type=WHISPER.")


def transcription_model(
    model_type: str,
    domain: str,
    language_code: str,
    diarization_enabled: bool,
    number_of_speakers: int | None,
    whisper_prompt: str | None,
) -> Any:
    if number_of_speakers is not None and not diarization_enabled:
        raise ValueError("number_of_speakers requires diarization_enabled=true.")
    settings: dict[str, Any] = {}
    if diarization_enabled:
        settings["diarization"] = oci.ai_speech.models.Diarization(
            is_diarization_enabled=True,
            number_of_speakers=number_of_speakers,
        )
    if whisper_prompt:
        settings["additional_settings"] = {"whisperPrompt": whisper_prompt}
    return oci.ai_speech.models.TranscriptionModelDetails(
        model_type=model_type,
        domain=domain,
        language_code=language_code,
        transcription_settings=oci.ai_speech.models.TranscriptionSettings(**settings),
    )


def normalization(punctuation_enabled: bool, profanity_mode: str | None) -> Any:
    filters = []
    if profanity_mode:
        filters.append(
            oci.ai_speech.models.ProfanityTranscriptionFilter(mode=profanity_mode)
        )
    return oci.ai_speech.models.TranscriptionNormalization(
        is_punctuation_enabled=punctuation_enabled,
        filters=filters,
    )


def create_transcription_job(
    compartment_id: str,
    display_name: str,
    input_namespace_name: str,
    input_bucket_name: str,
    object_names: list[str] = Field(min_length=1, max_length=100),
    output_namespace_name: str | None = None,
    output_bucket_name: str | None = None,
    output_prefix: str | None = None,
    description: str | None = None,
    model_type: str = "ORACLE",
    domain: Literal["GENERIC", "MEDICAL"] = "GENERIC",
    language_code: str = "en-US",
    diarization_enabled: bool = Field(
        default=False,
        description=(
            "Enable speaker diarization when the user says the media has multiple "
            "speakers. Ask when speaker context is unknown; this server does not "
            "inspect the audio to infer speakers."
        ),
    ),
    number_of_speakers: int | None = Field(
        default=None,
        ge=2,
        le=16,
        description=(
            "Known speaker count from 2 through 16. Leave unset when diarization is "
            "needed but the exact count is unknown."
        ),
    ),
    whisper_prompt: str | None = Field(default=None, max_length=4000),
    punctuation_enabled: bool = True,
    profanity_mode: Literal["MASK", "REMOVE", "TAG"] | None = None,
    include_srt: bool = False,
    freeform_tags: dict[str, str] | None = None,
) -> OperationResult:
    """Create a transcription job for media already in Object Storage."""
    validate_transcription_options(model_type, whisper_prompt, punctuation_enabled)
    details = oci.ai_speech.models.CreateTranscriptionJobDetails(
        compartment_id=compartment_id,
        display_name=display_name,
        description=description,
        input_location=oci.ai_speech.models.ObjectListInlineInputLocation(
            object_locations=[
                oci.ai_speech.models.ObjectLocation(
                    namespace_name=input_namespace_name,
                    bucket_name=input_bucket_name,
                    object_names=object_names,
                )
            ]
        ),
        output_location=oci.ai_speech.models.OutputLocation(
            namespace_name=output_namespace_name or input_namespace_name,
            bucket_name=output_bucket_name or input_bucket_name,
            prefix=output_prefix,
        ),
        model_details=transcription_model(
            model_type,
            domain,
            language_code,
            diarization_enabled,
            number_of_speakers,
            whisper_prompt,
        ),
        normalization=normalization(punctuation_enabled, profanity_mode),
        additional_transcription_formats=["SRT"] if include_srt else [],
        freeform_tags=freeform_tags,
    )
    return call_oci(
        "create_transcription_job",
        lambda: get_clients().speech.create_transcription_job(details),
    )


def get_transcription_job(transcription_job_id: str) -> OperationResult:
    """Get a transcription job by OCID."""
    return call_oci(
        "get_transcription_job",
        lambda: get_clients().speech.get_transcription_job(transcription_job_id),
    )


def list_transcription_jobs(
    compartment_id: str,
    lifecycle_state: TranscriptionLifecycle | None = None,
    display_name: str | None = None,
    transcription_job_id: str | None = None,
    sort_by: Literal["timeCreated", "displayName"] = "timeCreated",
    sort_order: Literal["ASC", "DESC"] = "DESC",
    max_items: int = Field(default=100, ge=1, le=1000),
    page: str | None = None,
) -> OperationResult:
    """List transcription jobs with bounded automatic pagination."""
    kwargs = {
        "compartment_id": compartment_id,
        "lifecycle_state": lifecycle_state,
        "display_name": display_name,
        "id": transcription_job_id,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
    }
    return list_oci(
        "list_transcription_jobs",
        get_clients().speech.list_transcription_jobs,
        {key: value for key, value in kwargs.items() if value is not None},
        max_items=max_items,
    )


def update_transcription_job(
    transcription_job_id: str,
    display_name: str | None = None,
    description: str | None = None,
    freeform_tags: dict[str, str] | None = None,
    if_match: str | None = None,
) -> OperationResult:
    """Update the mutable metadata of a transcription job."""
    if display_name is None and description is None and freeform_tags is None:
        raise ValueError("Provide at least one field to update.")
    details = oci.ai_speech.models.UpdateTranscriptionJobDetails(
        display_name=display_name,
        description=description,
        freeform_tags=freeform_tags,
    )
    kwargs = {"if_match": if_match} if if_match else {}
    return call_oci(
        "update_transcription_job",
        lambda: get_clients().speech.update_transcription_job(
            transcription_job_id, details, **kwargs
        ),
    )


def delete_transcription_job(
    transcription_job_id: str,
    if_match: str | None = None,
) -> OperationResult:
    """Delete a transcription job."""
    kwargs = {"if_match": if_match} if if_match else {}
    return call_oci(
        "delete_transcription_job",
        lambda: get_clients().speech.delete_transcription_job(
            transcription_job_id, **kwargs
        ),
    )


def cancel_transcription_job(transcription_job_id: str) -> OperationResult:
    """Cancel a transcription job that has not finished."""
    return call_oci(
        "cancel_transcription_job",
        lambda: get_clients().speech.cancel_transcription_job(transcription_job_id),
    )


def change_transcription_job_compartment(
    transcription_job_id: str,
    compartment_id: str,
) -> OperationResult:
    """Move a transcription job to another compartment."""
    details = oci.ai_speech.models.ChangeTranscriptionJobCompartmentDetails(
        compartment_id=compartment_id
    )
    return call_oci(
        "change_transcription_job_compartment",
        lambda: get_clients().speech.change_transcription_job_compartment(
            transcription_job_id, details
        ),
    )


def list_transcription_tasks(
    transcription_job_id: str,
    lifecycle_state: TaskLifecycle | None = None,
    max_items: int = Field(default=100, ge=1, le=1000),
    page: str | None = None,
) -> OperationResult:
    """List tasks in a transcription job with bounded pagination."""
    kwargs: dict[str, Any] = {"transcription_job_id": transcription_job_id}
    if lifecycle_state:
        kwargs["lifecycle_state"] = lifecycle_state
    if page:
        kwargs["page"] = page
    return list_oci(
        "list_transcription_tasks",
        get_clients().speech.list_transcription_tasks,
        kwargs,
        max_items=max_items,
    )


def get_transcription_task(
    transcription_job_id: str,
    transcription_task_id: str,
) -> OperationResult:
    """Get a task in a transcription job."""
    return call_oci(
        "get_transcription_task",
        lambda: get_clients().speech.get_transcription_task(
            transcription_job_id, transcription_task_id
        ),
    )


def cancel_transcription_task(
    transcription_job_id: str,
    transcription_task_id: str,
) -> OperationResult:
    """Cancel an unfinished task in a transcription job."""
    return call_oci(
        "cancel_transcription_task",
        lambda: get_clients().speech.cancel_transcription_task(
            transcription_job_id, transcription_task_id
        ),
    )


def wait_for_job(
    transcription_job_id: str,
    *,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> Any:
    deadline = time.monotonic() + timeout_seconds
    while True:
        response = get_clients().speech.get_transcription_job(transcription_job_id)
        state = response.data.lifecycle_state
        if state in {"SUCCEEDED", "FAILED", "CANCELED"}:
            return response
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timed out waiting for transcription job {transcription_job_id}; "
                f"last state was {state}."
            )
        time.sleep(poll_interval_seconds)


def download_job_outputs(
    transcription_job_id: str,
    output_directory: str,
    *,
    overwrite: bool,
) -> list[dict[str, Any]]:
    speech = get_clients().speech
    storage = get_clients().object_storage
    task_summaries: list[Any] = []
    page: str | None = None
    while True:
        kwargs = {"limit": 100}
        if page:
            kwargs["page"] = page
        response = speech.list_transcription_tasks(transcription_job_id, **kwargs)
        task_summaries.extend(page_items(response.data))
        page = response_header(response, "opc-next-page")
        if not page:
            break

    downloaded: list[dict[str, Any]] = []
    used_names: set[str] = set()
    for summary in task_summaries:
        task = speech.get_transcription_task(transcription_job_id, summary.id).data
        if task.lifecycle_state != "SUCCEEDED" or not task.output_location:
            continue
        location = task.output_location
        for object_name in location.object_names or []:
            filename = safe_object_filename(object_name)
            if filename in used_names:
                filename = f"{task.id}-{filename}"
            used_names.add(filename)
            relative_path = str(Path(output_directory) / filename)
            destination = safe_output_path(relative_path, overwrite=overwrite)
            object_response = storage.get_object(
                location.namespace_name,
                location.bucket_name,
                object_name,
            )
            byte_count = write_stream(object_response.data, destination)
            downloaded.append(
                {
                    "task_id": task.id,
                    "object_name": object_name,
                    "local_path": str(destination),
                    "bytes": byte_count,
                    "opc_request_id": response_header(
                        object_response, "opc-request-id"
                    ),
                }
            )
    return downloaded


def download_transcription_results(
    transcription_job_id: str,
    output_directory: str | None = None,
    overwrite: bool = False,
) -> OperationResult:
    """Download successful task outputs to a contained local directory."""
    directory = output_directory or f"transcriptions/{transcription_job_id}"
    try:
        downloaded = download_job_outputs(
            transcription_job_id, directory, overwrite=overwrite
        )
        return OperationResult(
            operation="download_transcription_results",
            data=downloaded,
            count=len(downloaded),
            notes=[] if downloaded else ["No successful task outputs were available."],
        )
    except Exception as error:
        raise_safe("download_transcription_results", error)


def transcribe_local_file(
    local_path: str,
    compartment_id: str,
    bucket_name: str,
    display_name: str,
    namespace_name: str | None = None,
    input_object_name: str | None = None,
    output_bucket_name: str | None = None,
    output_prefix: str | None = None,
    local_output_directory: str | None = None,
    model_type: str = "ORACLE",
    domain: Literal["GENERIC", "MEDICAL"] = "GENERIC",
    language_code: str = "en-US",
    diarization_enabled: bool = Field(
        default=False,
        description=(
            "Enable when the user says the audio has multiple speakers. Ask when "
            "speaker context is unknown; this tool cannot infer it from the file."
        ),
    ),
    number_of_speakers: int | None = Field(
        default=None,
        ge=2,
        le=16,
        description="Known speaker count; omit when the exact count is unknown.",
    ),
    whisper_prompt: str | None = Field(default=None, max_length=4000),
    punctuation_enabled: bool = True,
    profanity_mode: Literal["MASK", "REMOVE", "TAG"] | None = None,
    include_srt: bool = False,
    wait_for_completion: bool = True,
    timeout_seconds: int = Field(default=1200, ge=10, le=7200),
    poll_interval_seconds: int = Field(default=10, ge=2, le=60),
    overwrite_local_outputs: bool = False,
) -> OperationResult:
    """Upload a local media file, transcribe it, and optionally download results."""
    try:
        validate_transcription_options(model_type, whisper_prompt, punctuation_enabled)
        source = validate_media_input(local_path)
        clients = get_clients()
        namespace = namespace_name
        if not namespace:
            namespace_response = clients.object_storage.get_namespace(
                compartment_id=compartment_id
            )
            namespace = namespace_response.data
        object_name = input_object_name or (
            f"oci-speech-mcp/inputs/{uuid.uuid4().hex}/{source.name}"
        )
        if object_name.startswith("/") or ".." in Path(object_name).parts:
            raise ValueError("input_object_name must be a relative Object Storage name.")
        prefix = output_prefix or f"oci-speech-mcp/outputs/{uuid.uuid4().hex}/"
        details = oci.ai_speech.models.CreateTranscriptionJobDetails(
            compartment_id=compartment_id,
            display_name=display_name,
            input_location=oci.ai_speech.models.ObjectListInlineInputLocation(
                object_locations=[
                    oci.ai_speech.models.ObjectLocation(
                        namespace_name=namespace,
                        bucket_name=bucket_name,
                        object_names=[object_name],
                    )
                ]
            ),
            output_location=oci.ai_speech.models.OutputLocation(
                namespace_name=namespace,
                bucket_name=output_bucket_name or bucket_name,
                prefix=prefix,
            ),
            model_details=transcription_model(
                model_type,
                domain,
                language_code,
                diarization_enabled,
                number_of_speakers,
                whisper_prompt,
            ),
            normalization=normalization(punctuation_enabled, profanity_mode),
            additional_transcription_formats=["SRT"] if include_srt else [],
        )
        with source.open("rb") as media:
            upload_response = clients.object_storage.put_object(
                namespace,
                bucket_name,
                object_name,
                media,
                content_length=source.stat().st_size,
            )
        upload_data = {
            "namespace_name": namespace,
            "bucket_name": bucket_name,
            "object_name": object_name,
            "etag": response_header(upload_response, "etag"),
            "opc_request_id": response_header(upload_response, "opc-request-id"),
        }
        try:
            create_response = clients.speech.create_transcription_job(details)
        except Exception as create_error:
            try:
                clients.object_storage.delete_object(
                    namespace, bucket_name, object_name
                )
            except Exception as cleanup_error:
                return OperationResult(
                    operation="transcribe_local_file",
                    data={
                        "upload": upload_data,
                        "job": None,
                        "downloads": [],
                        "failure": {
                            "operation": "create_transcription_job",
                            **safe_error_details(create_error),
                        },
                        "cleanup": {
                            "attempted": True,
                            "succeeded": False,
                            "error": safe_error_details(cleanup_error),
                        },
                    },
                    status=getattr(create_error, "status", None),
                    opc_request_id=getattr(create_error, "request_id", None),
                    notes=[
                        "Transcription job creation and uploaded-input cleanup both "
                        "failed. The upload identity is returned for explicit cleanup."
                    ],
                )
            raise
        job = create_response.data
        result_data: dict[str, Any] = {
            "upload": upload_data,
            "job": to_dict(job),
            "downloads": [],
        }
        notes = [
            "The uploaded input is retained in Object Storage; manage it with your normal lifecycle policy."
        ]
        if wait_for_completion:
            completed_response = wait_for_job(
                job.id,
                timeout_seconds=timeout_seconds,
                poll_interval_seconds=poll_interval_seconds,
            )
            result_data["job"] = to_dict(completed_response.data)
            if completed_response.data.lifecycle_state == "SUCCEEDED":
                directory = local_output_directory or f"transcriptions/{job.id}"
                result_data["downloads"] = download_job_outputs(
                    job.id,
                    directory,
                    overwrite=overwrite_local_outputs,
                )
            else:
                notes.append(
                    f"The job ended in {completed_response.data.lifecycle_state}; no outputs were downloaded."
                )
        else:
            notes.append(
                "The tool returned after job creation. Use get_transcription_job and download_transcription_results."
            )
        return OperationResult(
            operation="transcribe_local_file",
            data=result_data,
            status=getattr(create_response, "status", None),
            opc_request_id=response_header(create_response, "opc-request-id"),
            notes=notes,
        )
    except Exception as error:
        raise_safe("transcribe_local_file", error)


def register_tools(mcp: FastMCP) -> None:
    for tool in (
        create_transcription_job,
        get_transcription_job,
        list_transcription_jobs,
        update_transcription_job,
        delete_transcription_job,
        cancel_transcription_job,
        change_transcription_job_compartment,
        list_transcription_tasks,
        get_transcription_task,
        cancel_transcription_task,
        download_transcription_results,
        transcribe_local_file,
    ):
        mcp.tool()(tool)
