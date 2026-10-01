"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from pathlib import Path
from types import SimpleNamespace

import oci
import pytest

from oracle.oci_speech_mcp_server.tools import (
    customization as customization_tools,
    notifications as extras_tools,
    transcription as transcription_tools,
    tts as tts_tools,
)
from oracle.oci_speech_mcp_server.models import (
    CustomizationDatasetInput,
    EntityInput,
    EntityListInput,
    InlineCustomizationInput,
    ObjectStorageCustomizationInput,
)


def resp(data=None, headers=None, status=200):
    return SimpleNamespace(
        data=data,
        headers=headers or {"opc-request-id": "req", "etag": "tag"},
        status=status,
    )


def stream_data(*chunks):
    return SimpleNamespace(
        raw=SimpleNamespace(
            stream=lambda size, decode_content: iter(chunks)
        )
    )


def test_wait_for_job_success_and_timeout(mock_clients, monkeypatch):
    accepted = oci.ai_speech.models.TranscriptionJob(
        id="job", lifecycle_state="IN_PROGRESS"
    )
    succeeded = oci.ai_speech.models.TranscriptionJob(
        id="job", lifecycle_state="SUCCEEDED"
    )
    mock_clients.speech.get_transcription_job.side_effect = [
        resp(accepted),
        resp(succeeded),
    ]
    monkeypatch.setattr(transcription_tools.time, "sleep", lambda _: None)
    assert transcription_tools.wait_for_job(
        "job", timeout_seconds=10, poll_interval_seconds=2
    ).data.lifecycle_state == "SUCCEEDED"

    mock_clients.speech.get_transcription_job.side_effect = None
    mock_clients.speech.get_transcription_job.return_value = resp(accepted)
    values = iter([0, 20])
    monkeypatch.setattr(transcription_tools.time, "monotonic", lambda: next(values))
    with pytest.raises(TimeoutError, match="last state"):
        transcription_tools.wait_for_job(
            "job", timeout_seconds=10, poll_interval_seconds=2
        )


def test_download_transcription_outputs(mock_clients, monkeypatch, tmp_path):
    monkeypatch.setenv("OCI_SPEECH_OUTPUT_ROOT", str(tmp_path))
    summaries = SimpleNamespace(
        items=[
            oci.ai_speech.models.TranscriptionTaskSummary(id="task-1"),
            oci.ai_speech.models.TranscriptionTaskSummary(id="task-2"),
        ]
    )
    mock_clients.speech.list_transcription_tasks.return_value = resp(summaries)
    location = oci.ai_speech.models.ObjectLocation(
        namespace_name="namespace",
        bucket_name="bucket",
        object_names=["folder/result.json", "other/result.json"],
    )
    good = oci.ai_speech.models.TranscriptionTask(
        id="task-1", lifecycle_state="SUCCEEDED", output_location=location
    )
    failed = oci.ai_speech.models.TranscriptionTask(
        id="task-2", lifecycle_state="FAILED"
    )
    mock_clients.speech.get_transcription_task.side_effect = [resp(good), resp(failed)]
    mock_clients.object_storage.get_object.side_effect = [
        resp(stream_data(b"first")),
        resp(stream_data(b"second")),
    ]
    result = transcription_tools.download_transcription_results(
        "job", "results", overwrite=False
    )
    assert result.count == 2
    assert Path(result.data[0]["local_path"]).read_bytes() == b"first"
    assert Path(result.data[1]["local_path"]).name == "task-1-result.json"

    mock_clients.speech.list_transcription_tasks.return_value = resp(
        SimpleNamespace(items=[])
    )
    empty = transcription_tools.download_transcription_results("job", "empty")
    assert empty.count == 0
    assert empty.notes


def test_local_transcription_end_to_end(mock_clients, monkeypatch, tmp_path):
    media_root = tmp_path / "media"
    output_root = tmp_path / "output"
    media_root.mkdir()
    audio = media_root / "audio.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(media_root))
    monkeypatch.setenv("OCI_SPEECH_OUTPUT_ROOT", str(output_root))

    mock_clients.object_storage.get_namespace.return_value = resp("namespace")
    mock_clients.object_storage.put_object.return_value = resp(None)
    created_job = oci.ai_speech.models.TranscriptionJob(
        id="job", lifecycle_state="ACCEPTED"
    )
    completed_job = oci.ai_speech.models.TranscriptionJob(
        id="job", lifecycle_state="SUCCEEDED"
    )
    mock_clients.speech.create_transcription_job.return_value = resp(created_job, status=202)
    monkeypatch.setattr(
        transcription_tools,
        "wait_for_job",
        lambda *args, **kwargs: resp(completed_job),
    )
    monkeypatch.setattr(
        transcription_tools,
        "download_job_outputs",
        lambda *args, **kwargs: [{"local_path": "/safe/result.json"}],
    )

    result = transcription_tools.transcribe_local_file(
        str(audio),
        "compartment",
        "bucket",
        "display",
        namespace_name=None,
        input_object_name=None,
        output_bucket_name=None,
        output_prefix=None,
        local_output_directory=None,
        model_type="ORACLE",
        domain="GENERIC",
        language_code="en-US",
        diarization_enabled=False,
        number_of_speakers=None,
        whisper_prompt=None,
        punctuation_enabled=True,
        profanity_mode=None,
        include_srt=False,
        wait_for_completion=True,
        timeout_seconds=60,
        poll_interval_seconds=2,
        overwrite_local_outputs=False,
    )
    assert result.data["job"]["lifecycle_state"] == "SUCCEEDED"
    assert result.data["downloads"][0]["local_path"] == "/safe/result.json"
    assert "retained" in result.notes[0]
    assert mock_clients.object_storage.put_object.call_args.kwargs["content_length"] == 5


def test_local_transcription_async_and_failed(mock_clients, monkeypatch, tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(tmp_path))
    mock_clients.object_storage.put_object.return_value = resp(None)
    created = oci.ai_speech.models.TranscriptionJob(id="job", lifecycle_state="ACCEPTED")
    mock_clients.speech.create_transcription_job.return_value = resp(created)

    async_result = transcription_tools.transcribe_local_file(
        str(audio),
        "c",
        "b",
        "display",
        namespace_name="ns",
        input_object_name="inputs/audio.wav",
        wait_for_completion=False,
        number_of_speakers=None,
        whisper_prompt=None,
        timeout_seconds=60,
        poll_interval_seconds=2,
    )
    assert "returned after job creation" in async_result.notes[-1]

    failed = oci.ai_speech.models.TranscriptionJob(id="job", lifecycle_state="FAILED")
    monkeypatch.setattr(
        transcription_tools,
        "wait_for_job",
        lambda *args, **kwargs: resp(failed),
    )
    failed_result = transcription_tools.transcribe_local_file(
        str(audio),
        "c",
        "b",
        "display",
        namespace_name="ns",
        input_object_name="inputs/audio-2.wav",
        wait_for_completion=True,
        number_of_speakers=None,
        whisper_prompt=None,
        timeout_seconds=60,
        poll_interval_seconds=2,
    )
    assert "FAILED" in failed_result.notes[-1]

    with pytest.raises(RuntimeError, match="relative Object Storage"):
        transcription_tools.transcribe_local_file(
            str(audio),
            "c",
            "b",
            "display",
            namespace_name="ns",
            input_object_name="../escape.wav",
            wait_for_completion=False,
            number_of_speakers=None,
            whisper_prompt=None,
            timeout_seconds=60,
            poll_interval_seconds=2,
        )


def test_local_transcription_cleans_upload_after_create_failure(
    mock_clients, monkeypatch, tmp_path
):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(tmp_path))
    mock_clients.object_storage.put_object.return_value = resp(None)
    mock_clients.object_storage.delete_object.return_value = resp(None, status=204)
    mock_clients.speech.create_transcription_job.side_effect = ValueError(
        "job creation failed"
    )

    with pytest.raises(RuntimeError, match="job creation failed"):
        transcription_tools.transcribe_local_file(
            str(audio),
            "compartment",
            "bucket",
            "display",
            namespace_name="namespace",
            input_object_name="inputs/audio.wav",
            number_of_speakers=None,
            whisper_prompt=None,
            punctuation_enabled=True,
            wait_for_completion=False,
        )

    mock_clients.object_storage.delete_object.assert_called_once_with(
        "namespace", "bucket", "inputs/audio.wav"
    )


def test_local_transcription_surfaces_upload_when_cleanup_fails(
    mock_clients, monkeypatch, tmp_path
):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(tmp_path))
    mock_clients.object_storage.put_object.return_value = resp(None)
    mock_clients.speech.create_transcription_job.side_effect = ValueError(
        "job creation failed"
    )
    mock_clients.object_storage.delete_object.side_effect = oci.exceptions.ServiceError(
        500,
        "InternalError",
        {"opc-request-id": "cleanup-request"},
        "cleanup failed",
    )

    result = transcription_tools.transcribe_local_file(
        str(audio),
        "compartment",
        "bucket",
        "display",
        namespace_name="namespace",
        input_object_name="inputs/audio.wav",
        number_of_speakers=None,
        whisper_prompt=None,
        punctuation_enabled=True,
        wait_for_completion=False,
    )

    assert result.data["upload"] == {
        "namespace_name": "namespace",
        "bucket_name": "bucket",
        "object_name": "inputs/audio.wav",
        "etag": "tag",
        "opc_request_id": "req",
    }
    assert result.data["failure"] == {
        "operation": "create_transcription_job",
        "type": "ValueError",
    }
    assert result.data["cleanup"]["succeeded"] is False
    assert result.data["cleanup"]["error"]["request_id"] == "cleanup-request"
    assert "explicit cleanup" in result.notes[0]


def test_list_voices_and_synthesis(mock_clients, monkeypatch, tmp_path):
    monkeypatch.setenv("OCI_SPEECH_OUTPUT_ROOT", str(tmp_path))
    voice = oci.ai_speech.models.VoiceSummary(voice_id="voice")
    mock_clients.speech_tts.list_voices.return_value = resp(
        SimpleNamespace(items=[voice])
    )
    listed = tts_tools.list_voices(
        "compartment",
        model_name="TTS_1_STANDARD",
        language_code="en-US",
        display_name="Amy",
        max_items=10,
    )
    assert listed.data[0]["voice_id"] == "voice"
    assert "us-phoenix-1" in listed.notes[0]
    mock_clients.speech_tts.list_voices.assert_called_once_with(
        compartment_id="compartment",
        model_name="TTS_1_STANDARD",
        language_code="en-US",
        display_name="Amy",
    )

    mock_clients.speech_tts.synthesize_speech.return_value = resp(
        stream_data(b"audio"), status=200
    )
    standard = tts_tools.synthesize_speech(
        "hello",
        "compartment",
        "voice",
        "standard.mp3",
        model_name="TTS_1_STANDARD",
        language_code=None,
        text_type="TEXT",
        output_format="MP3",
        sample_rate_in_hz=24000,
        speech_mark_types=None,
        overwrite=False,
    )
    assert Path(standard.data["local_path"]).read_bytes() == b"audio"

    mock_clients.speech_tts.synthesize_speech.return_value = resp(stream_data(b"marks"))
    natural = tts_tools.synthesize_speech(
        "<speak>Hello</speak>",
        "compartment",
        "voice",
        "marks.json",
        model_name="TTS_2_NATURAL",
        language_code="en-US",
        text_type="SSML",
        output_format="JSON",
        sample_rate_in_hz=None,
        speech_mark_types=["WORD"],
        overwrite=False,
    )
    assert natural.data["output_format"] == "JSON"

    with pytest.raises(RuntimeError, match="only accepted"):
        tts_tools.synthesize_speech(
            "hello", "c", "v", "bad.mp3", language_code="en-US"
        )
    with pytest.raises(RuntimeError, match="require output_format"):
        tts_tools.synthesize_speech(
            "hello", "c", "v", "bad.mp3", speech_mark_types=["WORD"]
        )


def test_ssml_validation_and_model_constraints(mock_clients, monkeypatch, tmp_path):
    monkeypatch.setenv("OCI_SPEECH_OUTPUT_ROOT", str(tmp_path))
    assert "say-as" in tts_tools.validate_ssml(
        '<speak>Order <say-as interpret-as="digits">42</say-as></speak>'
    )
    with pytest.raises(ValueError, match="well-formed"):
        tts_tools.validate_ssml("<speak>broken")
    with pytest.raises(ValueError, match="root"):
        tts_tools.validate_ssml("<p>Not wrapped</p>")
    with pytest.raises(ValueError, match="Unsupported"):
        tts_tools.validate_ssml("<speak><emphasis>no</emphasis></speak>")

    with pytest.raises(RuntimeError, match="only for en-US"):
        tts_tools.synthesize_speech(
            "<speak>Bonjour</speak>",
            "c",
            "v",
            "bad.mp3",
            model_name="TTS_2_NATURAL",
            language_code="fr-FR",
            text_type="SSML",
        )
    with pytest.raises(RuntimeError, match="only by standard"):
        tts_tools.synthesize_speech(
            '<speak><prosody rate="slow">Hello</prosody></speak>',
            "c",
            "v",
            "bad.mp3",
            model_name="TTS_2_NATURAL",
            language_code="en-US",
            text_type="SSML",
        )


def inline_dataset(with_audio=False):
    return CustomizationDatasetInput(
        inline=InlineCustomizationInput(
            entity_lists=[
                EntityListInput(
                    alias="products",
                    entity_type="product",
                    entities=[
                        EntityInput(
                            value="MySQL",
                            sounds_like=["my sequel"],
                            audio_object_names=["mysql.wav"] if with_audio else [],
                            weight=10,
                        )
                    ],
                )
            ],
            reference_examples=["Use <product> today"],
        )
    )


def test_customization_dataset_mapping():
    mapped = customization_tools.customization_dataset(inline_dataset())
    assert mapped.entity_list[0].entities[0].pronunciations[0].sounds_like == "my sequel"
    with pytest.raises(ValueError, match="Audio pronunciations require"):
        customization_tools.customization_dataset(inline_dataset(with_audio=True))
    mapped_audio = customization_tools.customization_dataset(
        inline_dataset(with_audio=True),
        pronunciation_namespace_name="ns",
        pronunciation_bucket_name="bucket",
    )
    assert mapped_audio.entity_list[0].entities[0].pronunciations[-1].audio.object_names == [
        "mysql.wav"
    ]

    storage = CustomizationDatasetInput(
        object_storage=ObjectStorageCustomizationInput(
            entity_type="product",
            namespace_name="ns",
            bucket_name="bucket",
            object_names=["dataset.json"],
        )
    )
    assert (
        customization_tools.customization_dataset(storage).location_details.bucket_name
        == "bucket"
    )

    reused = CustomizationDatasetInput(
        inline=InlineCustomizationInput(
            entity_lists=[
                EntityListInput(
                    entity_type="product",
                    customization_id="ocid1.aispeechcustomization.example",
                )
            ],
            reference_examples=["Use <PRODUCT> today"],
        )
    )
    reused_mapping = customization_tools.customization_dataset(reused)
    assert (
        reused_mapping.entity_list[0].id
        == "ocid1.aispeechcustomization.example"
    )
    assert reused_mapping.entity_list[0].entities is None


def test_customization_crud(mock_clients):
    customization = oci.ai_speech.models.Customization(
        id="customization", lifecycle_state="CREATING"
    )
    mock_clients.speech.create_customization.return_value = resp(customization)
    created = customization_tools.create_customization(
        "compartment",
        "alias",
        "display",
        inline_dataset(),
        description="description",
        domain="GENERIC",
        language_code="en-US",
        freeform_tags={"team": "speech"},
    )
    assert created.data["id"] == "customization"

    mock_clients.speech.get_customization.return_value = resp(customization)
    assert (
        customization_tools.get_customization("customization").data["id"]
        == "customization"
    )

    summary = oci.ai_speech.models.CustomizationSummary(id="customization")
    mock_clients.speech.list_customizations.return_value = resp(
        SimpleNamespace(items=[summary])
    )
    listed = customization_tools.list_customizations(
        "compartment",
        lifecycle_state="ACTIVE",
        display_name="display",
        customization_id="customization",
        sort_by="displayName",
        sort_order="ASC",
        max_items=10,
        page=None,
    )
    assert listed.count == 1

    mock_clients.speech.update_customization.return_value = resp(customization)
    updated = customization_tools.update_customization(
        "customization",
        alias="new",
        dataset=inline_dataset(),
        domain="GENERIC",
        language_code="en-US",
        if_match="etag",
    )
    assert updated.data["id"] == "customization"
    assert mock_clients.speech.update_customization.call_args.kwargs["if_match"] == "etag"
    with pytest.raises(ValueError, match="at least one"):
        customization_tools.update_customization("customization")
    with pytest.raises(ValueError, match="both domain"):
        customization_tools.update_customization("customization", domain="GENERIC")

    mock_clients.speech.delete_customization.return_value = resp(None, status=204)
    assert (
        customization_tools.delete_customization(
            "customization", if_match="etag"
        ).status
        == 204
    )
    mock_clients.speech.change_customization_compartment.return_value = resp(None, status=202)
    assert (
        customization_tools.change_customization_compartment(
            "customization", "new"
        ).status
        == 202
    )


def test_notification_setup(mock_clients):
    topic = oci.ons.models.NotificationTopic(topic_id="topic")
    subscription = oci.ons.models.Subscription(id="subscription")
    rule = oci.events.models.Rule(id="rule")
    mock_clients.notifications.create_topic.return_value = resp(topic)
    mock_clients.subscriptions.create_subscription.return_value = resp(subscription)
    mock_clients.events.create_rule.return_value = resp(rule, status=201)

    result = extras_tools.setup_transcription_notifications(
        "compartment",
        "Speech completed",
        topic_name="speech-topic",
        subscription_protocol="EMAIL",
        subscription_endpoint="person@example.com",
        transcription_job_id="job",
    )
    assert result.data["topic"]["topic_id"] == "topic"
    assert result.data["rule"]["id"] == "rule"
    assert any("PENDING" in note for note in result.notes)
    condition = mock_clients.events.create_rule.call_args.args[0].condition
    assert '"resourceId":"job"' in condition

    mock_clients.events.create_rule.reset_mock()
    extras_tools.setup_transcription_notifications(
        "compartment",
        "All Speech jobs",
        topic_id="topic",
        event_types=["com.oraclecloud.aiservicespeech.createtranscriptionjob"],
    )
    assert '"data"' not in mock_clients.events.create_rule.call_args.args[0].condition

    with pytest.raises(ValueError, match="exactly one"):
        extras_tools.setup_transcription_notifications("c", "r")
    with pytest.raises(ValueError, match="provided together"):
        extras_tools.setup_transcription_notifications(
            "c", "r", topic_id="topic", subscription_protocol="EMAIL"
        )
    with pytest.raises(ValueError, match="must not be empty"):
        extras_tools.setup_transcription_notifications(
            "c", "r", topic_id="topic", event_types=[]
        )


def test_notification_partial_failure(mock_clients, caplog):
    topic = oci.ons.models.NotificationTopic(topic_id="topic")
    subscription = oci.ons.models.Subscription(id="subscription")
    mock_clients.notifications.create_topic.return_value = resp(topic)
    mock_clients.subscriptions.create_subscription.return_value = resp(subscription)
    mock_clients.events.create_rule.side_effect = ValueError("rule failed")
    result = extras_tools.setup_transcription_notifications(
        "c",
        "r",
        topic_name="new",
        subscription_protocol="EMAIL",
        subscription_endpoint="person@example.com",
    )
    assert result.data["topic"]["topic_id"] == "topic"
    assert result.data["subscription"]["id"] == "subscription"
    assert result.data["failure"] == {
        "operation": "create_rule",
        "type": "ValueError",
    }
    assert "identifiers are returned" in result.notes[-1]
    assert "stopped after creating" in caplog.text
