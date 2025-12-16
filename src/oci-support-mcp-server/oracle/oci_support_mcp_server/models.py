"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- OCI Support CIMS Pydantic Models ---

class Contact(BaseModel):
    email: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    timezone: Optional[str] = Field(None)
    country: Optional[str] = Field(None)


class Category(BaseModel):
    name: Optional[str] = Field(None)
    label: Optional[str] = Field(None)


class SubCategory(BaseModel):
    name: Optional[str] = Field(None)
    label: Optional[str] = Field(None)


class IncidentType(BaseModel):
    name: Optional[str] = Field(None)
    label: Optional[str] = Field(None)
    category: Optional[Category] = Field(None)
    sub_category: Optional[SubCategory] = Field(None)


class Resource(BaseModel):
    item: Optional[str] = Field(None)
    region: Optional[str] = Field(None)
    availability_domain: Optional[str] = Field(None)
    compartment_id: Optional[str] = Field(None)


class Ticket(BaseModel):
    key: Optional[str] = Field(None)
    summary: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    time_created: Optional[datetime] = Field(None)
    time_updated: Optional[datetime] = Field(None)


class IncidentSummary(BaseModel):
    key: Optional[str] = Field(None)
    compartment_id: Optional[str] = Field(None)
    ticket_number: Optional[str] = Field(None)
    incident_type: Optional[IncidentType] = Field(None)
    severity: Optional[str] = Field(None)
    resource: Optional[Resource] = Field(None)
    status: Optional[str] = Field(None)
    time_created: Optional[datetime] = Field(None)
    time_updated: Optional[datetime] = Field(None)
    referrer: Optional[str] = Field(None)
    tenancy_id: Optional[str] = Field(None)
    contact_list: Optional[List[Contact]] = Field(None)
    lifecycle_state: Optional[str] = Field(None)
    ticket: Optional[str] = Field(None)

# --- Mapping Utilities ---

def map_contact(oci_contact) -> Contact | None:
    if not oci_contact:
        return None
    return Contact(
        email=getattr(oci_contact, "email", None),
        name=getattr(oci_contact, "name", None),
        phone=getattr(oci_contact, "phone", None),
        timezone=getattr(oci_contact, "timezone", None),
        country=getattr(oci_contact, "country", None),
    )

def map_category(oci_category) -> Category | None:
    if not oci_category:
        return None
    return Category(
        name=getattr(oci_category, "name", None),
        label=getattr(oci_category, "label", None),
    )

def map_sub_category(oci_sub_category) -> SubCategory | None:
    if not oci_sub_category:
        return None
    return SubCategory(
        name=getattr(oci_sub_category, "name", None),
        label=getattr(oci_sub_category, "label", None),
    )

def map_incident_type(oci_incident_type) -> IncidentType | None:
    if not oci_incident_type:
        return None
    return IncidentType(
        name=getattr(oci_incident_type, "name", None),
        label=getattr(oci_incident_type, "label", None),
        category=map_category(getattr(oci_incident_type, "category", None)),
        sub_category=map_sub_category(getattr(oci_incident_type, "sub_category", None)),
    )

def map_resource(oci_resource) -> Resource | None:
    if not oci_resource:
        return None
    return Resource(
        item=getattr(oci_resource, "item", None),
        region=getattr(oci_resource, "region", None),
        availability_domain=getattr(oci_resource, "availability_domain", None),
        compartment_id=getattr(oci_resource, "compartment_id", None),
    )

def map_ticket(oci_ticket) -> Optional[str]:
    if not oci_ticket:
        return None
    if isinstance(oci_ticket, str):
        return oci_ticket
    if isinstance(oci_ticket, dict):
        # Try to get ticket['key'] first; else fallback to something unique or string repr
        return oci_ticket.get("key") or oci_ticket.get("summary") or str(oci_ticket)
    # Try attribute access (object with .key or .summary), else fallback to str(obj)
    return getattr(oci_ticket, "key", None) or getattr(oci_ticket, "summary", None) or str(oci_ticket)

def map_incident_summary(oci_incident_summary) -> IncidentSummary | None:
    if not oci_incident_summary:
        return None

    def get(field, default=None):
        if isinstance(oci_incident_summary, dict):
            return oci_incident_summary.get(field, default)
        return getattr(oci_incident_summary, field, default)

    return IncidentSummary(
        key=get("key"),
        compartment_id=get("compartment_id"),
        ticket_number=get("ticket_number"),
        incident_type=map_incident_type(get("incident_type")),
        severity=get("severity"),
        resource=map_resource(get("resource")),
        status=get("status"),
        time_created=get("time_created"),
        time_updated=get("time_updated"),
        referrer=get("referrer"),
        tenancy_id=get("tenancy_id"),
        contact_list=[
            map_contact(c) for c in (get("contact_list") or [])
        ],
        lifecycle_state=get("lifecycle_state"),
        ticket=map_ticket(get("ticket")),
    )
