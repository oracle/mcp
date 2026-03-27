"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import runpy
import sys

from fastmcp import FastMCP

from oracle.python_mcp_server.models import SandboxResult, map_sandbox_result
from oracle.python_mcp_server import server
from oracle.python_mcp_server.sandbox import SandboxResult as RawSandboxResult


def test_map_sandbox_result_preserves_all_fields():
    raw = RawSandboxResult(
        stdout="stdout",
        stderr="stderr",
        exit_code=3,
        timed_out=True,
    )

    result = map_sandbox_result(raw)

    assert isinstance(result, SandboxResult)
    assert result.model_dump() == {
        "stdout": "stdout",
        "stderr": "stderr",
        "exit_code": 3,
        "timed_out": True,
    }


def test_run_python_uses_default_timeout_when_none(monkeypatch):
    raw = RawSandboxResult(stdout="ok", stderr="", exit_code=0, timed_out=False)
    captured = {}

    def fake_run_python(code, stdin_data, timeout_seconds):
        captured["code"] = code
        captured["stdin_data"] = stdin_data
        captured["timeout_seconds"] = timeout_seconds
        return raw

    monkeypatch.setattr(server, "_run_python", fake_run_python)

    result = server.run_python.fn("print(1)", timeout=None)

    assert result.model_dump() == {
        "stdout": "ok",
        "stderr": "",
        "exit_code": 0,
        "timed_out": False,
    }
    assert captured == {
        "code": "print(1)",
        "stdin_data": None,
        "timeout_seconds": 30.0,
    }


def test_run_python_with_input_passes_stdin_and_timeout(monkeypatch):
    raw = RawSandboxResult(stdout="hello", stderr="", exit_code=0, timed_out=False)
    captured = {}

    def fake_run_python(code, stdin_data, timeout_seconds):
        captured["code"] = code
        captured["stdin_data"] = stdin_data
        captured["timeout_seconds"] = timeout_seconds
        return raw

    monkeypatch.setattr(server, "_run_python", fake_run_python)

    result = server.run_python_with_input.fn(
        "import sys; print(sys.stdin.read())",
        stdin="hello",
        timeout=7.5,
    )

    assert result.model_dump() == {
        "stdout": "hello",
        "stderr": "",
        "exit_code": 0,
        "timed_out": False,
    }
    assert captured == {
        "code": "import sys; print(sys.stdin.read())",
        "stdin_data": "hello",
        "timeout_seconds": 7.5,
    }


def test_run_python_reraises_sandbox_errors(monkeypatch):
    def fake_run_python(code, stdin_data, timeout_seconds):
        raise RuntimeError("sandbox failed")

    monkeypatch.setattr(server, "_run_python", fake_run_python)

    try:
        server.run_python.fn("print(1)")
    except RuntimeError as exc:
        assert str(exc) == "sandbox failed"
    else:
        raise AssertionError("run_python should re-raise sandbox failures")


def test_run_python_with_input_reraises_sandbox_errors(monkeypatch):
    def fake_run_python(code, stdin_data, timeout_seconds):
        raise RuntimeError("sandbox failed")

    monkeypatch.setattr(server, "_run_python", fake_run_python)

    try:
        server.run_python_with_input.fn("print(input())", stdin="hello")
    except RuntimeError as exc:
        assert str(exc) == "sandbox failed"
    else:
        raise AssertionError("run_python_with_input should re-raise sandbox failures")


def test_main_runs_stdio_by_default(monkeypatch):
    calls = []

    def fake_run(**kwargs):
        calls.append(kwargs)

    monkeypatch.delenv("ORACLE_MCP_HOST", raising=False)
    monkeypatch.delenv("ORACLE_MCP_PORT", raising=False)
    monkeypatch.setattr(server.mcp, "run", fake_run)

    server.main()

    assert calls == [{}]


def test_main_runs_http_when_host_and_port_are_set(monkeypatch):
    calls = []

    def fake_run(**kwargs):
        calls.append(kwargs)

    monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("ORACLE_MCP_PORT", "8080")
    monkeypatch.setattr(server.mcp, "run", fake_run)

    server.main()

    assert calls == [{"transport": "http", "host": "127.0.0.1", "port": 8080}]


def test_module_entrypoint_invokes_main(monkeypatch):
    calls = []

    def fake_run(self, **kwargs):
        calls.append(kwargs)

    monkeypatch.delenv("ORACLE_MCP_HOST", raising=False)
    monkeypatch.delenv("ORACLE_MCP_PORT", raising=False)
    monkeypatch.setattr(FastMCP, "run", fake_run)
    monkeypatch.delitem(sys.modules, "oracle.python_mcp_server.server", raising=False)

    runpy.run_module("oracle.python_mcp_server.server", run_name="__main__")

    assert calls == [{}]
