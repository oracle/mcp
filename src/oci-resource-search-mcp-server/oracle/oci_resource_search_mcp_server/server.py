"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import configparser
import os
import re
from logging import Logger
from typing import Optional

import oci
from fastmcp import FastMCP
from fastmcp.server.auth.providers.oci import OCIProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.utilities.auth import parse_scopes
from oci.resource_search.models import FreeTextSearchDetails, StructuredSearchDetails
from oracle.oci_resource_search_mcp_server.models import (
    ResourceSummary,
    map_resource_summary,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)

_OCID_RE = re.compile(r"^ocid1\.[a-z0-9-]+\.[a-z0-9-]*\.[a-z0-9-]*\..+$")
_RESOURCE_TYPE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_compartment_id(compartment_id: str) -> str:
    if not _OCID_RE.fullmatch(compartment_id):
        raise ValueError("compartment_id must be a valid OCI OCID.")
    return compartment_id


def _validate_display_name(display_name: str) -> str:
    if "'" in display_name:
        raise ValueError("display_name must not contain single quotes.")
    return display_name


def _list_resource_type_names(client) -> set[str]:
    resource_type_names: set[str] = set()
    has_next_page = True
    next_page = None

    while has_next_page:
        kwargs = {"page": next_page} if next_page else {}
        response = client.list_resource_types(**kwargs)
        resource_type_names.update(
            resource_type.name.lower() for resource_type in response.data
        )

        has_next_page = getattr(response, "has_next_page", False) is True
        next_page = getattr(response, "next_page", None) if has_next_page else None
        if has_next_page and not next_page:
            break

    return resource_type_names


def _validate_resource_type(client, resource_type: str) -> str:
    normalized = resource_type.lower()
    if not _RESOURCE_TYPE_RE.fullmatch(normalized):
        raise ValueError("resource_type must contain only lowercase letters, digits, and underscores.")
    if normalized not in _list_resource_type_names(client):
        raise ValueError(f"resource_type '{resource_type}' is not supported by OCI Resource Search.")
    return normalized


def _get_http_config_and_signer():
    if not (os.getenv("ORACLE_MCP_HOST") and os.getenv("ORACLE_MCP_PORT")):
        return None, None
    token = get_access_token()
    if token is None:
        raise RuntimeError("HTTP requests require an authenticated IDCS access token.")
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    if not all((domain, client_id, client_secret)):
        raise RuntimeError(
            "HTTP requests require IDCS authentication. Set IDCS_DOMAIN, IDCS_CLIENT_ID, and IDCS_CLIENT_SECRET."
        )
    region = os.getenv("OCI_REGION")
    if not region:
        raise RuntimeError("HTTP requests require OCI_REGION.")
    config = {"region": region}
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    return config, oci.auth.signers.TokenExchangeSigner(
        token.token,
        f"https://{domain}",
        client_id,
        client_secret,
        region=config.get("region"),
    )

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


def get_search_client():
    logger.info("entering get_search_client")
    config, signer = _get_http_config_and_signer()
    if signer is not None:
        return oci.resource_search.ResourceSearchClient(config, **_get_oci_client_kwargs(signer))
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )

    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    signer = _build_signer(config)
    return oci.resource_search.ResourceSearchClient(config, **_get_oci_client_kwargs(signer))


@mcp.tool(description="Returns all resources")
def list_all_resources(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    compartment_id: str = Field(..., description="The OCID of the compartment to list from"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []
    compartment_id = _validate_compartment_id(compartment_id)

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": StructuredSearchDetails(
                    type="Structured",
                    query=f"query all resources where compartmentId = '{compartment_id}'",
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in list_all_resources tool: {str(e)}")
        raise e


@mcp.tool(description="Searches for resources by display name")
def search_resources(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    compartment_id: str = Field(..., description="The OCID of the compartment to list from"),
    display_name: str = Field(..., description="The display name (full or substring) of the resource"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []
    compartment_id = _validate_compartment_id(compartment_id)
    display_name = _validate_display_name(display_name)

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": StructuredSearchDetails(
                    type="Structured",
                    query=(
                        f"query all resources where compartmentId = '{compartment_id}' "
                        f"&& displayName =~ '{display_name}'"
                    ),
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in search_resources tool: {str(e)}")
        raise e


@mcp.tool(description="Searches for the presence of the search string in all resource fields")
def search_resources_free_form(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    text: str = Field(..., description="Free-form search string"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": FreeTextSearchDetails(
                    type="FreeText",
                    text=text,
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in search_resources_free_form tool: {str(e)}")
        raise e


@mcp.tool(description="Search for resources by resource type")
def search_resources_by_type(
    tenant_id: str = Field(
        ...,
        description="The tenancy ID, which can be used to specify a different tenancy "
        "(for cross-tenancy authorization) when searching for resources in a different tenancy",
    ),
    compartment_id: str = Field(..., description="The OCID of the compartment to list from"),
    resource_type: str = Field(
        ...,
        description="The source type to search by"
        "You may call list_resource_types to see the list of possible values"
        "Note: The values MUST be in lowercase",
    ),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[ResourceSummary]:
    resources: list[ResourceSummary] = []
    compartment_id = _validate_compartment_id(compartment_id)

    try:
        client = get_search_client()
        normalized_resource_type = _validate_resource_type(client, resource_type)

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resources) < limit):
            kwargs = {
                "tenant_id": tenant_id,
                "search_details": StructuredSearchDetails(
                    type="Structured",
                    query=(
                        f"query {normalized_resource_type} resources where compartmentId = '{compartment_id}'"
                    ),
                ),
                "page": next_page,
                "limit": limit,
            }

            response = client.search_resources(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceSummary] = response.data.items
            for d in data:
                resources.append(map_resource_summary(d))

        logger.info(f"Found {len(resources)} Resources")
        return resources

    except Exception as e:
        logger.error(f"Error in search_resources_by_type tool: {str(e)}")
        raise e


@mcp.tool(description="Returns a list of all supported OCI resource types")
def list_resource_types(
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of resources to return. If None, there is no limit.",
        ge=1,
    ),
) -> list[str]:
    resource_types: list[str] = []

    try:
        client = get_search_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(resource_types) < limit):
            kwargs = {
                "page": next_page,
                "limit": limit,
            }

            response = client.list_resource_types(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.resource_search.models.ResourceType] = response.data
            for d in data:
                resource_types.append(d.name)

        logger.info(f"Found {len(resource_types)} resource types")
        return resource_types

    except Exception as e:
        logger.error(f"Error in list_resource_types tool: {str(e)}")
        raise e


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if not (host and port):
        mcp.run()
        return
    domain = os.getenv("IDCS_DOMAIN")
    client_id = os.getenv("IDCS_CLIENT_ID")
    client_secret = os.getenv("IDCS_CLIENT_SECRET")
    base_url = os.getenv("ORACLE_MCP_BASE_URL", "")
    audience = os.getenv("IDCS_AUDIENCE")
    if not all((domain, client_id, client_secret, audience, base_url)):
        raise RuntimeError(
            "HTTP transport requires IDCS authentication. "
            "Set IDCS_DOMAIN, IDCS_CLIENT_ID, IDCS_CLIENT_SECRET, IDCS_AUDIENCE, "
            "ORACLE_MCP_BASE_URL, ORACLE_MCP_HOST, and ORACLE_MCP_PORT."
        )
    mcp.auth = OCIProvider(
        config_url=f"https://{domain}/.well-known/openid-configuration",
        client_id=client_id,
        client_secret=client_secret,
        audience=audience,
        required_scopes=parse_scopes(os.getenv("IDCS_REQUIRED_SCOPES")) or f"openid profile email oci_mcp.{__project__.removeprefix('oracle.oci-').removesuffix('-mcp-server').replace('-', '_')}.invoke".split(),
        base_url=base_url,
    )
    mcp.run(transport="http", host=host, port=int(port))


if __name__ == "__main__":
    main()
