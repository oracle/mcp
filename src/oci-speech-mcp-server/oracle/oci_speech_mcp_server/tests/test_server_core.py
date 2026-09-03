"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import errno
import stat
from types import SimpleNamespace
from unittest.mock import MagicMock

import oci
import pytest

from oracle.oci_speech_mcp_server import prompts, resources, server
from oracle.oci_speech_mcp_server.tools import transcription as transcription_tools
from oracle.oci_speech_mcp_server.utils import responses


def resp(data=None, headers=None, status=200):
    return SimpleNamespace(
        data=data,
        headers=headers or {"opc-request-id": "req", "etag": "tag"},
        status=status,
    )


def test_resources_and_prompts():
    assert "Available guides" in resources.index_guide()
    assert "credential mode" in resources.prerequisites_guide()
    assert "IAM policy" in resources.policies_guide()
    assert "2 GB" in resources.service_limits_guide()
    assert "Diarization decision" in resources.transcription_guide()
    assert "Local-file safety" in resources.local_files_guide()
    assert "Text-to-speech" in resources.text_to_speech_guide()
    assert "SSML composition" in resources.ssml_guide()
    assert "Speech customizations" in resources.customizations_guide()
    assert "Job notifications" in resources.notifications_guide()
    realtime_guide = resources.realtime_guide()
    for expected in (
        "oci-ai-speech-realtime",
        "RealtimeSpeechClientListener",
        "request_final_result",
        "call_soon_threadsafe",
        "bounded queue",
        "WHISPER",
        "should_ignore_invalid_customizations=False",
    ):
        assert expected in realtime_guide
    assert "audio.wav" in prompts.transcribe_local_audio_prompt("audio.wav")
    assert "job" in prompts.manage_transcription_job_prompt("job")
    assert "hello" in prompts.synthesize_narration_prompt("hello")
    ssml_prompt = prompts.customize_tts_with_ssml_prompt("hello", "slower")
    assert "hello" in ssml_prompt
    assert "slower" in ssml_prompt
    assert "vocabulary" in prompts.build_speech_customization_prompt("vocabulary")
    policy_prompt = prompts.plan_speech_policies_prompt("SpeechUsers", "Speech")
    assert "SpeechUsers" in policy_prompt
    assert "Speech" in policy_prompt
    assert "compartment" in prompts.setup_job_notifications_prompt("compartment")
    assert "job" in prompts.troubleshoot_speech_job_prompt("job")
    realtime_prompt = prompts.plan_realtime_integration_prompt("captions")
    assert "captions" in realtime_prompt
    assert "bounded thread-safe audio queue" in realtime_prompt
    assert "partial-versus-final" in realtime_prompt


def test_response_helpers_and_safe_errors(caplog):
    response = resp(oci.ai_speech.models.TranscriptionJob(id="job"))
    result = responses.operation_result("get", response, notes=["note"])
    assert result.data["id"] == "job"
    assert result.opc_request_id == "req"
    assert result.etag == "tag"
    assert result.notes == ["note"]
    assert responses.to_dict(None) is None
    assert (
        responses.response_header(
            SimpleNamespace(headers={"Opc-Next-Page": "next"}), "opc-next-page"
        )
        == "next"
    )
    assert responses.response_header(SimpleNamespace(headers=None), "missing") is None

    with pytest.raises(RuntimeError, match="OCI status 400"):
        responses.call_oci(
            "bad",
            lambda: (_ for _ in ()).throw(
                oci.exceptions.ServiceError(
                    400,
                    "Bad",
                    {"opc-request-id": "request"},
                    "invalid",
                )
            ),
        )
    with pytest.raises(RuntimeError, match="network"):
        responses.call_oci(
            "bad",
            lambda: (_ for _ in ()).throw(oci.exceptions.RequestException("network")),
        )
    with pytest.raises(RuntimeError, match="unexpectedly"):
        responses.call_oci(
            "bad", lambda: (_ for _ in ()).throw(TypeError("private"))
        )
    assert "Unexpected TypeError" in caplog.text
    assert "private" not in caplog.text

    with pytest.raises(RuntimeError, match=r"EACCES \(errno 13\)") as failure:
        responses.call_oci(
            "write",
            lambda: (_ for _ in ()).throw(
                PermissionError(errno.EACCES, "denied", "/sensitive/path")
            ),
        )
    assert "/sensitive/path" not in str(failure.value)


def test_pagination(mock_clients):
    first = resp(
        SimpleNamespace(
            items=[oci.ai_speech.models.TranscriptionJobSummary(id="1")]
        ),
        {"opc-next-page": "second", "opc-request-id": "one"},
    )
    second = resp(
        SimpleNamespace(
            items=[oci.ai_speech.models.TranscriptionJobSummary(id="2")]
        ),
        {"opc-request-id": "two"},
    )
    mock_clients.speech.list_transcription_jobs.side_effect = [first, second]
    result = transcription_tools.list_transcription_jobs(
        "compartment",
        lifecycle_state="SUCCEEDED",
        display_name="name",
        transcription_job_id="job",
        sort_by="displayName",
        sort_order="ASC",
        max_items=2,
        page=None,
    )
    assert result.count == 2
    assert [item["id"] for item in result.data] == ["1", "2"]
    assert mock_clients.speech.list_transcription_jobs.call_args_list[1].kwargs["page"] == "second"

    mock_clients.speech.list_transcription_jobs.side_effect = None
    mock_clients.speech.list_transcription_jobs.return_value = first
    transcription_tools.list_transcription_jobs("c", max_items=1)
    assert mock_clients.speech.list_transcription_jobs.call_args.kwargs["sort_by"] == "timeCreated"

    mock_clients.speech.list_transcription_jobs.side_effect = ValueError("bad list")
    with pytest.raises(RuntimeError, match="bad list"):
        transcription_tools.list_transcription_jobs("c", max_items=1)


def test_transcription_crud_and_tasks(mock_clients):
    job = oci.ai_speech.models.TranscriptionJob(id="job", lifecycle_state="ACCEPTED")
    mock_clients.speech.create_transcription_job.return_value = resp(job)
    created = transcription_tools.create_transcription_job(
        "compartment",
        "display",
        "namespace",
        "bucket",
        ["audio.wav"],
        output_namespace_name=None,
        output_bucket_name=None,
        output_prefix="results/",
        description="description",
        model_type="ORACLE",
        domain="GENERIC",
        language_code="en-US",
        diarization_enabled=True,
        number_of_speakers=2,
        whisper_prompt=None,
        punctuation_enabled=True,
        profanity_mode="MASK",
        include_srt=True,
        freeform_tags={"team": "speech"},
    )
    assert created.data["id"] == "job"
    details = mock_clients.speech.create_transcription_job.call_args.args[0]
    assert details.output_location.bucket_name == "bucket"
    assert details.additional_transcription_formats == ["SRT"]
    assert details.normalization.filters[0].mode == "MASK"
    assert details.model_details.transcription_settings.diarization.number_of_speakers == 2

    with pytest.raises(ValueError, match="requires diarization"):
        transcription_tools.transcription_model(
            "ORACLE", "GENERIC", "en-US", False, 2, None
        )
    whisper = transcription_tools.transcription_model(
        "WHISPER", "GENERIC", "auto", False, None, "domain words"
    )
    assert whisper.transcription_settings.additional_settings["whisperPrompt"] == "domain words"
    assert transcription_tools.normalization(False, None).filters == []

    mock_clients.speech.create_transcription_job.reset_mock()
    with pytest.raises(ValueError, match="whisper_prompt.*WHISPER"):
        transcription_tools.create_transcription_job(
            "compartment",
            "display",
            "namespace",
            "bucket",
            ["audio.wav"],
            model_type="ORACLE",
            whisper_prompt="domain words",
        )
    with pytest.raises(ValueError, match="punctuation_enabled.*WHISPER"):
        transcription_tools.create_transcription_job(
            "compartment",
            "display",
            "namespace",
            "bucket",
            ["audio.wav"],
            model_type="WHISPER",
            punctuation_enabled=False,
        )
    transcription_tools.validate_transcription_options("FUTURE_MODEL", None, False)
    mock_clients.speech.create_transcription_job.assert_not_called()

    mock_clients.speech.get_transcription_job.return_value = resp(job)
    assert transcription_tools.get_transcription_job("job").data["id"] == "job"

    mock_clients.speech.update_transcription_job.return_value = resp(job)
    assert (
        transcription_tools.update_transcription_job("job", display_name="new").data[
            "id"
        ]
        == "job"
    )
    with pytest.raises(ValueError, match="at least one"):
        transcription_tools.update_transcription_job("job")

    for function, method, args in (
        (
            transcription_tools.delete_transcription_job,
            "delete_transcription_job",
            ("job",),
        ),
        (
            transcription_tools.cancel_transcription_job,
            "cancel_transcription_job",
            ("job",),
        ),
        (
            transcription_tools.change_transcription_job_compartment,
            "change_transcription_job_compartment",
            ("job", "new-compartment"),
        ),
        (
            transcription_tools.get_transcription_task,
            "get_transcription_task",
            ("job", "task"),
        ),
        (
            transcription_tools.cancel_transcription_task,
            "cancel_transcription_task",
            ("job", "task"),
        ),
    ):
        getattr(mock_clients.speech, method).return_value = resp(None, status=202)
        result = function(*args)
        assert result.status == 202

    task = oci.ai_speech.models.TranscriptionTaskSummary(id="task")
    mock_clients.speech.list_transcription_tasks.return_value = resp(
        SimpleNamespace(items=[task])
    )
    listed = transcription_tools.list_transcription_tasks(
        "job", lifecycle_state="SUCCEEDED", max_items=10, page="page"
    )
    assert listed.data[0]["id"] == "task"


def test_update_and_delete_pass_if_match(mock_clients):
    mock_clients.speech.update_transcription_job.return_value = resp(None)
    transcription_tools.update_transcription_job(
        "job", description="new", if_match="etag"
    )
    assert mock_clients.speech.update_transcription_job.call_args.kwargs["if_match"] == "etag"
    mock_clients.speech.delete_transcription_job.return_value = resp(None)
    transcription_tools.delete_transcription_job("job", if_match="etag")
    assert mock_clients.speech.delete_transcription_job.call_args.kwargs["if_match"] == "etag"


def test_stream_writer_variants(tmp_path):
    tmp_path.chmod(0o755)
    raw_path = tmp_path / "raw"
    data = SimpleNamespace(
        raw=SimpleNamespace(stream=lambda size, decode_content: iter([b"one", b"", b"two"]))
    )
    assert responses.write_stream(data, raw_path) == 6
    assert raw_path.read_bytes() == b"onetwo"
    assert stat.S_IMODE(raw_path.stat().st_mode) == 0o600

    iter_path = tmp_path / "iter"
    data = SimpleNamespace(iter_content=lambda chunk_size: iter([b"three"]))
    assert responses.write_stream(data, iter_path) == 5
    byte_path = tmp_path / "bytes"
    assert responses.write_stream(b"four", byte_path) == 4
    with pytest.raises(ValueError, match="unsupported"):
        responses.write_stream(object(), tmp_path / "bad")

    interrupted_path = tmp_path / "interrupted"

    def interrupted_stream():
        yield b"partial"
        raise OSError(errno.ENOSPC, "disk full")

    interrupted = SimpleNamespace(
        raw=SimpleNamespace(
            stream=lambda size, decode_content: interrupted_stream()
        )
    )
    with pytest.raises(OSError, match="disk full"):
        responses.write_stream(interrupted, interrupted_path)
    assert not interrupted_path.exists()
    assert not list(tmp_path.glob(f".{interrupted_path.name}.*.tmp"))


def test_main(monkeypatch):
    run = MagicMock()
    monkeypatch.setattr(server.mcp, "run", run)
    server.main()
    run.assert_called_once_with()
