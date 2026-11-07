
from unittest.mock import Mock

import pytest

from oracle.oci_iot_mcp_server import resolvers
from oracle.oci_iot_mcp_server.resolvers import (
    resolve_domain_selector,
    resolve_twin_selector,
)


COMPARTMENT_ID = "compartment-ocid"
DOMAIN_ID = "domain-ocid"


def _domain(resource_id, name, device_host=None):
    return {
        "id": resource_id,
        "name": name,
        "device_host": device_host,
    }


def _twin(resource_id, name, iot_domain_id):
    return {
        "id": resource_id,
        "name": name,
        "iot_domain_id": iot_domain_id,
    }


def _domain_page(items, next_page=None):
    return {
        "items": items,
        "opc_next_page": next_page,
    }


def _twin_page(items, next_page=None):
    return {
        "items": items,
        "opc_next_page": next_page,
    }

def test_resolve_domain_selector_returns_match_for_short_id(monkeypatch):
    page_mock = Mock(
        return_value=_domain_page([
            _domain(
                "domain-ocid",
                "factory-domain",
                "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
            )
        ])
    )
    monkeypatch.setattr(
        resolvers, "list_iot_domains_page_record", page_mock
    )

    result = resolve_domain_selector(
        domain_short_id="abc123",
        compartment_id=COMPARTMENT_ID,
    )

    assert result["ok"] is True
    assert result["data"]["id"] == "domain-ocid"
    page_mock.assert_called_once()
    assert page_mock.call_args.kwargs["compartment_id"] == COMPARTMENT_ID
    assert page_mock.call_args.kwargs["page"] is None


def test_resolve_domain_selector_returns_not_found_when_no_match(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "list_iot_domains_page_record",
        Mock(return_value=_domain_page([])),
    )

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        compartment_id=COMPARTMENT_ID,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_resolve_domain_selector_returns_ambiguity_error_for_multiple_matches(
    monkeypatch,
):
    monkeypatch.setattr(
        resolvers,
        "list_iot_domains_page_record",
        Mock(
            return_value=_domain_page([
                _domain(
                    "domain-1",
                    "factory-domain",
                    "abc.device.iot.example.com",
                ),
                _domain(
                    "domain-2",
                    "factory-domain",
                    "xyz.device.iot.example.com",
                ),
            ])
        ),
    )

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        compartment_id=COMPARTMENT_ID,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"


def test_resolve_domain_selector_deduplicates_name_and_short_id_match(
    monkeypatch,
):
    monkeypatch.setattr(
        resolvers,
        "list_iot_domains_page_record",
        Mock(
            return_value=_domain_page([
                _domain(
                    "domain-ocid",
                    "factory-domain",
                    "abc123.device.iot.us-phoenix-1.oci.oraclecloud.com",
                )
            ])
        ),
    )

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        domain_short_id="abc123",
        compartment_id=COMPARTMENT_ID,
    )

    assert result["ok"] is True
    assert result["data"]["id"] == "domain-ocid"


def test_resolve_domain_selector_finds_match_on_later_page(monkeypatch):
    page_mock = Mock(
        side_effect=[
            _domain_page(
                [_domain("domain-other", "other-domain")],
                next_page="page-2",
            ),
            _domain_page([
                _domain(
                    "domain-2",
                    "factory-domain",
                    "abc.device.iot.example.com",
                )
            ]),
        ]
    )
    monkeypatch.setattr(
        resolvers, "list_iot_domains_page_record", page_mock
    )

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        compartment_id=COMPARTMENT_ID,
    )

    assert result["ok"] is True
    assert result["data"]["id"] == "domain-2"
    assert page_mock.call_count == 2
    assert page_mock.call_args_list[0].kwargs["page"] is None
    assert page_mock.call_args_list[1].kwargs["page"] == "page-2"


def test_resolve_domain_selector_detects_ambiguity_across_pages(
    monkeypatch,
):
    page_mock = Mock(
        side_effect=[
            _domain_page(
                [_domain("domain-1", "factory-domain")],
                next_page="page-2",
            ),
            _domain_page([
                _domain("domain-2", "factory-domain")
            ]),
        ]
    )
    monkeypatch.setattr(
        resolvers, "list_iot_domains_page_record", page_mock
    )

    result = resolve_domain_selector(
        iot_domain_display_name="factory-domain",
        compartment_id=COMPARTMENT_ID,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"
    assert page_mock.call_count == 2

def test_resolve_twin_selector_returns_single_friendly_match(monkeypatch):
    monkeypatch.setattr(
        resolvers,
        "list_digital_twin_instances_page_record",
        Mock(
            return_value=_twin_page([
                _twin("twin-1", "pump-01", DOMAIN_ID)
            ])
        ),
    )

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id=DOMAIN_ID,
    )

    assert result == {
        "ok": True,
        "data": {
            "id": "twin-1",
            "name": "pump-01",
            "iot_domain_id": DOMAIN_ID,
        },
    }


def test_resolve_twin_selector_returns_not_found_when_name_has_no_match(
    monkeypatch,
):
    monkeypatch.setattr(
        resolvers,
        "list_digital_twin_instances_page_record",
        Mock(return_value=_twin_page([])),
    )

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id=DOMAIN_ID,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "resource_not_found"


def test_resolve_twin_selector_returns_ambiguity_error_with_candidates(
    monkeypatch,
):
    monkeypatch.setattr(
        resolvers,
        "list_digital_twin_instances_page_record",
        Mock(
            return_value=_twin_page([
                _twin("twin-1", "pump-01", DOMAIN_ID),
                _twin("twin-2", "pump-01", DOMAIN_ID),
            ])
        ),
    )

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id=DOMAIN_ID,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"


def test_resolve_twin_selector_finds_match_on_later_page(monkeypatch):
    page_mock = Mock(
        side_effect=[
            _twin_page(
                [_twin("twin-other", "other-pump", DOMAIN_ID)],
                next_page="page-2",
            ),
            _twin_page([
                _twin("twin-2", "pump-01", DOMAIN_ID)
            ]),
        ]
    )
    monkeypatch.setattr(
        resolvers, "list_digital_twin_instances_page_record", page_mock
    )

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id=DOMAIN_ID,
    )

    assert result["ok"] is True
    assert result["data"]["id"] == "twin-2"
    assert page_mock.call_count == 2
    assert page_mock.call_args_list[0].kwargs["page"] is None
    assert page_mock.call_args_list[1].kwargs["page"] == "page-2"


def test_resolve_twin_selector_detects_ambiguity_across_pages(
    monkeypatch,
):
    page_mock = Mock(
        side_effect=[
            _twin_page(
                [_twin("twin-1", "pump-01", DOMAIN_ID)],
                next_page="page-2",
            ),
            _twin_page([
                _twin("twin-2", "pump-01", DOMAIN_ID)
            ]),
        ]
    )
    monkeypatch.setattr(
        resolvers, "list_digital_twin_instances_page_record", page_mock
    )

    result = resolve_twin_selector(
        digital_twin_instance_name="pump-01",
        iot_domain_id=DOMAIN_ID,
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "ambiguous_identifier"
    assert page_mock.call_count == 2


# ---------------------------------------------------------------------------
# Pagination safety tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("selector", "mock_name", "kwargs"),
    [
        (
            resolve_domain_selector,
            "list_iot_domains_page_record",
            {
                "iot_domain_display_name": "factory-domain",
                "compartment_id": COMPARTMENT_ID,
            },
        ),
        (
            resolve_twin_selector,
            "list_digital_twin_instances_page_record",
            {
                "digital_twin_instance_name": "pump-01",
                "iot_domain_id": DOMAIN_ID,
            },
        ),
    ],
)
def test_selector_stops_when_next_page_token_repeats(
    monkeypatch, selector, mock_name, kwargs
):
    if selector is resolve_domain_selector:
        first_page = _domain_page(
            [_domain("domain-1", "other-domain")],
            next_page="page-2",
        )
        repeated_page = _domain_page(
            [_domain("domain-2", "other-domain")],
            next_page="page-2",
        )
    else:
        first_page = _twin_page(
            [_twin("twin-1", "other-pump", DOMAIN_ID)],
            next_page="page-2",
        )
        repeated_page = _twin_page(
            [_twin("twin-2", "other-pump", DOMAIN_ID)],
            next_page="page-2",
        )

    page_mock = Mock(side_effect=[first_page, repeated_page])
    monkeypatch.setattr(resolvers, mock_name, page_mock)

    result = selector(**kwargs)

    assert result["ok"] is False
    assert page_mock.call_count == 2
