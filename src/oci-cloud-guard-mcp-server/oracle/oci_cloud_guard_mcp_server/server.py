"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import configparser
import os
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Literal, Optional

import oci
from fastmcp import FastMCP
from fastmcp.server.auth.providers.oci import OCIProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.utilities.auth import parse_scopes
from oci.cloud_guard import CloudGuardClient
from oracle.oci_cloud_guard_mcp_server.models import (
    Problem,
    map_problem,
)
from pydantic import Field

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


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


def get_cloud_guard_client():
    config, signer = _get_http_config_and_signer()
    if signer is not None:
        return CloudGuardClient(config, **_get_oci_client_kwargs(signer))
    config = oci.config.from_file(
        file_location=os.getenv("OCI_CONFIG_FILE", oci.config.DEFAULT_LOCATION),
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE),
    )

    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    signer = _build_signer(config)
    return CloudGuardClient(config, **_get_oci_client_kwargs(signer))


@mcp.tool(
    name="list_problems",
    description="Returns a list of all Problems identified by Cloud Guard.",
)
def list_problems(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    risk_level: Optional[str] = Field(None, description="Risk level of the problem"),
    lifecycle_state: Optional[Literal["ACTIVE", "INACTIVE", "UNKNOWN_ENUM_VALUE"]] = Field(
        "ACTIVE",
        description="The field lifecycle state. "
        "Only one state can be provided. Default value for state is active.",
    ),
    detector_rule_ids: Optional[list[str]] = Field(
        None,
        description="Comma separated list of detector rule IDs to be passed in to match against Problems.",
    ),
    time_range_days: Optional[int] = Field(30, description="Number of days to look back for problems"),
    limit: Optional[int] = Field(10, description="The number of problems to return"),
) -> list[Problem]:
    time_filter = (datetime.now(timezone.utc) - timedelta(days=time_range_days)).isoformat()

    kwargs = {
        "compartment_id": compartment_id,
        "time_last_detected_greater_than_or_equal_to": time_filter,
        "limit": limit,
    }

    if risk_level:
        kwargs["risk_level"] = risk_level
    if lifecycle_state:
        kwargs["lifecycle_state"] = lifecycle_state
    if detector_rule_ids:
        kwargs["detector_rule_id_list"] = detector_rule_ids

    response = get_cloud_guard_client().list_problems(**kwargs)

    problems: list[Problem] = []
    data: list[oci.cloud_guard.models.Problem] = response.data.items
    for d in data:
        problem = map_problem(d)
        problems.append(problem)
    return problems


@mcp.tool(
    name="get_problem_details",
    description="Get the details for a Problem identified by problemId.",
)
def get_problem_details(problem_id: str = Field(..., description="The OCID of the problem")) -> Problem:
    response = get_cloud_guard_client().get_problem(problem_id=problem_id)
    problem = response.data
    return map_problem(problem)


@mcp.tool(
    name="update_problem_status",
    description="Changes the current status of the problem, identified by problemId, to the status "
    "specified in the UpdateProblemStatusDetails resource that you pass.",
)
def update_problem_status(
    problem_id: str = Field(..., description="The OCID of the problem"),
    status: Literal["OPEN", "RESOLVED", "DISMISSED", "DELETED", "UNKNOWN_ENUM_VALUE"] = Field(
        "OPEN",
        description="Action taken by user. Allowed values are: OPEN, RESOLVED, DISMISSED, CLOSED",
    ),
    comment: str = Field(None, description="A comment from the user"),
) -> Problem:
    updated_problem_status = oci.cloud_guard.models.UpdateProblemStatusDetails(status=status, comment=comment)
    response = get_cloud_guard_client().update_problem_status(
        problem_id=problem_id,
        update_problem_status_details=updated_problem_status,
    )
    problem = response.data
    return map_problem(problem)


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
