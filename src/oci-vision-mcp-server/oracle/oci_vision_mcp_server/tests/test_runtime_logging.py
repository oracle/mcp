"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import io
import sys

from oracle.oci_vision_mcp_server.observability import stderr as stderr_logging
from oracle.oci_vision_mcp_server.observability.stderr import _StderrTee, configure_stderr_log


def test_configure_stderr_log_mirrors_stderr_and_keeps_fileno(monkeypatch, tmp_path) -> None:
    original_stderr = sys.stderr

    try:
        log_path = configure_stderr_log(str(tmp_path / "logs"))

        print("diagnostic message", file=sys.stderr)
        sys.stderr.flush()

        assert log_path.read_text(encoding="utf-8").strip().endswith("diagnostic message")
        assert sys.stderr.fileno() == original_stderr.fileno()
    finally:
        monkeypatch.setattr(sys, "stderr", original_stderr)


def test_stderr_tee_delegates_tty_encoding_and_flush() -> None:
    primary = io.StringIO()
    secondary = io.StringIO()
    tee = _StderrTee(primary, secondary)

    assert tee.write("hello") == 5
    tee.flush()
    assert primary.getvalue() == "hello"
    assert secondary.getvalue() == "hello"
    assert tee.isatty() is False
    assert tee.encoding is None


def test_configure_stderr_log_is_idempotent(monkeypatch, tmp_path) -> None:
    original_stderr = sys.stderr
    first_log_path = configure_stderr_log(str(tmp_path / "logs"))

    try:
        second_log_path = configure_stderr_log(str(tmp_path / "logs"))
        assert second_log_path == first_log_path
        assert sys.stderr is not original_stderr
    finally:
        monkeypatch.setattr(sys, "stderr", original_stderr)


def test_configure_stderr_log_ignores_chmod_errors(monkeypatch, tmp_path) -> None:
    original_stderr = sys.stderr

    def fail_chmod(*_args, **_kwargs):
        raise OSError("chmod denied")

    try:
        monkeypatch.setattr(stderr_logging.Path, "chmod", fail_chmod)
        log_path = configure_stderr_log(str(tmp_path / "logs"))
        print("still logs", file=sys.stderr)
        sys.stderr.flush()
        assert log_path.read_text(encoding="utf-8").strip().endswith("still logs")
    finally:
        monkeypatch.setattr(sys, "stderr", original_stderr)
