"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import Field

from .auth import get_auth_provider
from .ag_client import AccessGovernanceClient
from .models import (
    map_identity,
    map_identity_collection,
    map_access_bundle,
    map_orchestrated_system,
    map_access_request,
)

# ---------- ENV ----------

load_dotenv()

# ---------- MCP INIT ----------

mcp = FastMCP(
    name="oci-ag-mcp-server",
    auth=get_auth_provider()
)

client = AccessGovernanceClient()

# ---------- TOOLS ----------


@mcp.tool(
    name="health_check",
    description="Check if the MCP server is running and reachable. Returns basic health status."
)
async def health_check() -> dict:
    return {"status": "Healthy"}


@mcp.tool(
    name="list_identities",
    description="Retrieve all identities (users) available in Access Governance."
)
async def list_identities() -> list[dict]:
    data = await client.list_identities()
    return [map_identity(d).model_dump() for d in data.get("items", [])]


@mcp.tool(
    name="list_identity_collections",
    description="Retrieve all identity collections (groups of users)."
)
async def list_identity_collections() -> list[dict]:
    data = await client.list_identity_collections()
    return [map_identity_collection(d).model_dump() for d in data.get("items", [])]


@mcp.tool(
    name="create_identity_collection",
    description="Create a new identity collection (group of users)."
)
async def create_identity_collection(
    display_name: str = Field(
        ...,
        description="Display name of the identity collection"
    ),
    owner: str = Field(
        ...,
        description="Owner (user name or ID)"
    ),
    included_identities: list[str] | None = Field(
        None,
        description="Optional list of identities to include"
    ),
) -> dict:

    included_identities = included_identities or []
    owner_identity = await _resolve_identity(owner)

    included = [
        {
            "id": resolved["id"],
            "name": resolved["name"],
        }
        for x in included_identities
        for resolved in [await _resolve_identity(x)]
    ]

    payload = {
        "name": _generate_name(display_name),
        "displayName": display_name,
        "description": _generate_description(display_name),
        "includedIdentities": included,
        "excludedIdentities": [],
        "owners": [
            {
                "id": owner_identity["id"],
                "name": owner_identity["name"],
                "isPrimary": True,
            }
        ],
        "tags": _generate_tags(display_name),
        "isManagedAtOrchestratedSystem": False,
    }

    return await client.create_identity_collection(payload)


@mcp.tool(
    name="list_access_bundles",
    description="Retrieve all access bundles."
)
async def list_access_bundles() -> list[dict]:
    data = await client.list_access_bundles()
    return [map_access_bundle(d).model_dump() for d in data.get("items", [])]


@mcp.tool(
    name="list_orchestrated_systems",
    description="Retrieve all orchestrated systems."
)
async def list_orchestrated_systems() -> list[dict]:
    data = await client.list_orchestrated_systems()
    return [map_orchestrated_system(d).model_dump() for d in data.get("items", [])]


@mcp.tool(
    name="list_access_requests",
    description="Retrieve all access requests."
)
async def list_access_requests() -> list[dict]:
    data = await client.list_access_requests()
    return [map_access_request(d).model_dump() for d in data.get("items", [])]


@mcp.tool(
    name="create_access_request",
    description="Create a new access request."
)
async def create_access_request(
    justification: str = Field(..., description="Reason for requesting access"),
    beneficiaries: list[str] = Field(..., description="Users receiving access"),
    access_bundles: list[str] = Field(..., description="Access bundles to assign"),
    created_by_user: str = Field(..., description="Requester"),
) -> dict:
    created_by = await _resolve_identity(created_by_user)

    identities = [(await _resolve_identity(b))["id"] for b in beneficiaries]
    bundles = [(await _resolve_access_bundle(b))["id"] for b in access_bundles]

    payload = {
        "justification": justification,
        "createdBy": created_by["id"],
        "accessBundles": bundles,
        "identities": identities,
    }

    return await client.create_access_request(payload)


# ---------- HELPERS ----------

IDENTITY_CACHE = None
ACCESS_BUNDLE_CACHE = None


async def _get_identities():
    global IDENTITY_CACHE
    if IDENTITY_CACHE is None:
        data = await client.list_identities()
        IDENTITY_CACHE = [map_identity(d) for d in data.get("items", [])]
    return IDENTITY_CACHE


async def _resolve_identity(identifier: str) -> dict:
    identities = await _get_identities()
    identifier = identifier.lower()

    for i in identities:
        if identifier in {(i.id or "").lower(), (i.name or "").lower()}:
            return {"id": i.id, "name": i.name}

    raise ValueError(f"Identity not found: {identifier}")


async def _get_access_bundles():
    global ACCESS_BUNDLE_CACHE
    if ACCESS_BUNDLE_CACHE is None:
        data = await client.list_access_bundles()
        ACCESS_BUNDLE_CACHE = [map_access_bundle(d) for d in data.get("items", [])]
    return ACCESS_BUNDLE_CACHE


async def _resolve_access_bundle(name: str) -> dict:
    bundles = await _get_access_bundles()
    name = name.lower()

    for b in bundles:
        if name in {(b.id or "").lower(), (b.name or "").lower()}:
            return {"id": b.id, "name": b.name}

    raise ValueError(f"Access bundle not found: {name}")


def _generate_name(display_name: str) -> str:
    return display_name.lower().replace(" ", "_")


def _generate_description(display_name: str) -> str:
    return f"Identity collection for {display_name}"


def _generate_tags(display_name: str) -> list[str]:
    return [_generate_name(display_name)]


# ---------- RUN ----------

def main():
    mcp.run(
        transport="http",
        host="localhost",
        port=8000,
    )


if __name__ == "__main__":
    main()