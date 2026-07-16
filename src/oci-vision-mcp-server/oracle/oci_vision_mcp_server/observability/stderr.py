"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO


class _StderrTee:
    def __init__(self, primary: TextIO, secondary: TextIO) -> None:
        self._primary = primary
        self._secondary = secondary

    def write(self, text: str) -> int:
        self._primary.write(text)
        self._secondary.write(text)
        return len(text)

    def flush(self) -> None:
        self._primary.flush()
        self._secondary.flush()

    def isatty(self) -> bool:
        return self._primary.isatty()

    def fileno(self) -> int:
        return self._primary.fileno()

    @property
    def encoding(self) -> str | None:
        return self._primary.encoding


def configure_stderr_log(log_dir: str) -> Path:
    """Mirror stderr to a private log file without touching stdout."""
    directory = Path(log_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    try:
        directory.chmod(0o700)
    except OSError:
        pass

    log_path = directory / "oci-vision-mcp-server.log"
    if isinstance(sys.stderr, _StderrTee):
        return log_path

    log_file = log_path.open("a", encoding="utf-8", buffering=1)
    try:
        log_path.chmod(0o600)
    except OSError:
        pass

    # MCP stdio uses stdout for protocol messages; diagnostics must stay on stderr.
    sys.stderr = _StderrTee(sys.stderr, log_file)  # type: ignore[assignment]
    return log_path
