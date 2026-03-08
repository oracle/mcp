"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional

import oci
from pydantic import BaseModel, Field


def _oci_to_dict(obj):
    """Best-effort conversion of OCI SDK model objects to plain dicts."""
    if obj is None:
        return None
    try:
        from oci.util import to_dict as oci_to_dict

        return oci_to_dict(obj)
    except Exception:
        pass
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return None


# region Compartment


class Compartment(BaseModel):
    """
    Pydantic model mirroring the fields of oci.identity.models.Compartment.
    There are no nested OCI model types in this class.
    """

    id: Optional[str] = Field(None, description="The OCID of the compartment.")
    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the parent compartment "
        "(remember that the tenancy is simply the root compartment).",
    )
    name: Optional[str] = Field(
        None,
        description="The name you assign to the compartment during creation. "
        "The name must be unique across all compartments in the parent. "
        "Avoid entering confidential information.",
    )
    description: Optional[str] = Field(
        None,
        description="The description you assign to the compartment. "
        "Does not have to be unique, and it's changeable.",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="Date and time the compartment was created, in the format "
        "defined by RFC3339. Example: `2016-08-25T21:10:29.600Z`",
    )
    lifecycle_state: Optional[Literal["CREATING", "ACTIVE", "INACTIVE", "DELETING", "DELETED", "FAILED"]] = (
        Field(None, description="The compartment's current state.")
    )
    inactive_status: Optional[int] = Field(
        None, description="The detailed status of INACTIVE lifecycleState."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with "'
        '"no predefined name, type, or namespace. For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Department": "Finance"}`',
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description='Defined tags for this resource. Each key is predefined and scoped to a namespace. "'
        '"For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Operations": {"CostCenter": "42"}}`',
    )


def map_compartment(compartment_data: oci.identity.models.Compartment) -> Compartment:
    """
    Convert an oci.identity.models.Compartment to oracle.oci_identity_mcp_server.models.Compartment.
    """
    return Compartment(
        id=getattr(compartment_data, "id", None),
        compartment_id=getattr(compartment_data, "compartment_id", None),
        name=getattr(compartment_data, "name", None),
        description=getattr(compartment_data, "description", None),
        time_created=getattr(compartment_data, "time_created", None),
        lifecycle_state=getattr(compartment_data, "lifecycle_state", None),
        inactive_status=getattr(compartment_data, "inactive_status", None),
        freeform_tags=getattr(compartment_data, "freeform_tags", None),
        defined_tags=getattr(compartment_data, "defined_tags", None),
    )


# end region

# region Tenancy


class Tenancy(BaseModel):
    """
    Pydantic model mirroring the fields of oci.identity.models.Tenancy.
    There are no nested OCI model types in this class.
    """

    id: Optional[str] = Field(None, description="The OCID of the tenancy.")
    name: Optional[str] = Field(None, description="The name of the tenancy.")
    description: Optional[str] = Field(None, description="The description of the tenancy.")
    home_region_key: Optional[str] = Field(None, description="The region key for the tenancy's home region.")
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with "'
        '"no predefined name, type, or namespace. For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Department": "Finance"}`',
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description='Defined tags for this resource. Each key is predefined and scoped to a namespace. "'
        '"For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Operations": {"CostCenter": "42"}}`',
    )


def map_tenancy(tenancy_data: oci.identity.models.Tenancy) -> Tenancy:
    """
    Convert an oci.identity.models.Tenancy to oracle.oci_identity_mcp_server.models.Tenancy.
    """
    return Tenancy(
        id=getattr(tenancy_data, "id", None),
        name=getattr(tenancy_data, "name", None),
        description=getattr(tenancy_data, "description", None),
        home_region_key=getattr(tenancy_data, "home_region_key", None),
        freeform_tags=getattr(tenancy_data, "freeform_tags", None),
        defined_tags=getattr(tenancy_data, "defined_tags", None),
    )


# endregion

# region AvailabilityDomain


class AvailabilityDomain(BaseModel):
    """
    Pydantic model mirroring the fields of oci.identity.models.AvailabilityDomain.
    There are no nested OCI model types in this class.
    """

    id: Optional[str] = Field(None, description="The OCID of the Availability Domain.")
    name: Optional[str] = Field(None, description="The name of the Availability Domain.")
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the tenancy containing the Availability Domain."
    )


def map_availability_domain(
    availability_domain_data: oci.identity.models.AvailabilityDomain,
) -> AvailabilityDomain:
    """
    Convert an oci.identity.models.AvailabilityDomain to
    oracle.oci_identity_mcp_server.models.AvailabilityDomain.
    """
    return AvailabilityDomain(
        id=getattr(availability_domain_data, "id", None),
        name=getattr(availability_domain_data, "name", None),
        compartment_id=getattr(availability_domain_data, "compartment_id", None),
    )


# end region

# region AuthToken


class AuthToken(BaseModel):
    """
    Pydantic model mirroring the fields of oci.identity.models.AuthToken.
    There are no nested OCI model types in this class.
    """

    id: Optional[str] = Field(None, description="The OCID of the auth token.")
    token: Optional[str] = Field(None, description="The raw auth token string.")
    user_id: Optional[str] = Field(None, description="The OCID of the user the password belongs to.")
    description: Optional[str] = Field(
        None,
        description="The description you assign to the auth token. "
        "Does not have to be unique, and it's changeable.",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="Date and time the auth token was created, in the format "
        "defined by RFC3339. Example: `2016-08-25T21:10:29.600Z`",
    )
    time_expires: Optional[datetime] = Field(
        None,
        description="Date and time when this auth token will expire, in the format "
        "defined by RFC3339. Example: `2016-08-25T21:10:29.600Z`",
    )
    lifecycle_state: Optional[Literal["CREATING", "ACTIVE", "INACTIVE", "DELETING", "DELETED"]] = Field(
        None, description="The auth token's current state."
    )
    inactive_status: Optional[int] = Field(
        None, description="The detailed status of INACTIVE lifecycleState."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with "'
        '"no predefined name, type, or namespace. For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Department": "Finance"}`',
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description='Defined tags for this resource. Each key is predefined and scoped to a namespace. "'
        '"For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Operations": {"CostCenter": "42"}}`',
    )


def map_auth_token(auth_token_data: oci.identity.models.AuthToken) -> AuthToken:
    """
    Convert an oci.identity.models.AuthToken to oracle.oci_identity_mcp_server.models.AuthToken.
    """
    return AuthToken(
        id=getattr(auth_token_data, "id", None),
        token=getattr(auth_token_data, "token", None),
        user_id=getattr(auth_token_data, "user_id", None),
        description=getattr(auth_token_data, "description", None),
        time_created=getattr(auth_token_data, "time_created", None),
        time_expires=getattr(auth_token_data, "time_expires", None),
        lifecycle_state=getattr(auth_token_data, "lifecycle_state", None),
        inactive_status=getattr(auth_token_data, "inactive_status", None),
        freeform_tags=getattr(auth_token_data, "freeform_tags", None),
        defined_tags=getattr(auth_token_data, "defined_tags", None),
    )


# endregion

# region User


class User(BaseModel):
    """
    Pydantic model mirroring the fields of oci.identity.models.User.
    There are no nested OCI model types in this class.
    """

    id: Optional[str] = Field(None, description="The OCID of the user.")
    compartment_id: Optional[str] = Field(None, description="The OCID of the tenancy containing the user.")
    name: Optional[str] = Field(
        None,
        description="The name you assign to the user during creation. "
        "This is the user's login value. The name must be unique "
        "across all users in the tenancy and cannot be changed.",
    )
    description: Optional[str] = Field(
        None,
        description="The description you assign to the user. "
        "Does not have to be unique, and it's changeable.",
    )
    email: Optional[str] = Field(None, description="The email address of the user.")
    email_verified: Optional[bool] = Field(None, description="Whether the email address has been validated.")
    db_user_name: Optional[str] = Field(
        None,
        description="DB username of the DB credential. Has to be unique across the tenancy.",
    )
    identity_provider_id: Optional[str] = Field(
        None, description="The OCID of the IdentityProvider this user belongs to."
    )
    external_identifier: Optional[str] = Field(
        None, description="Identifier of the user in the identity provider"
    )
    time_created: Optional[datetime] = Field(
        None,
        description="Date and time the user was created, in the format defined by RFC3339. "
        "Example: `2016-08-25T21:10:29.600Z`",
    )
    lifecycle_state: Optional[Literal["CREATING", "ACTIVE", "INACTIVE", "DELETING", "DELETED"]] = Field(
        None, description="The user's current state."
    )
    inactive_status: Optional[int] = Field(
        None,
        description="Returned only if the user's `lifecycleState` is INACTIVE. "
        "A 16-bit value showing the reason why the user is inactive: "
        "- bit 0: SUSPENDED (reserved for future use) "
        "- bit 1: DISABLED (reserved for future use) "
        "- bit 2: BLOCKED (the user has exceeded the maximum number of "
        "failed login attempts for the Console)",
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description='Free-form tags for this resource. Each tag is a simple key-value pair with "'
        '"no predefined name, type, or namespace. For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Department": "Finance"}`',
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description='Defined tags for this resource. Each key is predefined and scoped to a namespace. "'
        '"For more information, see "'
        '"[Resource Tags](https://docs.cloud.oracle.com/Content/General/Concepts/resourcetags.htm). "'
        '"Example: `{"Operations": {"CostCenter": "42"}}`',
    )
    is_mfa_activated: Optional[bool] = Field(
        None,
        description="Indicates whether the user has activated multi-factor authentication.",
    )


def map_user(user_data: oci.identity.models.User) -> User:
    """
    Convert an oci.identity.models.User to oracle.oci_identity_mcp_server.models.User.
    """
    return User(
        id=getattr(user_data, "id", None),
        compartment_id=getattr(user_data, "compartment_id", None),
        name=getattr(user_data, "name", None),
        description=getattr(user_data, "description", None),
        email=getattr(user_data, "email", None),
        email_verified=getattr(user_data, "email_verified", None),
        db_user_name=getattr(user_data, "db_user_name", None),
        identity_provider_id=getattr(user_data, "identity_provider_id", None),
        external_identifier=getattr(user_data, "external_identifier", None),
        time_created=getattr(user_data, "time_created", None),
        lifecycle_state=getattr(user_data, "lifecycle_state", None),
        inactive_status=getattr(user_data, "inactive_status", None),
        freeform_tags=getattr(user_data, "freeform_tags", None),
        defined_tags=getattr(user_data, "defined_tags", None),
        is_mfa_activated=getattr(user_data, "is_mfa_activated", None),
    )


# endregion


class RegionSubscription(BaseModel):
    """
    Pydantic model mirroring the fields of oci.identity.models.RegionSubscription.
    """

    region_key: Optional[str] = Field(None, description="The region key. Example: `PHX`")
    region_name: Optional[str] = Field(None, description="The region name. Example: `us-phoenix-1`")
    status: Optional[str] = Field(None, description="The status of the region subscription.")
    is_home_region: Optional[bool] = Field(
        None, description="Indicates if the region is the home region for the tenancy."
    )


def map_region_subscription(
    region_data: oci.identity.models.RegionSubscription,
) -> RegionSubscription:
    """
    Convert an oci.identity.models.RegionSubscription to
    oracle.oci_identity_mcp_server.models.RegionSubscription.
    """
    return RegionSubscription(
        region_key=getattr(region_data, "region_key", None),
        region_name=getattr(region_data, "region_name", None),
        status=getattr(region_data, "status", None),
        is_home_region=getattr(region_data, "is_home_region", None),
    )
