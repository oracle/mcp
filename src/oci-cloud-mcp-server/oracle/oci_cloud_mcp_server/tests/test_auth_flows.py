from types import SimpleNamespace

import oci
import pytest
from fastmcp.server.auth import AccessToken
from fastmcp.server.dependencies import AuthenticatedUser

from oracle.oci_cloud_mcp_server.server import (
    _ADDITIONAL_UA,
    _build_auth_provider,
    _get_config_and_signer,
    _load_oci_config,
    main,
)


def _authenticated_http_user(token="JWT-TOKEN"):
    return AuthenticatedUser(
        AccessToken(
            token=token,
            client_id="client-id",
            scopes=["openid"],
            claims={"jti": "token-id"},
        )
    )


class TestConfigLoading:
    def test_load_oci_config_respects_config_file_env(self, monkeypatch):
        monkeypatch.setenv("OCI_CONFIG_FILE", "~/custom/config")
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "TEAM")

        called = {}

        def fake_from_file(file_location=None, profile_name=None):
            called["file_location"] = file_location
            called["profile_name"] = profile_name
            return {"region": "us-phoenix-1"}

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.oci.config.from_file", fake_from_file)

        config = _load_oci_config(require_file=True)

        assert called["file_location"] == "~/custom/config"
        assert called["profile_name"] == "TEAM"
        assert config["additional_user_agent"] == _ADDITIONAL_UA

    def test_load_oci_config_uses_region_for_oidc_when_config_file_missing(self, monkeypatch):
        monkeypatch.setenv("OCI_REGION", "us-phoenix-1")

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.config.from_file",
            lambda **kwargs: (_ for _ in ()).throw(oci.exceptions.ConfigFileNotFound("missing")),
        )

        config = _load_oci_config(require_file=False)

        assert config["region"] == "us-phoenix-1"
        assert config["additional_user_agent"] == _ADDITIONAL_UA


class TestOidcProviderBootstrap:
    def test_build_auth_provider_supports_sample_idcs_env(self, monkeypatch):
        monkeypatch.setenv("IDCS_DOMAIN", "sample.identity.oraclecloud.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "5000")

        captured = {}

        class FakeProvider:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.OCIProvider", FakeProvider)

        provider = _build_auth_provider()

        assert isinstance(provider, FakeProvider)
        assert (
            captured["config_url"]
            == "https://sample.identity.oraclecloud.com/.well-known/openid-configuration"
        )
        assert captured["client_id"] == "client-id"
        assert captured["client_secret"] == "client-secret"
        assert captured["base_url"] == "http://127.0.0.1:5000"

    def test_build_auth_provider_rejects_missing_idcs_env_when_required(self, monkeypatch):
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "5000")
        monkeypatch.delenv("IDCS_DOMAIN", raising=False)
        monkeypatch.delenv("IDCS_CLIENT_ID", raising=False)
        monkeypatch.delenv("IDCS_CLIENT_SECRET", raising=False)

        with pytest.raises(RuntimeError, match="HTTP transport requires IDCS authentication"):
            _build_auth_provider(required=True)


class TestDualAuthSelection:
    def test_get_config_and_signer_prefers_oidc_for_authenticated_request(self, monkeypatch):
        called = {}
        signer_args = {}
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.get_http_request",
            lambda: SimpleNamespace(scope={"user": _authenticated_http_user()}),
        )

        def fake_load_config(*, require_file):
            called["require_file"] = require_file
            return {"region": "us-phoenix-1", "additional_user_agent": _ADDITIONAL_UA}

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._load_oci_config",
            fake_load_config,
        )
        monkeypatch.setenv("IDCS_DOMAIN", "sample.identity.oraclecloud.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

        def fake_token_exchange_signer(jwt_or_func, oci_domain_id, client_id, client_secret, region=None):
            signer_args["jwt_or_func"] = jwt_or_func
            signer_args["oci_domain_id"] = oci_domain_id
            signer_args["client_id"] = client_id
            signer_args["client_secret"] = client_secret
            signer_args["region"] = region
            return {"signer": "oidc"}

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.auth.signers.TokenExchangeSigner",
            fake_token_exchange_signer,
        )

        config, signer = _get_config_and_signer()

        assert called["require_file"] is False
        assert config["region"] == "us-phoenix-1"
        assert signer == {"signer": "oidc"}
        assert signer_args["jwt_or_func"] == "JWT-TOKEN"
        assert signer_args["oci_domain_id"] == "sample"
        assert signer_args["client_id"] == "client-id"
        assert signer_args["client_secret"] == "client-secret"
        assert signer_args["region"] == "us-phoenix-1"

    def test_get_config_and_signer_rejects_http_without_idcs_config(self, monkeypatch):
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.get_http_request",
            lambda: SimpleNamespace(scope={"user": _authenticated_http_user()}),
        )

        with pytest.raises(RuntimeError, match="IDCS authentication configuration"):
            _get_config_and_signer()

    def test_get_config_and_signer_rejects_unauthenticated_http_request(self, monkeypatch):
        monkeypatch.setenv("IDCS_DOMAIN", "sample.identity.oraclecloud.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.get_http_request",
            lambda: SimpleNamespace(scope={}),
        )

        with pytest.raises(RuntimeError, match="authenticated IDCS access token"):
            _get_config_and_signer()

    def test_get_config_and_signer_falls_back_to_local_config_for_stdio(
        self, monkeypatch
    ):
        sentinel_signer = object()

        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.get_http_request",
            lambda: (_ for _ in ()).throw(RuntimeError("No active HTTP request found.")),
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._load_oci_config",
            lambda *, require_file: {
                "region": "us-ashburn-1",
                "additional_user_agent": _ADDITIONAL_UA,
                "key_file": "/tmp/key.pem",
            },
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._build_config_signer",
            lambda config: sentinel_signer,
        )

        config, signer = _get_config_and_signer()

        assert config["region"] == "us-ashburn-1"
        assert signer is sentinel_signer


class TestMain:
    def test_main_rejects_http_without_idcs(self, monkeypatch):
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "5000")
        monkeypatch.delenv("IDCS_DOMAIN", raising=False)
        monkeypatch.delenv("IDCS_CLIENT_ID", raising=False)
        monkeypatch.delenv("IDCS_CLIENT_SECRET", raising=False)

        with pytest.raises(RuntimeError, match="HTTP transport requires IDCS authentication"):
            main()

    def test_main_runs_http_with_required_auth_provider(self, monkeypatch):
        provider = object()
        called = {}

        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "5000")
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server._build_auth_provider",
            lambda *, required=False: provider,
        )

        def fake_run(*, transport=None, host=None, port=None):
            called["transport"] = transport
            called["host"] = host
            called["port"] = port

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.mcp.run", fake_run)

        main()

        assert called == {
            "transport": "http",
            "host": "127.0.0.1",
            "port": 5000,
        }

    def test_main_clears_auth_for_stdio(self, monkeypatch):
        monkeypatch.delenv("ORACLE_MCP_HOST", raising=False)
        monkeypatch.delenv("ORACLE_MCP_PORT", raising=False)
        called = {}

        def fake_run():
            called["ran"] = True

        fake_mcp = SimpleNamespace(auth=object(), run=fake_run)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.mcp", fake_mcp)

        main()

        assert called == {"ran": True}
        assert fake_mcp.auth is None
