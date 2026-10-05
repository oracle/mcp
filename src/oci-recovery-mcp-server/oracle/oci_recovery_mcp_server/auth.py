"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Credential resolution for both transports, and the tenancy that follows from it.

stdio runs on the operator's own OCI profile; HTTP authenticates every caller
against an OCI IAM (IDCS) domain and derives a per-request signer from their
token. Both paths converge on ``_config_and_signer()``, which is the only thing
the client factories need to know about.
"""

import os
from typing import Optional

import oci
from fastmcp.server.dependencies import get_access_token, get_http_request
from fastmcp.utilities.auth import parse_scopes
from oracle_mcp_common import (
    AuthOptions,
    AuthType,
    IDCSHttpAuth,
    IDCSHttpAuthOptions,
    build_auth_context,
    build_idcs_http_auth,
    resolve_auth_type,
    resolve_config_file,
    resolve_profile_name,
)

from . import __project__, __version__
from .logging_setup import logger

_USER_AGENT_NAME = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
_ADDITIONAL_UA = f"{_USER_AGENT_NAME}/{__version__}"


# Auth-type variables the shared library reads ahead of ORACLE_MCP_AUTH_METHOD, in
# its own order of precedence. Anything set here already decides the auth type, so
# the deprecated spelling below must not be translated.
_CANONICAL_AUTH_TYPE_ENV = ("OCI_MCP_AUTH_TYPE", "OCI_IOT_AUTH_TYPE", "OCI_AUTH_TYPE")


def _deprecated_auth_method_override() -> Optional[AuthType]:
    """Translate the one 2.x ORACLE_MCP_AUTH_METHOD spelling the shared library rejects.

    oracle-mcp-common already reads ORACLE_MCP_AUTH_METHOD itself and maps
    "session"/"api_key"/"api-key" onto its own auth types, so this server does not
    need to interpret them. Its normalizer does not recognize the unseparated
    "apikey" spelling that this server's 2.x README documented, though, and an
    unrecognized value is a hard error -- so translate only that case.

    The translation is passed to build_auth_context() as an explicit AuthOptions
    value, which outranks every environment variable in resolve_auth_type(). So it
    is applied only when no canonical OCI_* auth-type variable is set: otherwise the
    deprecated name would silently beat OCI_MCP_AUTH_TYPE, the opposite of what this
    server documents, and OCI_MCP_AUTH_TYPE=security_token would authenticate with
    the profile's API key -- either failing to build a signer at all, or building one
    from the ephemeral session key that OCI then rejects with 401 on every request.

    Everything else is left to resolve_auth_type(), including an unset value, which
    selects "auto": session-token when the profile directly declares a
    security_token_file, otherwise API-key. Forcing a type here instead would break
    that detection -- an API-key-only profile would be rejected for having no
    security_token_file.
    """
    if any((os.getenv(name) or "").strip() for name in _CANONICAL_AUTH_TYPE_ENV):
        return None
    raw = (os.getenv("ORACLE_MCP_AUTH_METHOD") or "").strip().lower()
    if raw == "apikey":
        return AuthType.API_KEY
    return None


def _resolved_auth_type_label() -> str:
    """The auth type the shared library will use, for the startup log line only."""
    try:
        override = _deprecated_auth_method_override()
        return (override or resolve_auth_type()).value
    except Exception:
        return "unresolved"


def _first_env(*names: str, default: Optional[str] = None) -> Optional[str]:
    """Return the first non-empty environment variable among names."""
    for n in names:
        v = (os.getenv(n) or "").strip()
        if v:
            return v
    return default


def _load_oci_config_for_server() -> dict:
    """Read the selected profile's raw OCI config (for informational lookups only,
    e.g. actor-id logging and tenancy discovery). Client construction uses
    oracle_mcp_common.build_auth_context() instead; see _build_profile_auth_context().

    The config file is resolved through oracle_mcp_common.resolve_config_file() so
    these lookups read the same file the credentials came from. The OCI SDK only
    consults OCI_CONFIG_FILE when ~/.oci/config is absent, so reading the file
    directly would resolve the tenancy and region from a different profile than
    the signer whenever both exist.
    """
    config = oci.config.from_file(
        file_location=resolve_config_file(),
        profile_name=resolve_profile_name(),
    )
    config["additional_user_agent"] = _ADDITIONAL_UA
    return config


def _build_profile_auth_context():
    """Resolve stdio OCI credentials through the shared oracle-mcp-common library.

    The library owns auth-type and profile resolution, including this server's
    ORACLE_MCP_AUTH_METHOD/ORACLE_MCP_AUTH_PROFILE variables, so nothing is passed
    unless the deprecated "apikey" spelling needs translating (see
    _deprecated_auth_method_override).
    """
    override = _deprecated_auth_method_override()
    if override is not None:
        return build_auth_context(AuthOptions(auth_type=override))
    return build_auth_context()


# ---------------- HTTP transport auth (OCI IAM / IDCS) ----------------
#
# Transport decides the credential path, exactly as in the other OCI MCP servers:
#
#   * stdio  -- the operator's own OCI credentials, resolved by
#               oracle_mcp_common.build_auth_context() from the selected profile.
#   * HTTP   -- each caller signs in to an OCI IAM (IDCS) domain, and that caller's
#               access token is exchanged for caller-specific OCI credentials by
#               oracle_mcp_common.IDCSHttpAuth.context_for().
#
# The policy (provider + the confidential application's credentials) is built once
# in main() when ORACLE_MCP_HOST/ORACLE_MCP_PORT select the HTTP listener. A fresh
# signer is built for every tool call: it carries the caller's own IAM domain JWT,
# so nothing is cached process-wide outside the request that established it.

_OAUTH_SCOPE_SUFFIX = __project__.removeprefix("oracle.oci-").removesuffix("-mcp-server").replace("-", "_")
_DEFAULT_REQUIRED_SCOPES = f"openid profile email oci_mcp.{_OAUTH_SCOPE_SUFFIX}.invoke".split()

_http_auth: Optional[IDCSHttpAuth] = None


def _required_scopes() -> list[str]:
    """The scopes required of every authenticated caller over HTTP."""
    return parse_scopes(os.getenv("IDCS_REQUIRED_SCOPES")) or list(_DEFAULT_REQUIRED_SCOPES)


def _build_http_auth() -> IDCSHttpAuth:
    """Build the HTTP IDCS policy, with CIMD client registration disabled.

    CIMD makes the server fetch a client's metadata URL, an outbound request that
    fails on a VPN-only host or behind a CONNECT proxy and reaches the user as "The
    client ID ... was not found in the server's client registry". Clients register
    with DCR against /register instead, which never leaves the host. The shared
    builder also qualifies the resource scopes with IDCS_AUDIENCE for IDCS.
    """
    return build_idcs_http_auth(_required_scopes(), IDCSHttpAuthOptions(enable_cimd=False))


def _current_access_token():
    """The authenticated caller's IDCS token, or None outside an HTTP request."""
    try:
        return get_access_token()
    except Exception:
        return None


def _serving_http() -> bool:
    """Whether this call arrived over the authenticated HTTP transport."""
    if _current_access_token() is not None:
        return True
    try:
        get_http_request()
    except RuntimeError:
        return False
    return True


def _http_config_and_signer(region: str | None = None):
    """Resolve request-scoped OCI credentials for the current caller.

    The IAM domain JWT is taken from the active request's access token and passed
    to IDCSHttpAuth.context_for(), which returns a signer built for this request
    only: it is never stored outside the request that established the caller's
    identity, so a signer built for one caller can never be reused for another.
    """
    if _http_auth is None:
        raise RuntimeError(
            "HTTP authentication policy has not been initialized. Start the server "
            "through main() with ORACLE_MCP_HOST/ORACLE_MCP_PORT set."
        )
    access_token = _current_access_token()
    try:
        request_auth = _http_auth.context_for(
            access_token.token if access_token else None, region=region
        )
    except Exception as e:
        # Surface the IAM domain's actual error body instead of a bare
        # "401 Unauthorized". A 401/403 here almost always means the OCI side is
        # not set up to exchange the user JWT for a UPST yet: a missing or
        # misconfigured Identity Propagation Trust, the confidential app missing
        # the token-exchange/client-credentials grant, or wrong client credentials.
        # The IAM error body is a diagnostic description and contains no secrets.
        # context_for() wraps SDK failures in ValueError, so the IAM response hangs
        # off the wrapped cause.
        resp = getattr(e, "response", None) or getattr(getattr(e, "__cause__", None), "response", None)
        detail = ""
        if resp is not None:
            try:
                detail = f" | IAM {resp.status_code}: {resp.text}"
            except Exception:
                pass
        logger.error("OCI UPST token exchange failed%s", detail, exc_info=True)
        raise RuntimeError(
            "OCI UPST token exchange failed. The OCI IAM domain rejected the request to "
            "exchange the user's token for a UPST. Verify, in this deployment's IAM domain: "
            "(1) an Identity Propagation Trust exists that lists this client_id; (2) the "
            "confidential app has the Authorization Code and Client Credentials grants; "
            "(3) IDCS_CLIENT_ID/IDCS_CLIENT_SECRET are correct." + detail
        ) from e
    config = {**request_auth.config, "additional_user_agent": _ADDITIONAL_UA}
    return config, request_auth.signer


def _config_and_signer(region: str | None = None):
    """Resolve OCI SDK configuration and a signer for the current call."""
    if _serving_http():
        return _http_config_and_signer(region)
    if _http_auth is not None:
        # main() built an HTTP authentication policy, so this process serves
        # network callers and has no business signing anything with the
        # operator's own credentials. Reaching here means the per-request
        # detection above failed to see a request it should have seen; refusing
        # is the only safe outcome, since the alternative is performing one
        # caller's request under a different, probably broader, identity.
        raise RuntimeError(
            "Refusing to use local profile credentials on an HTTP deployment: this call "
            "arrived outside an authenticated request context, so there is no caller "
            "identity to act as."
        )
    auth_context = _build_profile_auth_context()
    config = {**auth_context.config, "additional_user_agent": _ADDITIONAL_UA}
    if region is not None:
        config["region"] = region
    return config, auth_context.signer


def _effective_region(default: Optional[str] = None) -> Optional[str]:
    """
    Resolve the OCI region without requiring a local config file.

    Over HTTP there is no OCI config file to read, so OCI_REGION supplies the
    default region; over stdio it is the configured profile's region.
    """
    if _serving_http():
        return _first_env("OCI_REGION", "ORACLE_MCP_REGION", default=default)
    try:
        return _load_oci_config_for_server().get("region") or default
    except Exception:
        return _first_env("OCI_REGION", "ORACLE_MCP_REGION", default=default)


def get_tenancy():
    """
    Return the OCID of the tenancy this server serves.

    Under HTTP transport the env override is the only source, since a hosted
    deployment has no local OCI config file to read a tenancy from.
    """
    # An explicit override always wins. Over HTTP it is the only source: there is
    # no local OCI config file on a hosted deployment to read a tenancy from.
    #
    # OCI_MCP_TENANCY_ID_OVERRIDE first, because that is the name oracle-mcp-common
    # reads and documents; a deployment configured from the shared library's own docs
    # was previously finding no tenancy here at all. The other two follow it for the
    # deployments already using them.
    override = _first_env(
        "OCI_MCP_TENANCY_ID_OVERRIDE",
        "ORACLE_MCP_TENANCY_ID",
        "TENANCY_ID_OVERRIDE",
    )
    if override:
        return override
    if _serving_http():
        raise RuntimeError(
            "HTTP deployments must set OCI_MCP_TENANCY_ID_OVERRIDE (or "
            "ORACLE_MCP_TENANCY_ID, or TENANCY_ID_OVERRIDE) to the OCID of the tenancy "
            "this server serves; there is no local OCI config file to read it from."
        )
    config = _load_oci_config_for_server()
    return config["tenancy"]
