"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import oci
import pytest

from oracle.oci_oracle_db_observability.v1.oci_opsi_mcp_server import models, runtime, tools


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


def _database_insight_summary(suffix: str) -> oci.opsi.models.DatabaseInsightSummary:
    return oci.opsi.models.DatabaseInsightSummary(
        id=f"ocid1.opsidatabaseinsight.oc1..{suffix}",
        database_id=f"ocid1.database.oc1..{suffix}",
        entity_source="AUTONOMOUS_DATABASE",
    )


def _database_insight_response() -> _Response:
    return _Response(
        oci.opsi.models.DatabaseInsight(
            entity_source="AUTONOMOUS_DATABASE",
            id="ocid1.opsidatabaseinsight.oc1..example",
            compartment_id="ocid1.compartment.oc1..example",
            status="ENABLED",
            freeform_tags={},
            defined_tags={},
            time_created=datetime(2026, 1, 1, tzinfo=UTC),
            lifecycle_state="ACTIVE",
        )
    )


def _pe_comanaged_host_insight() -> oci.opsi.models.PeComanagedHostInsight:
    return oci.opsi.models.PeComanagedHostInsight(
        entity_source="PE_COMANAGED_HOST",
        id="ocid1.opsihostinsight.oc1..example",
        compartment_id="ocid1.compartment.oc1..example",
        host_name=None,
        freeform_tags={},
        defined_tags={},
        status="ENABLED",
        time_created=datetime(2026, 1, 1, tzinfo=UTC),
        lifecycle_state="ACTIVE",
        opsi_private_endpoint_id="ocid1.opsiprivateendpoint.oc1..example",
    )


def _pe_comanaged_host_insight_summary() -> oci.opsi.models.PeComanagedHostInsightSummary:
    return oci.opsi.models.PeComanagedHostInsightSummary(
        entity_source="PE_COMANAGED_HOST",
        id="ocid1.opsihostinsight.oc1..example",
        compartment_id="ocid1.compartment.oc1..example",
        host_name=None,
        opsi_private_endpoint_id="ocid1.opsiprivateendpoint.oc1..example",
    )


def test_create_tool_converts_pydantic_model_to_sdk_model(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeClient:
        def create_database_insight(self, **kwargs):
            captured.update(kwargs)
            return _database_insight_response()

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.create_database_insight(
        create_database_insight_details=models.CreateDatabaseInsightDetails(
            entity_source="EM_MANAGED_EXTERNAL_DATABASE",
            compartment_id="ocid1.compartment.oc1..example",
        )
    )

    assert isinstance(captured["create_database_insight_details"], oci.opsi.models.CreateDatabaseInsightDetails)
    assert captured["create_database_insight_details"].entity_source == "EM_MANAGED_EXTERNAL_DATABASE"
    assert result["id"] == "ocid1.opsidatabaseinsight.oc1..example"


def test_create_tool_accepts_polymorphic_dict_request(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeClient:
        def create_database_insight(self, **kwargs):
            captured.update(kwargs)
            return _database_insight_response()

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    tools.create_database_insight(
        create_database_insight_details={
            "entity_source": "EM_MANAGED_EXTERNAL_DATABASE",
            "compartment_id": "ocid1.compartment.oc1..example",
            "enterprise_manager_identifier": "em1",
            "enterprise_manager_bridge_id": "ocid1.opsienterprisemanagerbridge.oc1..example",
            "enterprise_manager_entity_identifier": "entity1",
        }
    )

    details = captured["create_database_insight_details"]
    assert isinstance(details, oci.opsi.models.CreateEmManagedExternalDatabaseInsightDetails)
    assert details.entity_source == "EM_MANAGED_EXTERNAL_DATABASE"
    assert details.enterprise_manager_identifier == "em1"
    assert details.enterprise_manager_bridge_id == "ocid1.opsienterprisemanagerbridge.oc1..example"
    assert details.enterprise_manager_entity_identifier == "entity1"


def test_create_tool_accepts_polymorphic_dict_request_with_camel_case_keys(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeClient:
        def create_database_insight(self, **kwargs):
            captured.update(kwargs)
            return _database_insight_response()

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    tools.create_database_insight(
        create_database_insight_details={
            "entitySource": "EM_MANAGED_EXTERNAL_DATABASE",
            "compartmentId": "ocid1.compartment.oc1..example",
            "enterpriseManagerIdentifier": "em1",
            "enterpriseManagerBridgeId": "ocid1.opsienterprisemanagerbridge.oc1..example",
            "enterpriseManagerEntityIdentifier": "entity1",
        }
    )

    details = captured["create_database_insight_details"]
    assert isinstance(details, oci.opsi.models.CreateEmManagedExternalDatabaseInsightDetails)
    assert details.compartment_id == "ocid1.compartment.oc1..example"
    assert details.enterprise_manager_identifier == "em1"


def test_polymorphic_dict_request_rejects_unknown_fields_before_sdk_call(monkeypatch) -> None:
    called = False

    class FakeClient:
        def create_database_insight(self, **kwargs):
            nonlocal called
            called = True
            return _database_insight_response()

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    with pytest.raises(ValueError, match="unsupported fields"):
        tools.create_database_insight(
            create_database_insight_details={
                "entity_source": "EM_MANAGED_EXTERNAL_DATABASE",
                "compartment_id": "ocid1.compartment.oc1..example",
                "enterprise_manager_identifier": "em1",
                "enterprise_manager_bridge_id": "ocid1.opsienterprisemanagerbridge.oc1..example",
                "enterprise_manager_entity_identifier": "entity1",
                "not_a_real_field": "bad",
            }
        )

    assert called is False


def test_polymorphic_dict_request_rejects_tag_fields_before_sdk_call(monkeypatch) -> None:
    called = False

    class FakeClient:
        def create_database_insight(self, **kwargs):
            nonlocal called
            called = True
            return _database_insight_response()

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    with pytest.raises(ValueError, match="forbidden request tag mutation fields"):
        tools.create_database_insight(
            create_database_insight_details={
                "entitySource": "EM_MANAGED_EXTERNAL_DATABASE",
                "compartmentId": "ocid1.compartment.oc1..example",
                "enterpriseManagerIdentifier": "em1",
                "enterpriseManagerBridgeId": "ocid1.opsienterprisemanagerbridge.oc1..example",
                "enterpriseManagerEntityIdentifier": "entity1",
                "freeformTags": {"owner": "opsi"},
            }
        )

    assert called is False


def test_get_host_insight_allows_null_host_name(monkeypatch) -> None:
    class FakeClient:
        def get_host_insight(self, **kwargs):
            return _Response(_pe_comanaged_host_insight())

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.get_host_insight(host_insight_id="ocid1.opsihostinsight.oc1..example")

    assert result["host_name"] is None
    assert result["id"] == "ocid1.opsihostinsight.oc1..example"


def test_list_host_insights_allows_null_host_name(monkeypatch) -> None:
    class FakeClient:
        def list_host_insights(self, **kwargs):
            return _Response(
                oci.opsi.models.HostInsightSummaryCollection(
                    items=[_pe_comanaged_host_insight_summary()]
                )
            )

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.list_host_insights(
        compartment_id="ocid1.compartment.oc1..example",
        limit=10,
    )

    assert result["items"][0]["host_name"] is None
    assert result["items"][0]["id"] == "ocid1.opsihostinsight.oc1..example"


def test_list_tool_auto_paginates_collection_with_next_page(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeClient:
        def list_database_insights(self, page=None, limit=None, **kwargs):
            calls.append({"page": page, "limit": limit, **kwargs})
            if page is None:
                return _Response(
                    oci.opsi.models.DatabaseInsightsCollection(
                        items=[_database_insight_summary("one")]
                    ),
                    next_page="page-2",
                )
            return _Response(
                oci.opsi.models.DatabaseInsightsCollection(
                    items=[_database_insight_summary("two")]
                )
            )

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.list_database_insights(
        compartment_id="ocid1.compartment.oc1..example",
        limit=10,
    )

    assert [item["id"] for item in result["items"]] == [
        "ocid1.opsidatabaseinsight.oc1..one",
        "ocid1.opsidatabaseinsight.oc1..two",
    ]
    assert calls[0]["page"] is None
    assert calls[0]["limit"] == 10
    assert calls[1]["page"] == "page-2"
    assert calls[1]["limit"] == 9


def test_list_tool_uses_opc_next_page_header_fallback(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeClient:
        def list_database_insights(self, page=None, limit=None, **kwargs):
            calls.append({"page": page, "limit": limit, **kwargs})
            if page is None:
                return _Response(
                    oci.opsi.models.DatabaseInsightsCollection(
                        items=[_database_insight_summary("one")]
                    ),
                    headers={"opc-next-page": "page-2"},
                )
            return _Response(
                oci.opsi.models.DatabaseInsightsCollection(
                    items=[_database_insight_summary("two")]
                )
            )

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.list_database_insights(compartment_id="ocid1.compartment.oc1..example")

    assert [item["id"] for item in result["items"]] == [
        "ocid1.opsidatabaseinsight.oc1..one",
        "ocid1.opsidatabaseinsight.oc1..two",
    ]
    assert calls[1]["page"] == "page-2"


def test_list_tool_limit_caps_total_items(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeClient:
        def list_database_insights(self, page=None, limit=None, **kwargs):
            calls.append({"page": page, "limit": limit, **kwargs})
            if page is None:
                return _Response(
                    oci.opsi.models.DatabaseInsightsCollection(
                        items=[
                            _database_insight_summary("one"),
                            _database_insight_summary("two"),
                        ]
                    ),
                    next_page="page-2",
                )
            return _Response(
                oci.opsi.models.DatabaseInsightsCollection(
                    items=[
                        _database_insight_summary("three"),
                        _database_insight_summary("four"),
                    ]
                )
            )

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.list_database_insights(
        compartment_id="ocid1.compartment.oc1..example",
        limit=3,
    )

    assert [item["id"] for item in result["items"]] == [
        "ocid1.opsidatabaseinsight.oc1..one",
        "ocid1.opsidatabaseinsight.oc1..two",
        "ocid1.opsidatabaseinsight.oc1..three",
    ]
    assert calls[1]["limit"] == 1


def test_non_paginated_get_operation_makes_one_sdk_call(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeClient:
        def get_database_insight(self, database_insight_id=None, **kwargs):
            calls.append({"database_insight_id": database_insight_id, **kwargs})
            return _Response(
                oci.opsi.models.DatabaseInsight(
                    entity_source="AUTONOMOUS_DATABASE",
                    id=database_insight_id,
                    compartment_id="ocid1.compartment.oc1..example",
                    status="ENABLED",
                    freeform_tags={},
                    defined_tags={},
                    time_created=datetime(2026, 1, 1, tzinfo=UTC),
                    lifecycle_state="ACTIVE",
                ),
                next_page="ignored",
            )

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.get_database_insight("ocid1.opsidatabaseinsight.oc1..example")

    assert result["id"] == "ocid1.opsidatabaseinsight.oc1..example"
    assert len(calls) == 1


def test_list_tool_passes_limit_and_filters(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeClient:
        def list_database_insights(self, **kwargs):
            captured.update(kwargs)
            return _Response(oci.opsi.models.DatabaseInsightsCollection(items=[]))

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.list_database_insights(
        compartment_id="ocid1.compartment.oc1..example",
        limit=25,
        status=["ENABLED"],
    )

    assert captured["limit"] == 25
    assert captured["status"] == ["ENABLED"]
    assert result == {"items": []}


def test_list_host_configurations_accepts_nullable_platform_and_cpu_fields(monkeypatch) -> None:
    class FakeClient:
        def list_host_configurations(self, **kwargs):
            return _Response(
                oci.opsi.models.HostConfigurationCollection(
                    items=[
                        oci.opsi.models.HostConfigurationSummary(
                            host_insight_id="ocid1.opsihostinsight.oc1..example",
                            entity_source="EM_MANAGED_EXTERNAL_HOST",
                            compartment_id="ocid1.compartment.oc1..example",
                            host_name="host.example.com",
                            platform_type=None,
                            platform_version=None,
                            platform_vendor=None,
                            total_cpus=4,
                            total_memory_in_gbs=16.0,
                            cpu_architecture=None,
                            cpu_cache_in_mbs=8.0,
                            cpu_vendor=None,
                            cpu_frequency_in_mhz=2400.0,
                            cpu_implementation=None,
                            cores_per_socket=2,
                            total_sockets=2,
                            threads_per_socket=2,
                            is_hyper_threading_enabled=True,
                            defined_tags={},
                            freeform_tags={},
                        )
                    ]
                )
            )

    monkeypatch.setattr(runtime, "get_opsi_client", lambda: FakeClient())

    result = tools.list_host_configurations(compartment_id="ocid1.compartment.oc1..example")

    assert result["items"][0]["platform_type"] is None
    assert result["items"][0]["platform_version"] is None
    assert result["items"][0]["platform_vendor"] is None
    assert result["items"][0]["cpu_architecture"] is None
    assert result["items"][0]["cpu_vendor"] is None
    assert result["items"][0]["cpu_implementation"] is None
