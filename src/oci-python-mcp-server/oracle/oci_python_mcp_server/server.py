"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Generic OCI MCP server: an RPC endpoint for the OCI Python SDK.

The agent writes a straight-line OCI SDK script and sends it to `oci_exec`.
The server parses and tree-walks it. It never calls exec/eval. Only literals,
variables, subscripts on returned data, inline model constructors, and
dispatched calls are evaluated. The dispatched call is the only effect that
leaves the box, gated by OCI_MCP_ENABLE_MUTATIONS for writes. The SDK surface
is discovered by reflection at startup.
"""

import ast
import difflib
import importlib
import inspect
import os
import pkgutil

import oci
from fastmcp import FastMCP

from . import __project__

READ_PREFIXES = ("list_", "get_", "head_")


def _discover():
    """Reflect over the installed SDK once: every service client and model class."""
    clients, models = {}, {}
    for info in pkgutil.iter_modules(oci.__path__):
        try:
            mod = importlib.import_module(f"oci.{info.name}")
        except Exception:
            continue
        for name, obj in inspect.getmembers(mod, inspect.isclass):
            if name.endswith("Client"):
                clients[(info.name, name)] = obj
        mm = getattr(mod, "models", None)
        if mm is not None:
            models[info.name] = dict(inspect.getmembers(mm, inspect.isclass))
    return clients, models


CLIENTS, MODELS = _discover()

BY_CLIENT: dict = {}
for _s, _c in CLIENTS:
    BY_CLIENT.setdefault(_c, []).append(_s)


def _ops(cls):
    names = {
        n for n, _ in inspect.getmembers(cls, inspect.isfunction) if not n.startswith("_")
    }
    writes = {n for n in names if not n.startswith(READ_PREFIXES)}
    return names, writes


OPS = {key: _ops(cls) for key, cls in CLIENTS.items()}
_cache: dict = {}


def mutations_enabled() -> bool:
    return os.environ.get("OCI_MCP_ENABLE_MUTATIONS") == "1"


def _auth():
    try:
        return {}, {"signer": oci.auth.signers.InstancePrincipalsSecurityTokenSigner()}
    except Exception:
        return oci.config.from_file(), {}


def _client(service, client):
    key = (service, client)
    if key not in _cache:
        config, kwargs = _auth()
        _cache[key] = CLIENTS[key](config, **kwargs)
    return _cache[key]


def _resolve(client, service):
    """Return (key, None) on success, else (None, error dict). Infer service."""
    if service:
        key = (service, client)
        return (key, None) if key in CLIENTS else (
            None,
            {
                "error": "UnknownClient",
                "message": f"no {service}.{client}",
                "did_you_mean": difflib.get_close_matches(client, BY_CLIENT, n=5),
            },
        )
    hits = BY_CLIENT.get(client, [])
    if len(hits) == 1:
        return (hits[0], client), None
    if len(hits) > 1:
        return None, {
            "error": "AmbiguousClient",
            "message": f"{client} exists in {hits}; pass service=",
            "services": hits,
        }
    return None, {
        "error": "UnknownClient",
        "message": f"no client named {client}",
        "did_you_mean": difflib.get_close_matches(client, BY_CLIENT, n=5),
    }


MAX_CODE = 40000
MAX_STMTS = 200
MAX_CALLS = 50
_UNSET = object()


class OciCodeError(Exception):
    def __init__(self, kind, message, extra=None):
        super().__init__(message)
        self.kind, self.extra = kind, extra or {}


class Pending:
    """A model construction materialized against the dispatch target service."""

    __slots__ = ("name", "kwargs", "service")

    def __init__(self, name, kwargs, service):
        self.name, self.kwargs, self.service = name, kwargs, service


def _is_model(cls):
    m = getattr(cls, "__module__", "")
    return m.startswith("oci.") and ".models" in m


def _dotted_name(node):
    """Return dotted Name/Attribute parts. Reject underscore/dunder attributes."""
    parts = []
    while isinstance(node, ast.Attribute):
        if node.attr.startswith("_"):
            raise OciCodeError(
                "DisallowedCode",
                "access to underscore/dunder attributes is not allowed",
            )
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return None


def _resolve_client_expr(node):
    """Read the client from a call head or a ClientClass(config) constructor."""
    if isinstance(node, ast.Call):
        node = node.func
    parts = _dotted_name(node)
    if not parts:
        return None, None
    svc = parts[1] if len(parts) >= 2 and parts[0] == "oci" else None
    return parts[-1], svc


def _eval(node, env, dispatch):
    """Evaluate one expression in the accepted straight-line subset."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise OciCodeError("NameError", f"'{node.id}' is not defined")
    if isinstance(node, (ast.List, ast.Tuple)):
        vals = [_eval(e, env, dispatch) for e in node.elts]
        return vals if isinstance(node, ast.List) else tuple(vals)
    if isinstance(node, ast.Dict):
        return {
            _eval(k, env, dispatch): _eval(v, env, dispatch)
            for k, v in zip(node.keys, node.values)
        }
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _eval(node.operand, env, dispatch)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return -v if isinstance(node.op, ast.USub) else +v
        raise OciCodeError("DisallowedCode", "unary +/- is only allowed on numbers")
    if isinstance(node, ast.Subscript):
        try:
            return _eval(node.value, env, dispatch)[_eval(node.slice, env, dispatch)]
        except (KeyError, IndexError, TypeError) as e:
            raise OciCodeError("IndexError", f"{type(e).__name__}: {e}")
    if isinstance(node, ast.Call):
        return _eval_call(node, env, dispatch)
    raise OciCodeError(
        "DisallowedCode",
        f"{type(node).__name__} is not allowed - use literals, variables, "
        "subscripts, model constructors, and Client.operation(...) calls",
    )


def _eval_call(node, env, dispatch):
    """A call is an OCI model constructor or a Client.operation dispatch."""
    func = node.func
    parts = _dotted_name(func) if not isinstance(func, ast.Call) else None

    if parts and len(parts) >= 4 and parts[0] == "oci" and parts[-2] == "models":
        svc, name = parts[1], parts[-1]
        if name in MODELS.get(svc, {}) and _is_model(MODELS[svc][name]):
            return _pending(node, name, svc, env, dispatch)
        raise OciCodeError(
            "UnknownModel",
            f"no model '{name}' in oci.{svc}.models",
            {"did_you_mean": difflib.get_close_matches(name, MODELS.get(svc, {}), n=5)},
        )

    if isinstance(func, ast.Name):
        name = func.id
        if name.startswith("_"):
            raise OciCodeError("DisallowedCode", "names may not start with underscore")
        if any(name in m for m in MODELS.values()):
            return _pending(node, name, None, env, dispatch)
        raise OciCodeError(
            "UnknownModel",
            f"no OCI model named '{name}'",
            {
                "did_you_mean": difflib.get_close_matches(
                    name, {n for m in MODELS.values() for n in m}, n=5
                )
            },
        )

    if isinstance(func, ast.Attribute):
        operation = func.attr
        if operation.startswith("_"):
            raise OciCodeError("DisallowedCode", "operation may not start with underscore")
        client_name, svc_hint = _resolve_client_expr(func.value)
        key, err = _resolve(client_name, svc_hint)
        if err:
            raise OciCodeError(
                err["error"],
                err["message"],
                {k: v for k, v in err.items() if k not in ("error", "message")},
            )
        service, cl = key
        names, _ = OPS[key]
        if operation not in names:
            raise OciCodeError(
                "UnknownOperation",
                f"{cl} has no operation '{operation}'",
                {"did_you_mean": difflib.get_close_matches(operation, names, n=5)},
            )
        args = [_materialize(_eval(a, env, dispatch), service) for a in node.args]
        kwargs = {}
        for kw in node.keywords:
            if kw.arg is None:
                raise OciCodeError("DisallowedCode", "** unpacking is not allowed")
            kwargs[kw.arg] = _materialize(_eval(kw.value, env, dispatch), service)
        return dispatch(service, cl, operation, args, kwargs)

    raise OciCodeError(
        "DisallowedCode",
        "calls must be Client.operation(...) or a model constructor",
    )


def _pending(node, name, service, env, dispatch):
    if node.args:
        raise OciCodeError("DisallowedCode", f"{name}(...) takes keyword arguments only")
    kwargs = {}
    for kw in node.keywords:
        if kw.arg is None:
            raise OciCodeError("DisallowedCode", "** unpacking is not allowed")
        kwargs[kw.arg] = _eval(kw.value, env, dispatch)
    return Pending(name, kwargs, service)


def _materialize(value, service):
    """Turn Pending models into real OCI model objects."""
    if isinstance(value, Pending):
        svc = value.service or service
        cls = MODELS.get(svc, {}).get(value.name)
        if cls is None or not _is_model(cls):
            raise OciCodeError(
                "UnknownModel",
                f"no model '{value.name}' in oci.{svc}.models",
            )
        kwargs = {k: _materialize(v, svc) for k, v in value.kwargs.items()}
        try:
            return cls(**kwargs)
        except TypeError as e:
            raise OciCodeError("BadModelField", f"{value.name}: {e}")
    if isinstance(value, list):
        return [_materialize(v, service) for v in value]
    if isinstance(value, tuple):
        return tuple(_materialize(v, service) for v in value)
    if isinstance(value, dict):
        return {k: _materialize(v, service) for k, v in value.items()}
    return value


def _run(code, dispatch):
    """Parse and walk a straight-line script."""
    if len(code) > MAX_CODE:
        raise OciCodeError("TooLong", f"code exceeds {MAX_CODE} chars")
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        raise OciCodeError("SyntaxError", str(e))
    if len(tree.body) > MAX_STMTS:
        raise OciCodeError("TooLong", f"more than {MAX_STMTS} statements")
    env, last = {}, _UNSET
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                raise OciCodeError(
                    "DisallowedCode",
                    "only single-name assignment is supported (x = ...)",
                )
            env[stmt.targets[0].id] = _eval(stmt.value, env, dispatch)
        elif isinstance(stmt, ast.Expr):
            last = _eval(stmt.value, env, dispatch)
        else:
            raise OciCodeError(
                "DisallowedCode",
                f"{type(stmt).__name__} is not allowed - use assignments and calls only "
                "(no imports, loops, conditionals, or functions)",
            )
    if last is _UNSET:
        raise OciCodeError("NoResult", "end your script with an OCI call or a value to return")
    if isinstance(last, Pending):
        raise OciCodeError(
            "NoResult",
            "your script ends on a model construction; end with the call that uses it, "
            "e.g. ComputeClient.launch_instance(details)",
        )
    return last


mcp = FastMCP(name=__project__)


@mcp.tool()
def oci_exec(code: str) -> dict:
    """RPC endpoint: write an OCI Python SDK script and return the final value.

    Build model objects, thread them into Client.operation(...) calls, and index
    results. Earlier results can feed later calls. Service is inferred from the
    client.

      shape = LaunchInstanceShapeConfigDetails(ocpus=2, memory_in_gbs=16)
      details = LaunchInstanceDetails(compartment_id="ocid1...", shape="VM.Standard.E4.Flex", shape_config=shape)
      ComputeClient.launch_instance(details)

    Allowed: assignments, variables, literals, subscripts, model constructors,
    and calls.
    Not allowed: imports, loops, conditionals, functions, and attribute access.
    Discover the surface with oci_discover.
    """
    calls = [0]

    def dispatch(service, cl, operation, args, kwargs):
        calls[0] += 1
        if calls[0] > MAX_CALLS:
            raise OciCodeError("TooManyCalls", f"a script may make at most {MAX_CALLS} calls")
        _, writes = OPS[(service, cl)]
        if operation in writes and not mutations_enabled():
            raise OciCodeError(
                "MutationsDisabled",
                f"'{operation}' changes state; set OCI_MCP_ENABLE_MUTATIONS=1 to allow it",
            )
        method = getattr(_client(service, cl), operation)
        resp = (
            oci.pagination.list_call_get_all_results(method, *args, **kwargs)
            if operation.startswith("list_")
            else method(*args, **kwargs)
        )
        return oci.util.to_dict(resp.data)

    try:
        return {"data": _run(code, dispatch)}
    except OciCodeError as e:
        return {"error": e.kind, "message": str(e), **e.extra}
    except oci.exceptions.ServiceError as e:
        return {
            "error": "ServiceError",
            "status": e.status,
            "code": e.code,
            "message": e.message,
        }
    except TypeError as e:
        return {"error": "TypeError", "message": str(e)}
    except Exception as e:
        return {"error": type(e).__name__, "message": str(e)}


@mcp.tool()
def oci_discover(
    client: str | None = None,
    operation: str | None = None,
    service: str | None = None,
) -> dict:
    """Discover the SDK surface.

    No args returns every service's client classes. `client` returns its
    operations with writes flagged. `client` plus `operation` returns signature
    and docstring.
    """
    if client is None:
        out: dict = {}
        for s, c in CLIENTS:
            out.setdefault(s, []).append(c)
        return {s: sorted(cs) for s, cs in sorted(out.items())}
    key, err = _resolve(client, service)
    if err:
        return err
    names, writes = OPS[key]
    if operation is None:
        return {"service": key[0], "operations": sorted(names), "write_ops": sorted(writes)}
    if operation not in names:
        return {
            "error": "UnknownOperation",
            "message": f"{client} has no operation '{operation}'",
            "did_you_mean": difflib.get_close_matches(operation, names, n=5),
        }
    fn = getattr(CLIENTS[key], operation)
    return {
        "service": key[0],
        "operation": operation,
        "write": operation in writes,
        "signature": str(inspect.signature(fn)),
        "doc": inspect.getdoc(fn),
    }


def main() -> None:
    """Console-script entry point: start the stdio MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
