from __future__ import annotations

import builtins
import inspect
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from oracle.mcp_common import helpers


class DummyClient:
    def __init__(self, config: dict[str, Any], signer: Any) -> None:
        self.config = config
        self.signer = signer


class DummySigner:
    def __init__(self, token: str, private_key: str) -> None:
        self.token = token
        self.private_key = private_key


def test_create_oci_client(monkeypatch, tmp_path):
    token_path = tmp_path / "token"
    token_path.write_text("TOKEN")
    key_path = tmp_path / "key.pem"
    key_path.write_text("PRIVATE KEY")

    config = {
        "key_file": str(key_path),
        "security_token_file": str(token_path),
    }

    captured_config = {}

    def fake_from_file(file_location, profile_name):
        captured_config["file_location"] = file_location
        captured_config["profile_name"] = profile_name
        return config

    def fake_load_private_key(path):
        assert path == str(key_path)
        return "PRIVATE"

    def fake_expanduser(path):
        assert path == str(token_path)
        return path

    original_open = builtins.open

    def fake_open(path, mode):
        assert mode == "r"
        assert str(path) == str(token_path)
        return original_open(token_path, mode)

    monkeypatch.setattr(helpers.oci.config, "from_file", fake_from_file)
    monkeypatch.setattr(
        helpers.oci.signer, "load_private_key_from_file", fake_load_private_key
    )
    monkeypatch.setattr(helpers.os.path, "expanduser", fake_expanduser)
    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(helpers.oci.auth.signers, "SecurityTokenSigner", DummySigner)
    monkeypatch.setenv("OCI_CONFIG_FILE", "~/.oci/config")
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "DEFAULT")

    client = helpers._create_oci_client(
        DummyClient, "oracle.example-server", "1.0.0", "sample_tool"
    )

    assert isinstance(client, DummyClient)
    assert client.config == config
    assert client.signer.token == "TOKEN"
    assert client.signer.private_key == "PRIVATE"
    assert config["additional_user_agent"] == "example/1.0.0 (sample_tool)"
    assert captured_config["file_location"] == "~/.oci/config"
    assert captured_config["profile_name"] == "DEFAULT"


def test_resolve_project_metadata_direct_attr(monkeypatch):
    module = ModuleType("oracle.product.module")
    module.__dict__["__project__"] = "oracle.product-server"
    module.__dict__["__version__"] = "2.1.3"

    def sample(client=None):
        return client

    sample.__module__ = module.__name__

    monkeypatch.setitem(sys.modules, module.__name__, module)
    func = SimpleNamespace(__module__=module.__name__)
    func.__call__ = sample
    module.__dict__["sample"] = sample

    project, version = helpers._resolve_project_metadata(sample)

    assert project == "oracle.product-server"
    assert version == "2.1.3"


def test_resolve_project_metadata_parent_lookup(monkeypatch):
    parent_module = ModuleType("oracle.parent")
    parent_module.__dict__["__project__"] = "oracle.parent-server"
    parent_module.__dict__["__version__"] = "3.0.0"

    child_module = ModuleType("oracle.parent.child")
    child_module.__dict__["__project__"] = None
    child_module.__dict__["__version__"] = None
    child_module.__dict__["__package__"] = "oracle.parent"

    monkeypatch.setitem(sys.modules, parent_module.__name__, parent_module)
    monkeypatch.setitem(sys.modules, child_module.__name__, child_module)

    def func(client=None):
        return client

    func.__module__ = child_module.__name__
    child_module.__dict__["func"] = func
    parent_module.__dict__["child"] = child_module

    project, version = helpers._resolve_project_metadata(func)

    assert project == "oracle.parent-server"
    assert version == "3.0.0"


def test_resolve_project_metadata_failure(monkeypatch):
    module = ModuleType("no_meta")
    module.__dict__["__project__"] = None
    module.__dict__["__version__"] = None
    monkeypatch.setitem(sys.modules, module.__name__, module)

    def func(client=None):
        return client

    func.__module__ = module.__name__
    module.__dict__["func"] = func

    with pytest.raises(RuntimeError):
        helpers._resolve_project_metadata(func)


def test_with_oci_client_missing_client_param():
    with pytest.raises(ValueError):

        @helpers.with_oci_client(DummyClient)
        def no_client_argument():
            return None


def test_with_oci_client_sync_injection(monkeypatch):
    def func(*, client):
        return client

    module = ModuleType("oracle.meta")
    module.__dict__["__project__"] = "oracle.meta-server"
    module.__dict__["__version__"] = "1.2.3"
    func.__module__ = module.__name__
    monkeypatch.setitem(sys.modules, module.__name__, module)

    dummy_client = object()

    def fake_create_client(client_class, project, version, tool_name):
        assert project == "oracle.meta-server"
        assert version == "1.2.3"
        assert tool_name == "test_with_oci_client_sync_injection.<locals>.func"
        return dummy_client

    monkeypatch.setattr(helpers, "_create_oci_client", fake_create_client)

    wrapped = helpers.with_oci_client(DummyClient)(func)

    result = wrapped()

    assert result is dummy_client
    assert "client" not in inspect.signature(wrapped).parameters


def test_with_oci_client_existing_client(monkeypatch):
    module = ModuleType("oracle.meta2")
    module.__dict__["__project__"] = "oracle.meta2-server"
    module.__dict__["__version__"] = "4.5.6"

    def func(*, client):
        return client

    func.__module__ = module.__name__
    monkeypatch.setitem(sys.modules, module.__name__, module)

    sentinel = object()

    wrapped = helpers.with_oci_client(DummyClient)(func)
    result = wrapped(client=sentinel)

    assert result is sentinel


@pytest.mark.asyncio
async def test_with_oci_client_async(monkeypatch):
    module = ModuleType("oracle.meta.async")
    module.__dict__["__project__"] = "oracle.meta-async-server"
    module.__dict__["__version__"] = "7.8.9"

    async def func(*, client):
        return client

    func.__module__ = module.__name__
    monkeypatch.setitem(sys.modules, module.__name__, module)

    dummy_client = object()

    def fake_create_client(client_class, project, version, tool_name):
        assert project == "oracle.meta-async-server"
        assert version == "7.8.9"
        assert tool_name == "test_with_oci_client_async.<locals>.func"
        return dummy_client

    monkeypatch.setattr(helpers, "_create_oci_client", fake_create_client)

    wrapped = helpers.with_oci_client(DummyClient)(func)

    result = await wrapped()

    assert result is dummy_client
    assert "client" not in inspect.signature(wrapped).parameters
