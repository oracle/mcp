import os
from dataclasses import dataclass
from typing import Any

import oci

from . import __project__, __version__

SUPPORTED_AUTH_TYPES = (
    "auto",
    "security_token",
    "api_key",
    "instance_principal",
    "resource_principal",
    "instance_principal_delegation",
    "resource_principal_delegation",
    "oke_workload_identity",
)
PRINCIPAL_AUTH_TYPES = {
    "instance_principal",
    "resource_principal",
    "instance_principal_delegation",
    "resource_principal_delegation",
    "oke_workload_identity",
}


@dataclass(frozen=True)
class AuthContext:
    auth_type: str
    config: dict[str, Any]
    signer: Any | None
    tenancy_id: str | None
    region: str | None
    profile_name: str | None


def resolved_profile_name(profile_name: str | None) -> str:
    return profile_name or os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")


def resolved_auth_type(auth_type: str | None = None) -> str:
    value = (auth_type or os.getenv("OCI_IOT_AUTH_TYPE", "auto")).strip().lower().replace("-", "_")
    if value not in SUPPORTED_AUTH_TYPES:
        supported = ", ".join(SUPPORTED_AUTH_TYPES)
        raise ValueError(f"Unsupported OCI_IOT_AUTH_TYPE '{value}'. Supported values: {supported}")
    return value


def build_auth_context(profile_name: str | None = None, auth_type: str | None = None) -> AuthContext:
    resolved_type = resolved_auth_type(auth_type)

    if resolved_type == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return _principal_auth_context(signer, resolved_type)

    if resolved_type == "instance_principal_delegation":
        signer = oci.auth.signers.InstancePrincipalsDelegationTokenSigner(
            delegation_token=_required_env("OCI_IOT_DELEGATION_TOKEN")
        )
        return _principal_auth_context(signer, resolved_type)

    if resolved_type == "resource_principal":
        signer = oci.auth.signers.get_resource_principals_signer()
        return _principal_auth_context(signer, resolved_type)

    if resolved_type == "resource_principal_delegation":
        signer = oci.auth.signers.get_resource_principal_delegation_token_signer(
            delegation_token=_required_env("OCI_IOT_DELEGATION_TOKEN")
        )
        return _principal_auth_context(signer, resolved_type)

    if resolved_type == "oke_workload_identity":
        signer = oci.auth.signers.get_oke_workload_identity_resource_principal_signer(**_oke_signer_kwargs())
        return _principal_auth_context(signer, resolved_type)

    resolved_profile = resolved_profile_name(profile_name)
    config = _profile_config(resolved_profile)

    if resolved_type == "security_token":
        signer = _build_security_token_signer(config)
        return _profile_auth_context(config, signer, "security_token", resolved_profile)

    if resolved_type == "api_key":
        signer = _build_api_key_signer(config)
        return _profile_auth_context(config, signer, "api_key", resolved_profile)

    token_file = config.get("security_token_file")
    if token_file:
        try:
            signer = _build_security_token_signer(config)
            return _profile_auth_context(config, signer, "security_token", resolved_profile)
        except Exception:
            pass

    signer = _build_api_key_signer(config)
    return _profile_auth_context(config, signer, "api_key", resolved_profile)


def get_default_region(profile_name: str | None = None, auth_type: str | None = None) -> str | None:
    resolved_type = resolved_auth_type(auth_type)
    if resolved_type in PRINCIPAL_AUTH_TYPES:
        return build_auth_context(profile_name=profile_name, auth_type=resolved_type).region
    return _profile_config(resolved_profile_name(profile_name)).get("region")


def _profile_config(profile_name: str) -> dict[str, Any]:
    config = dict(oci.config.from_file(profile_name=profile_name))
    config["additional_user_agent"] = _additional_user_agent()
    return config


def _profile_auth_context(
    config: dict[str, Any],
    signer: Any,
    auth_type: str,
    profile_name: str,
) -> AuthContext:
    return AuthContext(
        auth_type=auth_type,
        config=config,
        signer=signer,
        tenancy_id=config.get("tenancy"),
        region=config.get("region"),
        profile_name=profile_name,
    )


def _principal_auth_context(signer: Any, auth_type: str) -> AuthContext:
    config: dict[str, Any] = {"additional_user_agent": _additional_user_agent()}
    region = getattr(signer, "region", None)
    if region:
        config["region"] = region
    tenancy_id = getattr(signer, "tenancy_id", None) or os.getenv("OCI_IOT_TENANCY_ID_OVERRIDE")

    return AuthContext(
        auth_type=auth_type,
        config=config,
        signer=signer,
        tenancy_id=tenancy_id,
        region=region,
        profile_name=None,
    )


def _build_security_token_signer(config: dict[str, Any]):
    private_key = oci.signer.load_private_key_from_file(
        config["key_file"],
        config.get("pass_phrase"),
    )
    with open(os.path.expanduser(config["security_token_file"]), "r") as token_file:
        token = token_file.read()
    return oci.auth.signers.SecurityTokenSigner(token, private_key)


def _build_api_key_signer(config: dict[str, Any]):
    return oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
        pass_phrase=config.get("pass_phrase"),
    )


def _additional_user_agent() -> str:
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    return f"{user_agent_name}/{__version__}"


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is required for the selected OCI_IOT_AUTH_TYPE")
    return value


def _oke_signer_kwargs() -> dict[str, Any]:
    explicit_token = os.getenv("OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN")
    if explicit_token:
        return {"service_account_token": explicit_token}

    token_path = os.getenv("OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN_PATH")
    if token_path:
        return {"service_account_token_path": token_path}

    return {}
