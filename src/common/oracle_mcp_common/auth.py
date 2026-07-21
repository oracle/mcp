"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import configparser
import logging
import os
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse

import oci
from fastmcp.server.auth.providers.oci import OCIProvider

LOGGER = logging.getLogger(__name__)
SESSION_AUTH_GUIDANCE = "Run `oci session authenticate` to use session-token authentication."
COMPATIBILITY_WINDOW = (
    "Compatibility is available from 0.1.0 until the later of 180 days or two "
    "published adopter-server release waves; removal is no earlier than 0.2.0."
)


class AuthType(StrEnum):
    """Supported OCI SDK credential resolution modes."""

    AUTO = "auto"
    API_KEY = "api_key"
    SECURITY_TOKEN = "security_token"
    IDENTITY_DOMAIN_UPST = "identity_domain_upst"
    INSTANCE_PRINCIPAL = "instance_principal"
    RESOURCE_PRINCIPAL = "resource_principal"
    INSTANCE_PRINCIPAL_DELEGATION = "instance_principal_delegation"
    RESOURCE_PRINCIPAL_DELEGATION = "resource_principal_delegation"
    OKE_WORKLOAD_IDENTITY = "oke_workload_identity"


PROFILE_AUTH_TYPES = {AuthType.AUTO, AuthType.API_KEY, AuthType.SECURITY_TOKEN}


@dataclass(frozen=True)
class AuthOptions:
    """Explicit resolver inputs. Non-empty values override environment variables."""

    auth_type: AuthType | str | None = None
    config_file: str | None = None
    profile_name: str | None = None
    region: str | None = None
    identity_domain_url: str | None = None
    upst_jwt_file: str | None = None
    identity_domain_client_id: str | None = None
    identity_domain_client_secret_file: str | None = None
    delegation_token_file: str | None = None
    delegation_token: str | None = None
    oke_service_account_token_path: str | None = None
    oke_service_account_token: str | None = None
    tenancy_id_override: str | None = None


@dataclass(frozen=True)
class AuthContext:
    """Native OCI SDK authentication ingredients owned by an adopting server."""

    auth_type: AuthType
    config: dict[str, Any]
    signer: Any | None
    tenancy_id: str | None
    region: str | None
    profile_name: str | None


@dataclass(frozen=True)
class IDCSHttpAuthOptions:
    """Explicit HTTP IDCS inputs. Non-empty values override environment variables."""

    domain: str | None = None
    client_id: str | None = None
    client_secret: str | None = field(default=None, repr=False)
    audience: str | None = None
    base_url: str | None = None
    region: str | None = None


@dataclass(frozen=True)
class IDCSHttpAuthContext:
    """OCI SDK configuration and signer derived from one authenticated HTTP request."""

    config: dict[str, Any]
    signer: Any = field(repr=False)
    region: str = ""


@dataclass(frozen=True)
class IDCSHttpAuth:
    """Shared HTTP IDCS authentication policy for an adopting FastMCP server.

    The provider is configured once during server startup.  A separate context is
    produced for each authenticated request so a caller's signer cannot be
    reused for a different caller.
    """

    provider: Any = field(repr=False)
    _identity_domain_url: str = field(repr=False)
    _client_id: str = field(repr=False)
    _client_secret: str = field(repr=False)
    _configured_region: str | None = field(repr=False)

    def context_for(self, access_token: str | None, *, region: str | None = None) -> IDCSHttpAuthContext:
        """Exchange an explicitly supplied authenticated request token for OCI signing."""
        token = _nonempty(access_token)
        if not token:
            raise ValueError("HTTP requests require an authenticated IDCS access token.")
        resolved_region = _nonempty(region) or self._configured_region or _env("OCI_REGION")
        if not resolved_region:
            raise ValueError("HTTP requests require an explicit region or OCI_REGION.")
        try:
            signer = oci.auth.signers.TokenExchangeSigner(
                token,
                self._identity_domain_url,
                self._client_id,
                self._client_secret,
                region=resolved_region,
            )
        except Exception as error:
            raise ValueError("Unable to construct the HTTP IDCS token-exchange signer") from error
        return IDCSHttpAuthContext(config={"region": resolved_region}, signer=signer, region=resolved_region)


@dataclass(frozen=True)
class _ResolvedInputs:
    """Normalized resolver inputs after applying option and environment precedence."""

    auth_type: AuthType
    config_file: str
    profile_name: str
    region: str | None
    identity_domain_url: str | None
    upst_jwt_file: str | None
    identity_domain_client_id: str | None
    identity_domain_client_secret_file: str | None
    delegation_token_file: str | None
    delegation_token: str | None
    oke_service_account_token_path: str | None
    oke_service_account_token: str | None
    tenancy_id_override: str | None


@dataclass(frozen=True)
class _ResolvedIDCSHttpInputs:
    """Validated shared settings for the HTTP IDCS provider and signer."""

    domain_url: str
    client_id: str
    client_secret: str = field(repr=False)
    audience: str = ""
    base_url: str = ""
    region: str | None = None


def build_auth_context(options: AuthOptions | None = None) -> AuthContext:
    """Resolve explicit or configured outbound OCI SDK authentication."""
    inputs = _resolve_inputs(options)

    if inputs.auth_type in PROFILE_AUTH_TYPES:
        return _build_profile_context(inputs)
    if inputs.auth_type is AuthType.IDENTITY_DOMAIN_UPST:
        return _build_token_exchange_context(inputs)
    return _build_principal_context(inputs)


def build_idcs_http_auth(
    required_scopes: Sequence[str], options: IDCSHttpAuthOptions | None = None
) -> IDCSHttpAuth:
    """Build the HTTP-only IDCS policy used by an adopting FastMCP server.

    This function deliberately does not inspect transport host or port, retrieve
    a FastMCP request token, assign ``mcp.auth``, or construct OCI service
    clients. The server owns those lifecycle decisions and passes each
    authenticated access token to :meth:`IDCSHttpAuth.context_for`.
    """
    scopes = _normalize_required_scopes(required_scopes)
    inputs = _resolve_idcs_http_inputs(options)
    try:
        provider = OCIProvider(
            config_url=f"{inputs.domain_url}/.well-known/openid-configuration",
            client_id=inputs.client_id,
            client_secret=inputs.client_secret,
            audience=inputs.audience,
            required_scopes=scopes,
            base_url=inputs.base_url,
        )
    except Exception as error:
        raise ValueError("Unable to construct the HTTP IDCS authentication provider") from error
    return IDCSHttpAuth(
        provider=provider,
        _identity_domain_url=inputs.domain_url,
        _client_id=inputs.client_id,
        _client_secret=inputs.client_secret,
        _configured_region=inputs.region,
    )


def resolve_auth_type(options: AuthOptions | None = None) -> AuthType:
    """Resolve an auth type with explicit and canonical-value precedence."""
    options = options or AuthOptions()
    value = _nonempty(options.auth_type) or _env("OCI_MCP_AUTH_TYPE")
    if value is None:
        value = _legacy_env("OCI_IOT_AUTH_TYPE", "OCI_AUTH_TYPE", "ORACLE_MCP_AUTH_METHOD")
    normalized = _normalize_auth_type(value or AuthType.AUTO.value)
    try:
        return AuthType(normalized)
    except ValueError as error:
        supported = ", ".join(auth_type.value for auth_type in AuthType)
        raise ValueError(f"Unsupported OCI authentication type. Supported values: {supported}") from error


def _resolve_inputs(options: AuthOptions | None) -> _ResolvedInputs:
    options = options or AuthOptions()
    return _ResolvedInputs(
        auth_type=resolve_auth_type(options),
        config_file=resolve_config_file(options),
        profile_name=resolve_profile_name(options),
        region=_resolve_region(options.region),
        identity_domain_url=_option_or_env(options.identity_domain_url, "OCI_MCP_IDENTITY_DOMAIN_URL"),
        upst_jwt_file=_option_or_env(options.upst_jwt_file, "OCI_MCP_UPST_JWT_FILE"),
        identity_domain_client_id=_option_or_env(
            options.identity_domain_client_id, "OCI_MCP_IDENTITY_DOMAIN_CLIENT_ID"
        ),
        identity_domain_client_secret_file=_option_or_env(
            options.identity_domain_client_secret_file, "OCI_MCP_IDENTITY_DOMAIN_CLIENT_SECRET_FILE"
        ),
        delegation_token_file=_option_or_env(options.delegation_token_file, "OCI_MCP_DELEGATION_TOKEN_FILE"),
        delegation_token=_option_or_env(options.delegation_token, "OCI_MCP_DELEGATION_TOKEN"),
        oke_service_account_token_path=_option_or_env(
            options.oke_service_account_token_path, "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH"
        ),
        oke_service_account_token=_option_or_env(options.oke_service_account_token, "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN"),
        tenancy_id_override=_option_or_env(options.tenancy_id_override, "OCI_MCP_TENANCY_ID_OVERRIDE"),
    )


def _resolve_idcs_http_inputs(options: IDCSHttpAuthOptions | None) -> _ResolvedIDCSHttpInputs:
    options = options or IDCSHttpAuthOptions()
    values = {
        "IDCS_DOMAIN": _option_or_env(options.domain, "IDCS_DOMAIN"),
        "IDCS_CLIENT_ID": _option_or_env(options.client_id, "IDCS_CLIENT_ID"),
        "IDCS_CLIENT_SECRET": _option_or_env(options.client_secret, "IDCS_CLIENT_SECRET"),
        "IDCS_AUDIENCE": _option_or_env(options.audience, "IDCS_AUDIENCE"),
        "ORACLE_MCP_BASE_URL": _option_or_env(options.base_url, "ORACLE_MCP_BASE_URL"),
    }
    missing = [name for name, value in values.items() if value is None]
    if missing:
        raise ValueError(f"HTTP IDCS authentication requires: {', '.join(missing)}")
    return _ResolvedIDCSHttpInputs(
        domain_url=_normalize_idcs_domain(values["IDCS_DOMAIN"]),
        client_id=values["IDCS_CLIENT_ID"],
        client_secret=values["IDCS_CLIENT_SECRET"],
        audience=values["IDCS_AUDIENCE"],
        base_url=_validate_mcp_base_url(values["ORACLE_MCP_BASE_URL"]),
        region=_nonempty(options.region) or _env("OCI_REGION"),
    )


def resolve_profile_name(options: AuthOptions | None = None) -> str:
    """Resolve the OCI SDK profile name without interpreting empty values as profiles."""
    options = options or AuthOptions()
    return (
        _nonempty(options.profile_name)
        or _env("OCI_CONFIG_PROFILE")
        or _legacy_env("ORACLE_MCP_AUTH_PROFILE")
        or oci.config.DEFAULT_PROFILE
    )


def resolve_config_file(options: AuthOptions | None = None) -> str:
    """Resolve the OCI SDK configuration location."""
    options = options or AuthOptions()
    return _nonempty(options.config_file) or _env("OCI_CONFIG_FILE") or oci.config.DEFAULT_LOCATION


def profile_declares_security_token(config_file: str, profile_name: str) -> bool:
    """Classify only the selected profile's raw section, excluding DEFAULT inheritance."""
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with Path(config_file).expanduser().open(encoding="utf-8") as config:
            parser.read_file(config)
    except (OSError, configparser.Error) as error:
        raise ValueError("Unable to read OCI_CONFIG_FILE for the selected profile") from error

    section = profile_name if profile_name != oci.config.DEFAULT_PROFILE else parser.default_section
    if section != parser.default_section and not parser.has_section(section):
        raise ValueError("Selected OCI_CONFIG_PROFILE was not found in OCI_CONFIG_FILE")
    return _raw_profile_has_option(parser, section, "security_token_file")


def _raw_profile_has_option(parser: configparser.ConfigParser, section: str, option: str) -> bool:
    """Check a section without ConfigParser's normal DEFAULT-value inheritance."""
    if section == parser.default_section:
        return option in parser.defaults()
    # ConfigParser's public accessors merge DEFAULT values, which can select the
    # wrong OCI principal. _sections is its raw parsed representation.
    return option in parser._sections.get(section, {})


def _build_profile_context(inputs: _ResolvedInputs) -> AuthContext:
    config = _load_profile(inputs.config_file, inputs.profile_name)
    selected_auth_type = inputs.auth_type
    direct_session = profile_declares_security_token(inputs.config_file, inputs.profile_name)

    if selected_auth_type is AuthType.AUTO:
        selected_auth_type = AuthType.SECURITY_TOKEN if direct_session else AuthType.API_KEY
    if selected_auth_type is AuthType.SECURITY_TOKEN and not direct_session:
        raise ValueError(
            "security_token_file must be declared directly in the selected OCI_CONFIG_PROFILE; "
            "declare it in that profile rather than [DEFAULT]."
        )

    if selected_auth_type is AuthType.SECURITY_TOKEN:
        signer = _security_token_signer(config)
    else:
        signer = _api_key_signer(config)
        _warn_once("api_key", f"API-key authentication is in use. {SESSION_AUTH_GUIDANCE}")

    region = inputs.region or config.get("region")
    if region:
        config["region"] = region
    return AuthContext(selected_auth_type, config, signer, config.get("tenancy"), region, inputs.profile_name)


def _load_profile(config_file: str, profile_name: str) -> dict[str, Any]:
    try:
        return dict(oci.config.from_file(file_location=config_file, profile_name=profile_name))
    except Exception as error:
        raise ValueError("Unable to load the selected OCI profile") from error


def _api_key_signer(config: dict[str, Any]) -> Any:
    _require_config_fields(config, "API-key authentication", "tenancy", "user", "fingerprint", "key_file")
    try:
        return oci.signer.Signer(
            tenancy=config["tenancy"],
            user=config["user"],
            fingerprint=config["fingerprint"],
            private_key_file_location=config["key_file"],
            pass_phrase=config.get("pass_phrase"),
        )
    except Exception as error:
        raise ValueError("Unable to construct the API-key signer from the selected OCI profile") from error


def _security_token_signer(config: dict[str, Any]) -> Any:
    _require_config_fields(
        config,
        "security-token authentication",
        "tenancy",
        "user",
        "fingerprint",
        "key_file",
        "security_token_file",
    )
    token = _read_required_secret_file(config["security_token_file"], "security_token_file")
    try:
        private_key = oci.signer.load_private_key_from_file(config["key_file"], config.get("pass_phrase"))
        return oci.auth.signers.SecurityTokenSigner(token, private_key)
    except Exception as error:
        raise ValueError("Unable to construct the security-token signer from the selected OCI profile") from error


def _build_principal_context(inputs: _ResolvedInputs) -> AuthContext:
    try:
        if inputs.auth_type is AuthType.INSTANCE_PRINCIPAL:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        elif inputs.auth_type is AuthType.RESOURCE_PRINCIPAL:
            signer = oci.auth.signers.get_resource_principals_signer()
        elif inputs.auth_type is AuthType.INSTANCE_PRINCIPAL_DELEGATION:
            signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
                delegation_token=_delegation_token(inputs)
            )
        elif inputs.auth_type is AuthType.RESOURCE_PRINCIPAL_DELEGATION:
            signer = oci.auth.signers.get_resource_principal_delegation_token_signer(
                delegation_token=_delegation_token(inputs)
            )
        elif inputs.auth_type is AuthType.OKE_WORKLOAD_IDENTITY:
            signer = oci.auth.signers.get_oke_workload_identity_resource_principal_signer(
                **_oke_signer_kwargs(inputs)
            )
        else:
            raise AssertionError(f"Unhandled auth type: {inputs.auth_type}")
    except ValueError:
        raise
    except Exception as error:
        raise ValueError(f"Unable to construct the {inputs.auth_type.value} signer") from error

    signer_region = getattr(signer, "region", None)
    region = inputs.region or signer_region
    config: dict[str, Any] = {}
    if region:
        config["region"] = region
    tenancy_id = (
        getattr(signer, "tenancy_id", None)
        or inputs.tenancy_id_override
        or _legacy_env("OCI_IOT_TENANCY_ID_OVERRIDE", "TENANCY_ID_OVERRIDE")
    )
    return AuthContext(inputs.auth_type, config, signer, tenancy_id, region, None)


def _build_token_exchange_context(inputs: _ResolvedInputs) -> AuthContext:
    url = inputs.identity_domain_url
    _validate_identity_domain_url(url)
    jwt_file = inputs.upst_jwt_file
    client_id = inputs.identity_domain_client_id
    secret_file = inputs.identity_domain_client_secret_file
    if not client_id:
        raise ValueError("OCI_MCP_IDENTITY_DOMAIN_CLIENT_ID is required for identity_domain_upst")
    client_secret = _read_required_secret_file(secret_file, "OCI_MCP_IDENTITY_DOMAIN_CLIENT_SECRET_FILE")
    _read_required_secret_file(jwt_file, "OCI_MCP_UPST_JWT_FILE")
    region = inputs.region
    if not region:
        raise ValueError("identity_domain_upst requires an explicit region or OCI_REGION")

    def read_jwt() -> str:
        return _read_required_secret_file(jwt_file, "OCI_MCP_UPST_JWT_FILE")

    try:
        signer = oci.auth.signers.TokenExchangeSigner(read_jwt, url, client_id, client_secret, region=region)
    except Exception as error:
        raise ValueError("Unable to construct the identity_domain_upst signer") from error
    return AuthContext(AuthType.IDENTITY_DOMAIN_UPST, {"region": region}, signer, None, region, None)


def _delegation_token(inputs: _ResolvedInputs) -> str:
    token_file = inputs.delegation_token_file
    inline = inputs.delegation_token
    if inline is None:
        inline = _legacy_env("OCI_IOT_DELEGATION_TOKEN")
    if token_file and inline:
        raise ValueError("Set only OCI_MCP_DELEGATION_TOKEN_FILE; inline delegation tokens are deprecated.")
    if token_file:
        return _read_required_secret_file(token_file, "OCI_MCP_DELEGATION_TOKEN_FILE")
    if inline:
        _warn_once(
            "inline_delegation_token",
            "OCI_MCP_DELEGATION_TOKEN is deprecated; use OCI_MCP_DELEGATION_TOKEN_FILE. "
            f"{COMPATIBILITY_WINDOW}",
        )
        return inline
    raise ValueError("OCI_MCP_DELEGATION_TOKEN_FILE is required for delegation authentication")


def _oke_signer_kwargs(inputs: _ResolvedInputs) -> dict[str, str]:
    token_path = inputs.oke_service_account_token_path
    inline = inputs.oke_service_account_token
    if token_path is None:
        token_path = _legacy_env("OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN_PATH")
    if inline is None:
        inline = _legacy_env("OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN")
    if token_path and inline:
        raise ValueError("Set only OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH; inline OKE tokens are deprecated.")
    if token_path:
        return {"service_account_token_path": token_path}
    if inline:
        _warn_once(
            "inline_oke_token",
            "OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN is deprecated; use OCI_MCP_OKE_SERVICE_ACCOUNT_TOKEN_PATH. "
            f"{COMPATIBILITY_WINDOW}",
        )
        return {"service_account_token": inline}
    return {}


def _resolve_region(explicit_region: str | None) -> str | None:
    return _nonempty(explicit_region) or _env("OCI_REGION")


def _validate_identity_domain_url(url: str | None) -> None:
    if not url:
        raise ValueError("OCI_MCP_IDENTITY_DOMAIN_URL is required for identity_domain_upst")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("OCI_MCP_IDENTITY_DOMAIN_URL must be an absolute https:// URL with a host")


def _normalize_idcs_domain(value: str | None) -> str:
    """Return the canonical HTTPS Identity Domains origin for the legacy host input."""
    if not value:
        raise ValueError("IDCS_DOMAIN is required")
    url = value if "://" in value else f"https://{value}"
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.path not in ("", "/")
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("IDCS_DOMAIN must be an HTTPS Identity Domains host")
    return f"https://{parsed.netloc}"


def _validate_mcp_base_url(value: str | None) -> str:
    if not value:
        raise ValueError("ORACLE_MCP_BASE_URL is required")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError("ORACLE_MCP_BASE_URL must be an absolute http:// or https:// URL")
    return value


def _normalize_required_scopes(required_scopes: Sequence[str]) -> list[str]:
    if isinstance(required_scopes, str):
        raise ValueError("required_scopes must be a non-empty sequence of scope values")
    scopes = [scope for value in required_scopes if (scope := _nonempty(value))]
    if not scopes:
        raise ValueError("required_scopes must contain at least one scope value")
    return scopes


def _require_config_fields(config: dict[str, Any], description: str, *fields: str) -> None:
    missing = [field for field in fields if not _nonempty(config.get(field))]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"{description} profile is missing required fields: {names}. {SESSION_AUTH_GUIDANCE}")


def _read_required_secret_file(path: str | None, variable: str) -> str:
    if not path:
        raise ValueError(f"{variable} is required")
    try:
        value = Path(path).expanduser().read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ValueError(f"Unable to read {variable}") from error
    if not value:
        raise ValueError(f"{variable} must reference a non-empty file")
    return value


def _normalize_auth_type(value: str | AuthType) -> str:
    normalized = str(value).strip().lower().replace("-", "_")
    legacy_mapping = {
        "api_key_auth": AuthType.API_KEY.value,
        "api_key": AuthType.API_KEY.value,
        "security_token": AuthType.SECURITY_TOKEN.value,
        "session_token": AuthType.SECURITY_TOKEN.value,
        "session": AuthType.SECURITY_TOKEN.value,
    }
    return legacy_mapping.get(normalized, normalized)


def _nonempty(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _env(name: str) -> str | None:
    return _nonempty(os.getenv(name))


def _option_or_env(option: str | None, environment_variable: str) -> str | None:
    return _nonempty(option) or _env(environment_variable)


# Compatibility aliases remain separate from canonical input resolution so they
# can be removed as a bounded migration concern.
def _legacy_env(*names: str) -> str | None:
    for name in names:
        value = _env(name)
        if value:
            _warn_once(f"legacy_{name}", f"{name} is deprecated; use the OCI_MCP_* equivalent. {COMPATIBILITY_WINDOW}")
            return value
    return None


_WARNED: set[str] = set()


def _warn_once(key: str, message: str) -> None:
    if key not in _WARNED:
        _WARNED.add(key)
        LOGGER.warning(message)
