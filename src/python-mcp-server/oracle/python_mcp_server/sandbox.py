"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

WASM sandbox for executing Python code in isolation.
"""

from __future__ import annotations

import os
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

from wasmtime import Config, Engine, ExitTrap, Linker, Module, Store, Trap, WasiConfig

# v3.13 stable release — zip contains python.wasm + lib/python3.13/
WASM_RELEASE_URL = (
    "https://github.com/brettcannon/cpython-wasi-build/releases/download"
    "/v3.13.12/python-3.13.12-wasi_sdk-24.zip"
)
CACHE_DIR = Path.home() / ".cache" / "python-sandbox-mcp"
WASM_FILENAME = "python.wasm"
LIB_DIR_NAME = "lib"  # extracted inside CACHE_DIR

# Fuel per second — 1 unit ≈ 10ns at ~100M instructions/sec.
# Tuning: increase for faster machines, decrease if timeouts fire too late.
FUEL_PER_SECOND = 100_000_000

MAX_CODE_LENGTH = 1_000_000  # 1 MB — reject oversized inputs early

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
        with zipfile.ZipFile(zip_tmp) as zf:
            zf.extractall(cache)
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

    with (
        tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as stdout_f,
        tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as stderr_f,
    ):
        stdout_path = stdout_f.name
        stderr_path = stderr_f.name

    stdin_path: str | None = None

    try:
        wasi = WasiConfig()
        wasi.argv = ["python", "-c", code]
        wasi.env = [("HOME", "/tmp"), ("PYTHONDONTWRITEBYTECODE", "1")]
        # Mount stdlib: lib_dir (containing python3.13/) is visible as /lib
        # inside the sandbox, giving Python access to its stdlib without
        # exposing any other host paths.
        wasi.preopen_dir(str(lib_dir), "/lib")
        wasi.stdout_file = stdout_path
        wasi.stderr_file = stderr_path

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

        instance = linker.instantiate(store, module)

        timed_out = False
        exit_code = 0

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

        stdout = Path(stdout_path).read_text(encoding="utf-8", errors="replace")
        stderr = Path(stderr_path).read_text(encoding="utf-8", errors="replace")

        return SandboxResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
        )
    finally:
        for p in filter(None, [stdout_path, stderr_path, stdin_path]):
            try:
                Path(p).unlink()
            except OSError:
                pass
