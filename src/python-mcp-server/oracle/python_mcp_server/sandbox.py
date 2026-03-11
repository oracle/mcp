"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

WASM sandbox for executing Python code in isolation.
"""

from __future__ import annotations

import errno
import hashlib
import os
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from wasmtime import Config, Engine, ExitTrap, Linker, Module, Store, Trap, WasiConfig, WasmtimeError

# v3.13 stable release — zip contains python.wasm + lib/python3.13/
WASM_RELEASE_URL = (
    "https://github.com/brettcannon/cpython-wasi-build/releases/download"
    "/v3.13.12/python-3.13.12-wasi_sdk-24.zip"
)
CACHE_DIR = Path.home() / ".cache" / "python-sandbox-mcp"
WASM_FILENAME = "python.wasm"
LIB_DIR_NAME = "lib"  # extracted inside CACHE_DIR
EXPECTED_WASM_SHA256 = "875dd63414642fbeda8c45517777b891d5936b304d261879e3dcc1b201daf5d9"

# Fuel per second — 1 unit ≈ 10ns at ~100M instructions/sec.
# Tuning: increase for faster machines, decrease if timeouts fire too late.
FUEL_PER_SECOND = 100_000_000

MAX_CODE_LENGTH = 1_000_000  # 1 MB — reject oversized inputs early
MAX_MEMORY_BYTES = 256 * 1024 * 1024  # 256 MiB guest linear memory cap
MAX_STDOUT_BYTES = 1 * 1024 * 1024  # 1 MiB captured stdout per execution
MAX_STDERR_BYTES = 1 * 1024 * 1024  # 1 MiB captured stderr per execution

# Cached across calls: Engine is expensive to create, Module avoids
# re-reading the ~30 MB WASM binary on every execution.
_engine: Engine | None = None
_module: Module | None = None
_lib_dir: Path | None = None


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False


@dataclass
class _CappedOutput:
    """Collect output up to a fixed byte budget and fail further writes."""

    name: str
    max_bytes: int
    chunks: bytearray = field(default_factory=bytearray)
    exceeded: bool = False

    def callback(self, data: bytes) -> int:
        if self.exceeded:
            return -errno.EIO

        remaining = self.max_bytes - len(self.chunks)
        if remaining <= 0:
            self.exceeded = True
            return -errno.EIO

        take = min(len(data), remaining)
        if take:
            self.chunks.extend(data[:take])

        if take < len(data):
            self.exceeded = True

        return take

    def text(self) -> str:
        return self.chunks.decode("utf-8", errors="replace")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_wasm_checksum(path: Path) -> None:
    digest = _sha256_file(path)
    if digest != EXPECTED_WASM_SHA256:
        raise ValueError(
            "Downloaded python.wasm checksum mismatch: "
            f"expected {EXPECTED_WASM_SHA256}, got {digest}"
        )


def _cache_dir() -> Path:
    """Return the cache directory, creating it if needed."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def get_wasm_path() -> tuple[Path, Path]:
    """Return (wasm_path, lib_dir) for the CPython WASM binary, downloading if necessary.

    lib_dir contains ``python3.13/`` and must be mounted inside the sandbox
    at ``/lib`` so Python can locate its stdlib.
    """
    env_path = os.environ.get("PYTHON_WASM_PATH")
    if env_path:
        path = Path(env_path)
        if not path.exists():
            raise FileNotFoundError(f"PYTHON_WASM_PATH set but file not found: {path}")
        # Expect a sibling lib/ directory next to the wasm file.
        lib_dir = path.parent / LIB_DIR_NAME
        return path, lib_dir

    cache = _cache_dir()
    wasm_path = cache / WASM_FILENAME
    lib_dir = cache / LIB_DIR_NAME

    if wasm_path.exists() and lib_dir.exists():
        _verify_wasm_checksum(wasm_path)
        return wasm_path, lib_dir

    print(
        "Downloading CPython 3.13 WASM runtime (~30 MB) to",
        cache,
        "…",
        flush=True,
    )
    zip_tmp = cache / "python-wasi.zip.tmp"
    try:
        urllib.request.urlretrieve(WASM_RELEASE_URL, zip_tmp)
        extract_dir = cache / "extract-tmp"
        if extract_dir.exists():
            for child in sorted(extract_dir.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink(missing_ok=True)
                elif child.is_dir():
                    child.rmdir()
            extract_dir.rmdir()
        extract_dir.mkdir(parents=True, exist_ok=False)
        with zipfile.ZipFile(zip_tmp) as zf:
            zf.extractall(extract_dir)

        extracted_wasm = extract_dir / WASM_FILENAME
        extracted_lib = extract_dir / LIB_DIR_NAME
        _verify_wasm_checksum(extracted_wasm)

        wasm_path.write_bytes(extracted_wasm.read_bytes())
        if lib_dir.exists():
            for child in sorted(lib_dir.rglob("*"), reverse=True):
                if child.is_file() or child.is_symlink():
                    child.unlink(missing_ok=True)
                elif child.is_dir():
                    child.rmdir()
            lib_dir.rmdir()
        extracted_lib.rename(lib_dir)
        for child in sorted(extract_dir.rglob("*"), reverse=True):
            if child.is_file() or child.is_symlink():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        extract_dir.rmdir()
        zip_tmp.unlink(missing_ok=True)
    except Exception:
        zip_tmp.unlink(missing_ok=True)
        raise

    print("Download complete.", flush=True)
    return wasm_path, lib_dir


def _get_engine() -> Engine:
    """Return a cached Engine (created once, reused across calls)."""
    global _engine
    if _engine is None:
        config = Config()
        config.consume_fuel = True
        _engine = Engine(config)
    return _engine


def _get_module() -> tuple[Module, Path]:
    """Return a cached (Module, lib_dir) pair.

    The Module is compiled once from the WASM binary and reused.
    """
    global _module, _lib_dir
    if _module is None:
        engine = _get_engine()
        wasm_path, _lib_dir = get_wasm_path()
        _module = Module(engine, wasm_path.read_bytes())
    assert _lib_dir is not None
    return _module, _lib_dir


def run_python(
    code: str,
    stdin_data: str | None = None,
    timeout_seconds: float = 30.0,
) -> SandboxResult:
    """Execute *code* inside a WASM sandbox and return the result.

    The sandbox has:
    - No host filesystem access (stdlib available via read-only /lib mount)
    - No network access
    - A fuel-based instruction budget derived from *timeout_seconds*
    """
    if len(code) > MAX_CODE_LENGTH:
        return SandboxResult(
            stdout="",
            stderr=f"Code too large ({len(code)} bytes, max {MAX_CODE_LENGTH})",
            exit_code=1,
        )

    engine = _get_engine()
    module, lib_dir = _get_module()
    store = Store(engine)
    store.set_fuel(int(timeout_seconds * FUEL_PER_SECOND))
    store.set_limits(memory_size=MAX_MEMORY_BYTES, instances=1, tables=1, memories=1)

    stdout_capture = _CappedOutput(name="stdout", max_bytes=MAX_STDOUT_BYTES)
    stderr_capture = _CappedOutput(name="stderr", max_bytes=MAX_STDERR_BYTES)

    stdin_path: str | None = None

    try:
        wasi = WasiConfig()
        wasi.argv = ["python", "-c", code]
        wasi.env = [("HOME", "/tmp"), ("PYTHONDONTWRITEBYTECODE", "1")]
        # Mount stdlib: lib_dir (containing python3.13/) is visible as /lib
        # inside the sandbox, giving Python access to its stdlib without
        # exposing any other host paths.
        wasi.preopen_dir(str(lib_dir), "/lib")
        wasi.stdout_custom = stdout_capture.callback
        wasi.stderr_custom = stderr_capture.callback

        # Always write stdin to a temp file — never inherit the host's stdin
        # since that carries the MCP protocol stream.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as stdin_f:
            if stdin_data is not None:
                stdin_f.write(stdin_data)
            stdin_path = stdin_f.name
        wasi.stdin_file = stdin_path

        store.set_wasi(wasi)

        linker = Linker(engine)
        linker.define_wasi()

        timed_out = False
        exit_code = 0

        try:
            instance = linker.instantiate(store, module)
        except WasmtimeError as e:
            return SandboxResult(
                stdout="",
                stderr=f"Sandbox instantiation failed: {e}",
                exit_code=1,
            )

        try:
            instance.exports(store)["_start"](store)
        except ExitTrap as e:
            exit_code = e.code
        except Trap as e:
            msg = str(e).lower()
            if "fuel" in msg or "all fuel consumed" in msg:
                timed_out = True
                exit_code = -1
            else:
                raise

        stdout = stdout_capture.text()
        stderr = stderr_capture.text()

        if stdout_capture.exceeded:
            stderr += (
                f"\n[stdout exceeded {MAX_STDOUT_BYTES} bytes; further output was blocked]"
            )
            if exit_code == 0:
                exit_code = 1

        if stderr_capture.exceeded:
            stderr += (
                f"\n[stderr exceeded {MAX_STDERR_BYTES} bytes; further output was blocked]"
            )
            if exit_code == 0:
                exit_code = 1

        return SandboxResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
        )
    finally:
        for p in filter(None, [stdin_path]):
            try:
                Path(p).unlink()
            except OSError:
                pass
