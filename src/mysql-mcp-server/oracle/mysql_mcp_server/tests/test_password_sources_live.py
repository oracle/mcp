"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Opt in with MYSQL_MCP_RUN_CREDENTIAL_LIVE_TESTS=1, MYSQL_MCP_CONFIG pointing
to one disposable database connection, and MYSQL_MCP_TEST_SSL_CA pointing
to its trusted CA. The database certificate must match the configured host.
The runtime account must be able to write and delete a synthetic OS keyring entry.
Run this file separately from the HeatWave/OCI live suite, using pytest --no-cov.
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
import secrets
import sys
import uuid

import keyring
from mysql import connector
import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from oracle.mysql_mcp_server import utils

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("MYSQL_MCP_RUN_CREDENTIAL_LIVE_TESTS") != "1",
        reason="Set MYSQL_MCP_RUN_CREDENTIAL_LIVE_TESTS=1 for disposable credential tests",
    ),
]


@dataclass(repr=False)
class _LiveCredentials:
    # Prevent pytest from rendering the password-bearing fixture in failures.
    connection: dict
    reference: dict
    backend_name: str
    directory: Path
    wrapper: Path


@pytest.fixture(scope="module")
def live_credentials(tmp_path_factory):
    if not os.environ.get("MYSQL_MCP_CONFIG") or not os.environ.get("MYSQL_MCP_TEST_SSL_CA"):
        pytest.fail("Set MYSQL_MCP_CONFIG and MYSQL_MCP_TEST_SSL_CA for the disposable database", pytrace=False)
    connections = utils.load_mysql_config()["server_infos"]
    if len(connections) != 1:
        pytest.fail("Credential live tests require exactly one disposable database connection", pytrace=False)
    connection = dict(next(iter(connections.values())))
    if not connection["password"]:
        pytest.fail("Credential live tests require a non-empty disposable password", pytrace=False)

    # Probe the actual runtime identity and route before provisioning test credentials.
    with connector.connect(
        **connection,
        ssl_ca=os.environ["MYSQL_MCP_TEST_SSL_CA"],
        ssl_verify_cert=True,
        ssl_verify_identity=True,
        connection_timeout=10,
    ) as database:
        with database.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                pytest.fail("Authenticated TLS preflight returned an unexpected result", pytrace=False)

    backend = keyring.get_keyring()
    backend_name = f"{type(backend).__module__}.{type(backend).__name__}"
    if backend_name not in utils._SECURE_KEYRING_BACKENDS:
        pytest.fail("Credential live tests require a supported OS keyring backend", pytrace=False)
    service = f"mysql-mcp-live-test-{uuid.uuid4().hex}"
    reference = {"service": service, "username": "synthetic-test-user"}
    directory = tmp_path_factory.mktemp("mysql-credential-live")
    directory.chmod(0o700)
    wrapper = directory / "stdio_server.py"
    wrapper.write_text(
        "from oracle.mysql_mcp_server import utils\n"
        "def disabled_oci():\n"
        "    raise RuntimeError('OCI disabled during credential live tests')\n"
        "utils.OciInfo = disabled_oci\n"
        "from oracle.mysql_mcp_server.server import main\n"
        "main()\n"
    )
    created = False
    try:
        backend.set_password(service, reference["username"], connection["password"])
        created = True
        if backend.get_password(service, reference["username"]) != connection["password"]:
            pytest.fail("Synthetic OS keyring entry did not round-trip", pytrace=False)
        yield _LiveCredentials(connection, reference, backend_name, directory, wrapper)
    finally:
        try:
            if created:
                backend.delete_password(service, reference["username"])
                if backend.get_password(service, reference["username"]) is not None:
                    pytest.fail("Synthetic OS keyring entry was not removed", pytrace=False)
        finally:
            wrapper.unlink(missing_ok=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["password", "password_env", "password_keyring"])
async def test_live_password_source_over_stdio(live_credentials, source):
    connection = live_credentials.connection
    reference = live_credentials.reference
    backend_name = live_credentials.backend_name
    directory = live_credentials.directory
    wrapper = live_credentials.wrapper
    password = connection["password"]
    entry = {key: value for key, value in connection.items() if key != "password"}
    entry[source] = {
        "password": password,
        "password_env": "MYSQL_MCP_LIVE_TEST_PASSWORD",
        "password_keyring": reference,
    }[source]
    path = directory / f"{source}.json"
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as config_file:
        json.dump({"server_infos": {"synthetic": entry}}, config_file)
    log_path = directory / f"{source}.stderr"
    try:
        env = {
            **os.environ,
            "MYSQL_MCP_CONFIG": str(path),
            "MYSQL_MCP_LIVE_TEST_PASSWORD": password,
            "PYTHON_KEYRING_BACKEND": backend_name,
        }
        with log_path.open("w") as log:
            transport = StdioTransport(command=sys.executable, args=[str(wrapper)], env=env, log_file=log)
            async with Client(transport, timeout=20, init_timeout=20) as client:
                assert any(tool.name == "execute_sql_tool_by_connection_id" for tool in await client.list_tools())
                result = await client.call_tool("execute_sql_tool_by_connection_id", {
                    "connection_id": "synthetic", "sql_script": "SELECT 1",
                })
                if json.loads(result.content[0].text) != [[1]]:
                    pytest.fail("Authenticated MCP query returned an unexpected result", pytrace=False)
                if password in result.content[0].text:
                    pytest.fail("MCP query response exposed a password", pytrace=False)
                summary = await client.call_tool("list_all_connections", {})
                if password in summary.content[0].text:
                    pytest.fail("Connection summary exposed a password", pytrace=False)
        if password in log_path.read_text():
            pytest.fail("STDIO diagnostics exposed a password", pytrace=False)
    finally:
        path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("case, expected", [
    ("missing-env", "unset or empty"),
    ("missing-keyring", "missing or empty"),
    ("conflict", "exactly one"),
    ("wrong-password", "Connection failed"),
])
async def test_live_password_failures_are_redacted(live_credentials, case, expected):
    connection = live_credentials.connection
    reference = live_credentials.reference
    backend_name = live_credentials.backend_name
    directory = live_credentials.directory
    wrapper = live_credentials.wrapper
    password = connection["password"]
    wrong_password = secrets.token_urlsafe(30)
    entry = {key: value for key, value in connection.items() if key != "password"}
    entry.update({
        "missing-env": {"password_env": "MYSQL_MCP_LIVE_TEST_UNSET"},
        "missing-keyring": {"password_keyring": {**reference, "service": reference["service"] + "-missing"}},
        "conflict": {"password": password, "password_env": "MYSQL_MCP_LIVE_TEST_UNSET"},
        "wrong-password": {"password": wrong_password},
    }[case])
    path = directory / f"{case}.json"
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as config_file:
        json.dump({"server_infos": {"synthetic": entry}}, config_file)
    log_path = directory / f"{case}.stderr"
    try:
        env = {**os.environ, "MYSQL_MCP_CONFIG": str(path), "PYTHON_KEYRING_BACKEND": backend_name}
        env.pop("MYSQL_MCP_LIVE_TEST_UNSET", None)
        with log_path.open("w") as log:
            transport = StdioTransport(command=sys.executable, args=[str(wrapper)], env=env, log_file=log)
            async with Client(transport, timeout=20, init_timeout=20) as client:
                result = await client.call_tool("list_all_connections", {})
                if expected not in result.content[0].text:
                    pytest.fail("MCP response did not report the expected credential failure", pytrace=False)
                if password in result.content[0].text or wrong_password in result.content[0].text:
                    pytest.fail("MCP failure response exposed a password", pytrace=False)
        if password in log_path.read_text():
            pytest.fail("STDIO diagnostics exposed a password", pytrace=False)
        if wrong_password in log_path.read_text():
            pytest.fail("STDIO diagnostics exposed the invalid password", pytrace=False)
    finally:
        path.unlink(missing_ok=True)
        log_path.unlink(missing_ok=True)
