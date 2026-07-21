"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from oracle_mcp_common import auth


@pytest.fixture(autouse=True)
def clear_environment(monkeypatch):
    for name in (
        "OCI_CONFIG_FILE",
        "OCI_CONFIG_PROFILE",
        "OCI_MCP_AUTH_TYPE",
        "OCI_REGION",
        "OCI_MCP_IDENTITY_DOMAIN_URL",
        "OCI_MCP_UPST_JWT_FILE",
        "OCI_MCP_IDENTITY_DOMAIN_CLIENT_ID",
        "OCI_MCP_IDENTITY_DOMAIN_CLIENT_SECRET_FILE",
        "OCI_MCP_DELEGATION_TOKEN_FILE",
        "OCI_MCP_DELEGATION_TOKEN",
        "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH",
        "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN",
        "OCI_MCP_TENANCY_ID_OVERRIDE",
        "OCI_IOT_AUTH_TYPE",
        "OCI_IOT_DELEGATION_TOKEN",
        "OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN_PATH",
        "OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN",
        "OCI_IOT_TENANCY_ID_OVERRIDE",
        "OCI_AUTH_TYPE",
        "ORACLE_MCP_AUTH_METHOD",
        "ORACLE_MCP_AUTH_PROFILE",
        "TENANCY_ID_OVERRIDE",
        "IDCS_DOMAIN",
        "IDCS_CLIENT_ID",
        "IDCS_CLIENT_SECRET",
        "IDCS_AUDIENCE",
        "ORACLE_MCP_BASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    auth._WARNED.clear()


@pytest.fixture
def api_config():
    return {
        "tenancy": "ocid1.tenancy.oc1..example",
        "user": "ocid1.user.oc1..example",
        "fingerprint": "aa:bb",
        "key_file": "/keys/api.pem",
        "region": "us-phoenix-1",
    }


def write_config(tmp_path: Path, content: str) -> Path:
    config_file = tmp_path / "config"
    config_file.write_text(content, encoding="utf-8")
    return config_file


def patch_profile(monkeypatch, config):
    loaded = MagicMock(return_value=config)
    monkeypatch.setattr(auth.oci.config, "from_file", loaded)
    return loaded


def patch_api_signer(monkeypatch):
    signer = object()
    constructor = MagicMock(return_value=signer)
    monkeypatch.setattr(auth.oci.signer, "Signer", constructor)
    return signer, constructor


def test_resolve_auth_type_uses_explicit_option_over_environment(monkeypatch):
    monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "security_token")

    assert auth.resolve_auth_type(auth.AuthOptions(auth_type="api-key")) is auth.AuthType.API_KEY


def test_resolve_auth_type_uses_canonical_environment_and_validates(monkeypatch):
    monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "resource-principal")
    assert auth.resolve_auth_type() is auth.AuthType.RESOURCE_PRINCIPAL

    monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "unknown")
    with pytest.raises(ValueError, match="Supported values:.*api_key"):
        auth.resolve_auth_type()


def test_empty_values_are_unset_and_legacy_mode_is_mapped(monkeypatch, caplog):
    monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "")
    monkeypatch.setenv("ORACLE_MCP_AUTH_METHOD", "session")

    assert auth.resolve_auth_type() is auth.AuthType.SECURITY_TOKEN
    assert "ORACLE_MCP_AUTH_METHOD is deprecated" in caplog.text


def test_profile_and_config_resolution_honor_explicit_canonical_and_legacy(monkeypatch):
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "canonical")
    monkeypatch.setenv("OCI_CONFIG_FILE", "/canonical/config")
    assert auth.resolve_profile_name(auth.AuthOptions(profile_name="explicit")) == "explicit"
    assert auth.resolve_config_file(auth.AuthOptions(config_file="/explicit/config")) == "/explicit/config"

    monkeypatch.delenv("OCI_CONFIG_PROFILE")
    monkeypatch.setenv("ORACLE_MCP_AUTH_PROFILE", "legacy")
    assert auth.resolve_profile_name() == "legacy"


def test_profile_classifier_excludes_default_inheritance(tmp_path):
    config_file = write_config(
        tmp_path,
        "[DEFAULT]\nsecurity_token_file = /tokens/inherited\n[API]\nkey_file = /keys/api.pem\n[SESSION]\nsecurity_token_file = /tokens/direct\n",
    )

    assert not auth.profile_declares_security_token(str(config_file), "API")
    assert auth.profile_declares_security_token(str(config_file), "SESSION")
    assert auth.profile_declares_security_token(str(config_file), "DEFAULT")


@pytest.mark.parametrize("content, profile", [("[API]\n", "MISSING"), ("not an ini file", "API")])
def test_profile_classifier_reports_unreadable_or_missing_sections(tmp_path, content, profile):
    config_file = write_config(tmp_path, content)
    with pytest.raises(ValueError, match="OCI_CONFIG"):
        auth.profile_declares_security_token(str(config_file), profile)


def test_api_key_context_uses_selected_profile_and_safe_warning(tmp_path, monkeypatch, caplog, api_config):
    config_file = write_config(tmp_path, "[API]\n")
    loaded = patch_profile(monkeypatch, api_config)
    signer, constructor = patch_api_signer(monkeypatch)

    context = auth.build_auth_context(
        auth.AuthOptions(auth_type="api_key", config_file=str(config_file), profile_name="API")
    )

    assert context.auth_type is auth.AuthType.API_KEY
    assert context.signer is signer
    assert context.region == "us-phoenix-1"
    assert loaded.call_args.kwargs == {"file_location": str(config_file), "profile_name": "API"}
    assert constructor.call_args.kwargs["private_key_file_location"] == "/keys/api.pem"
    assert "API-key authentication" in caplog.text
    auth.build_auth_context(auth.AuthOptions(auth_type="api_key", config_file=str(config_file), profile_name="API"))
    assert caplog.text.count("API-key authentication") == 1


def test_api_key_missing_fields_are_actionable_and_secret_safe(tmp_path, monkeypatch):
    config_file = write_config(tmp_path, "[API]\n")
    patch_profile(monkeypatch, {"tenancy": "secret-tenancy", "key_file": "/secret/key"})

    with pytest.raises(ValueError, match="user, fingerprint") as error:
        auth.build_auth_context(auth.AuthOptions(auth_type="api_key", config_file=str(config_file), profile_name="API"))

    assert "secret-tenancy" not in str(error.value)
    assert "/secret/key" not in str(error.value)


def test_security_token_context_reads_direct_token_and_constructs_signer(tmp_path, monkeypatch, api_config):
    token_file = tmp_path / "token"
    token_file.write_text(" session-token \n", encoding="utf-8")
    config_file = write_config(tmp_path, f"[SESSION]\nsecurity_token_file = {token_file}\n")
    config = {**api_config, "security_token_file": str(token_file)}
    patch_profile(monkeypatch, config)
    private_key = object()
    monkeypatch.setattr(auth.oci.signer, "load_private_key_from_file", MagicMock(return_value=private_key))
    signer = object()
    constructor = MagicMock(return_value=signer)
    monkeypatch.setattr(auth.oci.auth.signers, "SecurityTokenSigner", constructor)

    context = auth.build_auth_context(
        auth.AuthOptions(auth_type="security_token", config_file=str(config_file), profile_name="SESSION")
    )

    assert context.auth_type is auth.AuthType.SECURITY_TOKEN
    assert context.signer is signer
    assert constructor.call_args.args == ("session-token", private_key)


def test_security_token_requires_direct_declaration_even_if_sdk_config_inherits(tmp_path, monkeypatch, api_config):
    config_file = write_config(tmp_path, "[DEFAULT]\nsecurity_token_file = /inherited\n[API]\n")
    patch_profile(monkeypatch, {**api_config, "security_token_file": "/inherited"})

    with pytest.raises(ValueError, match="declared directly"):
        auth.build_auth_context(
            auth.AuthOptions(auth_type="security_token", config_file=str(config_file), profile_name="API")
        )


def test_auto_uses_api_key_when_default_token_is_inherited(tmp_path, monkeypatch, api_config):
    config_file = write_config(tmp_path, "[DEFAULT]\nsecurity_token_file = /inherited\n[API]\n")
    patch_profile(monkeypatch, {**api_config, "security_token_file": "/inherited"})
    _, constructor = patch_api_signer(monkeypatch)

    context = auth.build_auth_context(auth.AuthOptions(config_file=str(config_file), profile_name="API"))

    assert context.auth_type is auth.AuthType.API_KEY
    assert constructor.called


def test_auto_direct_unreadable_token_fails_without_api_key_fallback(tmp_path, monkeypatch, api_config):
    config_file = write_config(tmp_path, "[SESSION]\nsecurity_token_file = /unreadable\n")
    patch_profile(monkeypatch, {**api_config, "security_token_file": "/unreadable"})
    _, constructor = patch_api_signer(monkeypatch)

    with pytest.raises(ValueError, match="Unable to read security_token_file"):
        auth.build_auth_context(auth.AuthOptions(config_file=str(config_file), profile_name="SESSION"))

    assert not constructor.called


def test_profile_region_resolution_precedence(tmp_path, monkeypatch, api_config):
    config_file = write_config(tmp_path, "[API]\n")
    patch_profile(monkeypatch, api_config)
    patch_api_signer(monkeypatch)
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")

    environment_context = auth.build_auth_context(
        auth.AuthOptions(auth_type="api_key", config_file=str(config_file), profile_name="API")
    )
    explicit_context = auth.build_auth_context(
        auth.AuthOptions(auth_type="api_key", config_file=str(config_file), profile_name="API", region="eu-frankfurt-1")
    )

    assert environment_context.config["region"] == "us-ashburn-1"
    assert explicit_context.config["region"] == "eu-frankfurt-1"


@pytest.mark.parametrize("url", ["http://insecure.example", "example.identity.oraclecloud.com", "https:///no-host"])
def test_identity_domain_upst_validates_url_before_signer_construction(monkeypatch, url):
    constructor = MagicMock()
    monkeypatch.setattr(auth.oci.auth.signers, "TokenExchangeSigner", constructor)
    monkeypatch.setenv("OCI_MCP_IDENTITY_DOMAIN_URL", url)

    with pytest.raises(ValueError, match="absolute https"):
        auth.build_auth_context(auth.AuthOptions(auth_type="identity_domain_upst"))

    assert not constructor.called


def test_identity_domain_upst_constructs_with_dynamic_jwt(tmp_path, monkeypatch):
    jwt_file = tmp_path / "jwt"
    secret_file = tmp_path / "secret"
    jwt_file.write_text("first-jwt\n", encoding="utf-8")
    secret_file.write_text("client-secret\n", encoding="utf-8")
    signer = object()
    constructor = MagicMock(return_value=signer)
    monkeypatch.setattr(auth.oci.auth.signers, "TokenExchangeSigner", constructor)

    context = auth.build_auth_context(
        auth.AuthOptions(
            auth_type="identity_domain_upst",
            identity_domain_url="https://example.identity.oraclecloud.com",
            upst_jwt_file=str(jwt_file),
            identity_domain_client_id="client-id",
            identity_domain_client_secret_file=str(secret_file),
            region="us-chicago-1",
        )
    )

    jwt_reader, url, client_id, client_secret = constructor.call_args.args
    assert context.signer is signer
    assert context.config == {"region": "us-chicago-1"}
    assert (url, client_id, client_secret) == (
        "https://example.identity.oraclecloud.com",
        "client-id",
        "client-secret",
    )
    jwt_file.write_text("rotated-jwt", encoding="utf-8")
    assert jwt_reader() == "rotated-jwt"
    secret_file.write_text("rotated-client-secret", encoding="utf-8")
    assert constructor.call_args.args[3] == "client-secret"


@pytest.mark.parametrize(
    "options, variable",
    [
        (auth.AuthOptions(auth_type="identity_domain_upst"), "OCI_MCP_IDENTITY_DOMAIN_URL"),
        (auth.AuthOptions(auth_type="identity_domain_upst", identity_domain_url="https://example.com"), "OCI_MCP_IDENTITY_DOMAIN_CLIENT_ID"),
        (
            auth.AuthOptions(
                auth_type="identity_domain_upst",
                identity_domain_url="https://example.com",
                identity_domain_client_id="client-id",
            ),
            "OCI_MCP_IDENTITY_DOMAIN_CLIENT_SECRET_FILE",
        ),
    ],
)
def test_identity_domain_upst_missing_inputs_are_safe(options, variable):
    with pytest.raises(ValueError, match=variable):
        auth.build_auth_context(options)


def test_identity_domain_upst_empty_files_and_constructor_failure_are_safe(tmp_path, monkeypatch):
    jwt_file = tmp_path / "jwt"
    secret_file = tmp_path / "secret"
    jwt_file.write_text("", encoding="utf-8")
    secret_file.write_text("top-secret", encoding="utf-8")
    options = auth.AuthOptions(
        auth_type="identity_domain_upst",
        identity_domain_url="https://example.com",
        upst_jwt_file=str(jwt_file),
        identity_domain_client_id="client-id",
        identity_domain_client_secret_file=str(secret_file),
        region="us-phoenix-1",
    )
    with pytest.raises(ValueError, match="OCI_MCP_UPST_JWT_FILE") as error:
        auth.build_auth_context(options)
    assert "top-secret" not in str(error.value)

    jwt_file.write_text("jwt", encoding="utf-8")
    monkeypatch.setattr(auth.oci.auth.signers, "TokenExchangeSigner", MagicMock(side_effect=RuntimeError("top-secret")))
    with pytest.raises(ValueError, match="Unable to construct") as error:
        auth.build_auth_context(options)
    assert "top-secret" not in str(error.value)


@pytest.mark.parametrize(
    "auth_type, signer_name, expected_kwargs",
    [
        (auth.AuthType.INSTANCE_PRINCIPAL, "InstancePrincipalsSecurityTokenSigner", {}),
        (auth.AuthType.RESOURCE_PRINCIPAL, "get_resource_principals_signer", {}),
    ],
)
def test_principal_types_do_not_load_profiles(monkeypatch, auth_type, signer_name, expected_kwargs):
    signer = SimpleNamespace(region="us-phoenix-1", tenancy_id="tenant")
    constructor = MagicMock(return_value=signer)
    monkeypatch.setattr(auth.oci.auth.signers, signer_name, constructor)
    profile_loader = MagicMock()
    monkeypatch.setattr(auth.oci.config, "from_file", profile_loader)

    context = auth.build_auth_context(auth.AuthOptions(auth_type=auth_type, region="us-ashburn-1"))

    assert context.auth_type is auth_type
    assert context.config == {"region": "us-ashburn-1"}
    assert context.tenancy_id == "tenant"
    assert constructor.call_args.kwargs == expected_kwargs
    assert not profile_loader.called


@pytest.mark.parametrize(
    "auth_type, signer_name",
    [
        (auth.AuthType.INSTANCE_PRINCIPAL_DELEGATION, "InstancePrincipalsDelegationTokenSigner"),
        (auth.AuthType.RESOURCE_PRINCIPAL_DELEGATION, "get_resource_principal_delegation_token_signer"),
    ],
)
def test_delegation_principal_types_read_file_tokens(tmp_path, monkeypatch, auth_type, signer_name):
    token_file = tmp_path / "delegation"
    token_file.write_text(" delegation-token \n", encoding="utf-8")
    signer = SimpleNamespace(region="us-phoenix-1")
    constructor = MagicMock(return_value=signer)
    monkeypatch.setattr(auth.oci.auth.signers, signer_name, constructor)

    context = auth.build_auth_context(auth.AuthOptions(auth_type=auth_type, delegation_token_file=str(token_file)))

    assert context.signer is signer
    assert constructor.call_args.kwargs["delegation_token"] == "delegation-token"


def test_delegation_sources_validate_conflicts_and_legacy_warning(tmp_path, monkeypatch, caplog):
    token_file = tmp_path / "delegation"
    token_file.write_text("token", encoding="utf-8")
    with pytest.raises(ValueError, match="Set only OCI_MCP_DELEGATION_TOKEN_FILE"):
        auth.build_auth_context(
            auth.AuthOptions(
                auth_type="instance_principal_delegation",
                delegation_token_file=str(token_file),
                delegation_token="inline",
            )
        )
    with pytest.raises(ValueError, match="OCI_MCP_DELEGATION_TOKEN_FILE is required"):
        auth.build_auth_context(auth.AuthOptions(auth_type="instance_principal_delegation"))

    monkeypatch.setenv("OCI_IOT_DELEGATION_TOKEN", "legacy-token")
    signer = SimpleNamespace(region="us-phoenix-1")
    constructor = MagicMock(return_value=signer)
    monkeypatch.setattr(auth.oci.auth.signers, "InstancePrincipalsDelegationTokenSigner", constructor)
    auth.build_auth_context(auth.AuthOptions(auth_type="instance_principal_delegation"))
    assert constructor.call_args.kwargs["delegation_token"] == "legacy-token"
    assert "legacy-token" not in caplog.text
    assert "deprecated" in caplog.text


def test_oke_uses_default_path_and_inline_compatibility(monkeypatch, caplog):
    constructor = MagicMock(return_value=SimpleNamespace(region="us-phoenix-1"))
    monkeypatch.setattr(auth.oci.auth.signers, "get_oke_workload_identity_resource_principal_signer", constructor)

    auth.build_auth_context(auth.AuthOptions(auth_type="oke_workload_identity"))
    assert constructor.call_args.kwargs == {}

    auth.build_auth_context(
        auth.AuthOptions(auth_type="oke_workload_identity", oke_service_account_token_path="/token")
    )
    assert constructor.call_args.kwargs == {"service_account_token_path": "/token"}

    auth.build_auth_context(
        auth.AuthOptions(auth_type="oke_workload_identity", oke_service_account_token="inline-token")
    )
    assert constructor.call_args.kwargs == {"service_account_token": "inline-token"}
    assert "inline-token" not in caplog.text


def test_oke_conflicting_overrides_and_signer_failures_are_safe(monkeypatch):
    with pytest.raises(ValueError, match="Set only OCI_MCP_OKE"):
        auth.build_auth_context(
            auth.AuthOptions(
                auth_type="oke_workload_identity",
                oke_service_account_token_path="/token",
                oke_service_account_token="inline",
            )
        )
    monkeypatch.setattr(
        auth.oci.auth.signers,
        "InstancePrincipalsSecurityTokenSigner",
        MagicMock(side_effect=RuntimeError("secret details")),
    )
    with pytest.raises(ValueError, match="Unable to construct") as error:
        auth.build_auth_context(auth.AuthOptions(auth_type="instance_principal"))
    assert "secret details" not in str(error.value)


@pytest.mark.parametrize(
    "auth_type, signer_name, options",
    [
        (auth.AuthType.INSTANCE_PRINCIPAL, "InstancePrincipalsSecurityTokenSigner", auth.AuthOptions(auth_type="instance_principal")),
        (auth.AuthType.RESOURCE_PRINCIPAL, "get_resource_principals_signer", auth.AuthOptions(auth_type="resource_principal")),
        (
            auth.AuthType.INSTANCE_PRINCIPAL_DELEGATION,
            "InstancePrincipalsDelegationTokenSigner",
            auth.AuthOptions(auth_type="instance_principal_delegation", delegation_token="token"),
        ),
        (
            auth.AuthType.RESOURCE_PRINCIPAL_DELEGATION,
            "get_resource_principal_delegation_token_signer",
            auth.AuthOptions(auth_type="resource_principal_delegation", delegation_token="token"),
        ),
        (
            auth.AuthType.OKE_WORKLOAD_IDENTITY,
            "get_oke_workload_identity_resource_principal_signer",
            auth.AuthOptions(auth_type="oke_workload_identity"),
        ),
    ],
)
def test_every_principal_signer_failure_is_secret_safe(monkeypatch, auth_type, signer_name, options):
    monkeypatch.setattr(auth.oci.auth.signers, signer_name, MagicMock(side_effect=RuntimeError("private details")))

    with pytest.raises(ValueError, match=f"Unable to construct the {auth_type.value} signer") as error:
        auth.build_auth_context(options)

    assert "private details" not in str(error.value)


def test_canonical_values_override_aliases_and_tenancy_alias_is_supported(monkeypatch):
    monkeypatch.setenv("OCI_MCP_AUTH_TYPE", "instance_principal")
    monkeypatch.setenv("OCI_IOT_AUTH_TYPE", "resource_principal")
    signer = SimpleNamespace(region="us-phoenix-1", tenancy_id=None)
    monkeypatch.setattr(auth.oci.auth.signers, "InstancePrincipalsSecurityTokenSigner", MagicMock(return_value=signer))
    monkeypatch.setenv("TENANCY_ID_OVERRIDE", "legacy-tenancy")

    context = auth.build_auth_context()

    assert context.auth_type is auth.AuthType.INSTANCE_PRINCIPAL
    assert context.tenancy_id == "legacy-tenancy"


def test_secret_file_reader_rejects_missing_unreadable_and_empty(tmp_path):
    with pytest.raises(ValueError, match="FILE is required"):
        auth._read_required_secret_file(None, "FILE")
    with pytest.raises(ValueError, match="Unable to read FILE"):
        auth._read_required_secret_file(str(tmp_path / "missing"), "FILE")
    empty = tmp_path / "empty"
    empty.write_text(" \n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        auth._read_required_secret_file(str(empty), "FILE")


def set_idcs_http_environment(monkeypatch, **overrides):
    values = {
        "IDCS_DOMAIN": "idcs.example.com",
        "IDCS_CLIENT_ID": "client-id",
        "IDCS_CLIENT_SECRET": "client-secret",
        "IDCS_AUDIENCE": "mcp-audience",
        "ORACLE_MCP_BASE_URL": "https://mcp.example.com",
        "OCI_REGION": "us-phoenix-1",
    }
    values.update(overrides)
    for name, value in values.items():
        if value is not None:
            monkeypatch.setenv(name, value)


def test_idcs_http_auth_builds_provider_and_creates_request_context(monkeypatch):
    set_idcs_http_environment(monkeypatch)
    provider = object()
    provider_constructor = MagicMock(return_value=provider)
    monkeypatch.setattr(auth, "OCIProvider", provider_constructor)
    signer = object()
    signer_constructor = MagicMock(return_value=signer)
    monkeypatch.setattr(auth.oci.auth.signers, "TokenExchangeSigner", signer_constructor)

    http_auth = auth.build_idcs_http_auth(["openid", "oci_mcp.example.invoke"])
    context = http_auth.context_for("request-token")

    assert http_auth.provider is provider
    assert provider_constructor.call_args.kwargs == {
        "config_url": "https://idcs.example.com/.well-known/openid-configuration",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "audience": "mcp-audience",
        "required_scopes": ["openid", "oci_mcp.example.invoke"],
        "base_url": "https://mcp.example.com",
    }
    assert signer_constructor.call_args.args == (
        "request-token",
        "https://idcs.example.com",
        "client-id",
        "client-secret",
    )
    assert signer_constructor.call_args.kwargs == {"region": "us-phoenix-1"}
    assert context.config == {"region": "us-phoenix-1"}
    assert context.signer is signer
    assert "additional_user_agent" not in context.config


def test_idcs_http_auth_explicit_options_and_request_region_win(monkeypatch):
    set_idcs_http_environment(
        monkeypatch,
        IDCS_DOMAIN="environment.example.com",
        IDCS_CLIENT_ID="environment-client",
        IDCS_CLIENT_SECRET="environment-secret",
        IDCS_AUDIENCE="environment-audience",
        ORACLE_MCP_BASE_URL="https://environment.example.com",
        OCI_REGION="us-ashburn-1",
    )
    provider_constructor = MagicMock(return_value=object())
    monkeypatch.setattr(auth, "OCIProvider", provider_constructor)
    signer_constructor = MagicMock(return_value=object())
    monkeypatch.setattr(auth.oci.auth.signers, "TokenExchangeSigner", signer_constructor)

    http_auth = auth.build_idcs_http_auth(
        ["openid"],
        auth.IDCSHttpAuthOptions(
            domain="https://options.example.com",
            client_id="options-client",
            client_secret="options-secret",
            audience="options-audience",
            base_url="https://mcp.options.example.com",
            region="us-chicago-1",
        ),
    )
    context = http_auth.context_for("request-token", region="eu-frankfurt-1")

    assert provider_constructor.call_args.kwargs["config_url"] == (
        "https://options.example.com/.well-known/openid-configuration"
    )
    assert provider_constructor.call_args.kwargs["client_id"] == "options-client"
    assert context.region == "eu-frankfurt-1"
    assert signer_constructor.call_args.kwargs == {"region": "eu-frankfurt-1"}


@pytest.mark.parametrize(
    "environment, message",
    [
        ({"IDCS_CLIENT_SECRET": None}, "IDCS_CLIENT_SECRET"),
        ({"IDCS_DOMAIN": "http://insecure.example.com"}, "IDCS_DOMAIN"),
        ({"IDCS_DOMAIN": "idcs.example.com/path"}, "IDCS_DOMAIN"),
        ({"ORACLE_MCP_BASE_URL": "mcp.example.com"}, "ORACLE_MCP_BASE_URL"),
    ],
)
def test_idcs_http_auth_rejects_invalid_provider_inputs_before_construction(monkeypatch, environment, message):
    set_idcs_http_environment(monkeypatch, **environment)
    provider_constructor = MagicMock()
    monkeypatch.setattr(auth, "OCIProvider", provider_constructor)

    with pytest.raises(ValueError, match=message):
        auth.build_idcs_http_auth(["openid"])

    assert not provider_constructor.called


def test_idcs_http_auth_requires_scopes_and_safe_request_token_and_region(monkeypatch):
    set_idcs_http_environment(monkeypatch, OCI_REGION=None)
    provider_constructor = MagicMock(return_value=object())
    signer_constructor = MagicMock()
    monkeypatch.setattr(auth, "OCIProvider", provider_constructor)
    monkeypatch.setattr(auth.oci.auth.signers, "TokenExchangeSigner", signer_constructor)

    with pytest.raises(ValueError, match="required_scopes"):
        auth.build_idcs_http_auth([])
    with pytest.raises(ValueError, match="required_scopes"):
        auth.build_idcs_http_auth("openid")

    http_auth = auth.build_idcs_http_auth(["openid"])
    with pytest.raises(ValueError, match="authenticated IDCS access token"):
        http_auth.context_for(None)
    assert not signer_constructor.called

    with pytest.raises(ValueError, match="OCI_REGION") as error:
        http_auth.context_for("request-token")
    assert "request-token" not in str(error.value)
    assert not signer_constructor.called


def test_idcs_http_auth_sanitizes_token_exchange_failures(monkeypatch):
    secret = "client-secret-value"
    token = "request-token-value"
    set_idcs_http_environment(monkeypatch, IDCS_CLIENT_SECRET=secret)
    monkeypatch.setattr(auth, "OCIProvider", MagicMock(return_value=object()))
    monkeypatch.setattr(
        auth.oci.auth.signers,
        "TokenExchangeSigner",
        MagicMock(side_effect=RuntimeError(f"{secret} {token}")),
    )

    http_auth = auth.build_idcs_http_auth(["openid"])
    with pytest.raises(ValueError, match="Unable to construct") as error:
        http_auth.context_for(token)

    assert secret not in str(error.value)
    assert token not in str(error.value)
    assert secret not in repr(http_auth)
