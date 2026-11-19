"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

"""Isolated Codex CLI execution for the trusted, serial Behave test driver (POSIX)."""

from contextlib import contextmanager
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import tempfile
import threading
import time

import tomli_w


class CodexError(RuntimeError):
    """Configuration, process or event-stream failure; never an agent answer."""


@contextmanager
def termination_cleanup():
    """Unwind owned resources on TERM as on Ctrl-C; restore the caller's handler."""

    def cancel(signum, frame):
        raise KeyboardInterrupt("SIGTERM received")

    main_thread = threading.current_thread() is threading.main_thread()
    previous = signal.signal(signal.SIGTERM, cancel) if main_thread else None
    try:
        yield
    finally:
        if main_thread:
            signal.signal(signal.SIGTERM, previous)


def translate_hosts(host_file, mock_config, child_home, proxy_url="http://127.0.0.1:5000"):
    """Translate the existing stdio inventory, rejecting unsupported settings."""
    host_file = Path(host_file).resolve()
    hosts = json.loads(host_file.read_text())
    if set(hosts) != {"mcpServers"} or not isinstance(hosts["mcpServers"], dict):
        raise CodexError("Host file must contain an mcpServers object")
    translated = {}
    for name, settings in hosts["mcpServers"].items():
        if not re.fullmatch(r"[\w-]+", name) or not isinstance(settings, dict):
            raise CodexError("Invalid MCP server name or settings")
        if type(settings.get("disabled", False)) is not bool:
            raise CodexError(f"{name}: disabled must be a boolean")
        if settings.get("disabled", False):
            continue
        unknown = set(settings) - {"disabled", "timeout", "type", "command", "args", "env", "cwd"}
        if unknown or settings.get("type", "stdio") != "stdio":
            raise CodexError(f"{name}: only supported stdio settings may be translated")
        command, args = settings.get("command"), settings.get("args", [])
        if not isinstance(command, str) or not command or not isinstance(args, list):
            raise CodexError(f"{name}: command and args must be a string and array")
        if any(not isinstance(arg, str) for arg in args):
            raise CodexError(f"{name}: args must contain only strings")
        timeout = settings.get("timeout", 60)
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise CodexError(f"{name}: timeout must be positive and finite")
        cwd = settings.get("cwd", ".")
        if not isinstance(cwd, str) or not (host_file.parent / cwd).is_dir():
            raise CodexError(f"{name}: cwd must resolve to an existing directory")
        child_env = {
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(child_home),
            "OCI_CONFIG_FILE": str(mock_config),
            "UV_CACHE_DIR": os.environ.get("UV_CACHE_DIR", str(Path.home() / ".cache" / "uv")),
        }
        # Reuse the dependency cache, but never the caller's credentials or Python path.
        for key in ("TMPDIR", "LANG", "PROTO_HOME"):
            if key in os.environ:
                child_env[key] = os.environ[key]
        configured_env = settings.get("env", {})
        if not isinstance(configured_env, dict):
            raise CodexError(f"{name}: env must be an object")
        for key, value in configured_env.items():
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) or not isinstance(value, str):
                raise CodexError(f"{name}: invalid environment entry")
            value = value.replace("${env:OCI_CONFIG_FILE}", str(mock_config))
            value = value.replace("${env:MOCK_OCI_PROXY}", proxy_url)
            if "${" in value:
                raise CodexError(f"{name}: unsupported environment substitution in {key}")
            if key in {"HOME", "OCI_CONFIG_FILE"} and value != child_env[key]:
                raise CodexError(f"{name}: {key} must use the isolated mock environment")
            child_env[key] = value
        # env -i is an argv-based boundary: Codex auth never reaches MCP children.
        translated[name] = {
            "command": "/usr/bin/env",
            "args": ["-i", *[f"{k}={v}" for k, v in child_env.items()], command, *args],
            "cwd": str((host_file.parent / cwd).resolve()),
            "required": True,
            "default_tools_approval_mode": "approve",
            "startup_timeout_sec": timeout,
            "tool_timeout_sec": timeout,
        }
    if not translated:
        raise CodexError("No enabled MCP servers")
    return translated


@dataclass
class Session:
    command: list[str]
    env: dict[str, str]
    cwd: Path
    servers: dict


@contextmanager
def isolated_session(host_file, mock_config, model, proxy_url="http://127.0.0.1:5000"):
    """Create disposable configuration/auth; never copy personal servers or guidance."""
    source_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    with tempfile.TemporaryDirectory(prefix="mcp-codex-") as directory:
        root = Path(directory)
        home, codex_home, cwd = root / "home", root / "codex", root / "work"
        for path in (home, codex_home, cwd):
            path.mkdir(mode=0o700)
        env = {key: os.environ[key] for key in ("PATH", "TMPDIR", "LANG") if key in os.environ}
        for key in (
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "no_proxy",
            "SSL_CERT_FILE",
            "SSL_CERT_DIR",
        ):
            if os.environ.get(key) and os.environ[key] != proxy_url:
                env[key] = os.environ[key]
        env.update(HOME=str(home), CODEX_HOME=str(codex_home))
        if os.environ.get("CODEX_API_KEY"):
            env["CODEX_API_KEY"] = os.environ["CODEX_API_KEY"]
        elif (source_home / "auth.json").is_file():
            target = codex_home / "auth.json"
            target.touch(mode=0o600)
            shutil.copyfile(source_home / "auth.json", target)
        else:
            raise CodexError("Run codex login with file credential storage, or set CODEX_API_KEY")
        servers = translate_hosts(host_file, mock_config, home, proxy_url)
        config = {
            "model": model,
            "approval_policy": "on-request",
            "sandbox_mode": "read-only",
            "web_search": "disabled",
            "cli_auth_credentials_store": "file",
            "project_doc_max_bytes": 0,
            "mcp_servers": servers,
            "agents": {"enabled": False},
            "features": {
                key: False
                for key in (
                    "shell_tool",
                    "view_image",
                    "apps",
                    "plugins",
                    "memories",
                    "multi_agent_v2",
                    "js_repl",
                    "code_mode",
                    "browser_use",
                    "computer_use",
                )
            },
            "projects": {str(cwd): {"trust_level": "trusted"}},
        }
        (codex_home / "config.toml").write_text(tomli_w.dumps(config))
        executable = shutil.which(os.environ.get("CODEX_E2E_EXECUTABLE", "codex"))
        if not executable:
            raise CodexError("Codex executable not found; install Codex CLI 0.170.0")
        command = [
            executable,
            "--no-daemon",
            "exec",
            "--json",
            "--ephemeral",
            "--strict-config",
            "--skip-git-repo-check",
            "-C",
            str(cwd),
            "-",
        ]
        yield Session(command, env, cwd, servers)


def stop_process_group(proc):
    """Reap the leader and kill remaining descendants, even after the leader exits."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass
    proc.wait()


def run_process(command, prompt, env, cwd, *, timeout=180, max_output=8 * 1024 * 1024):
    """Run literal argv/stdin with bounded combined output and owned process groups."""
    if not math.isfinite(timeout) or timeout <= 0:
        raise CodexError("Process timeout must be positive and finite")
    output = bytearray()
    total = 0
    # A file descriptor for stdin avoids blocking on a full input pipe at startup.
    with termination_cleanup(), tempfile.TemporaryFile() as stdin, selectors.DefaultSelector() as selector:
        stdin.write(prompt.encode("utf-8"))
        stdin.seek(0)
        try:
            proc = subprocess.Popen(
                command,
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env,
                start_new_session=True,
            )
        except OSError as exc:
            raise CodexError(f"Could not start executable ({type(exc).__name__})") from None
        try:
            selector.register(proc.stdout, selectors.EVENT_READ)
            selector.register(proc.stderr, selectors.EVENT_READ)
            deadline = time.monotonic() + timeout
            while selector.get_map() or proc.poll() is None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CodexError(f"Process timed out after {timeout:g}s")
                for key, _ in selector.select(min(remaining, 0.1)):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    if total > max_output:
                        raise CodexError(f"Process output exceeded {max_output} bytes")
                    if key.fileobj is proc.stdout:
                        output.extend(chunk)
            if proc.wait() != 0:
                # Do not echo stderr: provider diagnostics may contain credentials.
                raise CodexError(f"Process exit {proc.returncode}; check Codex login, model and MCP setup")
            try:
                return output.decode("utf-8")
            except UnicodeDecodeError:
                raise CodexError("Invalid UTF-8 in CLI events") from None
        finally:
            stop_process_group(proc)
            proc.stdout.close()
            proc.stderr.close()


@dataclass
class CodexResult:
    text: str
    calls: list[dict]
    usage: dict
    thread_id: str
    warnings: list[str]
    resource_calls: list[dict]

    def require_call(self, tool):
        calls = [call for call in self.calls if call["tool"] == tool]
        assert calls, f"No successful MCP call to {tool}"
        return calls[-1]

    def require_chain(self, listing, lookup, argument):
        for index, call in enumerate(self.calls):
            if call["tool"] != lookup:
                continue
            identifier = call["arguments"].get(argument)
            for previous in self.calls[:index]:
                if previous["tool"] == listing and previous["server"] == call["server"]:
                    returned = result_strings(previous["result"])
                    if isinstance(identifier, str) and identifier and identifier in returned:
                        assert identifier in self.text, "Returned ID missing from final answer"
                        return
        raise AssertionError(f"{lookup} must use an ID returned by {listing}")


def result_strings(value):
    """Read exact values from structured results and JSON-encoded MCP text blocks."""
    if isinstance(value, dict):
        return {s for child in value.values() for s in result_strings(child)}
    if isinstance(value, list):
        return {s for child in value for s in result_strings(child)}
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except ValueError:
            return {value}
        return {value} if decoded == value else result_strings(decoded)
    return set()


def parse_events(output, servers):
    """Fail closed on terminal errors, foreign tools, and incomplete event streams."""
    calls, texts, usage, thread_id = [], [], None, None
    started = False
    pending = set()
    warnings = []
    resource_calls = []
    try:
        for line in output.splitlines():
            event = json.loads(line)
            kind = event["type"]
            if usage is not None:
                raise CodexError("Events after terminal turn")
            if kind == "thread.started" and thread_id is None:
                thread_id = event["thread_id"]
                if not isinstance(thread_id, str) or not thread_id:
                    raise CodexError("Invalid thread ID")
            elif kind == "turn.started" and thread_id and not started:
                started = True
            elif kind == "turn.completed" and started:
                usage = event["usage"]
                if not isinstance(usage, dict):
                    raise CodexError("Invalid usage event")
            elif kind == "item.completed" and thread_id and not started and event["item"]["type"] == "error":
                # CLI 0.170 emits configuration warnings as error items before turn.started.
                message = event["item"]["message"]
                if not isinstance(message, str):
                    raise CodexError("Invalid startup warning")
                warnings.append(message)
            elif kind in {"item.started", "item.updated", "item.completed"} and started:
                item = event["item"]
                item_type = item["type"]
                if item_type not in {"agent_message", "reasoning", "mcp_tool_call", "todo_list"}:
                    raise CodexError(f"Unexpected agent capability or error: {item_type}")
                if item_type == "mcp_tool_call":
                    resource_tool = item["tool"] in {
                        "list_mcp_resources",
                        "list_mcp_resource_templates",
                        "read_mcp_resource",
                    }
                    # Codex labels aggregate resource discovery with its own synthetic server ID.
                    aggregate = item["server"] == "codex" and item["tool"] in {
                        "list_mcp_resources",
                        "list_mcp_resource_templates",
                    }
                    if item["server"] not in servers and not aggregate:
                        raise CodexError(f"MCP call used an unconfigured server: {item['server']}")
                    arguments = item.get("arguments")
                    if resource_tool and isinstance(arguments, dict):
                        target = arguments.get("server")
                        if target is not None and (
                            not isinstance(target, str) or (target.strip() and target.strip() not in servers)
                        ):
                            raise CodexError("MCP resource request targeted an unconfigured server")
                    if kind == "item.started":
                        pending.add(item["id"])
                    if kind == "item.completed":
                        pending.discard(item["id"])
                        result = item.get("result")
                        if (
                            item.get("status") != "completed"
                            or item.get("error")
                            or not isinstance(result, dict)
                            or result.get("isError")
                            or not isinstance(result.get("content"), list)
                            or not (isinstance(arguments, dict) or (aggregate and arguments is None))
                        ):
                            raise CodexError(f"Unsuccessful MCP call: {item.get('tool')}")
                        (resource_calls if resource_tool else calls).append(item)
                elif item_type == "agent_message" and kind == "item.completed":
                    text = item["text"]
                    if not isinstance(text, str):
                        raise CodexError("Invalid agent message")
                    texts.append(text)
            else:
                raise CodexError(f"Failed or unexpected CLI event: {kind}")
    except (ValueError, KeyError, TypeError):
        raise CodexError("Invalid or truncated Codex JSONL events") from None
    if usage is None or not texts or not texts[-1].strip():
        raise CodexError("Missing completed turn or final agent output")
    if pending:
        raise CodexError("Codex completed with incomplete MCP calls")
    return CodexResult(texts[-1], calls, usage, thread_id, warnings, resource_calls)


def prepare_environments(host_file):
    """Sync inventory-owned uv projects before the mock proxy reaches server processes."""
    host_file = Path(host_file).resolve()
    prepared = set()
    for settings in json.loads(host_file.read_text())["mcpServers"].values():
        if settings.get("disabled", False) or Path(settings["command"]).name != "uv":
            continue
        args = settings.get("args", [])
        if args[:2] != ["run", "--project"] or args[3:5] != ["--locked", "--no-dev"]:
            raise CodexError("uv hosts must use run --project <path> --locked --no-dev <entrypoint>")
        cwd = (host_file.parent / settings.get("cwd", ".")).resolve()
        project = str((cwd / args[2]).resolve())
        if project not in prepared:
            run_process(
                [settings["command"], "sync", "--project", project, "--locked", "--no-dev"],
                "",
                os.environ.copy(),
                cwd,
                timeout=180,
            )
            prepared.add(project)
