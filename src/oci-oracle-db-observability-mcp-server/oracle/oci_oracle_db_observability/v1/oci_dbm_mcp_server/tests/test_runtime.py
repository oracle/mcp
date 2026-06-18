"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import oci

from oracle.oci_oracle_db_observability.v1.oci_dbm_mcp_server import models, runtime, tools


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


def _managed_database_summary(suffix: str) -> oci.database_management.models.ManagedDatabaseSummary:
    return oci.database_management.models.ManagedDatabaseSummary(
        id=f"ocid1.manageddatabase.oc1..{suffix}",
        compartment_id="ocid1.compartment.oc1..example",
        name=f"DB{suffix}",
        database_type="EXTERNAL_SIDB",
        database_sub_type="NON_CDB",
        is_cluster=False,
        time_created=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _alert_log_summary(suffix: str) -> oci.database_management.models.AlertLogSummary:
    return oci.database_management.models.AlertLogSummary(
        message_level="CRITICAL",
        message_type="ERROR",
        message_content=f"alert {suffix}",
    )


def _sql_tuning_set_summary(suffix: str) -> oci.database_management.models.SqlTuningSetSummary:
    return oci.database_management.models.SqlTuningSetSummary(
        name=f"STS{suffix}",
        owner="SYS",
    )


def test_create_tool_converts_pydantic_model_to_sdk_model(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeDbManagementClient:
        def create_managed_database_group(self, **kwargs):
            captured.update(kwargs)
            return _Response(None)

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "DbManagementClient", lambda: FakeDbManagementClient())

    result = tools.create_managed_database_group(
        create_managed_database_group_details=models.CreateManagedDatabaseGroupDetails(
            name="GROUP1",
            compartment_id="ocid1.compartment.oc1..example",
        )
    )

    details = captured["create_managed_database_group_details"]
    assert result is None
    assert isinstance(details, oci.database_management.models.CreateManagedDatabaseGroupDetails)
    assert details.name == "GROUP1"
    assert details.compartment_id == "ocid1.compartment.oc1..example"


def test_create_job_accepts_polymorphic_dict_request(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeDbManagementClient:
        def create_job(self, **kwargs):
            captured.update(kwargs)
            return _Response(None)

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "DbManagementClient", lambda: FakeDbManagementClient())

    result = tools.create_job(
        create_job_details={
            "name": "JOB1",
            "compartmentId": "ocid1.compartment.oc1..example",
            "managedDatabaseId": "ocid1.manageddatabase.oc1..example",
            "scheduleType": "IMMEDIATE",
            "jobType": "SQL",
            "operationType": "EXECUTE_SQL",
            "sqlText": "select 1 from dual",
        }
    )

    details = captured["create_job_details"]
    assert result is None
    assert isinstance(details, oci.database_management.models.CreateSqlJobDetails)
    assert details.job_type == "SQL"
    assert details.operation_type == "EXECUTE_SQL"
    assert details.sql_text == "select 1 from dual"


def test_update_tablespace_converts_nested_polymorphic_secret_credential(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeDbManagementClient:
        def update_tablespace(self, **kwargs):
            captured.update(kwargs)
            return _Response(None)

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "DbManagementClient", lambda: FakeDbManagementClient())

    result = tools.update_tablespace(
        managed_database_id="ocid1.manageddatabase.oc1..example",
        tablespace_name="USERS",
        update_tablespace_details={
            "credentialDetails": {
                "tablespaceAdminCredentialType": "SECRET",
                "username": "SYS",
                "role": "SYSDBA",
                "passwordSecretId": "ocid1.vaultsecret.oc1..example",
            },
            "name": "USERS_NEW",
        },
    )

    details = captured["update_tablespace_details"]
    assert result is None
    assert isinstance(details, oci.database_management.models.UpdateTablespaceDetails)
    assert isinstance(
        details.credential_details,
        oci.database_management.models.TablespaceAdminSecretCredentialDetails,
    )
    assert details.credential_details.password_secret_id == "ocid1.vaultsecret.oc1..example"
    assert details.name == "USERS_NEW"


def test_diagnosability_tool_routes_to_diagnosability_client(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeDiagnosabilityClient:
        def list_alert_logs(self, **kwargs):
            captured.update(kwargs)
            return _Response(None)

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "DiagnosabilityClient", lambda: FakeDiagnosabilityClient())

    result = tools.list_alert_logs(
        managed_database_id="ocid1.manageddatabase.oc1..example",
        level_filter="CRITICAL",
        limit=10,
    )

    assert result is None
    assert captured["managed_database_id"] == "ocid1.manageddatabase.oc1..example"
    assert captured["level_filter"] == "CRITICAL"
    assert captured["limit"] == 10


def test_db_management_tool_auto_paginates_collection(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeDbManagementClient:
        def list_managed_databases(self, page=None, limit=None, **kwargs):
            calls.append({"page": page, "limit": limit, **kwargs})
            if page is None:
                return _Response(
                    oci.database_management.models.ManagedDatabaseCollection(
                        items=[_managed_database_summary("one")]
                    ),
                    next_page="page-2",
                )
            return _Response(
                oci.database_management.models.ManagedDatabaseCollection(
                    items=[_managed_database_summary("two")]
                )
            )

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "DbManagementClient", lambda: FakeDbManagementClient())

    result = tools.list_managed_databases(
        compartment_id="ocid1.compartment.oc1..example",
        limit=10,
    )

    assert [item["id"] for item in result["items"]] == [
        "ocid1.manageddatabase.oc1..one",
        "ocid1.manageddatabase.oc1..two",
    ]
    assert calls[0]["limit"] == 10
    assert calls[1]["page"] == "page-2"
    assert calls[1]["limit"] == 9


def test_diagnosability_tool_auto_paginates_header_fallback(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeDiagnosabilityClient:
        def list_alert_logs(self, page=None, limit=None, **kwargs):
            calls.append({"page": page, "limit": limit, **kwargs})
            if page is None:
                return _Response(
                    oci.database_management.models.AlertLogCollection(
                        managed_database_id="ocid1.manageddatabase.oc1..example",
                        items=[_alert_log_summary("one")],
                    ),
                    headers={"opc-next-page": "page-2"},
                )
            return _Response(
                oci.database_management.models.AlertLogCollection(
                    managed_database_id="ocid1.manageddatabase.oc1..example",
                    items=[_alert_log_summary("two")],
                )
            )

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "DiagnosabilityClient", lambda: FakeDiagnosabilityClient())

    result = tools.list_alert_logs(
        managed_database_id="ocid1.manageddatabase.oc1..example",
        limit=10,
    )

    assert [item["message_content"] for item in result["items"]] == ["alert one", "alert two"]
    assert calls[1]["page"] == "page-2"
    assert calls[1]["limit"] == 9




def test_sql_tuning_tool_routes_to_sql_tuning_client(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class FakeSqlTuningClient:
        def create_sql_tuning_set(self, **kwargs):
            captured.update(kwargs)
            return _Response(None)

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "SqlTuningClient", lambda: FakeSqlTuningClient())

    result = tools.create_sql_tuning_set(
        managed_database_id="ocid1.manageddatabase.oc1..example",
        create_sql_tuning_set_details=models.CreateSqlTuningSetDetails(name="STS1"),
    )

    details = captured["create_sql_tuning_set_details"]
    assert result is None
    assert captured["managed_database_id"] == "ocid1.manageddatabase.oc1..example"
    assert isinstance(details, oci.database_management.models.CreateSqlTuningSetDetails)
    assert details.name == "STS1"


def test_sql_tuning_list_tool_routes_and_paginates(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class FakeSqlTuningClient:
        def list_sql_tuning_sets(self, page=None, limit=None, **kwargs):
            calls.append({"page": page, "limit": limit, **kwargs})
            if page is None:
                return _Response(
                    oci.database_management.models.SqlTuningSetCollection(
                        managed_database_id="ocid1.manageddatabase.oc1..example",
                        items=[_sql_tuning_set_summary("1")],
                    ),
                    next_page="page-2",
                )
            return _Response(
                oci.database_management.models.SqlTuningSetCollection(
                    managed_database_id="ocid1.manageddatabase.oc1..example",
                    items=[_sql_tuning_set_summary("2")],
                )
            )

    monkeypatch.setitem(runtime.CLIENT_GETTERS, "SqlTuningClient", lambda: FakeSqlTuningClient())

    result = tools.list_sql_tuning_sets(
        managed_database_id="ocid1.manageddatabase.oc1..example",
        limit=10,
    )

    assert [item["name"] for item in result["items"]] == ["STS1", "STS2"]
    assert calls[0]["managed_database_id"] == "ocid1.manageddatabase.oc1..example"
    assert calls[1]["page"] == "page-2"
    assert calls[1]["limit"] == 9


def test_perfhub_client_route_is_absent() -> None:
    assert "PerfhubClient" not in runtime.CLIENT_GETTERS
