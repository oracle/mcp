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
    contact_name: Optional[str] = Field(None)
    contact_email: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    contact_phone: Optional[str] = Field(None)
    contact_type: Optional[str] = Field(None)

class ContactList(BaseModel):
    contact_list: List[Contact]


class IssueType(BaseModel):
    issue_type_key: Optional[str] = Field(None)
    label: Optional[str] = Field(None)
    name: Optional[str] = Field(None)

class Category(BaseModel):
    category_key: Optional[str] = Field(None)
    name: Optional[str] = Field(None)

class SubCategory(BaseModel):
    sub_category_key: Optional[str] = Field(None)
    name: Optional[str] = Field(None)


class IncidentType(BaseModel):
    name: Optional[str] = Field(None)
    label: Optional[str] = Field(None)
    category: Optional[Category] = Field(None)
    sub_category: Optional[SubCategory] = Field(None)


class Item(BaseModel):
    item_key: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    type: Optional[str] = Field(None)
    category: Optional[Category] = Field(None)
    sub_category: Optional[SubCategory] = Field(None)
    issue_type: Optional[IssueType] = Field(None)

class Resource(BaseModel):
    item: Optional[Item] = Field(None)
    region: Optional[str] = Field(None)


class Ticket(BaseModel):
    ticket_number: Optional[str] = Field(None)
    severity: Optional[str] = Field(None)
    resource_list: Optional[List[Resource]] = Field(None)
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    time_created: Optional[int] = Field(None)
    time_updated: Optional[int] = Field(None)
    lifecycle_state: Optional[str] = Field(None)
    lifecycle_details: Optional[str] = Field(None)


class Impact(BaseModel):
    type: Optional[str] = Field(None)
    description: Optional[str] = Field(None)

class User(BaseModel):
    name: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    contact_number: Optional[str] = Field(None)
    country: Optional[str] = Field(None)

class Context(BaseModel):
    context_type: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    additional_details: Optional[dict] = Field(None)

class Incident(BaseModel):
    key: Optional[str] = Field(None)
    compartment_id: Optional[str] = Field(None)
    ticket_number: Optional[str] = Field(None)
    incident_type: Optional[IncidentType] = Field(None)
    severity: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    lifecycle_state: Optional[str] = Field(None)
    resource: Optional[Resource] = Field(None)
    resources: Optional[List[Resource]] = Field(None)
    time_created: Optional[datetime] = Field(None)
    time_updated: Optional[datetime] = Field(None)
    referrer: Optional[str] = Field(None)
    tenancy_id: Optional[str] = Field(None)
    contact_list: Optional[List[Contact]] = Field(None)
    ticket: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    impact: Optional[Impact] = Field(None)
    context: Optional[Context] = Field(None)
    user: Optional[User] = Field(None)
    department: Optional[str] = Field(None)
    problem_type: Optional[str] = Field(None)

class TenancyInformation(BaseModel):
    customer_support_key: Optional[str] = Field(None)
    tenancy_id: Optional[str] = Field(None)

class ServiceCategory(BaseModel):
    key: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    label: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    issue_type_list: Optional[List[IssueType]] = Field(None)
    supported_subscriptions: Optional[List[str]] = Field(None)
    scope: Optional[str] = Field(None)
    unit: Optional[str] = Field(None)
    limit_id: Optional[str] = Field(None)

class SubComponents(BaseModel):
    sub_category: Optional[Dict[str, str]] = Field(None)
    schema: Optional[str] = Field(None)

class SubCategories(BaseModel):
    service_category: Optional[Dict[str, str]] = Field(None)
    schema: Optional[str] = Field(None)
    has_sub_category: Optional[str] = Field(None)
    sub_categories: Optional[List[SubComponents]] = Field(None)

class Services(BaseModel):
    service: Optional[Dict[str, str]] = Field(None)
    schema: Optional[str] = Field(None)
    service_categories: Optional[List[SubCategories]] = Field(None)

class IncidentResourceType(BaseModel):
    resource_type_key: Optional[str] = Field(None)
    name: Optional[str] = Field(None)
    label: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    is_subscriptions_supported: Optional[bool] = Field(None)
    service_category_list: Optional[List[ServiceCategory]] = Field(None)
    service: Optional[Dict[str, str]] = Field(None)
    services: Optional[List[Services]] = Field(None)

class IncidentSummary(BaseModel):
    key: Optional[str] = Field(None)
    compartment_id: Optional[str] = Field(None)
    contact_list: Optional[ContactList] = Field(None)
    tenancy_information: Optional[TenancyInformation] = Field(None)
    ticket: Optional[Ticket] = Field(None)
    incident_type: Optional[IncidentResourceType] = Field(None)
    migrated_sr_number: Optional[str] = Field(None)
    user_group_id: Optional[str] = Field(None)
    user_group_name: Optional[str] = Field(None)
    primary_contact_party_id: Optional[str] = Field(None)
    primary_contact_party_name: Optional[str] = Field(None)
    is_write_permitted: Optional[bool] = Field(None)
    warn_message: Optional[str] = Field(None)
    problem_type: Optional[str] = Field(None)
# --- Mapping Utilities ---

def map_impact(oci_impact) -> Impact | None:
    if not oci_impact:
        return None
    return Impact(
        type=getattr(oci_impact, "type", None),
        description=getattr(oci_impact, "description", None),
    )

def map_user(oci_user) -> User | None:
    if not oci_user:
        return None
    return User(
        name=getattr(oci_user, "name", None),
        email=getattr(oci_user, "email", None),
        contact_number=getattr(oci_user, "contact_number", None),
        country=getattr(oci_user, "country", None),
    )

def map_context(oci_context) -> Context | None:
    if not oci_context:
        return None
    return Context(
        context_type=getattr(oci_context, "context_type", None),
        description=getattr(oci_context, "description", None),
        additional_details=getattr(oci_context, "additional_details", None),
    )

def map_incident(oci_incident) -> Incident | None:
    if not oci_incident:
        return None

    def get(field, default=None):
        if isinstance(oci_incident, dict):
            return oci_incident.get(field, default)
        return getattr(oci_incident, field, default)

    return Incident(
        key=get("key"),
        compartment_id=get("compartment_id"),
        ticket_number=get("ticket_number"),
        incident_type=map_incident_type(get("incident_type")),
        severity=get("severity"),
        status=get("status"),
        lifecycle_state=get("lifecycle_state"),
        resource=map_resource(get("resource")),
        resources=[map_resource(r) for r in (get("resources") or [])] if get("resources") else None,
        time_created=get("time_created"),
        time_updated=get("time_updated"),
        referrer=get("referrer"),
        tenancy_id=get("tenancy_id"),
        contact_list=[map_contact(c) for c in (get("contact_list") or [])] if get("contact_list") else None,
        ticket=map_ticket(get("ticket")),
        description=get("description"),
        impact=map_impact(get("impact")),
        context=map_context(get("context")),
        user=map_user(get("user")),
        department=get("department"),
        problem_type=get("problem_type"),
    )

def map_contact(oci_contact) -> Contact | None:
    if not oci_contact:
        return None
    def get(field, default=None):
        if isinstance(oci_contact, dict):
            return oci_contact.get(field, default)
        return getattr(oci_contact, field, default)
    return Contact(
        contact_name=get("contact_name"),
        contact_email=get("contact_email"),
        email=get("email"),
        contact_phone=get("contact_phone"),
        contact_type=get("contact_type"),
    )

def map_contact_list(oci_contact_list) -> ContactList | None:
    if not oci_contact_list:
        return None
    def get(field, default=None):
        if isinstance(oci_contact_list, dict):
            return oci_contact_list.get(field, default)
        return getattr(oci_contact_list, field, default)
    cl = get("contact_list")
    return ContactList(contact_list=[map_contact(c) for c in (cl or [])])

def map_category(oci_category) -> Category | None:
    if not oci_category:
        return None
    def get(field, default=None):
        if isinstance(oci_category, dict):
            return oci_category.get(field, default)
        return getattr(oci_category, field, default)
    return Category(
        category_key=get("category_key"),
        name=get("name"),
    )

def map_sub_category(oci_sub_category) -> SubCategory | None:
    if not oci_sub_category:
        return None
    def get(field, default=None):
        if isinstance(oci_sub_category, dict):
            return oci_sub_category.get(field, default)
        return getattr(oci_sub_category, field, default)
    return SubCategory(
        sub_category_key=get("sub_category_key"),
        name=get("name"),
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

def map_tenancy_information(oci_ti) -> TenancyInformation | None:
    if not oci_ti:
        return None
    def get(field, default=None):
        if isinstance(oci_ti, dict):
            return oci_ti.get(field, default)
        return getattr(oci_ti, field, default)
    return TenancyInformation(
        customer_support_key=get("customer_support_key"),
        tenancy_id=get("tenancy_id")
    )

def map_issue_type(oci_issue_type) -> IssueType | None:
    if not oci_issue_type:
        return None
    def get(field, default=None):
        if isinstance(oci_issue_type, dict):
            return oci_issue_type.get(field, default)
        return getattr(oci_issue_type, field, default)
    return IssueType(
        issue_type_key=get("issue_type_key"),
        label=get("label"),
        name=get("name"),
    )

def map_item(oci_item) -> Item | None:
    if not oci_item:
        return None
    def get(field, default=None):
        if isinstance(oci_item, dict):
            return oci_item.get(field, default)
        return getattr(oci_item, field, default)
    return Item(
        item_key=get("item_key"),
        name=get("name"),
        type=get("type"),
        category=map_category(get("category")),
        sub_category=map_sub_category(get("sub_category")),
        issue_type=map_issue_type(get("issue_type")),
    )

def map_resource(oci_resource) -> Resource | None:
    if not oci_resource:
        return None
    def get(field, default=None):
        if isinstance(oci_resource, dict):
            return oci_resource.get(field, default)
        return getattr(oci_resource, field, default)
    return Resource(
        item=map_item(get("item")),
        region=get("region"),
    )

def map_ticket(oci_ticket) -> Ticket | None:
    if not oci_ticket:
        return None
    def get(field, default=None):
        if isinstance(oci_ticket, dict):
            return oci_ticket.get(field, default)
        return getattr(oci_ticket, field, default)
    return Ticket(
        ticket_number=get("ticket_number"),
        severity=get("severity"),
        resource_list=[map_resource(r) for r in (get("resource_list") or [])],
        title=get("title"),
        description=get("description"),
        time_created=get("time_created"),
        time_updated=get("time_updated"),
        lifecycle_state=get("lifecycle_state"),
        lifecycle_details=get("lifecycle_details"),
    )

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
        contact_list=map_contact_list(get("contact_list")),
        tenancy_information=map_tenancy_information(get("tenancy_information")),
        ticket=map_ticket(get("ticket")),
        incident_type=get("incident_type"),  # for now, adjust if explicit mapping is required
        migrated_sr_number=get("migrated_sr_number"),
        user_group_id=get("user_group_id"),
        user_group_name=get("user_group_name"),
        primary_contact_party_id=get("primary_contact_party_id"),
        primary_contact_party_name=get("primary_contact_party_name"),
        is_write_permitted=get("is_write_permitted"),
        warn_message=get("warn_message"),
        problem_type=get("problem_type"),
    )
