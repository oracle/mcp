"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from typing import Any

import oci

from oracle.oci_oracle_db_observability.v1.oci_dbm_mcp_server import runtime, tools


class _Response:
    def __init__(
        self,
        data: Any,
        next_page: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.data = data
        self.next_page = next_page
        self.headers = headers or {}


def _oci_config(tenancy_id: str | None = "ocid1.tenancy.oc1..example") -> dict[str, str]:
    config = {"region": "us-phoenix-1"}
    if tenancy_id is not None:
        config["tenancy"] = tenancy_id
    return config


def _compartment(compartment_id: str = "ocid1.compartment.oc1..example") -> oci.identity.models.Compartment:
    return oci.identity.models.Compartment(
        id=compartment_id,
        compartment_id="ocid1.tenancy.oc1..example",
        name="Database",
        description="Database compartment",
        lifecycle_state="ACTIVE",
    )


def test_get_compartment_calls_identity_client(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeIdentityClient:
        def get_compartment(self, **kwargs):
            captured.update(kwargs)
            return _Response(_compartment())

    monkeypatch.setattr(runtime, "get_identity_client", lambda: FakeIdentityClient())

    result = tools.get_compartment("ocid1.compartment.oc1..example")

    assert captured["compartment_id"] == "ocid1.compartment.oc1..example"
    assert result["id"] == "ocid1.compartment.oc1..example"
    assert result["name"] == "Database"


def test_list_compartments_defaults_to_tenancy_and_maps_collection(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(tools, "get_oci_config", lambda project, version: _oci_config())

    class FakeIdentityClient:
        def list_compartments(self, **kwargs):
            captured.update(kwargs)
            return _Response([_compartment()])

    monkeypatch.setattr(runtime, "get_identity_client", lambda: FakeIdentityClient())

    result = tools.list_compartments(name="Database")

    assert captured["compartment_id"] == "ocid1.tenancy.oc1..example"
    assert captured["compartment_id_in_subtree"] is True
    assert captured["access_level"] == "ACCESSIBLE"
    assert captured["name"] == "Database"
    assert captured["limit"] == 50
    assert result["count"] == 1
    assert result["items"][0]["id"] == "ocid1.compartment.oc1..example"


def test_list_compartments_auto_paginates(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(tools, "get_oci_config", lambda project, version: _oci_config())

    class FakeIdentityClient:
        def list_compartments(self, page=None, limit=None, **kwargs):
            calls.append({"page": page, "limit": limit, **kwargs})
            if page is None:
                return _Response(
                    [_compartment("ocid1.compartment.oc1..one")],
                    next_page="page-2",
                )
            return _Response([_compartment("ocid1.compartment.oc1..two")])

    monkeypatch.setattr(runtime, "get_identity_client", lambda: FakeIdentityClient())

    result = tools.list_compartments(limit=10)

    assert result["count"] == 2
    assert [item["id"] for item in result["items"]] == [
        "ocid1.compartment.oc1..one",
        "ocid1.compartment.oc1..two",
    ]
    assert calls[0]["limit"] == 10
    assert calls[1]["page"] == "page-2"
    assert calls[1]["limit"] == 9


def test_list_compartments_allows_explicit_root_without_tenancy_config(monkeypatch) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setattr(tools, "get_oci_config", lambda project, version: _oci_config(tenancy_id=None))

    class FakeIdentityClient:
        def list_compartments(self, **kwargs):
            captured.update(kwargs)
            return _Response([_compartment()])

    monkeypatch.setattr(runtime, "get_identity_client", lambda: FakeIdentityClient())

    result = tools.list_compartments(
        root_compartment_id="ocid1.compartment.oc1..example",
        include_subtree=True,
    )

    assert captured["compartment_id"] == "ocid1.compartment.oc1..example"
    assert captured["compartment_id_in_subtree"] is True
    assert result["count"] == 1
