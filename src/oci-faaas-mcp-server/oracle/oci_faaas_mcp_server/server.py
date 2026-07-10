"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import configparser
import os
from logging import Logger
from typing import Any, Literal, Optional

import oci
from fastmcp import FastMCP
from pydantic import Field

from . import __project__, __version__
from .models import (
    FusionEnvironment,
    FusionEnvironmentFamily,
    FusionEnvironmentStatus,
    map_fusion_environment,
    map_fusion_environment_family,
    map_fusion_environment_status,
)

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def _get_oci_client_kwargs(signer=None):
    kwargs = {
        "circuit_breaker_strategy": oci.circuit_breaker.CircuitBreakerStrategy(
            failure_threshold=int(os.getenv("OCI_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "10")),
            recovery_timeout=int(os.getenv("OCI_CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "30")),
        ),
        "circuit_breaker_callback": lambda exc: logger.warning(
            "Circuit breaker triggered: %s", exc
        ),
    }
    if signer is not None:
        kwargs["signer"] = signer
    return kwargs


_SESSION_TOKEN_DOCS = "https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm"
_API_KEY_FIELDS = ("tenancy", "user", "fingerprint", "key_file")

# configparser reserves "DEFAULT" as the section whose keys are inherited by every
# other section. Naming a section that cannot appear in an OCI config disables that.
_NO_INHERIT = "\x00oci-mcp-no-inherited-defaults"

_api_key_warning_emitted = False


def _selected_profile():
    return os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)


def _profile_declares_session_token():
    """Whether the selected profile declares security_token_file in its own section.

    oci.config.from_file() merges the [DEFAULT] section into every named profile, so
    `"security_token_file" in config` is true for an API-key profile whenever [DEFAULT]
    happens to be a session profile -- which would sign requests with the wrong
    credentials. Re-read the file with that inheritance disabled.
    """
    parser = configparser.ConfigParser(default_section=_NO_INHERIT)
    parser.read(os.path.expanduser(os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION)))
    profile = _selected_profile()
    if not parser.has_section(profile):
        return False
    return parser.has_option(profile, "security_token_file")


def _build_signer(config):
    """Build a request signer matching the selected profile's authentication type."""
    global _api_key_warning_emitted

    if _profile_declares_session_token():
        private_key = oci.signer.load_private_key_from_file(config["key_file"])
        with open(os.path.expanduser(config["security_token_file"]), "r") as f:
            token = f.read()
        return oci.auth.signers.SecurityTokenSigner(token, private_key)

    profile = _selected_profile()
    missing = [field for field in _API_KEY_FIELDS if not config.get(field)]
    if missing:
        raise RuntimeError(
            f"OCI profile [{profile}] cannot authenticate: it declares no "
            f"security_token_file, and these API key fields are missing: "
            f"{', '.join(missing)}. Either run 'oci session authenticate' to create a "
            f"session-token profile, or add the missing fields. See {_SESSION_TOKEN_DOCS}"
        )

    if not _api_key_warning_emitted:
        _api_key_warning_emitted = True
        logger.warning(
            f"OCI profile [{profile}] authenticates with a long-lived API key. Session "
            f"tokens expire automatically and limit the damage from a leaked credential; "
            f"prefer 'oci session authenticate' where your tenancy supports it. "
            f"See {_SESSION_TOKEN_DOCS}"
        )

    return oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
        pass_phrase=config.get("pass_phrase"),
    )


def get_faaas_client():
    """Initialize and return an OCI Fusion Applications client using security token auth."""
    logger.info("entering get_faaas_client")

    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )

    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    signer = _build_signer(config)

    return oci.fusion_apps.FusionApplicationsClient(config, **_get_oci_client_kwargs(signer))


@mcp.tool(description="Returns a list of Fusion Environment Families in the specified compartment.")
def list_fusion_environment_families(
    compartment_id: str = Field(..., description="The ID of the compartment in which to list resources."),
    display_name: Optional[str] = Field(None, description="Filter to match entire display name."),
    lifecycle_state: Optional[
        Literal["CREATING", "UPDATING", "ACTIVE", "DELETING", "DELETED", "FAILED"]
    ] = Field(
        None,
        description=(
            "Filter by lifecycle state. Allowed: CREATING, UPDATING, ACTIVE, DELETING, DELETED, FAILED"
        ),
    ),
) -> list[FusionEnvironmentFamily]:
    client = get_faaas_client()

    families: list[FusionEnvironmentFamily] = []
    next_page: Optional[str] = None
    has_next_page = True

    while has_next_page:
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if next_page is not None:
            kwargs["page"] = next_page
        if display_name is not None:
            kwargs["display_name"] = display_name
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state

        response: oci.response.Response = client.list_fusion_environment_families(**kwargs)

        # Normalize response data to an iterable without using helpers
        data_obj = response.data or []
        items = getattr(data_obj, "items", None)
        iterable = items if items is not None else (data_obj if isinstance(data_obj, list) else [data_obj])
        for d in iterable:
            families.append(map_fusion_environment_family(d))

        # Robust pagination handling with header fallback
        headers = getattr(response, "headers", None)
        next_page = getattr(response, "next_page", None)
        if next_page is None and headers:
            try:
                next_page = dict(headers).get("opc-next-page")
            except Exception:
                next_page = None
        has_next_page = next_page is not None

    logger.info(f"Found {len(families)} Fusion Environment Families")
    return families


@mcp.tool(
    description=(
        "Returns a list of Fusion Environments in the specified compartment (optionally filtered by family)."
    )
)
def list_fusion_environments(
    compartment_id: str = Field(..., description="The ID of the compartment in which to list resources."),
    fusion_environment_family_id: Optional[str] = Field(
        None, description="Optional Fusion Environment Family OCID"
    ),
    display_name: Optional[str] = Field(None, description="Filter to match entire display name."),
    lifecycle_state: Optional[
        Literal[
            "CREATING",
            "UPDATING",
            "ACTIVE",
            "INACTIVE",
            "DELETING",
            "DELETED",
            "FAILED",
        ]
    ] = Field(
        None,
        description=(
            "Filter by lifecycle state. Allowed: CREATING, UPDATING, ACTIVE, "
            "INACTIVE, DELETING, DELETED, FAILED"
        ),
    ),
) -> list[FusionEnvironment]:
    client = get_faaas_client()

    environments: list[FusionEnvironment] = []
    next_page: Optional[str] = None
    has_next_page = True

    while has_next_page:
        kwargs: dict[str, Any] = {"compartment_id": compartment_id}
        if next_page is not None:
            kwargs["page"] = next_page
        if fusion_environment_family_id is not None:
            kwargs["fusion_environment_family_id"] = fusion_environment_family_id
        if display_name is not None:
            kwargs["display_name"] = display_name
        if lifecycle_state is not None:
            kwargs["lifecycle_state"] = lifecycle_state

        response: oci.response.Response = client.list_fusion_environments(**kwargs)

        # Normalize response data to an iterable without using helpers
        data_obj = response.data or []
        items = getattr(data_obj, "items", None)
        iterable = items if items is not None else (data_obj if isinstance(data_obj, list) else [data_obj])
        for d in iterable:
            environments.append(map_fusion_environment(d))

        # Robust pagination handling with header fallback
        headers = getattr(response, "headers", None)
        next_page = getattr(response, "next_page", None)
        if next_page is None and headers:
            try:
                next_page = dict(headers).get("opc-next-page")
            except Exception:
                next_page = None
        has_next_page = next_page is not None

    logger.info(f"Found {len(environments)} Fusion Environments")
    return environments


@mcp.tool(description="Gets a Fusion Environment by OCID.")
def get_fusion_environment(
    fusion_environment_id: str = Field(..., description="Unique FusionEnvironment identifier (OCID)"),
) -> FusionEnvironment:
    client = get_faaas_client()
    response: oci.response.Response = client.get_fusion_environment(fusion_environment_id)
    return map_fusion_environment(response.data)


@mcp.tool(description="Gets the status of a Fusion Environment by OCID.")
def get_fusion_environment_status(
    fusion_environment_id: str = Field(..., description="Unique FusionEnvironment identifier (OCID)"),
) -> FusionEnvironmentStatus:
    client = get_faaas_client()
    response: oci.response.Response = client.get_fusion_environment_status(fusion_environment_id)
    return map_fusion_environment_status(response.data)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
