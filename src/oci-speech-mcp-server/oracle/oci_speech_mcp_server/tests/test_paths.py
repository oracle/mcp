"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from pathlib import Path

import pytest

from oracle.oci_speech_mcp_server.utils import paths


def test_media_root_is_required(monkeypatch):
    monkeypatch.delenv("OCI_SPEECH_INPUT_ROOT", raising=False)
    with pytest.raises(ValueError, match="requires OCI_SPEECH_INPUT_ROOT"):
        paths.validate_media_input("audio.wav")


def test_media_input_validation(monkeypatch, tmp_path):
    root = tmp_path / "media"
    root.mkdir()
    audio = root / "voice.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(root))
    assert paths.validate_media_input(str(audio)) == audio.resolve()

    outside = tmp_path / "outside.wav"
    outside.write_bytes(b"audio")
    with pytest.raises(ValueError, match="inside"):
        paths.validate_media_input(str(outside))

    unsupported = root / "secret.txt"
    unsupported.write_text("secret")
    with pytest.raises(ValueError, match="not supported"):
        paths.validate_media_input(str(unsupported))

    directory = root / "folder.wav"
    directory.mkdir()
    with pytest.raises(ValueError, match="regular file"):
        paths.validate_media_input(str(directory))

    with pytest.raises(FileNotFoundError):
        paths.validate_media_input(str(root / "missing.wav"))

    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(audio))
    with pytest.raises(ValueError, match="must resolve to a directory"):
        paths.validate_media_input(str(audio))


def test_media_input_blocks_sensitive_location(monkeypatch, tmp_path):
    home = tmp_path / "home"
    secrets = home / ".oci"
    secrets.mkdir(parents=True)
    audio = secrets / "credential.wav"
    audio.write_bytes(b"no")
    monkeypatch.setattr(paths.Path, "home", lambda: home)
    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(home))
    with pytest.raises(ValueError, match="secret locations"):
        paths.validate_media_input(str(audio))


def test_media_size_limit(monkeypatch, tmp_path):
    audio = tmp_path / "large.wav"
    audio.write_bytes(b"x")
    monkeypatch.setenv("OCI_SPEECH_INPUT_ROOT", str(tmp_path))
    monkeypatch.setattr(paths, "MAX_MEDIA_BYTES", 0)
    with pytest.raises(ValueError, match="2 GiB"):
        paths.validate_media_input(str(audio))


def test_safe_output_paths(monkeypatch, tmp_path):
    output = tmp_path / "output"
    monkeypatch.setenv("OCI_SPEECH_OUTPUT_ROOT", str(output))
    destination = paths.safe_output_path("nested/result.json")
    assert destination == output / "nested/result.json"
    destination.write_text("existing")
    with pytest.raises(FileExistsError, match="overwrite=true"):
        paths.safe_output_path("nested/result.json")
    assert paths.safe_output_path("nested/result.json", overwrite=True) == destination
    with pytest.raises(ValueError, match="relative"):
        paths.safe_output_path(str(tmp_path / "absolute.json"))
    with pytest.raises(ValueError, match="inside"):
        paths.safe_output_path("../escape.json")


def test_output_default_and_safe_names(monkeypatch, tmp_path):
    monkeypatch.delenv("OCI_SPEECH_OUTPUT_ROOT", raising=False)
    monkeypatch.setattr(paths.Path, "home", lambda: tmp_path)
    assert paths.output_root() == (tmp_path / ".oci-speech-mcp/outputs").resolve()
    assert paths.safe_object_filename("folder/My result?.json") == "My_result_.json"
    assert paths.safe_object_filename("...") == "result.json"
    assert paths._is_within(Path("/tmp/a"), Path("/tmp"))
    assert not paths._is_within(Path("/other/a"), Path("/tmp"))
