from types import SimpleNamespace

import pytest
from oracle_mcp_common import AuthContext, AuthType
from oracle.oci_cloud_mcp_server import server as cloud_server
from oracle.oci_cloud_mcp_server.server import (
    _ADDITIONAL_UA,
    _align_params_to_signature,
    _extract_expected_kwargs_from_source,
    _get_config_and_signer,
    _import_client,
    main,
)


class TestGetConfigAndSigner:
    @staticmethod
    def _set_http_environment(monkeypatch):
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")

    def test_http_propagates_common_request_context_error(self, monkeypatch):
        self._set_http_environment(monkeypatch)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.get_access_token",
            lambda: SimpleNamespace(token="token"),
        )
        calls = []

        def context_for(token):
            calls.append(token)
            raise ValueError("HTTP requests require an explicit region or OCI_REGION.")

        monkeypatch.setattr(cloud_server, "_http_auth", SimpleNamespace(context_for=context_for))

        with pytest.raises(ValueError, match="OCI_REGION"):
            _get_config_and_signer()
        assert calls == ["token"]

    def test_http_passes_missing_access_token_to_common_policy(self, monkeypatch):
        self._set_http_environment(monkeypatch)
        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.get_access_token", lambda: None)
        calls = []

        def context_for(token):
            calls.append(token)
            raise ValueError("HTTP requests require an authenticated IDCS access token.")

        monkeypatch.setattr(cloud_server, "_http_auth", SimpleNamespace(context_for=context_for))

        with pytest.raises(ValueError, match="authenticated IDCS access token"):
            _get_config_and_signer()
        assert calls == [None]

    def test_http_requires_initialized_policy(self, monkeypatch):
        self._set_http_environment(monkeypatch)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.get_access_token",
            lambda: SimpleNamespace(token="token"),
        )
        monkeypatch.setattr(cloud_server, "_http_auth", None)

        with pytest.raises(RuntimeError, match="policy has not been initialized"):
            _get_config_and_signer()

    def test_http_request_context_retains_exact_user_agent_and_is_caller_specific(self, monkeypatch):
        self._set_http_environment(monkeypatch)
        tokens = iter(("first-token", "second-token"))
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.get_access_token",
            lambda: SimpleNamespace(token=next(tokens)),
        )
        first_signer = object()
        second_signer = object()
        contexts = {
            "first-token": SimpleNamespace(config={"region": "us-chicago-1"}, signer=first_signer),
            "second-token": SimpleNamespace(config={"region": "us-chicago-1"}, signer=second_signer),
        }
        calls = []

        def context_for(token):
            calls.append(token)
            return contexts[token]

        monkeypatch.setattr(cloud_server, "_http_auth", SimpleNamespace(context_for=context_for))
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.build_auth_context",
            lambda: pytest.fail("HTTP request authentication must not use the common provider"),
        )

        first_config, first_resolved_signer = _get_config_and_signer()
        second_config, second_resolved_signer = _get_config_and_signer()

        assert first_config == {
            "region": "us-chicago-1",
            "additional_user_agent": _ADDITIONAL_UA,
        }
        assert second_config == first_config
        assert first_resolved_signer is first_signer
        assert second_resolved_signer is second_signer
        assert calls == ["first-token", "second-token"]

    @pytest.mark.parametrize(
        "auth_type",
        [
            AuthType.API_KEY,
            AuthType.SECURITY_TOKEN,
            AuthType.IDENTITY_DOMAIN_UPST,
            AuthType.INSTANCE_PRINCIPAL,
            AuthType.RESOURCE_PRINCIPAL,
            AuthType.INSTANCE_PRINCIPAL_DELEGATION,
            AuthType.RESOURCE_PRINCIPAL_DELEGATION,
            AuthType.OKE_WORKLOAD_IDENTITY,
        ],
    )
    def test_common_auth_context_retains_exact_user_agent(self, monkeypatch, auth_type):
        signer = object()
        context_config = {"region": "us-chicago-1", "auth_type_marker": auth_type.value}
        auth_context = AuthContext(
            auth_type=auth_type,
            config=context_config,
            signer=signer,
            tenancy_id=None,
            region="us-chicago-1",
            profile_name=None,
        )
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.build_auth_context",
            lambda: auth_context,
        )

        config, resolved_signer = _get_config_and_signer()

        assert config == {**context_config, "additional_user_agent": _ADDITIONAL_UA}
        assert resolved_signer is signer
        assert "additional_user_agent" not in auth_context.config

    def test_inherited_default_session_token_does_not_replace_named_api_key_profile(
        self, monkeypatch, tmp_path
    ):
        key_file = tmp_path / "team-key.pem"
        key_file.write_text("unused test key", encoding="utf-8")
        config_file = tmp_path / "config"
        config_file.write_text(
            f"""[DEFAULT]
security_token_file=/wrong-principal/token

[TEAM]
tenancy=team-tenancy
user=team-user
fingerprint=team-fingerprint
key_file={key_file}
region=us-chicago-1
""",
            encoding="utf-8",
        )
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "TEAM")
        api_signer = object()
        api_calls = []

        def fake_api_signer(**kwargs):
            api_calls.append(kwargs)
            return api_signer

        monkeypatch.setattr("oracle.oci_cloud_mcp_server.server.oci.signer.Signer", fake_api_signer)
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.auth.signers.SecurityTokenSigner",
            lambda *args, **kwargs: pytest.fail("inherited session token selected the wrong principal"),
        )

        config, signer = _get_config_and_signer()

        assert signer is api_signer
        assert api_calls[0]["tenancy"] == "team-tenancy"
        assert config["additional_user_agent"] == _ADDITIONAL_UA

    def test_direct_session_token_failure_does_not_fall_back_to_api_key(
        self, monkeypatch, tmp_path
    ):
        missing_token = tmp_path / "missing-token"
        key_file = tmp_path / "session-key.pem"
        key_file.write_text("unused test key", encoding="utf-8")
        config_file = tmp_path / "config"
        config_file.write_text(
            f"""[SESSION]
tenancy=session-tenancy
user=session-user
fingerprint=session-fingerprint
key_file={key_file}
security_token_file={missing_token}
region=us-chicago-1
""",
            encoding="utf-8",
        )
        monkeypatch.setenv("OCI_CONFIG_FILE", str(config_file))
        monkeypatch.setenv("OCI_CONFIG_PROFILE", "SESSION")
        monkeypatch.setattr(
            "oracle.oci_cloud_mcp_server.server.oci.signer.Signer",
            lambda **kwargs: pytest.fail("failed session authentication fell back to API key"),
        )

        with pytest.raises(ValueError, match="Unable to read security_token_file"):
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
        called = {"args": None, "kwargs": None}
        provider = object()
        http_auth = SimpleNamespace(provider=provider)
        scopes = []

        def fake_run(*args, **kwargs):
            called["args"] = args
            called["kwargs"] = kwargs

        def build_http_auth(required_scopes):
            scopes.append(required_scopes)
            return http_auth

        monkeypatch.setattr(cloud_server.mcp, "run", fake_run)
        monkeypatch.setattr(cloud_server, "build_idcs_http_auth", build_http_auth)
        monkeypatch.setattr(cloud_server, "_http_auth", None)
        monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
        monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
        monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
        monkeypatch.setenv("IDCS_AUDIENCE", "mcp-audience")
        monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
        monkeypatch.setenv("ORACLE_MCP_PORT", "8081")
        monkeypatch.setenv("ORACLE_MCP_BASE_URL", "http://127.0.0.1:8081")

        main()

        assert scopes == [["openid", "profile", "email", "oci_mcp.cloud.invoke"]]
        assert cloud_server.mcp.auth is provider
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
            _import_client("oci.fake.NotClass")


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
