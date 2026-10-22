"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from . import __project__

_DEFAULT_PORT = 5432
_DEFAULT_CONNECT_TIMEOUT = 10
_DEFAULT_SSLMODE = "verify-full"
_ALLOWED_SSLMODES = {
    "require",
    "verify-ca",
    "verify-full",
}
_CONFIG_ENV_VAR = "POSTGRESQL_MCP_CONFIG"
_INTEGER_PATTERN = re.compile(r"[+-]?\d+")


@dataclass(frozen=True)
class _ConnectionProfile:
    connect_kwargs: dict[str, Any]


def _get_package_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _coerce_int(field_name: str, value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and _INTEGER_PATTERN.fullmatch(value.strip()):
        return int(value.strip())
    raise ValueError(f"{field_name} must be an integer")


def _pick_value(config: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in config and config[key] is not None:
            return config[key]
    return None


def _normalize_sslmode(value: Any) -> str:
    if value is None:
        return _DEFAULT_SSLMODE
    if not isinstance(value, str):
        raise ValueError("sslmode must be a string")

    sslmode = value.strip().lower()
    if sslmode not in _ALLOWED_SSLMODES:
        raise ValueError(
            "sslmode must be one of: " + ", ".join(sorted(_ALLOWED_SSLMODES))
        )
    return sslmode


def _normalize_connection(connection: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(connection, dict):
        raise ValueError("connection must be an object")

    host = _pick_value(connection, "host")
    dbname = _pick_value(connection, "database", "dbname")
    user = _pick_value(connection, "user", "username")
    password = _pick_value(connection, "password")

    missing_fields = [
        name
        for name, value in (
            ("host", host),
            ("database", dbname),
            ("user", user),
            ("password", password),
        )
        if not value
    ]
    if missing_fields:
        raise ValueError(
            "connection is missing required fields: " + ", ".join(missing_fields)
        )

    connect_kwargs: dict[str, Any] = {
        "host": host,
        "dbname": dbname,
        "user": user,
        "password": password,
        "port": _DEFAULT_PORT,
        "connect_timeout": _DEFAULT_CONNECT_TIMEOUT,
        "application_name": __project__,
    }

    port = _pick_value(connection, "port")
    if port is not None:
        connect_kwargs["port"] = _coerce_int("port", port)

    connect_timeout = _pick_value(connection, "connect_timeout")
    if connect_timeout is not None:
        connect_kwargs["connect_timeout"] = _coerce_int(
            "connect_timeout", connect_timeout
        )

    sslmode = _pick_value(connection, "sslmode", "ssl_mode")
    connect_kwargs["sslmode"] = _normalize_sslmode(sslmode)

    sslrootcert = _pick_value(connection, "sslrootcert", "ssl_root_cert_path")
    if sslrootcert is not None:
        connect_kwargs["sslrootcert"] = sslrootcert

    hostaddr = _pick_value(connection, "hostaddr", "host_addr")
    if hostaddr is not None:
        connect_kwargs["hostaddr"] = hostaddr

    return {
        "connect_kwargs": connect_kwargs,
    }


def _as_connection_profile(connection: dict[str, Any]) -> _ConnectionProfile:
    if "connect_kwargs" in connection:
        connect_kwargs = connection["connect_kwargs"]
    else:
        connect_kwargs = connection

    if not isinstance(connect_kwargs, dict):
        raise ValueError("connection profile connect_kwargs must be an object")
    connect_kwargs = dict(connect_kwargs)

    connect_kwargs["sslmode"] = _normalize_sslmode(connect_kwargs.get("sslmode"))

    return _ConnectionProfile(
        connect_kwargs=connect_kwargs,
    )


def _resolve_config_path(path: str) -> str:
    candidate_paths = [path]
    if not os.path.isabs(path):
        candidate_paths.append(os.path.join(_get_package_dir(), path))

    for candidate_path in candidate_paths:
        normalized_path = os.path.abspath(os.path.expanduser(candidate_path))
        if os.path.isfile(normalized_path):
            return normalized_path

    raise ValueError(
        f"Config file not found at {path}. Set {_CONFIG_ENV_VAR} to a valid file path."
    )


def load_postgresql_config() -> dict[str, Any]:
    env_path = os.environ.get(_CONFIG_ENV_VAR)
    default_path = os.path.join(_get_package_dir(), "local_config.json")

    if env_path:
        config_path = _resolve_config_path(env_path)
    elif os.path.isfile(default_path):
        config_path = default_path
    else:
        return {"connections": {}, "config_path": None}

    with open(config_path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise ValueError("Config must be a JSON object")

    connections = payload.get("connections")
    if connections is None:
        raise ValueError("Config must specify 'connections'")
    if not isinstance(connections, dict):
        raise ValueError("'connections' must be an object")

    normalized_connections: dict[str, dict[str, Any]] = {}
    for connection_name, connection in connections.items():
        if not isinstance(connection_name, str) or not connection_name.strip():
            raise ValueError("Connection names must be non-empty strings")
        normalized_connections[connection_name] = _normalize_connection(connection)

    return {
        "connections": normalized_connections,
        "config_path": config_path,
    }


def _summarize_connection(
    connection_name: str,
    profile: _ConnectionProfile,
) -> dict[str, Any]:
    connect_kwargs = profile.connect_kwargs
    return {
        "connection_name": connection_name,
        "host": connect_kwargs["host"],
        "hostaddr": connect_kwargs.get("hostaddr"),
        "port": connect_kwargs["port"],
        "database": connect_kwargs["dbname"],
        "user": connect_kwargs["user"],
        "sslmode": connect_kwargs["sslmode"],
        "connect_timeout": connect_kwargs["connect_timeout"],
    }
