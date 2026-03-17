from io import StringIO
from types import SimpleNamespace

import pytest
from oracle.oci_cloud_mcp_server.server import (
    _align_params_to_signature,
    _extract_expected_kwargs_from_source,
    _get_config_and_signer,
    _import_client,
)


class TestGetConfigAndSigner:
    def test_prefers_security_token_signer_when_token_file_present(self, monkeypatch):
        # fake config with token file
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/tmp/token",
        }

        # patch oci.config.from_file
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.config.from_file",
            lambda **kwargs: dict(cfg),
        )

        # patch exists to indicate token file present
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.os.path.exists",
            lambda p: p == cfg["security_token_file"],
        )

        # patch key loader
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file",
            lambda p: "PK",
        )

        # patch open to return token content
        def fake_open(path, mode="r", *args, **kwargs):  # noqa: ARG001
            assert path == cfg["security_token_file"]
            return StringIO("token-contents")

        monkeypatch.setattr("builtins.open", fake_open)

        # capture creation of security token signer
        class FakeSTS:
            def __init__(self, token, private_key):
                self.token = token
                self.private_key = private_key

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.auth.signers.SecurityTokenSigner",
            FakeSTS,
        )

        config, signer = _get_config_and_signer()
        assert isinstance(signer, FakeSTS)
        assert signer.token == "token-contents"
        assert signer.private_key == "PK"
        # ensure additional user agent was set
        assert isinstance(config, dict)
        assert "additional_user_agent" in config

    def test_falls_back_to_api_key_signer_when_no_token(self, monkeypatch):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/no/token",
        }

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.config.from_file",
            lambda **kwargs: dict(cfg),
        )
        # no token file
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.os.path.exists", lambda p: False)
        # key loader ok
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file",
            lambda p: "PK",
        )

        class FakeSigner:
            def __init__(
                self,
                tenancy,
                user,
                fingerprint,
                private_key_file_location,
                pass_phrase=None,
            ):  # noqa: ARG002
                self.tenancy = tenancy
                self.user = user
                self.fingerprint = fingerprint
                self.private_key_file_location = private_key_file_location

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.oci.signer.Signer", FakeSigner)

        config, signer = _get_config_and_signer()
        assert isinstance(signer, FakeSigner)
        assert signer.tenancy == "t"
        assert signer.private_key_file_location == "/path/to/key.pem"
        assert "additional_user_agent" in config

    def test_private_key_load_failure_raises(self, monkeypatch):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
        }
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.config.from_file",
            lambda **kwargs: dict(cfg),
        )

        def boom(path):  # noqa: ARG001
            raise Exception("bad key")

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file",
            boom,
        )

        with pytest.raises(Exception):
            _get_config_and_signer()


class TestAlignParamsToSignatureIntrospectionFailure:
    def test_returns_original_when_signature_raises(self, monkeypatch):
        def create_vcn(vcn_details):  # noqa: ARG001
            return None

        def boom(obj):
            raise Exception("no sig")

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.inspect.signature",
            boom,
        )
        params = {"vcn_details": {"x": 1}}
        out = _align_params_to_signature(create_vcn, "create_vcn", params)
        assert out == params


class TestMainHttpRun:
    def test_main_http_env_calls_run_with_transport_host_port(self, monkeypatch):
        from fastmcp import FastMCP as _FastMCP

        called = {"args": None, "kwargs": None}

        def fake_run(self, *args, **kwargs):
            called["args"] = args
            called["kwargs"] = kwargs

        # patch FastMCP.run
        monkeypatch.setattr(_FastMCP, "run", fake_run, raising=False)
        # set env for HTTP
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8081")

        # ensure module __main__ executes with our patched run
        import runpy
        import sys as _sys

        monkeypatch.delitem(_sys.modules, "oracle.oci_cloud_mcp_server.server", raising=False)

        runpy.run_module("oracle.oci_cloud_mcp_server.server", run_name="__main__", alter_sys=True)
        assert called["kwargs"] == {
            "transport": "http",
            "host": "127.0.0.1",
            "port": 8081,
        }


class TestImportClientValidation:
    def test_client_fqn_without_dot_raises(self):
        with pytest.raises(ValueError):
            _import_client("ComputeClient")

    def test_attribute_not_a_class_raises(self, monkeypatch):
        fake_mod = SimpleNamespace(NotClass=42)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.import_module", lambda name: fake_mod)
        with pytest.raises(ValueError):
            _import_client("x.y.NotClass")


class TestExtractExpectedKwargs:
    def test_extracts_expected_kwargs_from_source(self):
        def fn(**kwargs):  # noqa: ARG001
            expected_kwargs = ["if_match", "limit", "page"]  # noqa: F841
            return None

        out = _extract_expected_kwargs_from_source(fn)
        assert isinstance(out, set)
        assert "limit" in out and "page" in out and "if_match" in out

    def test_returns_empty_set_when_not_present(self):
        def fn(a, b):  # noqa: ARG001
            return a

        out = _extract_expected_kwargs_from_source(fn)
        assert isinstance(out, set)
        assert out == set()

    def test_returns_none_when_getsource_raises(self, monkeypatch):
        def boom(obj):
            raise Exception("no src")

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.inspect.getsource",
            boom,
        )
        out = _extract_expected_kwargs_from_source(lambda: None)
        assert out is None


class TestAlignParamsToSignature:
    def test_renames_details_key_when_signature_requires(self):
        def create_vcn(create_vcn_details):  # noqa: ARG001
            return None

        params = {"vcn_details": {"x": 1}}
        out = _align_params_to_signature(create_vcn, "create_vcn", params)
        assert "create_vcn_details" in out and "vcn_details" not in out
        assert out["create_vcn_details"] == {"x": 1}

    def test_does_not_rename_when_signature_does_not_have_dst(self):
        def create_vcn(vcn_details):  # noqa: ARG001
            return None

        params = {"vcn_details": {"x": 1}}
        out = _align_params_to_signature(create_vcn, "create_vcn", params)
        assert out == params


class TestGetConfigAndSignerMoreBranches:
    def test_token_signer_build_failure_falls_back_to_api_key(self, monkeypatch):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/tmp/token",
        }
        # config and file present
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.config.from_file",
            lambda **kwargs: dict(cfg),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.os.path.exists",
            lambda p: p == cfg["security_token_file"],
        )
        # key loader ok and token readable
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file",
            lambda p: "PK",
        )
        monkeypatch.setattr("builtins.open", lambda *a, **k: StringIO("token"), raising=False)

        # SecurityTokenSigner init fails to trigger warning path, then API key used
        class BoomSTS:
            def __init__(self, token, private_key):  # noqa: ARG002
                raise Exception("sts boom")

        class FakeSigner:
            def __init__(
                self,
                tenancy,
                user,
                fingerprint,
                private_key_file_location,
                pass_phrase=None,
            ):  # noqa: ARG002
                self.tenancy = tenancy
                self.pk_file = private_key_file_location

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.auth.signers.SecurityTokenSigner",
            BoomSTS,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.signer.Signer",
            FakeSigner,
        )

        config, signer = _get_config_and_signer()
        assert isinstance(signer, FakeSigner)
        assert signer.tenancy == "t"
        assert signer.pk_file == "/path/to/key.pem"
        assert "additional_user_agent" in config

    def test_api_key_signer_raises_is_propagated(self, monkeypatch):
        cfg = {
            "tenancy": "t",
            "user": "u",
            "fingerprint": "f",
            "key_file": "/path/to/key.pem",
            "security_token_file": "/no/token",
        }
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.config.from_file",
            lambda **kwargs: dict(cfg),
        )
        # token file not present
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.os.path.exists", lambda p: False)
        # key loader ok
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.signer.load_private_key_from_file",
            lambda p: "PK",
        )

        # API key signer ctor fails
        def boom_signer(**kwargs):  # noqa: ARG001
            raise Exception("signer ctor boom")

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.oci.signer.Signer", boom_signer)
        with pytest.raises(Exception):
            _get_config_and_signer()
