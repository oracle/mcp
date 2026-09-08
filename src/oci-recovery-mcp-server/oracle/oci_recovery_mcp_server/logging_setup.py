"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Logging configuration and the structured event log used across the server.

Owns the root logging setup (rotating private file plus optional console) and
the redaction/summarisation rules every ``_log_event`` record goes through, so
no other module has to know how a payload is made safe to write down.
"""

import json
import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import oci

_STATE_DIR_ENV = "ORACLE_MCP_STATE_DIR"
_STATE_DIR_NAME = ".oci-recovery-mcp"

# Where logging actually ended up, reported at startup. Set by setup_logging().
_LOG_DESTINATION = "stderr"


def _state_dir() -> Path:
    """Per-user directory for this server's own state (logs, installation id).

    Deliberately outside the install tree: the package directory belongs to the
    installer, is read-only on a hardened deployment, and is discarded entirely
    between `uvx` runs -- which would silently throw away the logs an operator is
    told to read. Override with ORACLE_MCP_STATE_DIR when the home directory is
    not writable either.
    """
    configured = (os.getenv(_STATE_DIR_ENV) or "").strip()
    if configured:
        return Path(configured).expanduser()
    try:
        return Path.home() / _STATE_DIR_NAME
    except (RuntimeError, OSError):
        # Path.home() raises when the environment has no home directory at all,
        # which happens in minimal containers.
        return Path(tempfile.gettempdir()) / _STATE_DIR_NAME


def _resolved_log_file() -> str:
    """The log file this process writes to, before any fallback is applied."""
    log_dir = os.getenv("ORACLE_MCP_LOG_DIR") or str(_state_dir() / "logs")
    return os.path.abspath(
        os.getenv("ORACLE_MCP_LOG_FILE") or os.path.join(log_dir, "oci_recovery_mcp_server.log")
    )


class _PrivateRotatingFileHandler(RotatingFileHandler):
    """Rotating handler whose files are readable only by their owner.

    Tool arguments, and tool results at DEBUG, put a tenancy's resource inventory
    in this file. Rotation opens a new file each time, so the mode is applied on
    every open rather than once at setup.
    """

    def _open(self):
        """Open the next log file and tighten its mode to owner-only."""
        stream = super()._open()
        try:
            os.chmod(self.baseFilename, 0o600)
        except OSError:
            # An unchmod-able file (a mounted pipe, an exotic filesystem) is not
            # a reason to stop logging; the file just keeps its default mode.
            pass
        return stream


def setup_logging():
    """
    Configure root logging for the server: level, rotating file handler, console.

    Called once at import, before any tool runs. File logging is best effort --
    when the log file cannot be opened the server keeps running and falls back to
    stderr -- so a read-only or full filesystem never blocks startup.

    Environment:
    - ORACLE_MCP_LOG_LEVEL: root level (default INFO).
    - ORACLE_MCP_LOG_TO_STDOUT: add a console handler (writes to stderr, so it is
      safe under stdio transport). Forced on when file logging is unavailable.
    - ORACLE_SDK_LOG_LEVEL: level for the noisy ``oci`` logger (default WARNING).
    """
    global _LOG_DESTINATION

    # Resolve log level from env, default to INFO
    level_name = os.getenv("ORACLE_MCP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_to_stdout_env = os.getenv("ORACLE_MCP_LOG_TO_STDOUT")
    if log_to_stdout_env is None:
        os.environ["ORACLE_MCP_LOG_TO_STDOUT"] = "0"

    # Configure root logger once
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S%z",
    )

    # Add a rotating file handler if not already present for this file. File
    # logging is best-effort: a read-only filesystem, a directory owned by
    # another user, or a full disk must not stop the server from starting, so
    # the handler falls back to stderr instead of raising through the import.
    abs_log_file = _resolved_log_file()
    has_file = any(
        isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == abs_log_file
        for h in root_logger.handlers
    )
    file_error: Optional[OSError] = None
    if not has_file:
        try:
            os.makedirs(os.path.dirname(abs_log_file), exist_ok=True)
            fh = _PrivateRotatingFileHandler(
                abs_log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
        except OSError as error:
            file_error = error
        else:
            fh.setLevel(level)
            fh.setFormatter(formatter)
            root_logger.addHandler(fh)
            _LOG_DESTINATION = abs_log_file
    elif not file_error:
        _LOG_DESTINATION = abs_log_file

    # Console handler. Off by default so it can never interleave with the MCP
    # protocol on stdout; note StreamHandler writes to stderr, so enabling it is
    # safe for stdio transport too. Forced on when file logging was unavailable,
    # since otherwise the server would run with no diagnostics at all.
    console_requested = os.getenv("ORACLE_MCP_LOG_TO_STDOUT", "0").lower() in (
        "1",
        "true",
        "yes",
        "y",
    )
    if console_requested or file_error is not None:
        has_stream = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
            for h in root_logger.handlers
        )
        if not has_stream:
            sh = logging.StreamHandler()
            sh.setLevel(level)
            sh.setFormatter(formatter)
            root_logger.addHandler(sh)

    # Quiet noisy libraries by default; override with ORACLE_SDK_LOG_LEVEL
    logging.getLogger("oci").setLevel(os.getenv("ORACLE_SDK_LOG_LEVEL", "WARNING"))
    logging.getLogger("urllib3").setLevel("WARNING")

    if file_error is not None:
        _LOG_DESTINATION = "stderr"
        logging.getLogger(__name__).warning(
            "File logging is disabled: %s is not writable (%s). Logging to stderr instead; "
            "set ORACLE_MCP_LOG_DIR or ORACLE_MCP_STATE_DIR to a writable path.",
            abs_log_file,
            file_error,
        )


setup_logging()

logger = logging.getLogger(__name__)

# Exhaustive structured logging helpers

_LOG_MAX_VALUE_CHARS = int(os.getenv("ORACLE_MCP_LOG_MAX_VALUE_CHARS", "20000"))
_LOG_REDACT_KEYS = {
    k.strip().lower()
    for k in os.getenv(
        "ORACLE_MCP_LOG_REDACT_KEYS",
        (
            "authorization,token,security_token,security_token_file,private_key,key_file,"
            "passphrase,password,secret,client_secret"
        ),
    ).split(",")
    if k.strip()
}


def _truncate_str(s: str) -> str:
    """Cap a string at ORACLE_MCP_LOG_MAX_VALUE_CHARS, noting the original length."""
    if _LOG_MAX_VALUE_CHARS and len(s) > _LOG_MAX_VALUE_CHARS:
        return s[:_LOG_MAX_VALUE_CHARS] + f"...(truncated,len={len(s)})"
    return s


def _payload_summary(obj: Any) -> dict[str, Any]:
    """Describe a result without reproducing it.

    Logged at INFO in place of the payload itself: a tool result is a tenancy's
    resource inventory, and writing it to disk on every call is both a lot of
    volume and a lot of customer data at rest. The full value is still logged at
    DEBUG, which is what a support engineer turns on deliberately.
    """
    if obj is None:
        return {"type": "none"}
    if isinstance(obj, (list, tuple, set)):
        return {"type": "list", "count": len(obj)}
    if isinstance(obj, dict):
        return {"type": "dict", "keys": sorted(str(k) for k in obj)[:20]}
    if isinstance(obj, (bool, int, float, str)):
        return {"type": type(obj).__name__}
    return {"type": type(obj).__name__}


def _log_full_payloads() -> bool:
    """Whether DEBUG logging is on, and full payloads should be written out."""
    return logger.isEnabledFor(logging.DEBUG)


def _safe_jsonable(obj: Any) -> Any:
    """
    Convert an arbitrary value into something ``json.dumps`` can render.

    Walks containers recursively, redacting any key whose name matches
    _LOG_REDACT_KEYS, and unwraps OCI SDK models and pydantic models to plain
    dicts. Every conversion is best effort: a value that resists all of them
    degrades to a truncated ``repr``, and a value that raises becomes
    ``"<unserializable>"``, because logging must never fail a tool call.
    """
    try:
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return _truncate_str(obj) if isinstance(obj, str) else obj
        if isinstance(obj, (list, tuple)):
            return [_safe_jsonable(x) for x in obj]
        if isinstance(obj, dict):
            out: dict[str, Any] = {}
            for k, v in obj.items():
                key_l = str(k).lower()
                if any(rk in key_l for rk in _LOG_REDACT_KEYS):
                    out[str(k)] = "***REDACTED***"
                else:
                    out[str(k)] = _safe_jsonable(v)
            return out

        # OCI SDK & pydantic helpers
        try:
            if hasattr(oci, "util") and hasattr(oci.util, "to_dict"):
                d = oci.util.to_dict(obj)
                if isinstance(d, dict):
                    return _safe_jsonable(d)
        except Exception:
            pass

        if hasattr(obj, "model_dump"):
            try:
                return _safe_jsonable(obj.model_dump(exclude_none=False, by_alias=True))
            except Exception:
                pass
        if hasattr(obj, "dict"):
            try:
                return _safe_jsonable(obj.dict(exclude_none=False, by_alias=True))
            except Exception:
                pass
        if hasattr(obj, "__dict__"):
            try:
                return _safe_jsonable(dict(obj.__dict__))
            except Exception:
                pass

        return _truncate_str(repr(obj))
    except Exception:
        return "<unserializable>"


def _log_event(
    event: str,
    *,
    request_id: str,
    tool: Optional[str] = None,
    phase: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    level: int = logging.INFO,
):
    """
    Emit one structured log record as a single line of JSON.

    ``request_id`` correlates the record with the other events of the same tool
    call and with the ``opc-request-id`` sent to OCI. ``payload`` is passed through
    _safe_jsonable, so callers may hand it SDK objects directly. Falls back to a
    plain ``str`` rendering if the record will not serialize.
    """
    rec = {
        "event": event,
        "request_id": request_id,
        "tool": tool,
        "phase": phase,
        "payload": _safe_jsonable(payload or {}),
    }
    # Log as single-line JSON for easy grepping / ingestion
    try:
        logger.log(level, json.dumps(rec, ensure_ascii=False, default=str))
    except Exception:
        logger.log(level, str(rec))
