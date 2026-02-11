"""
Unit tests for oracle.oci_support_mcp_server.models mapping utilities and Pydantic model validation.
Designed to increase coverage of models.py (mappings and edge cases).
"""

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
