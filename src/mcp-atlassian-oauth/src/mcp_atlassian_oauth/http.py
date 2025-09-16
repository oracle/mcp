from __future__ import annotations

import asyncio
import json
import os
import uuid
import logging
from logging.handlers import RotatingFileHandler
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from starlette.requests import ClientDisconnect

# Use domain modules directly to avoid FastMCP decorator objects in HTTP path
from .jira import api as jira_api
from .jira import search as jira_search
from .utils.query import substitute_current_user, inject_default_project, inject_default_space
from .confluence import api as conf_api
from .auth import authed_fetch, conf_state_from_env
from .config import set_defaults as set_defaults_fn, defaults_as_dict
from .resources.registry import parse_uri
from .jira import resources as jira_res
from .confluence import resources as conf_res
from . import __version__ as PKG_VERSION

# Lightweight wrappers (mirror logic from server tools)

async def _jira_get_myself_http() -> str:
    st, _, body = jira_api.get_myself()
    if st != 200:
        raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
    return body.decode("utf-8")

async def _jira_search_issues_http(
    jql: str,
    fields: Optional[List[str]] = None,
    maxResults: int = 50,
    startAt: int = 0,
) -> str:
    j = substitute_current_user(str(jql))
    j = inject_default_project(j)
    st, _, body = jira_api.search_issues(j, fields=fields, max_results=int(maxResults), start_at=int(startAt))
    if st != 200:
        raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
    return body.decode("utf-8")

async def _jira_get_issue_http(issueKey: str) -> str:
    st, _, body = jira_api.get_issue(str(issueKey))
    if st != 200:
        raise RuntimeError(f"Jira {st}: {body.decode('utf-8', 'ignore')}")
    return body.decode("utf-8")

async def _jira_add_comment_http(issueKey: str, body: str) -> str:
    st, _, resp = jira_api.add_comment(str(issueKey), str(body))
    if st not in (200, 201):
        raise RuntimeError(f"Jira {st}: {resp.decode('utf-8', 'ignore')}")
    return resp.decode("utf-8")

async def _jira_find_similar_http(
    issueKey: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    project: Optional[str] = None,
    maxResults: int = 20,
    includeClosed: bool = True,
    excludeSelf: bool = True,
    mode: str = "heuristic",
    modelName: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> dict:
    if not (issueKey or title or description):
        raise RuntimeError("Provide at least one of: issueKey, title, description")
    return jira_search.find_similar(
        issue_key=str(issueKey) if issueKey else None,
        title=str(title) if title else None,
        description=str(description) if description else None,
        project=str(project) if project else None,
        max_results=int(maxResults),
        include_closed=bool(includeClosed),
        exclude_self=bool(excludeSelf),
        mode=str(mode),
        model_name=str(modelName),
    )

async def _conf_get_server_info_http() -> str:
    st, _, body = conf_api.get_server_info()
    if st != 200:
        s2, _, _ = authed_fetch(conf_state_from_env(), "/", "GET")
        return f"systemInfo: {st}; root: {s2}"
    return body.decode("utf-8")

async def _conf_get_page_http(pageId: str) -> str:
    st, _, body = conf_api.get_page(str(pageId))
    if st != 200:
        raise RuntimeError(f"Confluence {st}: {body.decode('utf-8', 'ignore')}")
    return body.decode("utf-8")

async def _conf_search_cql_http(cql: str, limit: int = 25) -> str:
    cq = inject_default_space(substitute_current_user(str(cql)))
    st, _, body = conf_api.cql_search(cql=cq, limit=int(limit), start=0)
    if st != 200:
        raise RuntimeError(f"Confluence {st}: {body.decode('utf-8', 'ignore')}")
    return body.decode("utf-8")

async def _set_defaults_http(
    preferredUser: Optional[str] = None,
    jiraProject: Optional[str] = None,
    confSpace: Optional[str] = None,
    outputFormat: Optional[str] = None,
    show: bool = False,
) -> dict:
    if not bool(show):
        set_defaults_fn(
            preferred_user=str(preferredUser) if preferredUser is not None else None,
            jira_project=str(jiraProject) if jiraProject is not None else None,
            conf_space=str(confSpace) if confSpace is not None else None,
            output_format=str(outputFormat) if outputFormat is not None else None,
        )
    return defaults_as_dict()


# ------------------------------------------------------------------------------
# Outbound HTTP helper (used by auth/api layers)
# ------------------------------------------------------------------------------

def _resolve_verify() -> bool | str:
    """
    Determine TLS verification behavior from environment:
      - MCP_SSL_VERIFY=false  -> disable verification
      - MCP_CA_BUNDLE=/path   -> use custom CA bundle
      - default               -> verify=True
    """
    verify_env = (os.getenv("MCP_SSL_VERIFY") or "").strip().lower()
    if verify_env in {"0", "false", "no"}:
        return False
    ca_bundle = os.getenv("MCP_CA_BUNDLE")
    if ca_bundle:
        return ca_bundle
    return True


def _resolve_trust_env() -> bool:
    """
    Decide if httpx should honor environment proxies (HTTP(S)_PROXY, NO_PROXY).
    MCP_HTTP_TRUST_ENV=false disables using proxy env automatically.
    Defaults to True.
    """
    v = (os.getenv("MCP_HTTP_TRUST_ENV") or "").strip().lower()
    if v in {"0", "false", "no"}:
        return False
    return True


def _env_proxy_summary() -> str:
    hp = os.getenv("HTTP_PROXY") or os.getenv("http_proxy") or ""
    hps = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy") or ""
    np = os.getenv("NO_PROXY") or os.getenv("no_proxy") or ""
    parts = []
    if hp:
        parts.append(f"HTTP_PROXY={hp}")
    if hps:
        parts.append(f"HTTPS_PROXY={hps}")
    if np:
        parts.append(f"NO_PROXY={np}")
    return "; ".join(parts) if parts else "none"


def http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None,
    timeout: float = 30.0,
) -> Tuple[int, str, bytes]:
    """
    Minimal HTTP helper for outbound calls (e.g., Atlassian APIs).

    Returns:
      (status_code, content_type_header or "", body_bytes)
    """
    verify = _resolve_verify()
    trust_env = _resolve_trust_env()
    headers = dict(headers or {})

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("[HTTP->] %s %s verify=%s trust_env=%s proxies_env=%s", method.upper(), url, verify, trust_env, _env_proxy_summary())

    try:
        with httpx.Client(timeout=timeout, verify=verify, http2=False, trust_env=trust_env) as client:
            resp = client.request(method.upper(), url, headers=headers, content=data)
            status = resp.status_code
            ctype = resp.headers.get("Content-Type", "") or ""
            body = resp.content or b""
            return status, ctype, body
    except httpx.HTTPError as e:
        # Return a synthetic 599 status on network errors to keep the tuple contract
        return 599, "text/plain", str(e).encode("utf-8", errors="replace")


# ------------------------------------------------------------------------------
# Logging (LOG_LEVEL, LOG_FILE/MCP_LOG_FILE) for HTTP adapter
# ------------------------------------------------------------------------------

logger = logging.getLogger("atlassian.oauth.http")
_level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
_level = getattr(logging, _level_name, logging.INFO)
logging.basicConfig(level=_level)
logger.setLevel(_level)

_log_file = os.environ.get("LOG_FILE") or os.environ.get("MCP_LOG_FILE")
if _log_file:
    try:
        _fh = RotatingFileHandler(_log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
        _fh.setLevel(_level)
        _fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
            logger.addHandler(_fh)
    except Exception as _e:
        logger.warning("Failed to attach file logger: %s", _e)


def _debug_payload(prefix: str, payload: Any) -> None:
    if not logger.isEnabledFor(logging.DEBUG):
        return
    try:
        s = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload)
        txt = s[:4000]
        if len(s) > 4000:
            txt += "…(truncated)"
        logger.debug("%s %s", prefix, txt)
    except Exception:
        pass


# ------------------------------------------------------------------------------
# Tool registry (schema + description) for tools/list
# ------------------------------------------------------------------------------

TOOLS: List[Dict[str, Any]] = [
    {
        "name": "jira_get_myself",
        "description": "GET /rest/api/latest/myself",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "jira_search_issues",
        "description": "Search Jira by JQL",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jql": {"type": "string"},
                "fields": {"type": "array", "items": {"type": "string"}},
                "maxResults": {"type": "number"},
                "startAt": {"type": "number"},
            },
            "required": ["jql"],
        },
    },
    {
        "name": "jira_get_issue",
        "description": "Get issue by key",
        "inputSchema": {
            "type": "object",
            "properties": {"issueKey": {"type": "string"}},
            "required": ["issueKey"],
        },
    },
    {
        "name": "jira_add_comment",
        "description": "Add comment to issue",
        "inputSchema": {
            "type": "object",
            "properties": {"issueKey": {"type": "string"}, "body": {"type": "string"}},
            "required": ["issueKey", "body"],
        },
    },
    {
        "name": "jira_find_similar",
        "description": "Find related Jira issues by key or free text using heuristic/semantic search",
        "inputSchema": {
            "type": "object",
            "properties": {
                "issueKey": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "project": {"type": "string"},
                "maxResults": {"type": "number"},
                "includeClosed": {"type": "boolean"},
                "excludeSelf": {"type": "boolean"},
                "mode": {"type": "string", "enum": ["heuristic", "semantic", "hybrid"]},
                "modelName": {"type": "string"},
            },
        },
    },
    {
        "name": "conf_get_server_info",
        "description": "GET /rest/api/latest/settings/systemInfo (fallback to /)",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "conf_get_page",
        "description": "Get Confluence page by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"pageId": {"type": "string"}},
            "required": ["pageId"],
        },
    },
    {
        "name": "conf_search_cql",
        "description": "Search Confluence using CQL",
        "inputSchema": {
            "type": "object",
            "properties": {"cql": {"type": "string"}, "limit": {"type": "number"}},
            "required": ["cql"],
        },
    },
    {
        "name": "set_defaults",
        "description": "Set or view runtime defaults for preferred user, Jira project, and Confluence space. Returns current defaults.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "preferredUser": {"type": "string"},
                "jiraProject": {"type": "string"},
                "confSpace": {"type": "string"},
                "outputFormat": {"type": "string", "enum": ["markdown", "json", "storage"]},
                "show": {"type": "boolean"},
            },
        },
    },
]

# Map names to callables
TOOL_IMPLS: Dict[str, Any] = {
    "jira_get_myself": _jira_get_myself_http,
    "jira_search_issues": _jira_search_issues_http,
    "jira_get_issue": _jira_get_issue_http,
    "jira_add_comment": _jira_add_comment_http,
    "jira_find_similar": _jira_find_similar_http,
    "conf_get_server_info": _conf_get_server_info_http,
    "conf_get_page": _conf_get_page_http,
    "conf_search_cql": _conf_search_cql_http,
    "set_defaults": _set_defaults_http,
}


# ------------------------------------------------------------------------------
# JSON-RPC handlers + dispatcher
# ------------------------------------------------------------------------------

def _ok_result(id_: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err_result(id_: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


async def _handle_initialize(msg: Dict[str, Any]) -> Dict[str, Any]:
    id_ = msg.get("id")
    params = msg.get("params") or {}
    proto = params.get("protocolVersion") or "2024-11-05"
    result = {
        "protocolVersion": proto,
        "serverInfo": {"name": "atlassian.oauth", "version": PKG_VERSION},
        "capabilities": {
            "tools": {},
            "resources": {},
        },
    }
    return _ok_result(id_, result)


async def _handle_tools_list(msg: Dict[str, Any]) -> Dict[str, Any]:
    id_ = msg.get("id")
    return _ok_result(id_, {"tools": TOOLS})


def _normalize_content(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, str):
        return [{"type": "text", "text": value}]
    try:
        return [{"type": "text", "text": json.dumps(value, indent=2)}]
    except Exception:
        return [{"type": "text", "text": str(value)}]


async def _handle_tools_call(msg: Dict[str, Any]) -> Dict[str, Any]:
    id_ = msg.get("id")
    params = msg.get("params") or {}
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if not name or name not in TOOL_IMPLS:
        return _err_result(id_, -32601, f"Unknown tool: {name}")

    try:
        impl = TOOL_IMPLS[name]
        if asyncio.iscoroutinefunction(impl):
            value = await impl(**arguments)
        else:
            value = impl(**arguments)
        content = _normalize_content(value)
        return _ok_result(id_, {"content": content, "isError": False})
    except Exception as e:
        return _ok_result(id_, {"content": [{"type": "text", "text": str(e)}], "isError": True})


async def _handle_resources_list(msg: Dict[str, Any]) -> Dict[str, Any]:
    id_ = msg.get("id")
    params = msg.get("params") or {}
    uri = params.get("uri")
    if not uri:
        resources = [{"uri": "jira://", "name": "Jira"}, {"uri": "confluence://", "name": "Confluence"}]
        return _ok_result(id_, {"resources": resources})

    scheme, _, _, _ = parse_uri(uri)
    if scheme == "jira":
        items = await jira_res.list_resources(uri)
    elif scheme == "confluence":
        items = await conf_res.list_resources(uri)
    else:
        items = []
    return _ok_result(id_, {"resources": items})


async def _handle_resources_read(msg: Dict[str, Any]) -> Dict[str, Any]:
    id_ = msg.get("id")
    params = msg.get("params") or {}
    uri = params.get("uri")
    if not uri:
        return _err_result(id_, -32602, "Missing uri")
    scheme, _, _, _ = parse_uri(uri)
    if scheme == "jira":
        contents = await jira_res.read_resource(uri)
    elif scheme == "confluence":
        contents = await conf_res.read_resource(uri)
    else:
        contents = []
    return _ok_result(id_, {"contents": contents})


async def _dispatch(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        if "method" in msg:
            method = msg.get("method")
            _debug_payload("[HTTP->MCP] JSON-RPC", msg)
            if method == "initialize":
                return await _handle_initialize(msg)
            if method == "notifications/initialized":
                return None
            if method == "tools/list":
                return await _handle_tools_list(msg)
            if method == "tools/call":
                return await _handle_tools_call(msg)
            if method == "resources/list":
                return await _handle_resources_list(msg)
            if method == "resources/read":
                return await _handle_resources_read(msg)
            return _err_result(msg.get("id"), -32601, f"Unknown method: {method}")
        elif "result" in msg or "error" in msg:
            return None
        else:
            return _err_result(msg.get("id"), -32600, "Invalid Request")
    except Exception as e:
        return _err_result(msg.get("id"), -32000, f"Server error: {str(e)}")


# ------------------------------------------------------------------------------
# FastAPI app with streamable POST /mcp (NDJSON or concatenated JSON)
# ------------------------------------------------------------------------------

def create_app(path: str = "/mcp") -> FastAPI:
    app = FastAPI(title="Atlassian OAuth MCP (fastmcp) — HTTP")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    normalized_path = path if path.startswith("/") else ("/" + path)

    @app.options(normalized_path)
    async def options_handler() -> Response:
        return Response(status_code=204)

    @app.post(normalized_path)
    async def mcp_stream(request: Request) -> StreamingResponse:
        req_id = uuid.uuid4().hex[:8]
        client = request.client
        logger.info("[HTTP] Incoming POST stream: %s %s req=%s from=%s", request.method, request.url.path, req_id, f"{client.host}:{client.port}" if client else "?")
        logger.debug("[HTTP] req=%s content-type=%s content-length=%s", req_id, request.headers.get("content-type"), request.headers.get("content-length"))

        ctype_hdr = (request.headers.get("content-type") or "").lower()
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }

        # Fast-path for single JSON request bodies (non-streaming clients)
        if "application/json" in ctype_hdr:
            try:
                body_bytes = await request.body()
                text = (body_bytes or b"").decode("utf-8", errors="ignore").strip()
            except Exception:
                text = ""

            responses: List[str] = []
            if text:
                try:
                    obj = json.loads(text)
                    # Accept array-of-messages or single object
                    if isinstance(obj, list):
                        for item in obj:
                            resp = await _dispatch(item)
                            if resp is not None:
                                _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                                responses.append(json.dumps(resp))
                    else:
                        resp = await _dispatch(obj)
                        if resp is not None:
                            _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                            responses.append(json.dumps(resp))
                except Exception:
                    # Malformed JSON → return nothing (client may retry)
                    pass

            async def _oneshot() -> AsyncGenerator[bytes, None]:
                for line in responses:
                    data = (line + "\n").encode("utf-8")
                    logger.info("[HTTP] Streaming %d bytes req=%s", len(data), req_id)
                    yield data

            return StreamingResponse(_oneshot(), headers=headers, media_type="application/json")

        # Streaming path for NDJSON/concatenated JSON
        outbound_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        async def _read_and_dispatch():
            from json import JSONDecoder, JSONDecodeError
            text_buf: str = ""
            decoder = JSONDecoder()

            try:
                async for chunk in request.stream():
                    if not chunk:
                        continue
                    try:
                        part = chunk.decode("utf-8")
                    except Exception:
                        continue
                    text_buf += part

                    # 1) NDJSON lines
                    while "\n" in text_buf:
                        line, text_buf = text_buf.split("\n", 1)
                        s = line.strip()
                        if not s:
                            continue
                        try:
                            obj = json.loads(s)
                        except Exception:
                            continue
                        # Handle arrays of messages as well as single objects
                        if isinstance(obj, list):
                            for item in obj:
                                resp = await _dispatch(item)
                                if resp is not None:
                                    _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                                    await outbound_queue.put(json.dumps(resp))
                        else:
                            resp = await _dispatch(obj)
                            if resp is not None:
                                _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                                await outbound_queue.put(json.dumps(resp))

                    # 2) Concatenated JSON
                    while True:
                        s = text_buf.lstrip()
                        if not s:
                            break
                        try:
                            obj, idx = decoder.raw_decode(s)
                        except JSONDecodeError:
                            break
                        consumed = len(text_buf) - len(s) + idx
                        text_buf = text_buf[consumed:]
                        # Handle arrays of messages as well as single objects
                        if isinstance(obj, list):
                            for item in obj:
                                resp = await _dispatch(item)
                                if resp is not None:
                                    _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                                    await outbound_queue.put(json.dumps(resp))
                        else:
                            resp = await _dispatch(obj)
                            if resp is not None:
                                _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                                await outbound_queue.put(json.dumps(resp))

            except ClientDisconnect:
                logger.info("[HTTP] Client disconnected while streaming request body req=%s", req_id)
            except asyncio.CancelledError:
                logger.info("[HTTP] Reader task cancelled req=%s", req_id)
                raise
            except Exception as e:
                logger.warning("[HTTP] Reader error req=%s: %s", req_id, e)

            # Flush any remaining buffer at EOF
            s = text_buf.strip()
            if s:
                try:
                    obj = json.loads(s)
                    # Handle arrays of messages as well as single objects
                    if isinstance(obj, list):
                        for item in obj:
                            resp = await _dispatch(item)
                            if resp is not None:
                                _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                                await outbound_queue.put(json.dumps(resp))
                    else:
                        resp = await _dispatch(obj)
                        if resp is not None:
                            _debug_payload("[MCP->HTTP] JSON-RPC", resp)
                            await outbound_queue.put(json.dumps(resp))
                except Exception:
                    pass

            # Signal end of stream
            await outbound_queue.put(None)

        async def _response_generator() -> AsyncGenerator[bytes, None]:
            try:
                while True:
                    item = await outbound_queue.get()
                    if item is None:
                        break
                    data = (item + "\n").encode("utf-8")
                    logger.info("[HTTP] Streaming %d bytes req=%s", len(data), req_id)
                    yield data
            except asyncio.CancelledError:
                pass

        reader_task = asyncio.create_task(_read_and_dispatch(), name=f"mcp_reader_{req_id}")

        async def _wrapped_generator() -> AsyncGenerator[bytes, None]:
            try:
                async for chunk in _response_generator():
                    yield chunk
            finally:
                if not reader_task.done():
                    reader_task.cancel()
                    try:
                        await reader_task
                    except asyncio.CancelledError:
                        pass
                    except Exception:
                        pass

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        # Important: Cline expects application/json for streamableHttp
        return StreamingResponse(_wrapped_generator(), headers=headers, media_type="application/json")

    return app
