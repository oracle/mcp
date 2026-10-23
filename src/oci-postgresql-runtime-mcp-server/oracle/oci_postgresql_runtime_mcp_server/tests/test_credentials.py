"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import traceback
from unittest.mock import Mock

import pytest

from oracle.oci_postgresql_runtime_mcp_server import profiles


_PASSWORD = "this-is-not-the-secret"
_ENVIRONMENT_NAME = "POSTGRESQL_MCP_TEST_PASSWORD"
_CONNECTION = {"host": "db.example.com", "database": "app_db", "user": "app_user"}
_KEYRING_REFERENCE = {"service": "postgresql-mcp-test", "username": "credential-user"}


@pytest.fixture(autouse=True)
def keyring_lookup(monkeypatch):
    # No test may access the user's actual credential store.
    lookup = Mock(side_effect=AssertionError("OS keyring access must be mocked"))
    monkeypatch.setattr(profiles.keyring, "get_keyring", lookup)
    monkeypatch.delenv(_ENVIRONMENT_NAME, raising=False)
    return lookup


def _backend(password=_PASSWORD, *, module="keyring.backends.SecretService", name="Keyring"):
    backend_type = type(name, (), {"__module__": module, "get_password": Mock(return_value=password)})
    return backend_type()


@pytest.mark.parametrize("password", [_PASSWORD, " this-is-not-the-secret "])
def test_literal_password_keeps_existing_profile_shape(password, keyring_lookup):
    normalized = profiles._normalize_connection({**_CONNECTION, "password": password})

    assert set(normalized) == {"connect_kwargs"}
    assert normalized["connect_kwargs"]["password"] == password
    assert normalized["connect_kwargs"]["sslmode"] == "verify-full"
    keyring_lookup.assert_not_called()


def test_password_env_resolves_value_without_expanding_other_fields(monkeypatch, keyring_lookup):
    monkeypatch.setenv(_ENVIRONMENT_NAME, _PASSWORD)
    normalized = profiles._normalize_connection({
        **_CONNECTION, "host": "${DB_HOST}", "password_env": _ENVIRONMENT_NAME,
    })

    assert normalized["connect_kwargs"]["password"] == _PASSWORD
    assert normalized["connect_kwargs"]["host"] == "${DB_HOST}"
    assert "password_env" not in normalized["connect_kwargs"]
    keyring_lookup.assert_not_called()


@pytest.mark.parametrize("module,name", [
    ("keyring.backends.macOS", "Keyring"),
    ("keyring.backends.Windows", "WinVaultKeyring"),
    ("keyring.backends.SecretService", "Keyring"),
    ("keyring.backends.kwallet", "DBusKeyring"),
    ("keyring.backends.kwallet", "DBusKeyringKWallet4"),
    ("keyring.backends.libsecret", "Keyring"),
])
def test_keyring_resolves_explicit_service_and_username(keyring_lookup, module, name):
    backend = _backend(module=module, name=name)
    keyring_lookup.side_effect = None
    keyring_lookup.return_value = backend

    normalized = profiles._normalize_connection({
        **_CONNECTION, "password_keyring": _KEYRING_REFERENCE,
    })

    assert normalized["connect_kwargs"]["password"] == _PASSWORD
    assert normalized["connect_kwargs"]["user"] == "app_user"
    assert "password_keyring" not in normalized["connect_kwargs"]
    backend.get_password.assert_called_once_with("postgresql-mcp-test", "credential-user")


@pytest.mark.parametrize("sources", [
    {},
    {"password": _PASSWORD, "password_env": _ENVIRONMENT_NAME},
    {"password": None, "password_env": _ENVIRONMENT_NAME},
    {"password": "", "password_keyring": _KEYRING_REFERENCE},
    {"password_env": _ENVIRONMENT_NAME, "password_keyring": _KEYRING_REFERENCE},
    {"password": _PASSWORD, "password_env": _ENVIRONMENT_NAME,
     "password_keyring": _KEYRING_REFERENCE},
])
def test_requires_exactly_one_source_before_any_lookup(sources, keyring_lookup):
    with pytest.raises(ValueError, match="exactly one") as error:
        profiles._normalize_connection({**_CONNECTION, **sources})
    assert _PASSWORD not in str(error.value)
    keyring_lookup.assert_not_called()


@pytest.mark.parametrize("source,value,message", [
    ("password", None, "non-empty string"),
    ("password", "", "non-empty string"),
    ("password", 123, "non-empty string"),
    ("password", True, "non-empty string"),
    ("password_env", None, "valid environment variable"),
    ("password_env", "", "valid environment variable"),
    ("password_env", "NOT A NAME", "valid environment variable"),
    ("password_env", "HAS=EQUALS", "valid environment variable"),
    ("password_env", "HAS\x00NUL", "valid environment variable"),
    ("password_env", [], "valid environment variable"),
    ("password_keyring", None, "service and username"),
    ("password_keyring", {}, "service and username"),
    ("password_keyring", {"service": "example"}, "service and username"),
    ("password_keyring", {"service": "", "username": "user"}, "service and username"),
    ("password_keyring", {"service": "example", "username": " "}, "service and username"),
    ("password_keyring", {"service": "example", "username": 123}, "service and username"),
    ("password_keyring", {**_KEYRING_REFERENCE, "password": _PASSWORD}, "service and username"),
])
def test_invalid_references_are_rejected_without_lookup(source, value, message, keyring_lookup):
    with pytest.raises(ValueError, match=message) as error:
        profiles._normalize_connection({**_CONNECTION, source: value})
    assert _PASSWORD not in str(error.value)
    keyring_lookup.assert_not_called()


@pytest.mark.parametrize("value", [None, ""])
def test_missing_or_empty_environment_value_fails(monkeypatch, keyring_lookup, value):
    if value is not None:
        monkeypatch.setenv(_ENVIRONMENT_NAME, value)
    with pytest.raises(ValueError, match="unset or empty"):
        profiles._normalize_connection({**_CONNECTION, "password_env": _ENVIRONMENT_NAME})
    keyring_lookup.assert_not_called()


@pytest.mark.parametrize("module,name", [
    ("keyring.backends.fail", "Keyring"),
    ("keyring.backends.null", "Keyring"),
    ("keyring.backends.chainer", "ChainerBackend"),
    ("keyrings.alt.file", "PlaintextKeyring"),
    ("keyrings.alt.file", "EncryptedKeyring"),
    ("custom_backend", "Keyring"),
])
def test_non_os_and_chained_backends_are_rejected_before_secret_lookup(keyring_lookup, module, name):
    backend = _backend(module=module, name=name)
    keyring_lookup.side_effect = None
    keyring_lookup.return_value = backend

    with pytest.raises(ValueError, match="supported OS keyring backend"):
        profiles._normalize_connection({**_CONNECTION, "password_keyring": _KEYRING_REFERENCE})
    backend.get_password.assert_not_called()


@pytest.mark.parametrize("value", [None, "", 123])
def test_missing_or_invalid_keyring_entry_fails_without_fallback(keyring_lookup, value):
    keyring_lookup.side_effect = None
    keyring_lookup.return_value = _backend(value)
    with pytest.raises(ValueError, match="missing or empty"):
        profiles._normalize_connection({**_CONNECTION, "password_keyring": _KEYRING_REFERENCE})


@pytest.mark.parametrize("failure_stage", ["initialize", "lookup"])
def test_keyring_errors_suppress_backend_details(keyring_lookup, failure_stage, caplog):
    if failure_stage == "initialize":
        keyring_lookup.side_effect = RuntimeError(_PASSWORD)
    else:
        backend = _backend()
        backend.get_password.side_effect = RuntimeError(_PASSWORD)
        keyring_lookup.side_effect = None
        keyring_lookup.return_value = backend

    with pytest.raises(ValueError, match="password_keyring") as error:
        profiles._normalize_connection({**_CONNECTION, "password_keyring": _KEYRING_REFERENCE})
    rendered_error = "".join(traceback.format_exception(error.value))
    assert _PASSWORD not in rendered_error
    assert _PASSWORD not in caplog.text
    assert error.value.__suppress_context__ is True


@pytest.mark.parametrize("source", ["password_env", "password_keyring"])
def test_credentials_resolve_at_startup_and_refresh_only_on_reload(
    monkeypatch, tmp_path, keyring_lookup, source,
):
    backend = _backend()
    keyring_lookup.side_effect = None
    keyring_lookup.return_value = backend
    monkeypatch.setenv(_ENVIRONMENT_NAME, _PASSWORD)
    reference = _ENVIRONMENT_NAME if source == "password_env" else _KEYRING_REFERENCE
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({"connections": {"app-db": {**_CONNECTION, source: reference}}}))
    monkeypatch.setenv("POSTGRESQL_MCP_CONFIG", str(path))
    loaded = profiles.load_postgresql_config()
    profile = profiles._as_connection_profile(loaded["connections"]["app-db"])

    replacement = "this-is-not-the-new-secret"
    monkeypatch.setenv(_ENVIRONMENT_NAME, replacement)
    backend.get_password.return_value = replacement

    assert profile.connect_kwargs["password"] == _PASSWORD
    summary = profiles._summarize_connection("app-db", profile)
    assert "password" not in summary
    assert source not in summary
    assert _PASSWORD not in json.dumps(summary)
    assert _PASSWORD not in path.read_text()
    reloaded = profiles.load_postgresql_config()
    assert reloaded["connections"]["app-db"]["connect_kwargs"]["password"] == replacement
