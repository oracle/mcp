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
    resource_list: Optional[List[dict]] = Field(None)  # dict instead of Resource for serialization safety
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    time_created: Optional[int] = Field(None)
    time_updated: Optional[int] = Field(None)
    lifecycle_state: Optional[str] = Field(None)
    lifecycle_details: Optional[str] = Field(None)


class User(BaseModel):
    name: Optional[str] = Field(None)
    email: Optional[str] = Field(None)
    contact_number: Optional[str] = Field(None)
    country: Optional[str] = Field(None)

class Context(BaseModel):
    context_type: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    additional_details: Optional[dict] = Field(None)


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

class Incident(BaseModel):
    key: Optional[str] = Field(None)
    compartment_id: Optional[str] = Field(None)
    contact_list: Optional[ContactList] = Field(None)
    tenancy_information: Optional[TenancyInformation] = Field(None)
    ticket: Optional[Ticket] = Field(None)
    incident_type: Optional[IncidentType] = Field(None)
    migrated_sr_number: Optional[str] = Field(None)
    user_group_id: Optional[str] = Field(None)
    user_group_name: Optional[str] = Field(None)
    primary_contact_party_id: Optional[str] = Field(None)
    primary_contact_party_name: Optional[str] = Field(None)
    is_write_permitted: Optional[bool] = Field(None)
    warn_message: Optional[str] = Field(None)
    problem_type: Optional[str] = Field(None)
    referrer: Optional[str] = Field(None)

class ContextualData(BaseModel):
    client_id: Optional[str] = Field(None)
    schema_name: Optional[str] = Field(None)
    schema_version: Optional[str] = Field(None)
    payload: Optional[str] = Field(None)

class CreateCategoryDetails(BaseModel):
    category_key: Optional[str] = Field(None)

class CreateSubCategoryDetails(BaseModel):
    sub_category_key: Optional[str] = Field(None)

class CreateIssueTypeDetails(BaseModel):
    issue_type_key: Optional[str] = Field(None)

class CreateItemDetails(BaseModel):
    type: Optional[str] = Field(None)
    category: Optional[CreateCategoryDetails] = Field(None)
    sub_category: Optional[CreateSubCategoryDetails] = Field(None)
    issue_type: Optional[CreateIssueTypeDetails] = Field(None)
    name: Optional[str] = Field(None)

class CreateResourceDetails(BaseModel):
    item: Optional[CreateItemDetails] = Field(None)
    region: Optional[str] = Field(None)

class CreateTicketDetails(BaseModel):
    severity: Optional[str] = Field(None)
    resource_list: Optional[List[CreateResourceDetails]] = Field(None)
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    contextual_data: Optional[ContextualData] = Field(None)

class CreateIncident(BaseModel):
    compartment_id: Optional[str] = Field(None)
    ticket: Optional[CreateTicketDetails] = Field(None)
    csi: Optional[str] = Field(None)
    user_group_id: Optional[str] = Field(None)
    problem_type: Optional[str] = Field(None)
    contacts: Optional[List[Contact]] = Field(None)
    referrer: Optional[str] = Field(None)

class CmosUserGroupInfo(BaseModel):
    user_group_id: Optional[str] = Field(None)
    user_group_name: Optional[str] = Field(None)

class ValidationResponse(BaseModel):
    is_valid_user: Optional[bool] = Field(None)
    write_permitted_user_group_infos: Optional[List[CmosUserGroupInfo]] = Field(None)



# --- Conversion to OCI SDK Model Utilities ---

def to_oci_create_category_details(p):
    if p is None:
        return None
    import oci.cims.models
    return oci.cims.models.CreateCategoryDetails(category_key=p.category_key)

def to_oci_create_sub_category_details(p):
    if p is None:
        return None
    import oci.cims.models
    return oci.cims.models.CreateSubCategoryDetails(sub_category_key=p.sub_category_key)

def to_oci_create_issue_type_details(p):
    if p is None:
        return None
    import oci.cims.models
    return oci.cims.models.CreateIssueTypeDetails(issue_type_key=p.issue_type_key)

def to_oci_create_item_details(p):
    if p is None:
        return None
    import oci.cims.models
    return oci.cims.models.CreateItemDetails(
        type=p.type,
        category=to_oci_create_category_details(p.category) if hasattr(p, "category") else None,
        sub_category=to_oci_create_sub_category_details(p.sub_category) if hasattr(p, "sub_category") else None,
        issue_type=to_oci_create_issue_type_details(p.issue_type) if hasattr(p, "issue_type") else None,
        name=p.name
    )

def to_oci_create_resource_details(p):
    if p is None:
        return None
    import oci.cims.models
    return oci.cims.models.CreateResourceDetails(
        item=to_oci_create_item_details(p.item) if hasattr(p, "item") else None,
        region=p.region
    )

def to_oci_contextual_data(p):
    if p is None:
        return None
    import oci.cims.models
    return oci.cims.models.ContextualData(
        client_id=p.client_id,
        schema_name=p.schema_name,
        schema_version=p.schema_version,
        payload=p.payload
    )

def to_oci_create_ticket_details(p):
    if p is None:
        return None
    import oci.cims.models
    resource_list = [
        to_oci_create_resource_details(r)
        for r in (p.resource_list or [])
    ] if p.resource_list else None
    contextual_data = to_oci_contextual_data(p.contextual_data) if p.contextual_data else None
    return oci.cims.models.CreateTicketDetails(
        severity=p.severity,
        resource_list=resource_list,
        title=p.title,
        description=p.description,
        contextual_data=contextual_data
    )

def to_oci_create_incident(p):
    if p is None:
        return None
    import oci.cims.models
    ticket = to_oci_create_ticket_details(p.ticket) if p.ticket else None
    return oci.cims.models.CreateIncident(
        compartment_id=p.compartment_id,
        ticket=ticket,
        csi=p.csi,
        user_group_id=p.user_group_id,
        problem_type=p.problem_type,
        contacts=[c.model_dump(exclude_none=True) for c in (p.contacts or [])] if getattr(p, "contacts", None) else None,
        referrer=p.referrer
    )

# --- Mapping Utilities ---
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
    mapped_category = map_category(get("category"))
    if mapped_category is not None and hasattr(mapped_category, "model_dump"):
        mapped_category = mapped_category.model_dump(exclude_none=True)
    mapped_sub_category = map_sub_category(get("sub_category"))
    if mapped_sub_category is not None and hasattr(mapped_sub_category, "model_dump"):
        mapped_sub_category = mapped_sub_category.model_dump(exclude_none=True)
    mapped_issue_type = map_issue_type(get("issue_type"))
    if mapped_issue_type is not None and hasattr(mapped_issue_type, "model_dump"):
        mapped_issue_type = mapped_issue_type.model_dump(exclude_none=True)
    return Item(
        item_key=get("item_key"),
        name=get("name"),
        type=get("type"),
        category=mapped_category,
        sub_category=mapped_sub_category,
        issue_type=mapped_issue_type,
    )

def map_resource(oci_resource) -> Resource | None:
    if not oci_resource:
        return None
    def get(field, default=None):
        if isinstance(oci_resource, dict):
            return oci_resource.get(field, default)
        return getattr(oci_resource, field, default)
    mapped_item = map_item(get("item"))
    if mapped_item is not None and hasattr(mapped_item, "model_dump"):
        mapped_item = mapped_item.model_dump(exclude_none=True)
    return Resource(
        item=mapped_item,
        region=get("region"),
    )

def map_ticket(oci_ticket) -> Ticket | None:
    if not oci_ticket:
        return None
    def get(field, default=None):
        if isinstance(oci_ticket, dict):
            return oci_ticket.get(field, default)
        return getattr(oci_ticket, field, default)
    resource_list = []
    for r in get("resource_list") or []:
        mapped = map_resource(r)
        if mapped is not None:
            # Ensure mapped is dict for serialization
            if hasattr(mapped, "model_dump"):
                mapped = mapped.model_dump(exclude_none=True)
        resource_list.append(mapped)
    return Ticket(
        ticket_number=get("ticket_number"),
        severity=get("severity"),
        resource_list=resource_list if resource_list else None,
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
def map_contextual_data(oci_ctx) -> ContextualData | None:
    if not oci_ctx:
        return None
    def get(field, default=None):
        if isinstance(oci_ctx, dict):
            return oci_ctx.get(field, default)
        return getattr(oci_ctx, field, default)
    return ContextualData(
        client_id=get("client_id"),
        schema_name=get("schema_name"),
        schema_version=get("schema_version"),
        payload=get("payload"),
    )

def map_create_category_details(oci_cat) -> CreateCategoryDetails | None:
    if not oci_cat:
        return None
    def get(field, default=None):
        if isinstance(oci_cat, dict):
            return oci_cat.get(field, default)
        return getattr(oci_cat, field, default)
    return CreateCategoryDetails(
        category_key=get("category_key"),
    )

def map_create_sub_category_details(oci_subcat) -> CreateSubCategoryDetails | None:
    if not oci_subcat:
        return None
    def get(field, default=None):
        if isinstance(oci_subcat, dict):
            return oci_subcat.get(field, default)
        return getattr(oci_subcat, field, default)
    return CreateSubCategoryDetails(
        sub_category_key=get("sub_category_key"),
    )

def map_create_issue_type_details(oci_iss) -> CreateIssueTypeDetails | None:
    if not oci_iss:
        return None
    def get(field, default=None):
        if isinstance(oci_iss, dict):
            return oci_iss.get(field, default)
        return getattr(oci_iss, field, default)
    return CreateIssueTypeDetails(
        issue_type_key=get("issue_type_key"),
    )

def map_create_item_details(oci_item) -> CreateItemDetails | None:
    if not oci_item:
        return None
    def get(field, default=None):
        if isinstance(oci_item, dict):
            return oci_item.get(field, default)
        return getattr(oci_item, field, default)
    return CreateItemDetails(
        type=get("type"),
        category=map_create_category_details(get("category")),
        sub_category=map_create_sub_category_details(get("sub_category")),
        issue_type=map_create_issue_type_details(get("issue_type")),
        name=get("name"),
    )

def map_create_resource_details(oci_crd) -> CreateResourceDetails | None:
    if not oci_crd:
        return None
    def get(field, default=None):
        if isinstance(oci_crd, dict):
            return oci_crd.get(field, default)
        return getattr(oci_crd, field, default)
    return CreateResourceDetails(
        item=map_create_item_details(get("item")),
        region=get("region"),
    )

def map_create_ticket_details(oci_ticket) -> CreateTicketDetails | None:
    if not oci_ticket:
        return None
    def get(field, default=None):
        if isinstance(oci_ticket, dict):
            return oci_ticket.get(field, default)
        return getattr(oci_ticket, field, default)
    return CreateTicketDetails(
        severity=get("severity"),
        resource_list=[
            map_create_resource_details(r) for r in (get("resource_list") or [])
        ] if get("resource_list") else None,
        title=get("title"),
        description=get("description"),
        contextual_data=map_contextual_data(get("contextual_data")),
    )

def map_create_incident(oci_incident) -> CreateIncident | None:
    if not oci_incident:
        return None
    def get(field, default=None):
        if isinstance(oci_incident, dict):
            return oci_incident.get(field, default)
        return getattr(oci_incident, field, default)
    return CreateIncident(
        compartment_id=get("compartment_id"),
        ticket=map_create_ticket_details(get("ticket")),
        csi=get("csi"),
        user_group_id=get("user_group_id"),
        problem_type=get("problem_type"),
        contacts=[map_contact(c) for c in get("contacts") or []] if get("contacts") else None,
        referrer=get("referrer"),
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
        contact_list=map_contact_list(get("contact_list")),
        tenancy_information=map_tenancy_information(get("tenancy_information")),
        ticket=map_ticket(get("ticket")),
        incident_type=map_incident_type(get("incident_type")),
        migrated_sr_number=get("migrated_sr_number"),
        user_group_id=get("user_group_id"),
        user_group_name=get("user_group_name"),
        primary_contact_party_id=get("primary_contact_party_id"),
        primary_contact_party_name=get("primary_contact_party_name"),
        is_write_permitted=get("is_write_permitted"),
        warn_message=get("warn_message"),
        problem_type=get("problem_type"),
        referrer=get("referrer"),
    )

def map_incident_resource_type(oci_resource_type) -> IncidentResourceType | None:
    if not oci_resource_type:
        return None
    def get(field, default=None):
        if isinstance(oci_resource_type, dict):
            return oci_resource_type.get(field, default)
        return getattr(oci_resource_type, field, default)
    return IncidentResourceType(
        resource_type_key=get("resource_type_key"),
        name=get("name"),
        label=get("label"),
        description=get("description"),
        is_subscriptions_supported=get("is_subscriptions_supported"),
        service_category_list=[map_service_category(sc) for sc in (get("service_category_list") or [])] if get("service_category_list") else None,
        service=get("service"),
        services=[map_services(s) for s in (get("services") or [])] if get("services") else None,
    )

def map_service_category(oci_service_category) -> ServiceCategory | None:
    if not oci_service_category:
        return None
    def get(field, default=None):
        if isinstance(oci_service_category, dict):
            return oci_service_category.get(field, default)
        return getattr(oci_service_category, field, default)
    return ServiceCategory(
        key=get("key"),
        name=get("name"),
        label=get("label"),
        description=get("description"),
        issue_type_list=[map_issue_type(it) for it in (get("issue_type_list") or [])] if get("issue_type_list") else None,
        supported_subscriptions=get("supported_subscriptions"),
        scope=get("scope"),
        unit=get("unit"),
        limit_id=get("limit_id"),
    )

def map_services(oci_services) -> Services | None:
    if not oci_services:
        return None
    def get(field, default=None):
        if isinstance(oci_services, dict):
            return oci_services.get(field, default)
        return getattr(oci_services, field, default)
    return Services(
        service=get("service"),
        schema=get("schema"),
        service_categories=[map_sub_categories(sc) for sc in (get("service_categories") or [])] if get("service_categories") else None
    )

def map_sub_categories(oci_sub_categories) -> SubCategories | None:
    if not oci_sub_categories:
        return None
    def get(field, default=None):
        if isinstance(oci_sub_categories, dict):
            return oci_sub_categories.get(field, default)
        return getattr(oci_sub_categories, field, default)
    return SubCategories(
        service_category=get("service_category"),
        schema=get("schema"),
        has_sub_category=get("has_sub_category"),
        sub_categories=[map_sub_components(sc) for sc in (get("sub_categories") or [])] if get("sub_categories") else None
    )

def map_sub_components(oci_sub_components) -> SubComponents | None:
    if not oci_sub_components:
        return None
    def get(field, default=None):
        if isinstance(oci_sub_components, dict):
            return oci_sub_components.get(field, default)
        return getattr(oci_sub_components, field, default)
    return SubComponents(
        sub_category=get("sub_category"),
        schema=get("schema"),
    )

def map_cmos_user_group_info(oci_user_group_info) -> CmosUserGroupInfo | None:
    if not oci_user_group_info:
        return None
    def get(field, default=None):
        if isinstance(oci_user_group_info, dict):
            return oci_user_group_info.get(field, default)
        return getattr(oci_user_group_info, field, default)
    return CmosUserGroupInfo(
        user_group_id=get("user_group_id"),
        user_group_name=get("user_group_name"),
    )

def map_validation_response(oci_validation_response) -> ValidationResponse | None:
    if not oci_validation_response:
        return None
    def get(field, default=None):
        if isinstance(oci_validation_response, dict):
            return oci_validation_response.get(field, default)
        return getattr(oci_validation_response, field, default)
    user_groups = get("write_permitted_user_group_infos")
    mapped_groups = [map_cmos_user_group_info(g) for g in (user_groups or [])] if user_groups else None
    return ValidationResponse(
        is_valid_user=get("is_valid_user"),
        write_permitted_user_group_infos=mapped_groups
    )
