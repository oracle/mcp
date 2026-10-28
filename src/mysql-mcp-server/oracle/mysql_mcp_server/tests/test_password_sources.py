"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import copy
import importlib.util
import json
import traceback
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastmcp import Client

from oracle.mysql_mcp_server import utils

SECRET = "this-is-not-the-secret"
BASE_CONNECTION = {"host": "localhost", "user": "example", "database": "example", "port": 3306}
REFERENCE = {"service": "mysql-mcp-example", "username": "example"}


def configuration(**source):
    return {"server_infos": {"example": {**BASE_CONNECTION, **source}}}


def os_backend(name="keyring.backends.macOS.Keyring", password=SECRET):
    module, class_name = name.rsplit(".", 1)
    return type(class_name, (), {"__module__": module, "get_password": Mock(return_value=password)})()


def import_server():
    path = Path(utils.__file__).with_name("server.py")
    spec = importlib.util.spec_from_file_location("password_test_server", path)
    module = importlib.util.module_from_spec(spec)
    with patch.object(utils, "OciInfo", side_effect=RuntimeError("Offline test")):
        spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("password", [SECRET, ""])
def test_literal_password_remains_supported(password):
    raw = configuration(password=password)
    assert utils.fill_config_defaults(raw) == raw


def test_environment_resolved_once_without_mutating_input(monkeypatch):
    monkeypatch.setenv("MYSQL_MCP_TEST_PASSWORD", SECRET)
    raw = configuration(password_env="MYSQL_MCP_TEST_PASSWORD")
    original = copy.deepcopy(raw)
    result = utils.fill_config_defaults(raw)
    monkeypatch.setenv("MYSQL_MCP_TEST_PASSWORD", "changed-example-password")
    assert result == configuration(password=SECRET)
    assert raw == original


@pytest.mark.parametrize("name", sorted(utils._SECURE_KEYRING_BACKENDS))
def test_supported_os_backends_use_explicit_reference(monkeypatch, name):
    backend = os_backend(name)
    monkeypatch.setattr(utils.keyring, "get_keyring", lambda: backend)
    assert utils.fill_config_defaults(configuration(password_keyring=REFERENCE)) == configuration(password=SECRET)
    backend.get_password.assert_called_once_with(REFERENCE["service"], REFERENCE["username"])


@pytest.mark.parametrize("sources", [
    {},
    {"password": SECRET, "password_env": "MYSQL_MCP_TEST_PASSWORD"},
    {"password": "", "password_keyring": REFERENCE},
    {"password_env": "MYSQL_MCP_TEST_PASSWORD", "password_keyring": REFERENCE},
    {"password": SECRET, "password_env": "MYSQL_MCP_TEST_PASSWORD", "password_keyring": REFERENCE},
])
def test_missing_or_conflicting_sources_fail_before_lookup(monkeypatch, sources):
    lookup = Mock(side_effect=AssertionError("Keyring must not be read"))
    monkeypatch.setattr(utils.keyring, "get_keyring", lookup)
    with pytest.raises(ValueError, match="exactly one") as error:
        utils.fill_config_defaults(configuration(**sources))
    assert SECRET not in str(error.value)
    lookup.assert_not_called()


@pytest.mark.parametrize("reference", [None, 1, {}, "", "invalid-name", "1PASSWORD", "PASSWORD\n"])
def test_invalid_environment_reference_does_not_echo_value(reference):
    with pytest.raises(ValueError, match="valid environment variable"):
        utils.fill_config_defaults(configuration(password_env=reference))


@pytest.mark.parametrize("value", [None, ""])
def test_missing_environment_secret_is_rejected(monkeypatch, value):
    monkeypatch.delenv("MYSQL_MCP_TEST_PASSWORD", raising=False)
    if value is not None:
        monkeypatch.setenv("MYSQL_MCP_TEST_PASSWORD", value)
    with pytest.raises(ValueError, match="unset or empty"):
        utils.fill_config_defaults(configuration(password_env="MYSQL_MCP_TEST_PASSWORD"))


@pytest.mark.parametrize("reference", [None, "example", {}, {"service": "example"},
    {"service": "example", "username": ""}, {"service": " ", "username": "example"},
    {"service": 1, "username": "example"}, {**REFERENCE, "password": SECRET}])
def test_invalid_keyring_reference_is_rejected_without_echo(reference):
    with pytest.raises(ValueError, match="service and username") as error:
        utils.fill_config_defaults(configuration(password_keyring=reference))
    assert SECRET not in str(error.value)


@pytest.mark.parametrize("name", ["keyring.backends.fail.Keyring", "keyring.backends.null.Keyring",
    "keyring.backends.chainer.ChainerBackend", "keyrings.alt.file.PlaintextKeyring", "example.Keyring"])
def test_unsupported_backend_never_reads_a_password(monkeypatch, name):
    backend = os_backend(name)
    monkeypatch.setattr(utils.keyring, "get_keyring", lambda: backend)
    with pytest.raises(ValueError, match="supported OS keyring"):
        utils.fill_config_defaults(configuration(password_keyring=REFERENCE))
    backend.get_password.assert_not_called()


def test_keyring_initialization_failure_is_redacted(monkeypatch):
    monkeypatch.setattr(utils.keyring, "get_keyring", Mock(side_effect=RuntimeError(SECRET)))
    with pytest.raises(ValueError, match="initialize the OS keyring") as error:
        utils.fill_config_defaults(configuration(password_keyring=REFERENCE))
    assert SECRET not in "".join(traceback.format_exception(error.value))


def test_locked_keyring_failure_is_redacted(monkeypatch):
    backend = os_backend()
    backend.get_password.side_effect = RuntimeError(SECRET)
    monkeypatch.setattr(utils.keyring, "get_keyring", lambda: backend)
    with pytest.raises(ValueError, match="unlock and configure") as error:
        utils.fill_config_defaults(configuration(password_keyring=REFERENCE))
    assert SECRET not in "".join(traceback.format_exception(error.value))


@pytest.mark.parametrize("password", [None, "", 42])
def test_missing_keyring_secret_is_rejected(monkeypatch, password):
    monkeypatch.setattr(utils.keyring, "get_keyring", lambda: os_backend(password=password))
    with pytest.raises(ValueError, match="missing or empty"):
        utils.fill_config_defaults(configuration(password_keyring=REFERENCE))


@pytest.mark.parametrize("value", [None, 1, {"password": SECRET}])
def test_invalid_literal_password_does_not_echo_value(value):
    with pytest.raises(ValueError, match="password must be a string") as error:
        utils.fill_config_defaults(configuration(password=value))
    assert SECRET not in str(error.value)


@pytest.mark.parametrize("source", ["password", "password_env", "password_keyring"])
def test_startup_normalizes_connector_arguments(tmp_path, monkeypatch, source):
    monkeypatch.setenv("MYSQL_MCP_TEST_PASSWORD", SECRET)
    monkeypatch.setattr(utils.keyring, "get_keyring", lambda: os_backend())
    reference = {"password": SECRET, "password_env": "MYSQL_MCP_TEST_PASSWORD", "password_keyring": REFERENCE}[source]
    path = tmp_path / "config.json"
    path.write_text(json.dumps(configuration(**{source: reference})))
    monkeypatch.setenv("MYSQL_MCP_CONFIG", str(path))
    server = import_server()
    assert server.config_error_msg is None
    with patch.object(server.connector, "connect") as connect:
        assert server._get_db_connection("example") is connect.return_value
    connect.assert_called_once_with(**BASE_CONNECTION, password=SECRET)


@pytest.mark.asyncio
async def test_protocol_connection_summary_redacts_driver_errors(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(configuration(password=SECRET)))
    monkeypatch.setenv("MYSQL_MCP_CONFIG", str(path))
    server = import_server()
    with patch.object(server.connector, "connect", side_effect=RuntimeError(SECRET)):
        async with Client(server.mcp) as client:
            result = await client.call_tool("list_all_connections", {})
            payload = json.loads(result.content[0].text)
            assert payload["invalid keys"][0]["key"] == "example"
            assert "Connection failed" in payload["invalid keys"][0]["error"]
            assert SECRET not in result.content[0].text
            sql_result = await client.call_tool("execute_sql_tool_by_connection_id", {
                "connection_id": "example", "sql_script": "SELECT 1",
            })
            assert SECRET not in sql_result.content[0].text
            assert "unable to establish" in sql_result.content[0].text


@pytest.mark.asyncio
async def test_protocol_startup_error_has_no_keyring_exception_details(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(configuration(password_keyring=REFERENCE)))
    monkeypatch.setenv("MYSQL_MCP_CONFIG", str(path))
    backend = os_backend()
    backend.get_password.side_effect = RuntimeError(SECRET)
    monkeypatch.setattr(utils.keyring, "get_keyring", lambda: backend)
    server = import_server()
    assert server.config is None
    async with Client(server.mcp) as client:
        result = await client.call_tool("list_all_connections", {})
    assert "unlock and configure" in result.content[0].text
    assert SECRET not in result.content[0].text
