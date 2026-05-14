"""
Unit tests for oracle.oci_support_mcp_server.models mapping utilities and Pydantic model validation.
Designed to increase coverage of models.py (mappings and edge cases).
"""

import inspect
from types import SimpleNamespace

from oracle.oci_support_mcp_server import models


def test_map_incident_summary_with_dict():
    input_dict = {
        "key": "K1",
        "compartment_id": "C1",
        "problem_type": "TECH",
        "ticket": {
            "severity": "SEV1",
        },
    }
    result = models.map_incident_summary(input_dict)
    assert isinstance(result, models.IncidentSummary)
    assert result.key == "K1"
    assert result.compartment_id == "C1"
    assert result.problem_type == "TECH"
    assert result.ticket.severity == "SEV1"


def test_map_incident_summary_with_none():
    assert models.map_incident_summary(None) is None


def test_map_incident_with_dict():
    input_dict = {
        "key": "INC1",
        "compartment_id": "COMP1",
        "problem_type": "LIMIT",
        "ticket": {
            "severity": "SEV2",
        },
    }
    result = models.map_incident(input_dict)
    assert isinstance(result, models.Incident)
    assert result.key == "INC1"
    assert result.compartment_id == "COMP1"
    assert result.problem_type == "LIMIT"
    assert result.ticket.severity == "SEV2"


def test_map_incident_with_none():
    assert models.map_incident(None) is None


def test_map_incident_resource_type_with_dict():
    input_dict = {
        "resource_type_key": "RTKEY",
        "name": "ResourceType1",
        "description": "A type",
    }
    result = models.map_incident_resource_type(input_dict)
    assert isinstance(result, models.IncidentResourceType)
    assert result.resource_type_key == "RTKEY"
    assert result.name == "ResourceType1"
    assert result.description == "A type"


def test_map_validation_response_with_dict():
    input_dict = {
        "is_valid_user": True,
        "write_permitted_user_group_infos": [
            {"user_group_id": "UG1", "user_group_name": "Group One"}
        ],
    }
    result = models.map_validation_response(input_dict)
    assert result.is_valid_user is True
    assert isinstance(result.write_permitted_user_group_infos, list)
    assert result.write_permitted_user_group_infos[0].user_group_id == "UG1"
    assert result.write_permitted_user_group_infos[0].user_group_name == "Group One"


def test_contact_and_map_contact():
    d = {"contact_name": "A", "email": "a@example.com"}
    obj = models.Contact(**d)
    mapped = models.map_contact(d)
    assert mapped.contact_name == "A"
    assert mapped.email == "a@example.com"
    assert obj.model_dump() == mapped.model_dump()


def test_category_and_map_category():
    d = {"category_key": "cat-01", "name": "Hardware"}
    obj = models.Category(**d)
    mapped = models.map_category(d)
    assert mapped.category_key == "cat-01"
    assert mapped.name == "Hardware"
    assert obj.model_dump() == mapped.model_dump()


def test_item_and_map_item_with_none():
    assert models.map_item(None) is None


def test_all_generated_mappers_handle_none():
    for mapper_name, mapper in inspect.getmembers(models, inspect.isfunction):
        if mapper_name.startswith("map_"):
            assert mapper(None) is None, mapper_name


def test_create_incident_conversion_to_oci_sdk_models():
    incident = models.CreateIncident(
        compartment_id="compartment",
        user_group_id="group",
        problem_type="TECH",
        referrer="codex",
        contacts=[models.Contact(contact_name="Ada", email="ada@example.com")],
        ticket=models.CreateTicketDetails(
            severity="HIGH",
            title="Title",
            description="Description",
            contextual_data=models.ContextualData(
                client_id="client",
                schema_name="schema",
                schema_version="1",
                payload="{}",
            ),
            resource_list=[
                models.CreateResourceDetails(
                    region="us-ashburn-1",
                    item=models.CreateItemDetails(
                        type="service",
                        name="Compute",
                        category=models.CreateCategoryDetails(category_key="cat"),
                        sub_category=models.CreateSubCategoryDetails(
                            sub_category_key="subcat"
                        ),
                        issue_type=models.CreateIssueTypeDetails(
                            issue_type_key="issue"
                        ),
                    ),
                )
            ],
        ),
    )

    sdk_incident = models.to_oci_create_incident(incident)

    assert sdk_incident.compartment_id == "compartment"
    assert sdk_incident.user_group_id == "group"
    assert sdk_incident.problem_type == "TECH"
    assert sdk_incident.contacts == [{"contact_name": "Ada", "email": "ada@example.com"}]
    assert sdk_incident.ticket.severity == "HIGH"
    assert sdk_incident.ticket.contextual_data.client_id == "client"
    assert sdk_incident.ticket.resource_list[0].region == "us-ashburn-1"
    assert sdk_incident.ticket.resource_list[0].item.category.category_key == "cat"
    assert sdk_incident.ticket.resource_list[0].item.sub_category.sub_category_key == "subcat"
    assert sdk_incident.ticket.resource_list[0].item.issue_type.issue_type_key == "issue"


def test_create_incident_conversion_handles_none_and_missing_nested_fields():
    assert models.to_oci_create_category_details(None) is None
    assert models.to_oci_create_sub_category_details(None) is None
    assert models.to_oci_create_issue_type_details(None) is None
    assert models.to_oci_create_item_details(None) is None
    assert models.to_oci_create_resource_details(None) is None
    assert models.to_oci_contextual_data(None) is None
    assert models.to_oci_create_ticket_details(None) is None
    assert models.to_oci_create_incident(None) is None

    item = SimpleNamespace(type="service", name="Bare Item")
    assert models.to_oci_create_item_details(item).name == "Bare Item"

    resource = SimpleNamespace(region="us-phoenix-1")
    assert models.to_oci_create_resource_details(resource).region == "us-phoenix-1"

    ticket = models.CreateTicketDetails(severity="LOW")
    assert models.to_oci_create_ticket_details(ticket).resource_list is None
    assert models.to_oci_create_ticket_details(ticket).contextual_data is None

    incident = models.CreateIncident(compartment_id="compartment")
    sdk_incident = models.to_oci_create_incident(incident)
    assert sdk_incident.ticket is None
    assert sdk_incident.contacts is None


def test_nested_mapping_from_dicts():
    incident_payload = {
        "key": "INC1",
        "compartment_id": "compartment",
        "contact_list": {
            "contact_list": [
                {
                    "contact_name": "Ada",
                    "contact_email": "ada@oracle.com",
                    "contact_phone": "555",
                    "contact_type": "PRIMARY",
                }
            ]
        },
        "tenancy_information": {
            "customer_support_key": "csk",
            "tenancy_id": "tenancy",
        },
        "ticket": {
            "ticket_number": "SR1",
            "severity": "SEV2",
            "resource_list": [
                {
                    "region": "us-ashburn-1",
                    "item": {
                        "item_key": "item",
                        "name": "Compute",
                        "type": "service",
                        "category": {"category_key": "cat", "name": "Category"},
                        "sub_category": {
                            "sub_category_key": "subcat",
                            "name": "Subcategory",
                        },
                        "issue_type": {
                            "issue_type_key": "issue",
                            "label": "Issue Label",
                            "name": "Issue",
                        },
                    },
                }
            ],
            "title": "Title",
            "description": "Description",
            "time_created": 1,
            "time_updated": 2,
            "lifecycle_state": "ACTIVE",
            "lifecycle_details": "Open",
        },
        "incident_type": {
            "name": "Technical",
            "label": "Tech",
            "category": {"category_key": "cat", "name": "Category"},
            "sub_category": {"sub_category_key": "subcat", "name": "Subcategory"},
        },
        "migrated_sr_number": "MSR1",
        "user_group_id": "group-id",
        "user_group_name": "Group",
        "primary_contact_party_id": "party-id",
        "primary_contact_party_name": "Party",
        "is_write_permitted": True,
        "warn_message": "warn",
        "problem_type": "TECH",
        "referrer": "codex",
    }

    incident = models.map_incident(incident_payload)

    assert incident.key == "INC1"
    assert incident.contact_list.contact_list[0].contact_name == "Ada"
    assert incident.tenancy_information.customer_support_key == "csk"
    assert incident.ticket.resource_list[0].item.issue_type.issue_type_key == "issue"
    assert incident.incident_type.name is None
    assert incident.referrer == "codex"

    summary_payload = dict(incident_payload)
    summary_payload["incident_type"] = {"resource_type_key": "rt", "name": "Resource"}
    summary = models.map_incident_summary(summary_payload)
    assert summary.ticket.title == "Title"
    assert summary.incident_type.resource_type_key == "rt"
    assert summary.incident_type.name == "Resource"


def test_nested_mapping_from_objects():
    user = models.map_user(
        SimpleNamespace(
            name="Ada",
            email="ada@example.com",
            contact_number="555",
            country="US",
        )
    )
    assert user.email == "ada@example.com"

    context = models.map_context(
        SimpleNamespace(
            context_type="json",
            description="desc",
            additional_details={"key": "value"},
        )
    )
    assert context.additional_details == {"key": "value"}

    incident_type = models.map_incident_type(
        SimpleNamespace(
            name="Technical",
            label="Tech",
            category=SimpleNamespace(category_key="cat", name="Category"),
            sub_category=SimpleNamespace(sub_category_key="subcat", name="Subcategory"),
        )
    )
    assert incident_type.category.category_key == "cat"
    assert incident_type.sub_category.sub_category_key == "subcat"

    contact_list = models.map_contact_list(
        SimpleNamespace(
            contact_list=[SimpleNamespace(contact_name="Ada", email="ada@example.com")]
        )
    )
    assert contact_list.contact_list[0].email == "ada@example.com"


def test_create_model_mappers_and_resource_type_taxonomy():
    create_payload = {
        "compartment_id": "compartment",
        "user_group_id": "group",
        "problem_type": "TECH",
        "referrer": "codex",
        "contacts": [{"contact_name": "Ada"}],
        "ticket": {
            "severity": "SEV2",
            "title": "Title",
            "description": "Description",
            "resource_list": [
                {
                    "region": "us-ashburn-1",
                    "item": {
                        "type": "service",
                        "name": "Compute",
                        "category": {"category_key": "cat"},
                        "sub_category": {"sub_category_key": "subcat"},
                        "issue_type": {"issue_type_key": "issue"},
                    },
                }
            ],
            "contextual_data": {
                "client_id": "client",
                "schema_name": "schema",
                "schema_version": "1",
                "payload": "{}",
            },
        },
    }

    create_incident = models.map_create_incident(create_payload)

    assert create_incident.compartment_id == "compartment"
    assert create_incident.ticket.resource_list[0].item.category.category_key == "cat"
    assert create_incident.ticket.contextual_data.client_id == "client"
    assert create_incident.contacts[0].contact_name == "Ada"

    resource_type = models.map_incident_resource_type(
        {
            "resource_type_key": "rt",
            "name": "Resource",
            "label": "Label",
            "description": "Description",
            "is_subscriptions_supported": True,
            "service_category_list": [
                {
                    "key": "service-cat",
                    "name": "Service Category",
                    "label": "SC",
                    "description": "desc",
                    "issue_type_list": [
                        {
                            "issue_type_key": "issue",
                            "label": "Issue Label",
                            "name": "Issue",
                        }
                    ],
                    "supported_subscriptions": ["sub1"],
                    "scope": "TENANCY",
                    "unit": "COUNT",
                    "limit_id": "limit",
                }
            ],
            "service": {"key": "service"},
            "services": [
                {
                    "service": {"key": "compute"},
                    "schema": "schema",
                    "service_categories": [
                        {
                            "service_category": {"key": "compute-cat"},
                            "schema": "category-schema",
                            "has_sub_category": "true",
                            "sub_categories": [
                                {
                                    "sub_category": {"key": "sub"},
                                    "schema": "sub-schema",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )

    assert resource_type.service_category_list[0].issue_type_list[0].name == "Issue"
    assert resource_type.services[0].service_categories[0].sub_categories[0].schema == "sub-schema"


def test_validation_response_maps_object_user_groups():
    response = models.map_validation_response(
        SimpleNamespace(
            is_valid_user=False,
            write_permitted_user_group_infos=[
                SimpleNamespace(user_group_id="group-id", user_group_name="Group")
            ],
        )
    )

    assert response.is_valid_user is False
    assert response.write_permitted_user_group_infos[0].user_group_name == "Group"
