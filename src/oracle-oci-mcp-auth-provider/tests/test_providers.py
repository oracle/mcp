import json
from unittest.mock import MagicMock, mock_open

import pytest

from oracle_oci_mcp_auth_provider import providers


def test_upst_configuration_detection_and_validation(tmp_path):
    environment = {
        "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
        "OCI_UPST_CLIENT_ID": "client",
        "OCI_UPST_CLIENT_SECRET": "secret",
        "OCI_UPST_REGION": "us-ashburn-1",
        "OCI_UPST_CREDENTIALS_DIR": str(tmp_path / "credentials"),
    }
    assert providers.UserPrincipalSessionTokenProvider.is_configured(environment)
    providers._validate_upst_environment(environment)
    environment["OCI_UPST_DOMAIN_URL"] = "http://identity.example.com"
    with pytest.raises(providers.UpstAuthenticationError):
        providers._validate_upst_environment(environment)


def test_upst_provider_reuses_valid_session(monkeypatch, tmp_path):
    environment = {
        "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
        "OCI_UPST_CLIENT_ID": "client",
        "OCI_UPST_CLIENT_SECRET": "secret",
        "OCI_UPST_REGION": "us-ashburn-1",
        "OCI_UPST_CREDENTIALS_DIR": str(tmp_path / "credentials"),
    }
    provider = providers.UserPrincipalSessionTokenProvider(environment)
    monkeypatch.setattr(providers, "_get_service_bearer_token", lambda _: "a.b.c")
    monkeypatch.setattr(providers, "_exchange_for_upst", lambda *_: "opaque-token")
    signer = MagicMock(return_value="signer")
    monkeypatch.setattr(providers.oci.auth.signers, "SecurityTokenSigner", signer)

    assert provider.get_context().signer == "signer"
    assert provider.get_context().signer == "signer"
    assert signer.call_count == 2
    config_file, profile = provider.get_cli_context()
    assert profile == "UPST"
    assert config_file.endswith("config")


def test_jwt_expiration_parser():
    encoded = __import__("base64").urlsafe_b64encode(json.dumps({"exp": 1234}).encode()).decode().rstrip("=")
    assert providers._jwt_expiration(f"header.{encoded}.signature") == 1234
    assert providers._jwt_expiration("opaque") is None


def test_resource_principal_provider_creates_context(monkeypatch, tmp_path):
    key_path = tmp_path / "key.pem"
    key_path.write_text("key")
    private_key = MagicMock()
    monkeypatch.setattr(
        providers.serialization, "load_pem_private_key", lambda *_, **__: private_key
    )
    monkeypatch.setattr(providers, "_security_context", lambda *_: "context")
    monkeypatch.setattr(providers, "_fetch_resource_tokens", lambda *_: ("rpt", "spst"))
    monkeypatch.setattr(providers, "_exchange_rpst", lambda *_: ("rpst", "session-key"))
    signer = MagicMock(return_value="signer")
    monkeypatch.setattr(providers.oci.auth.signers, "SecurityTokenSigner", signer)

    provider = providers.ResourcePrincipalSessionTokenProvider(
        resource_token_endpoint="https://database.example.com",
        auth_endpoint="https://auth.example.com",
        tenancy_ocid="tenancy",
        resource_ocid="resource",
        private_key_path=str(key_path),
        rci="YQ==",
        t0="2026-01-01T00:00:00Z",
        region="us-ashburn-1",
    )
    assert provider.get_context().signer == "signer"
    assert provider.get_context().service_endpoint == "https://database.example.com"
    assert provider.get_context().config == {"region": "us-ashburn-1"}
    signer.assert_called_once_with("rpst", "session-key")


def test_instance_principal_provider_uses_standard_oci_signer(monkeypatch):
    signer_factory = MagicMock(return_value="instance-signer")
    monkeypatch.setattr(
        providers.oci.auth.signers,
        "InstancePrincipalsSecurityTokenSigner",
        signer_factory,
    )

    context = providers.InstancePrincipalProvider().get_context()

    signer_factory.assert_called_once_with()
    assert context.signer == "instance-signer"
    assert context.service_endpoint is None


def test_security_token_profile_provider_builds_security_token_signer(monkeypatch):
    config = {"key_file": "/key.pem", "security_token_file": "/token"}
    monkeypatch.setattr(providers.oci.config, "from_file", MagicMock(return_value=config))
    monkeypatch.setattr(
        providers.oci.signer, "load_private_key_from_file", MagicMock(return_value="private-key")
    )
    monkeypatch.setattr("builtins.open", mock_open(read_data="security-token"))
    signer = MagicMock(return_value="security-token-signer")
    monkeypatch.setattr(providers.oci.auth.signers, "SecurityTokenSigner", signer)

    context = providers.SecurityTokenProfileProvider(
        {"OCI_CONFIG_FILE": "/config", "OCI_CONFIG_PROFILE": "TEST"}
    ).get_context()

    providers.oci.config.from_file.assert_called_once_with(
        file_location="/config", profile_name="TEST"
    )
    signer.assert_called_once_with("security-token", "private-key")
    assert context.config == config


def test_upst_post_request_and_http_error(monkeypatch, tmp_path):
    environment = {
        "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
        "OCI_UPST_CLIENT_ID": "client",
        "OCI_UPST_CLIENT_SECRET": "secret",
        "OCI_UPST_REGION": "us-ashburn-1",
        "OCI_UPST_CREDENTIALS_DIR": str(tmp_path / "credentials"),
    }
    response = MagicMock()
    response.read.return_value = b'{"token":"upst"}'
    urlopen = MagicMock()
    urlopen.return_value.__enter__.return_value = response
    monkeypatch.setattr(providers, "urlopen", urlopen)

    assert providers._post_token_request(environment, {"grant_type": "client_credentials"}) == {"token": "upst"}
    request = urlopen.call_args.args[0]
    assert request.full_url == "https://identity.example.com/oauth2/v1/token"
    assert request.data == b"grant_type=client_credentials"
    assert request.headers["Authorization"].startswith("Basic ")

    monkeypatch.setattr(
        providers,
        "urlopen",
        MagicMock(side_effect=providers.HTTPError("url", 401, "Unauthorized", {}, None)),
    )
    with pytest.raises(providers.UpstAuthenticationError, match="HTTP 401"):
        providers._post_token_request(environment, {})


def test_upst_private_key_validation_and_expiring_session_renewal(monkeypatch, tmp_path):
    key_path = tmp_path / "bad.pem"
    key_path.write_text("not-a-key")
    key_path.chmod(0o600)
    with pytest.raises(providers.UpstAuthenticationError, match="Failed to load"):
        providers._load_or_create_private_key(key_path)
    key_path.chmod(0o644)
    with pytest.raises(providers.UpstAuthenticationError, match="must not be group or world"):
        providers._load_or_create_private_key(key_path)

    environment = {
        "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
        "OCI_UPST_CLIENT_ID": "client",
        "OCI_UPST_CLIENT_SECRET": "secret",
        "OCI_UPST_REGION": "us-ashburn-1",
        "OCI_UPST_CREDENTIALS_DIR": str(tmp_path / "credentials"),
    }
    provider = providers.UserPrincipalSessionTokenProvider(environment)
    monkeypatch.setattr(providers, "_get_service_bearer_token", lambda _: "a.b.c")
    tokens = iter([_jwt(1050), _jwt(2000)])
    monkeypatch.setattr(providers, "_exchange_for_upst", lambda *_: next(tokens))
    monkeypatch.setattr(providers.time, "time", lambda: 1000)
    monkeypatch.setattr(providers.oci.auth.signers, "SecurityTokenSigner", MagicMock(return_value="signer"))

    provider.get_context()
    provider.get_context()


def test_upst_rejects_expired_token_and_missing_environment(monkeypatch, tmp_path):
    with pytest.raises(providers.UpstAuthenticationError, match="OCI_UPST_CLIENT_ID"):
        providers.UserPrincipalSessionTokenProvider({"OCI_UPST_DOMAIN_URL": "https://identity.example.com"}).get_context()

    environment = {
        "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
        "OCI_UPST_CLIENT_ID": "client",
        "OCI_UPST_CLIENT_SECRET": "secret",
        "OCI_UPST_REGION": "us-ashburn-1",
        "OCI_UPST_CREDENTIALS_DIR": str(tmp_path / "credentials"),
    }
    provider = providers.UserPrincipalSessionTokenProvider(environment)
    monkeypatch.setattr(providers, "_get_service_bearer_token", lambda _: "a.b.c")
    monkeypatch.setattr(providers, "_exchange_for_upst", lambda *_: _jwt(1000))
    monkeypatch.setattr(providers.time, "time", lambda: 1000)
    with pytest.raises(providers.UpstAuthenticationError, match="expired token"):
        provider.get_context()


def test_upst_helper_responses_and_temporary_credentials_directory(monkeypatch, tmp_path):
    environment = {
        "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
        "OCI_UPST_CLIENT_ID": "client",
        "OCI_UPST_CLIENT_SECRET": "secret",
        "OCI_UPST_REGION": "us-ashburn-1",
    }
    monkeypatch.setattr(providers, "_temporary_directory", None)
    directory = providers._credential_directory(environment)
    assert directory.is_dir()
    assert directory.stat().st_mode & 0o077 == 0

    monkeypatch.setattr(
        providers,
        "_post_token_request",
        MagicMock(side_effect=[{"access_token": "a.b.c"}, {"token": "upst"}]),
    )
    assert providers._get_service_bearer_token(environment) == "a.b.c"
    assert providers._exchange_for_upst(environment, "a.b.c", "public-key") == "upst"
    monkeypatch.setattr(providers, "_post_token_request", MagicMock(return_value={}))
    with pytest.raises(providers.UpstAuthenticationError, match="access_token"):
        providers._get_service_bearer_token(environment)
    with pytest.raises(providers.UpstAuthenticationError, match="did not contain token"):
        providers._exchange_for_upst(environment, "a.b.c", "public-key")


def test_upst_token_request_rejects_non_json_object_and_network_error(monkeypatch, tmp_path):
    environment = {
        "OCI_UPST_DOMAIN_URL": "https://identity.example.com",
        "OCI_UPST_CLIENT_ID": "client",
        "OCI_UPST_CLIENT_SECRET": "secret",
        "OCI_UPST_REGION": "us-ashburn-1",
        "OCI_UPST_CREDENTIALS_DIR": str(tmp_path / "credentials"),
    }
    response = MagicMock()
    response.read.return_value = b"[]"
    urlopen = MagicMock()
    urlopen.return_value.__enter__.return_value = response
    monkeypatch.setattr(providers, "urlopen", urlopen)
    with pytest.raises(providers.UpstAuthenticationError, match="not a JSON object"):
        providers._post_token_request(environment, {})
    monkeypatch.setattr(providers, "urlopen", MagicMock(side_effect=OSError("offline")))
    with pytest.raises(providers.UpstAuthenticationError, match="token request failed"):
        providers._post_token_request(environment, {})


def test_resource_token_fetch_uses_legacy_query_retry(monkeypatch):
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    first_response = MagicMock(status_code=401)
    second_response = MagicMock(status_code=200)
    second_response.json.return_value = {
        "resourcePrincipalToken": "rpt",
        "servicePrincipalSessionToken": "spst",
    }
    session = MagicMock()
    session.send.return_value = second_response
    get = MagicMock(return_value=first_response)
    monkeypatch.setattr(providers.requests, "get", get)
    monkeypatch.setattr(providers.requests, "Session", MagicMock(return_value=session))

    assert providers._fetch_resource_tokens(
        "https://database.example.com", "resource", "tenancy", private_key, "context", (5, 30)
    ) == ("rpt", "spst")

    assert get.call_args.kwargs["timeout"] == (5, 30)
    assert get.call_args.kwargs["headers"]["security-context"] == "context"
    prepared_request = session.send.call_args.args[0]
    assert "securityContext=context" in prepared_request.path_url
    assert session.send.call_args.kwargs["timeout"] == (5, 30)


def test_resource_token_fetch_preserves_timeout_and_error_text(monkeypatch):
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    monkeypatch.setattr(
        providers.requests,
        "get",
        MagicMock(side_effect=providers.requests.exceptions.Timeout),
    )

    with pytest.raises(RuntimeError, match="Timed out fetching resource principal tokens"):
        providers._fetch_resource_tokens(
            "https://database.example.com", "resource", "tenancy", private_key, "context", (5, 30)
        )

    response = MagicMock(status_code=500, text="server-error")
    monkeypatch.setattr(providers.requests, "get", MagicMock(return_value=response))
    monkeypatch.setattr(providers.requests, "Session", MagicMock(return_value=MagicMock(send=MagicMock(return_value=response))))
    with pytest.raises(Exception, match="Token fetch failed: 500 server-error"):
        providers._fetch_resource_tokens(
            "https://database.example.com", "resource", "tenancy", private_key, "context", (5, 30)
        )


def test_rpst_exchange_preserves_timeout_and_error_text(monkeypatch):
    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    session_key = MagicMock()
    session_key.public_key.return_value.public_bytes.return_value = b"public-key"
    monkeypatch.setattr(providers.rsa, "generate_private_key", MagicMock(return_value=session_key))
    monkeypatch.setattr(
        providers.requests,
        "post",
        MagicMock(side_effect=providers.requests.exceptions.Timeout),
    )

    with pytest.raises(RuntimeError, match="Timed out exchanging resource principal session token"):
        providers._exchange_rpst(
            "https://auth.example.com", "tenancy", "resource", private_key, "rpt", "spst", (5, 30)
        )

    response = MagicMock(status_code=500, text="auth-error")
    monkeypatch.setattr(providers.requests, "post", MagicMock(return_value=response))
    with pytest.raises(Exception, match="RPST exchange failed: 500 auth-error"):
        providers._exchange_rpst(
            "https://auth.example.com", "tenancy", "resource", private_key, "rpt", "spst", (5, 30)
        )

    response = MagicMock(status_code=200)
    response.json.return_value = {"token": "rpst"}
    monkeypatch.setattr(providers.requests, "post", MagicMock(return_value=response))
    assert providers._exchange_rpst(
        "https://auth.example.com", "tenancy", "resource", private_key, "rpt", "spst", (5, 30)
    ) == ("rpst", session_key)


def test_database_rpst_environment_constructor_preserves_imds_and_endpoint_override(monkeypatch):
    environment = {
        "TENANCY_OCID": "tenancy",
        "PRIVATE_KEY_PATH": "/private/key.pem",
        "RESOURCE_OCID": "resource",
        "RCI": "Y29udGV4dA==",
        "T0": "2026-01-01T00:00:00Z",
        "DATABASE_ENDPOINT": "https://database.override.example.com",
    }
    monkeypatch.setattr(providers, "get_region_from_instance_metadata", lambda: "us-phoenix-1")

    provider = providers.ResourcePrincipalSessionTokenProvider.from_database_environment(environment)

    assert provider.resource_token_endpoint == "https://database.override.example.com"
    assert provider.auth_endpoint == "https://auth.us-phoenix-1.oraclecloud.com"
    assert provider.region == "us-phoenix-1"


def test_imds_region_resolution_matches_existing_flow(monkeypatch):
    response = MagicMock(status_code=200)
    response.json.return_value = {"canonicalRegionName": "us-ashburn-1"}
    get = MagicMock(return_value=response)
    monkeypatch.setattr(providers.requests, "get", get)

    assert providers.get_region_from_instance_metadata() == "us-ashburn-1"
    assert get.call_args.args[0] == providers.IMDS_INSTANCE_ENDPOINT
    assert get.call_args.kwargs["headers"] == {"Authorization": "Bearer Oracle"}
    assert get.call_args.kwargs["timeout"] == 5

    response = MagicMock(status_code=500, text="unavailable")
    monkeypatch.setattr(providers.requests, "get", MagicMock(return_value=response))
    with pytest.raises(Exception, match="IMDS lookup failed: 500 unavailable"):
        providers.get_region_from_instance_metadata()

    response = MagicMock(status_code=200)
    response.json.return_value = {}
    monkeypatch.setattr(providers.requests, "get", MagicMock(return_value=response))
    with pytest.raises(Exception, match="missing canonicalRegionName/region"):
        providers.get_region_from_instance_metadata()


def test_rpst_security_context_and_query_retry_timeout(monkeypatch):
    context = providers._security_context("Y29udGV4dA==", "2026-01-01T00:00:00Z")
    payload = json.loads(context)
    assert payload["RPTSecurityContext"]["contextVersion"] == "V1"

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    first_response = MagicMock(status_code=401)
    session = MagicMock()
    session.send.side_effect = providers.requests.exceptions.Timeout
    monkeypatch.setattr(providers.requests, "get", MagicMock(return_value=first_response))
    monkeypatch.setattr(providers.requests, "Session", MagicMock(return_value=session))
    with pytest.raises(RuntimeError, match="Timed out fetching resource principal tokens"):
        providers._fetch_resource_tokens(
            "https://database.example.com", "resource", "tenancy", private_key, "context", (5, 30)
        )


def test_database_rpst_environment_constructor_rejects_missing_values(monkeypatch):
    monkeypatch.setattr(providers, "get_region_from_instance_metadata", MagicMock())
    with pytest.raises(ValueError, match="TENANCY_OCID"):
        providers.ResourcePrincipalSessionTokenProvider.from_database_environment({})


def _jwt(expiration):
    payload = json.dumps({"exp": expiration}).encode()
    return "header." + __import__("base64").urlsafe_b64encode(payload).decode().rstrip("=") + ".signature"
