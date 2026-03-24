"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ----------- MODELS -----------

class Identity(BaseModel):
    id: str = Field(..., description="Unique identifier of the identity")
    name: Optional[str] = Field(
        None,
        description="Display name of the identity",
    )


class IdentityCollection(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier of the identity collection",
    )
    name: str = Field(
        ...,
        description="Name of the identity collection",
    )


class AccessBundle(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier of the access bundle",
    )
    name: str = Field(
        ...,
        description="Name of the access bundle",
    )


class OrchestratedSystem(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier of the orchestrated system",
    )
    name: str = Field(
        ...,
        description="Name of the orchestrated system",
    )
    type: Optional[str] = Field(
        None,
        description="Type of the orchestrated system",
    )


class AccessRequest(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier of the access request",
    )
    justification: Optional[str] = Field(
        None,
        description="Justification provided for the access request",
    )
    requestStatus: Optional[str] = Field(
        None,
        description="Current status of the access request",
    )
    timeCreated: Optional[str] = Field(
        None,
        description="Timestamp when the access request was created",
    )
    timeUpdated: Optional[str] = Field(
        None,
        description="Timestamp when the access request was last updated",
    )


# ----------- MAPPERS -----------

def map_identity(raw: dict) -> Identity:
    return Identity(
        id=raw.get("id"),
        name=raw.get("name"),
    )


def map_identity_collection(data: dict) -> IdentityCollection:
    name = (
        data.get("displayName")
        or data.get("name")
        or "Unknown"
    )

    return IdentityCollection(
        id=data.get("id"),
        name=name,
    )


def map_access_bundle(raw: dict) -> AccessBundle:
    name = (
        raw.get("displayName")
        or raw.get("name")
        or "Unknown"
    )

    return AccessBundle(
        id=raw.get("id"),
        name=name,
    )


def map_orchestrated_system(raw: dict) -> OrchestratedSystem:
    name = (
        raw.get("displayName")
        or raw.get("name")
        or "Unknown"
    )

    return OrchestratedSystem(
        id=raw.get("id"),
        name=name,
        type=raw.get("type"),
    )


def map_access_request(raw: dict) -> AccessRequest:
    return AccessRequest(
        id=raw.get("id"),
        justification=raw.get("justification"),
        requestStatus=raw.get("requestStatus"),
        timeCreated=raw.get("timeCreated"),
        timeUpdated=raw.get("timeUpdated"),
    )