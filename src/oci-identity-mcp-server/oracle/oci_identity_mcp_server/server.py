"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import base64
import json
import os

import oci
from fastmcp import FastMCP

from . import __project__, __version__

mcp = FastMCP(name=__project__)


def get_identity_client():
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"
    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.identity.IdentityClient(config, signer=signer)


@mcp.tool
def list_compartments(tenancy_id: str) -> list[dict]:
    identity = get_identity_client()
    compartments = identity.list_compartments(tenancy_id).data
    return [
        {
            "id": compartment.id,
            "name": compartment.name,
            "description": compartment.description,
            "lifecycle_state": compartment.lifecycle_state,
        }
        for compartment in compartments
    ]


@mcp.tool
def get_tenancy_info(tenancy_id: str) -> dict:
    identity = get_identity_client()
    tenancy = identity.get_tenancy(tenancy_id).data
    return {
        "id": tenancy.id,
        "name": tenancy.name,
        "description": tenancy.description,
        "home_region_key": tenancy.home_region_key,
    }


@mcp.tool(description="Lists all of the availability domains in a given tenancy")
def list_availability_domains(tenancy_id: str) -> list[dict]:
    identity = get_identity_client()
    ads: list[oci.identity.models.AvailabilityDomain] = (
        identity.list_availability_domains(tenancy_id).data
    )
    return [
        {
            "id": ad.id,
            "name": ad.name,
            "compartment_id": ad.compartment_id,
        }
        for ad in ads
    ]


@mcp.tool
def get_current_tenancy() -> dict:
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    tenancy_id = config["tenancy"]
    identity = get_identity_client()
    tenancy = identity.get_tenancy(tenancy_id).data
    return {
        "id": tenancy.id,
        "name": tenancy.name,
        "description": tenancy.description,
        "home_region_key": tenancy.home_region_key,
    }


@mcp.tool
def create_auth_token(user_id: str) -> dict:
    identity = get_identity_client()
    token = identity.create_auth_token(user_id=user_id).data
    return {
        "token": token.token,
        "description": token.description,
        "lifecycle_state": token.lifecycle_state,
    }


@mcp.tool
def get_current_user() -> dict:
    identity = get_identity_client()
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )

    # Prefer explicit user from config if present
    user_id = config.get("user")

    # Fallback: derive user OCID from the security token (session auth)
    if not user_id:
        token_file = config.get("security_token_file")
        if token_file and os.path.exists(token_file):
            with open(token_file, "r") as f:
                token = f.read().strip()

            # Expect JWT-like token: header.payload.signature (base64url)
            if "." in token:
                try:
                    payload_b64 = token.split(".", 2)[1]
                    padding = "=" * (-len(payload_b64) % 4)
                    payload_json = base64.urlsafe_b64decode(
                        payload_b64 + padding
                    ).decode("utf-8")
                    payload = json.loads(payload_json)
                    # 'sub' typically contains the user OCID for session tokens;
                    # fallback to opc-user-id if present
                    user_id = payload.get("sub") or payload.get("opc-user-id")
                except Exception:
                    user_id = None

        if not user_id:
            raise KeyError(
                "Unable to determine current user OCID from config or security token"
            )

    user = identity.get_user(user_id).data
    return {
        "id": user.id,
        "name": user.name,
        "description": user.description,
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
