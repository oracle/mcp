"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import hashlib
import errno
import os
import multiprocessing as mp
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pytest

from oracle.python_mcp_server import sandbox


@dataclass
class _PreopenDirCall:
    host_path: str
    guest_path: str
    dir_perms: Any
    file_perms: Any


@dataclass
class _FakeRuntimeState:
    execute: Callable[[Any], None]
    engine: Any
    lib_dir: Path
    stores: list[Any] = field(default_factory=list)


class _FakeExitTrap(Exception):
    def __init__(self, code: int):
        super().__init__(code)
        self.code = code


class _FakeTrap(Exception):
    pass


class _FakeWasmtimeError(Exception):
    pass


def _install_fake_runtime(monkeypatch, tmp_path, execute):
    fake_engine = object()
    fake_module = object()
    fake_lib_dir = tmp_path / "runtime-lib"
    (fake_lib_dir / "python3.13").mkdir(parents=True)
    state = _FakeRuntimeState(execute=execute, engine=fake_engine, lib_dir=fake_lib_dir)

    class FakeStore:
        def __init__(self, engine):
            self.engine = engine
            self.fuel = None
            self.limits = None
            self.wasi = None

        def set_fuel(self, fuel):
            self.fuel = fuel

        def set_limits(self, **kwargs):
            self.limits = kwargs

        def set_wasi(self, wasi):
            self.wasi = wasi

    class FakeWasiConfig:
        def __init__(self):
            self.argv = None
            self.env = []
            self.preopens = []
            self.stdout_custom = None
            self.stderr_custom = None
            self.stdin_file = None

        def preopen_dir(self, host_path, guest_path, dir_perms=None, file_perms=None):
            self.preopens.append(
                _PreopenDirCall(
                    host_path=host_path,
                    guest_path=guest_path,
                    dir_perms=dir_perms,
                    file_perms=file_perms,
                )
            )

    class FakeInstance:
        def exports(self, store):
            return {"_start": lambda call_store: state.execute(call_store)}

    class FakeLinker:
        def __init__(self, engine):
            self.engine = engine

        def define_wasi(self):
            return None

        def instantiate(self, store, module):
            state.stores.append(store)
            assert module is fake_module
            return FakeInstance()

    monkeypatch.setattr(sandbox, "_get_engine", lambda: fake_engine)
    monkeypatch.setattr(sandbox, "_get_module", lambda: (fake_module, fake_lib_dir))
    monkeypatch.setattr(sandbox, "Store", FakeStore)
    monkeypatch.setattr(sandbox, "WasiConfig", FakeWasiConfig)
    monkeypatch.setattr(sandbox, "Linker", FakeLinker)
    monkeypatch.setattr(sandbox, "ExitTrap", _FakeExitTrap)
    monkeypatch.setattr(sandbox, "Trap", _FakeTrap)
    monkeypatch.setattr(sandbox, "WasmtimeError", _FakeWasmtimeError)
    return state, fake_lib_dir


def _has_local_runtime() -> bool:
    env_path = os.environ.get("PYTHON_WASM_PATH")
    if env_path:
        wasm_path = Path(env_path)
        return wasm_path.exists() and (wasm_path.parent / sandbox.LIB_DIR_NAME).is_dir()

    cache = sandbox.CACHE_DIR
    return sandbox._runtime_is_cached(cache / sandbox.WASM_FILENAME, cache / sandbox.LIB_DIR_NAME)


def _concurrent_runtime_install_worker(
    cache_dir: str, runtime_zip: str, expected_sha256: str, result_queue
) -> None:
    import shutil

    from oracle.python_mcp_server import sandbox as worker_sandbox

    def fake_urlretrieve(url, dest):
        assert url == worker_sandbox.WASM_RELEASE_URL
        dest_path = Path(dest)
        shutil.copyfile(runtime_zip, dest_path)
        return str(dest_path), None

    worker_sandbox.CACHE_DIR = Path(cache_dir)
    worker_sandbox.EXPECTED_WASM_SHA256 = expected_sha256
    worker_sandbox._module = None
    worker_sandbox._lib_dir = None
    worker_sandbox.urllib.request.urlretrieve = fake_urlretrieve

    try:
        wasm_path, lib_dir = worker_sandbox.get_wasm_path()
        result_queue.put((True, str(wasm_path), str(lib_dir)))
    except Exception as exc:
        result_queue.put((False, type(exc).__name__, str(exc)))


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


def test_get_wasm_path_rejects_env_runtime_without_sibling_lib(tmp_path, monkeypatch):
    wasm_path = tmp_path / sandbox.WASM_FILENAME
    wasm_path.write_bytes(b"wasm contents")
    monkeypatch.setenv("PYTHON_WASM_PATH", str(wasm_path))

    with pytest.raises(FileNotFoundError, match="sibling lib directory not found"):
        sandbox.get_wasm_path()


def test_get_wasm_path_uses_env_runtime_when_present(tmp_path, monkeypatch):
    wasm_path = tmp_path / sandbox.WASM_FILENAME
    wasm_path.write_bytes(b"wasm contents")
    lib_dir = tmp_path / sandbox.LIB_DIR_NAME
    (lib_dir / "python3.13").mkdir(parents=True)
    monkeypatch.setenv("PYTHON_WASM_PATH", str(wasm_path))

    resolved_wasm_path, resolved_lib_dir = sandbox.get_wasm_path()

    assert resolved_wasm_path == wasm_path
    assert resolved_lib_dir == lib_dir


def test_get_wasm_path_rejects_missing_env_runtime_file(tmp_path, monkeypatch):
    missing_wasm_path = tmp_path / sandbox.WASM_FILENAME
    monkeypatch.setenv("PYTHON_WASM_PATH", str(missing_wasm_path))

    with pytest.raises(FileNotFoundError, match="file not found"):
        sandbox.get_wasm_path()


def test_get_wasm_path_download_path_stays_quiet_on_stdout(tmp_path, monkeypatch, capsys):
    cache_dir = tmp_path / "cache"
    runtime_zip = tmp_path / "runtime.zip"
    wasm_bytes = b"expected wasm contents"
    with zipfile.ZipFile(runtime_zip, "w") as zf:
        zf.writestr(sandbox.WASM_FILENAME, wasm_bytes)
        zf.writestr(f"{sandbox.LIB_DIR_NAME}/python3.13/os.py", "# stub stdlib\n")

    def fake_urlretrieve(url, dest):
        assert url == sandbox.WASM_RELEASE_URL
        dest_path = Path(dest)
        dest_path.write_bytes(runtime_zip.read_bytes())
        return str(dest_path), None

    monkeypatch.setattr(sandbox, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(
        sandbox,
        "EXPECTED_WASM_SHA256",
        hashlib.sha256(wasm_bytes).hexdigest(),
    )
    monkeypatch.setattr(sandbox.urllib.request, "urlretrieve", fake_urlretrieve)

    wasm_path, lib_dir = sandbox.get_wasm_path()
    captured = capsys.readouterr()

    assert captured.out == ""
    assert wasm_path.exists()
    assert (lib_dir / "python3.13" / "os.py").exists()


def test_get_wasm_path_serializes_cross_process_initialization(tmp_path):
    cache_dir = tmp_path / "cache"
    runtime_zip = tmp_path / "runtime.zip"
    wasm_bytes = b"expected wasm contents"
    with zipfile.ZipFile(runtime_zip, "w") as zf:
        zf.writestr(sandbox.WASM_FILENAME, wasm_bytes)
        zf.writestr(f"{sandbox.LIB_DIR_NAME}/python3.13/os.py", "# stub stdlib\n")

    expected_sha256 = hashlib.sha256(wasm_bytes).hexdigest()
    start_method = "spawn"
    if "fork" in mp.get_all_start_methods():
        start_method = "fork"
    ctx = mp.get_context(start_method)
    result_queue = ctx.Queue()
    workers = [
        ctx.Process(
            target=_concurrent_runtime_install_worker,
            args=(str(cache_dir), str(runtime_zip), expected_sha256, result_queue),
        )
        for _ in range(4)
    ]

    try:
        for worker in workers:
            worker.start()

        for worker in workers:
            worker.join(timeout=10)
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=2)
                pytest.fail("concurrent runtime install worker hung")

        results = [result_queue.get(timeout=2) for _ in workers]
    finally:
        result_queue.close()
        result_queue.join_thread()

    assert all(worker.exitcode == 0 for worker in workers)
    assert all(result[0] for result in results), results
    assert (cache_dir / sandbox.WASM_FILENAME).read_bytes() == wasm_bytes
    assert (cache_dir / sandbox.LIB_DIR_NAME / "python3.13" / "os.py").exists()


def test_run_python_configures_runtime_and_returns_clean_output(monkeypatch, tmp_path):
    def execute(store):
        assert store.engine is fake_state.engine
        assert store.fuel == int(12.5 * sandbox.FUEL_PER_SECOND)
        assert store.limits == {
            "memory_size": sandbox.MAX_MEMORY_BYTES,
            "instances": 1,
            "tables": 1,
            "memories": 1,
        }
        assert store.wasi.argv == ["python", "-c", "print(1)"]
        assert ("PYTHONHOME", sandbox.GUEST_PYTHONHOME) in store.wasi.env
        assert ("HOME", "/tmp") in store.wasi.env
        assert ("PYTHONDONTWRITEBYTECODE", "1") in store.wasi.env
        assert Path(store.wasi.stdin_file).read_bytes() == b""
        assert len(store.wasi.preopens) == 1
        preopen = store.wasi.preopens[0]
        assert preopen.host_path == str(fake_state.lib_dir)
        assert preopen.guest_path == sandbox.GUEST_LIB_ROOT
        assert preopen.dir_perms == sandbox.DirPerms.READ_ONLY
        assert preopen.file_perms == sandbox.FilePerms.READ_ONLY
        assert store.wasi.stdout_custom(b"1\n") == 2

    fake_state, _ = _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python("print(1)", timeout_seconds=12.5)

    assert len(fake_state.stores) == 1
    assert result.exit_code == 0
    assert result.stdout == "1\n"
    assert result.stderr == ""


def test_run_python_round_trips_stdin_via_temp_file(monkeypatch, tmp_path):
    stdin_paths = []

    def execute(store):
        stdin_path = Path(store.wasi.stdin_file)
        stdin_paths.append(stdin_path)
        assert store.wasi.stdout_custom(stdin_path.read_bytes()) == 11

    _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python("import sys; print(sys.stdin.read())", stdin_data="hello world")

    assert result.exit_code == 0
    assert result.stdout == "hello world"
    assert result.stderr == ""
    assert len(stdin_paths) == 1


def test_capped_output_reports_budget_exhaustion():
    capture = sandbox._CappedOutput(name="stdout", max_bytes=3)

    assert capture.callback(b"ab") == 2
    assert capture.callback(b"cd") == 1
    assert capture.exceeded is True
    assert capture.callback(b"z") == -errno.EIO
    assert capture.text() == "abc"

    empty_capture = sandbox._CappedOutput(name="stderr", max_bytes=0)
    assert empty_capture.callback(b"x") == -errno.EIO
    assert empty_capture.exceeded is True


def test_remove_tree_removes_nested_directories(tmp_path):
    root = tmp_path / "tree"
    nested_dir = root / "nested"
    nested_dir.mkdir(parents=True)
    (nested_dir / "payload.txt").write_text("payload")

    sandbox._remove_tree(root)

    assert not root.exists()


def test_run_python_rejects_oversized_code_without_touching_runtime(monkeypatch):
    called = {"engine": False}

    def fake_get_engine():
        called["engine"] = True
        raise AssertionError("_get_engine should not be called for oversized code")

    monkeypatch.setattr(sandbox, "_get_engine", fake_get_engine)

    result = sandbox.run_python("x" * (sandbox.MAX_CODE_LENGTH + 1))

    assert result.exit_code == 1
    assert result.stdout == ""
    assert "Code too large" in result.stderr
    assert called["engine"] is False


def test_run_python_rejects_oversized_stdin_before_tempfile_write(monkeypatch):
    monkeypatch.setattr(sandbox, "MAX_STDIN_BYTES", 4)

    def fail_named_temporary_file(*args, **kwargs):
        raise AssertionError("stdin should be rejected before creating a temp file")

    monkeypatch.setattr(sandbox.tempfile, "NamedTemporaryFile", fail_named_temporary_file)

    result = sandbox.run_python("print(1)", stdin_data="12345")

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "stdin too large (5 bytes, max 4)"


def test_run_python_reports_instantiation_failure(monkeypatch, tmp_path):
    def execute(store):
        raise AssertionError("_start should not run when instantiation fails")

    fake_state, _ = _install_fake_runtime(monkeypatch, tmp_path, execute)

    class FailingLinker:
        def __init__(self, engine):
            assert engine is fake_state.engine

        def define_wasi(self):
            return None

        def instantiate(self, store, module):
            raise _FakeWasmtimeError("boom")

    monkeypatch.setattr(sandbox, "Linker", FailingLinker)

    result = sandbox.run_python("print(1)")

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "Sandbox instantiation failed: boom"


def test_run_python_reports_missing_extension_modules_without_startup_warning(
    monkeypatch, tmp_path
):
    def execute(store):
        assert store.wasi.stderr_custom(
            b"Traceback (most recent call last):\n"
            b'  File "<string>", line 1, in <module>\n'
            b"ModuleNotFoundError: No module named '_sqlite3'\n"
        ) > 0
        raise _FakeExitTrap(1)

    _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python("import sqlite3")

    assert result.exit_code == 1
    assert "ModuleNotFoundError: No module named '_sqlite3'" in result.stderr
    assert "Could not find platform dependent libraries <exec_prefix>" not in result.stderr


def test_run_python_stdlib_mount_is_read_only(monkeypatch, tmp_path):
    def execute(store):
        assert len(store.wasi.preopens) == 1
        preopen = store.wasi.preopens[0]
        assert preopen.guest_path == sandbox.GUEST_LIB_ROOT
        assert preopen.dir_perms == sandbox.DirPerms.READ_ONLY
        assert preopen.file_perms == sandbox.FilePerms.READ_ONLY
        assert store.wasi.stderr_custom(
            b"PermissionError: [Errno 13] Permission denied: "
            b"'/usr/local/lib/python3.13/__codex_probe__.txt'\n"
        ) > 0
        raise _FakeExitTrap(1)

    _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python(
        "from pathlib import Path\n"
        "Path('/usr/local/lib/python3.13/__codex_probe__.txt').write_text('x')"
    )

    assert result.exit_code == 1
    assert "PermissionError" in result.stderr


def test_run_python_caps_stdout(monkeypatch, tmp_path):
    monkeypatch.setattr(sandbox, "MAX_STDOUT_BYTES", 64)

    def execute(store):
        written = store.wasi.stdout_custom(b"x" * 256)
        if written != 256:
            assert store.wasi.stderr_custom(b"OSError: [Errno 29] I/O error\n") > 0
            raise _FakeExitTrap(1)

    _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python("print(\"x\" * 256)")

    assert result.exit_code != 0
    assert len(result.stdout.encode("utf-8")) == 64
    assert "stdout exceeded 64 bytes" in result.stderr
    assert "OSError" in result.stderr


def test_run_python_caps_stderr(monkeypatch, tmp_path):
    monkeypatch.setattr(sandbox, "MAX_STDERR_BYTES", 64)

    def execute(store):
        written = store.wasi.stderr_custom(b"e" * 256)
        if written != 256:
            raise _FakeExitTrap(1)

    _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python(
        "import sys\nsys.stderr.write(\"e\" * 256)\nsys.stderr.flush()"
    )

    assert result.exit_code != 0
    assert "stderr exceeded 64 bytes" in result.stderr


def test_run_python_enforces_memory_cap(monkeypatch, tmp_path):
    monkeypatch.setattr(sandbox, "MAX_MEMORY_BYTES", 32 * 1024 * 1024)

    def execute(store):
        assert store.limits["memory_size"] == 32 * 1024 * 1024
        assert store.wasi.stderr_custom(b"MemoryError\n") > 0
        raise _FakeExitTrap(1)

    _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python("x = bytearray(64 * 1024 * 1024)\nprint(len(x))")

    assert result.exit_code == 1
    assert not result.timed_out
    assert "MemoryError" in result.stderr


def test_run_python_times_out_on_fuel_trap(monkeypatch, tmp_path):
    def execute(store):
        raise _FakeTrap("all fuel consumed by WebAssembly")

    _install_fake_runtime(monkeypatch, tmp_path, execute)
    result = sandbox.run_python("while True:\n    pass")

    assert result.exit_code == -1
    assert result.timed_out
    assert result.stdout == ""
    assert result.stderr == ""


def test_run_python_integration_smoke_if_runtime_present():
    if not _has_local_runtime():
        pytest.skip("requires a preinstalled CPython WASM runtime")

    result = sandbox.run_python("print(1)")

    assert result.exit_code == 0
    assert result.stdout == "1\n"
    assert result.stderr == ""
