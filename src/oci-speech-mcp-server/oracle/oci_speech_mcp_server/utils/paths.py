"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
import re
from pathlib import Path

MAX_MEDIA_BYTES: int = 2 * 1024 * 1024 * 1024
SUPPORTED_MEDIA_SUFFIXES = {
    ".aac",
    ".ac3",
    ".amr",
    ".au",
    ".flac",
    ".m4a",
    ".mkv",
    ".mp3",
    ".mp4",
    ".oga",
    ".ogg",
    ".opus",
    ".wav",
    ".webm",
}
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _sensitive_roots() -> tuple[Path, ...]:
    home = Path.home().resolve()
    return (
        (home / ".oci").resolve(),
        (home / ".ssh").resolve(),
        Path("/etc").resolve(),
        Path("/run/secrets").resolve(),
        Path("/var/run/secrets").resolve(),
    )


def validate_media_input(path_value: str) -> Path:
    root_value = os.getenv("OCI_SPEECH_INPUT_ROOT")
    if not root_value:
        raise ValueError(
            "Local-file transcription requires OCI_SPEECH_INPUT_ROOT to be configured."
        )
    root = Path(root_value).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("OCI_SPEECH_INPUT_ROOT must resolve to a directory.")
    path = Path(path_value).expanduser().resolve(strict=True)
    if not _is_within(path, root):
        raise ValueError("The input file must be inside OCI_SPEECH_INPUT_ROOT.")
    if any(_is_within(path, sensitive) for sensitive in _sensitive_roots()):
        raise ValueError("Files in credential or operating-system secret locations are blocked.")
    if not path.is_file():
        raise ValueError("The input path must be a regular file.")
    if path.suffix.lower() not in SUPPORTED_MEDIA_SUFFIXES:
        raise ValueError("The input file type is not supported by OCI Speech.")
    if path.stat().st_size > MAX_MEDIA_BYTES:
        raise ValueError("The input file exceeds OCI Speech's 2 GiB file limit.")
    return path


def output_root() -> Path:
    configured = os.getenv("OCI_SPEECH_OUTPUT_ROOT")
    root = (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".oci-speech-mcp" / "outputs"
    ).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root


def safe_output_path(relative_name: str, *, overwrite: bool = False) -> Path:
    candidate_value = Path(relative_name)
    if candidate_value.is_absolute():
        raise ValueError("Output paths must be relative to OCI_SPEECH_OUTPUT_ROOT.")
    root = output_root()
    candidate = (root / candidate_value).resolve()
    if not _is_within(candidate, root):
        raise ValueError("The output path must remain inside OCI_SPEECH_OUTPUT_ROOT.")
    candidate.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if candidate.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {candidate.name}. Set overwrite=true to replace it."
        )
    return candidate


def safe_object_filename(object_name: str, fallback: str = "result.json") -> str:
    raw = Path(object_name).name or fallback
    cleaned = _SAFE_NAME.sub("_", raw).strip("._")
    return cleaned or fallback
