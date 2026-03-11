"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import hashlib
from pathlib import Path

import pytest

from oracle.python_mcp_server import sandbox


def test_verify_wasm_checksum_accepts_expected_hash(tmp_path, monkeypatch):
    wasm_path = tmp_path / "python.wasm"
    wasm_path.write_bytes(b"expected wasm contents")
    monkeypatch.setattr(
        sandbox,
        "EXPECTED_WASM_SHA256",
        hashlib.sha256(wasm_path.read_bytes()).hexdigest(),
    )

    sandbox._verify_wasm_checksum(wasm_path)


def test_verify_wasm_checksum_rejects_unexpected_hash(tmp_path, monkeypatch):
    wasm_path = tmp_path / "python.wasm"
    wasm_path.write_bytes(b"unexpected wasm contents")
    monkeypatch.setattr(sandbox, "EXPECTED_WASM_SHA256", "0" * 64)

    with pytest.raises(ValueError, match="checksum mismatch"):
        sandbox._verify_wasm_checksum(wasm_path)


def test_get_wasm_path_rejects_cached_runtime_with_bad_checksum(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"
    wasm_path = cache_dir / sandbox.WASM_FILENAME
    lib_dir = cache_dir / sandbox.LIB_DIR_NAME
    lib_dir.mkdir(parents=True)
    (lib_dir / "python3.13").mkdir()
    wasm_path.write_bytes(b"cached wasm contents")

    monkeypatch.setattr(sandbox, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(sandbox, "EXPECTED_WASM_SHA256", "f" * 64)

    with pytest.raises(ValueError, match="checksum mismatch"):
        sandbox.get_wasm_path()


def test_run_python_caps_stdout(monkeypatch):
    monkeypatch.setattr(sandbox, "MAX_STDOUT_BYTES", 64)

    result = sandbox.run_python("print(\"x\" * 256)")

    assert result.exit_code != 0
    assert len(result.stdout.encode("utf-8")) == 64
    assert "stdout exceeded 64 bytes" in result.stderr
    assert "OSError" in result.stderr


def test_run_python_caps_stderr(monkeypatch):
    monkeypatch.setattr(sandbox, "MAX_STDERR_BYTES", 64)

    result = sandbox.run_python(
        "import sys\nsys.stderr.write(\"e\" * 256)\nsys.stderr.flush()"
    )

    assert result.exit_code != 0
    assert "stderr exceeded 64 bytes" in result.stderr


def test_run_python_enforces_memory_cap(monkeypatch):
    monkeypatch.setattr(sandbox, "MAX_MEMORY_BYTES", 32 * 1024 * 1024)

    result = sandbox.run_python("x = bytearray(64 * 1024 * 1024)\nprint(len(x))")

    assert result.exit_code == 1
    assert not result.timed_out
    assert "MemoryError" in result.stderr
