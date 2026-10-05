"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Request, actor and installation identifiers, and the call/tool log wrappers.

Everything here exists to make one OCI call traceable end to end: the
``opc-request-id`` stamped on outbound SDK calls, the pseudonymous per-installation
and per-caller markers embedded in it, and the decorators that log a tool
invocation and every SDK call it makes.
"""

import hashlib
import inspect
import logging
import os
import re
import time
import traceback
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Callable, Optional

from . import auth, logging_setup

_MCP_OPC_REQUEST_ID_PREFIX = "rcvmcp"
_MCP_INSTALLATION_ID_ENV = "ORACLE_MCP_INSTALLATION_ID"
_MCP_INSTALLATION_ID_FILE_ENV = "ORACLE_MCP_INSTALLATION_ID_FILE"
_MCP_INSTALLATION_ID_LENGTH = 8
_MCP_ACTOR_ID_LENGTH = 6
_MCP_REQUEST_ID_LENGTH = 6
_MCP_ACTOR_ID_CONTEXT: ContextVar[str] = ContextVar("mcp_actor_id", default="unknown")
_MCP_TOOL_ID_CONTEXT: ContextVar[str] = ContextVar("mcp_tool_id", default="unknown")
# The tool call's correlation id. _tool_logger sets it, and everything that runs inside
# the call -- the tool body, helpers, every OCI client -- reads it instead of minting its
# own, so the tool_call and oci_call events and the opc-request-id all share one id.
_MCP_REQUEST_ID_CONTEXT: ContextVar[Optional[str]] = ContextVar("mcp_request_id", default=None)
# Used only when a request is made outside an active FastMCP session. It is not
# persisted, so it cannot identify a person across server restarts.
_MCP_SERVER_INSTANCE_ID = uuid.uuid4().hex
_MCP_TOOL_CODES = {
    "list_protected_databases": "lpd",
    "get_protected_database": "gpd",
    "summarize_protected_database_health": "pdh",
    "summarize_protected_database_redo_status": "pdr",
    "summarize_backup_space_used": "bsu",
    "check_recovery_service_limits": "rsl",
    "fetch_regions_subscribed": "frs",
    "list_protection_policies": "lpp",
    "get_protection_policy": "gpp",
    "list_recovery_service_subnets": "lrs",
    "get_recovery_service_subnet": "grs",
    "get_recovery_service_metrics": "rmt",
    "list_databases": "ldb",
    "get_database": "gdb",
    "list_restore": "lwr",
    "list_backups": "lbk",
    "get_backup": "gbk",
    "summarize_protected_database_backup_destination": "pbd",
    "list_db_homes": "ldh",
    "get_db_home": "gdh",
    "list_db_systems": "lds",
    "get_db_system": "gds",
}


def _marker_fragment(value: str, length: int) -> str:
    """Return a fixed-width, lowercase base-36 pseudonym for an internal value."""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    number = int.from_bytes(hashlib.sha256(value.encode()).digest(), "big")
    chars: list[str] = []
    for _ in range(length):
        number, remainder = divmod(number, len(alphabet))
        chars.append(alphabet[remainder])
    return "".join(reversed(chars))


def _installation_id_file() -> Path:
    """Return the per-installation ID file, overridable for managed deployments."""
    configured = (os.getenv(_MCP_INSTALLATION_ID_FILE_ENV) or "").strip()
    if configured:
        return Path(configured).expanduser()
    return logging_setup._state_dir() / "installation-id"


def _current_request_id() -> str:
    """The active tool call's request id, or a fresh one outside a tool call."""
    return _MCP_REQUEST_ID_CONTEXT.get() or uuid.uuid4().hex


def _mcp_installation_id() -> str:
    """Return a durable opaque ID for this local install or hosted deployment."""
    configured = (os.getenv(_MCP_INSTALLATION_ID_ENV) or "").strip()
    if configured:
        return _marker_fragment(configured, _MCP_INSTALLATION_ID_LENGTH)

    id_file = _installation_id_file()
    try:
        persisted = id_file.read_text(encoding="utf-8").strip()
    except OSError:
        persisted = ""
    if persisted:
        return _marker_fragment(persisted, _MCP_INSTALLATION_ID_LENGTH)

    generated = uuid.uuid4().hex
    try:
        id_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(id_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(f"{generated}\n")
    except FileExistsError:
        try:
            generated = id_file.read_text(encoding="utf-8").strip() or generated
        except OSError:
            pass
    except OSError:
        # An unwritable home/state directory must not stop a tool call. This
        # fallback remains stable for the current server process only.
        generated = _MCP_SERVER_INSTANCE_ID
    return _marker_fragment(generated, _MCP_INSTALLATION_ID_LENGTH)


def _mcp_actor_id() -> str:
    """
    Return a pseudonymous identifier for the active MCP user/session.

    Pseudonymous, not anonymous: it is a truncated hash of the caller's identity, so
    it stays stable per caller and anyone who already knows that identity can
    recompute it. What it does is keep the raw identity (an IDCS ``sub`` is often a
    username or email) out of ``opc-request-id``, a value that gets copied into logs
    and support tickets. It hides nothing from OCI, which authenticates the same
    caller from the credentials signing every request that carries it.
    """
    principal = None
    scope = None
    access_token = auth._current_access_token()
    if access_token is not None:
        claims = getattr(access_token, "claims", None) or {}
        # Some OAuth providers omit sub from the access token. The token jti
        # still provides an opaque, authenticated session identifier.
        principal = claims.get("sub") or claims.get("jti")
        # The issuer identifies the IAM domain this deployment authenticates
        # against, which scopes the pseudonym without naming the user.
        scope = claims.get("iss")

    if not principal:
        # For session/API-key deployments, OCI credentials identify the server
        # account, not the MCP caller. Prefer FastMCP's per-client session so
        # users sharing one configured server remain distinguishable.
        try:
            from fastmcp.server.dependencies import get_context

            principal = get_context().session_id
            scope = scope or "mcp-session"
        except Exception:
            principal = None

    if not principal:
        # Direct SDK use can occur outside a FastMCP request context. Retain a
        # stable server-account pseudonym when a local OCI config is available.
        try:
            config = auth._load_oci_config_for_server()
            principal = config.get("user")
            scope = scope or config.get("tenancy")
        except Exception:
            principal = _MCP_SERVER_INSTANCE_ID
            scope = "mcp-server"
    return _marker_fragment(f"{scope or ''}:{principal}", _MCP_ACTOR_ID_LENGTH)


def _mcp_opc_request_id(value: Optional[str]) -> str:
    """Return a 32-character OCI request ID with MCP telemetry markers.

    OCI services preserve only the first 32 characters before appending their
    own request-id segments. Keep all telemetry fields inside that prefix.
    """
    request_id = str(value or uuid.uuid4().hex)
    if re.fullmatch(r"rcvmcp-[0-9a-z]{8}-[0-9a-z]{6}-[0-9a-z]{3}[0-9a-z]{6}", request_id):
        return request_id
    installation_id = _mcp_installation_id()
    actor_id = _MCP_ACTOR_ID_CONTEXT.get()[:_MCP_ACTOR_ID_LENGTH].ljust(_MCP_ACTOR_ID_LENGTH, "0")
    tool_code = _MCP_TOOL_CODES.get(_MCP_TOOL_ID_CONTEXT.get(), "unk")
    request_code = _marker_fragment(request_id, _MCP_REQUEST_ID_LENGTH)
    return f"{_MCP_OPC_REQUEST_ID_PREFIX}-{installation_id}-{actor_id}-{tool_code}{request_code}"


def _operation_supports_opc_request_id(operation: Callable[..., Any]) -> bool:
    """Return whether an OCI SDK operation accepts ``opc_request_id``."""
    try:
        return '"opc_request_id"' in inspect.getsource(operation)
    except (OSError, TypeError):
        return False


def _install_opc_request_id_fallback(client: Any, request_id: str) -> None:
    """Mark generated OCI SDK calls that do not expose an ``opc_request_id`` kwarg."""
    base_client = getattr(client, "base_client", None)
    call_api = getattr(base_client, "call_api", None)
    if base_client is None or not callable(call_api):
        return

    marker = _mcp_opc_request_id(request_id)

    def _call_api(*args, **kwargs):
        """Stand in for ``BaseClient.call_api`` and stamp the request-id header."""
        # Generated OCI operations pass header_params to BaseClient.call_api. Adding
        # the header here avoids unsupported operation kwargs and does not enable
        # the SDK's process-wide request-id propagation state.
        call_kwargs = dict(kwargs)
        headers = dict(call_kwargs.get("header_params") or {})
        headers["opc-request-id"] = _mcp_opc_request_id(headers.get("opc-request-id") or marker)
        call_kwargs["header_params"] = headers
        return call_api(*args, **call_kwargs)

    base_client.call_api = _call_api


def _wrap_oci_client(client: Any, *, request_id: str, client_name: str):
    """Proxy that marks and logs every OCI SDK method call and response summary."""
    _install_opc_request_id_fallback(client, request_id)

    class _Proxy:
        """Attribute-forwarding wrapper around one OCI SDK client."""

        def __init__(self, inner: Any):
            """Wrap ``inner`` and start an empty per-method opc_request_id support cache."""
            self._inner = inner
            self._opc_request_id_support: dict[str, bool] = {}

        def __getattr__(self, name: str):
            """
            Return non-callables untouched; wrap SDK operations in a logging shim.

            Whether an operation accepts an ``opc_request_id`` kwarg is decided by reading
            its source, which is expensive, so the answer is cached per method name.
            """
            attr = getattr(self._inner, name)
            if not callable(attr):
                return attr
            if name not in self._opc_request_id_support:
                self._opc_request_id_support[name] = _operation_supports_opc_request_id(
                    getattr(attr, "__func__", attr)
                )
            supports_opc_request_id = self._opc_request_id_support[name]

            def _call(*args, **kwargs):
                """
                Invoke the SDK operation, logging start, end and error events.

                Response metadata (status, headers, paging) is logged at INFO; the response
                body follows the same rule as tool results -- its shape at INFO, its content
                only at DEBUG. Exceptions are logged with a traceback and re-raised.
                """
                kwargs = dict(kwargs)
                if supports_opc_request_id:
                    kwargs["opc_request_id"] = _mcp_opc_request_id(kwargs.get("opc_request_id") or request_id)
                start = time.time()
                logging_setup._log_event(
                    "oci_call",
                    request_id=request_id,
                    tool=None,
                    phase="start",
                    payload={
                        "client": client_name,
                        "method": name,
                        "args": logging_setup._safe_jsonable(args),
                        "kwargs": logging_setup._safe_jsonable(kwargs),
                    },
                )
                try:
                    resp = attr(*args, **kwargs)
                    dur_ms = int((time.time() - start) * 1000)
                    # Response object may be oci.response.Response or other
                    payload = {
                        "client": client_name,
                        "method": name,
                        "duration_ms": dur_ms,
                    }
                    try:
                        payload["status"] = getattr(resp, "status", None)
                        payload["headers"] = getattr(resp, "headers", None)
                        payload["request_id"] = getattr(resp, "request_id", None)
                        payload["opc_request_id"] = getattr(resp, "opc_request_id", None)
                        payload["has_next_page"] = getattr(resp, "has_next_page", None)
                        payload["next_page"] = getattr(resp, "next_page", None)
                    except Exception:
                        pass
                    # Response bodies carry the same customer data as tool results,
                    # so they follow the same rule: shape at INFO, body at DEBUG.
                    try:
                        data = getattr(resp, "data", resp)
                        payload["data_summary"] = logging_setup._payload_summary(data)
                        if logging_setup._log_full_payloads():
                            payload["data"] = logging_setup._safe_jsonable(data)
                    except Exception:
                        payload["data_summary"] = {"type": "unavailable"}
                    logging_setup._log_event(
                        "oci_call",
                        request_id=request_id,
                        tool=None,
                        phase="end",
                        payload=payload,
                    )
                    return resp
                except Exception as e:
                    dur_ms = int((time.time() - start) * 1000)
                    logging_setup._log_event(
                        "oci_call",
                        request_id=request_id,
                        tool=None,
                        phase="error",
                        payload={
                            "client": client_name,
                            "method": name,
                            "duration_ms": dur_ms,
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        },
                        level=logging.ERROR,
                    )
                    raise

            return _call

    return _Proxy(client)


def _tool_logger(tool_name: str):
    """
    Decorator to log MCP tool inputs/outputs/errors with a correlation id.

    IMPORTANT (FastMCP constraint):
    FastMCP tool functions must NOT use *args or **kwargs in their signature.
    So this decorator MUST preserve the original function signature.

    We therefore wrap by delegating with the original signature via ParamSpec.
    """
    from functools import wraps
    from typing import ParamSpec, TypeVar

    P = ParamSpec("P")
    R = TypeVar("R")

    def _decorator(fn: Callable[P, R]) -> Callable[P, R]:
        """Wrap one tool function, preserving its signature for FastMCP."""

        @wraps(fn)
        def _wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            """Log the call's start, end and any error, then return the tool's result."""
            request_id = uuid.uuid4().hex
            start = time.time()
            request_id_token = _MCP_REQUEST_ID_CONTEXT.set(request_id)
            actor_id_token = _MCP_ACTOR_ID_CONTEXT.set(_mcp_actor_id())
            tool_id_token = _MCP_TOOL_ID_CONTEXT.set(tool_name)
            logging_setup._log_event(
                "tool_call",
                request_id=request_id,
                tool=tool_name,
                phase="start",
                payload={
                    "args": logging_setup._safe_jsonable(args),
                    "kwargs": logging_setup._safe_jsonable(kwargs),
                },
            )
            try:
                out = fn(*args, **kwargs)
                dur_ms = int((time.time() - start) * 1000)
                end_payload: dict[str, Any] = {
                    "duration_ms": dur_ms,
                    "result_summary": logging_setup._payload_summary(out),
                }
                if logging_setup._log_full_payloads():
                    end_payload["result"] = logging_setup._safe_jsonable(out)
                logging_setup._log_event(
                    "tool_call",
                    request_id=request_id,
                    tool=tool_name,
                    phase="end",
                    payload=end_payload,
                )
                return out
            except Exception as e:
                dur_ms = int((time.time() - start) * 1000)
                logging_setup._log_event(
                    "tool_call",
                    request_id=request_id,
                    tool=tool_name,
                    phase="error",
                    payload={
                        "duration_ms": dur_ms,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    },
                    level=logging.ERROR,
                )
                raise
            finally:
                _MCP_TOOL_ID_CONTEXT.reset(tool_id_token)
                _MCP_ACTOR_ID_CONTEXT.reset(actor_id_token)
                _MCP_REQUEST_ID_CONTEXT.reset(request_id_token)

        return _wrapped

    return _decorator
