"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Summary tools and backup tools: health, redo status, space used, and the backup
destination summaries built from object-store listings.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from _helpers import _raise, _response
import oracle.oci_recovery_mcp_server.models as models
from oracle.oci_recovery_mcp_server import auth
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import compartments
import oracle.oci_recovery_mcp_server.server as server


def test_summary_tools_fall_back_on_counts_and_metrics(monkeypatch):
    """
    Each summary tool reads its field from the list response first and falls back
    to a per-database GET, counting a database it cannot read as unknown rather
    than dropping it. Space used skips deleted databases, falls back to the summary
    metrics when the GET fails, and counts a database with no metrics as missing.
    """
    recovery_client = MagicMock()
    monkeypatch.setattr(
        clients,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        compartments,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")

    recovery_client.list_protected_databases.return_value = _response(
        [
            SimpleNamespace(id="pd1", health="PROTECTED"),
            SimpleNamespace(id="pd2"),
            SimpleNamespace(data=SimpleNamespace(id="pd3")),
            SimpleNamespace(display_name="missing id"),
        ]
    )
    recovery_client.get_protected_database.side_effect = [
        _response(SimpleNamespace(health="ALERT")),
        _response(SimpleNamespace()),
    ]

    health = server.summarize_protected_database_health(
        compartment_id=None, region="us-ashburn-1"
    )
    assert health.aggregated.model_dump(by_alias=True) == {
        "compartmentId": "tenancy",
        "region": "us-ashburn-1",
        "protected": 1,
        "warning": 0,
        "alert": 1,
        "unknown": 1,
        "total": 3,
        "partial": False,
    }
    assert [c.model_dump(by_alias=True) for c in health.per_compartment] == [
        {
            "compartmentId": "tenancy",
            "region": "us-ashburn-1",
            "protected": 1,
            "warning": 0,
            "alert": 1,
            "unknown": 1,
            "total": 3,
            "partial": False,
        }
    ]
    assert health.compartment_ids_scanned == ["tenancy"]
    assert health.truncated is False

    recovery_client.list_protected_databases.return_value = _response(
        [
            SimpleNamespace(id="pd1"),
            SimpleNamespace(id="pd2"),
            SimpleNamespace(id="pd3"),
            SimpleNamespace(display_name="missing id"),
        ]
    )
    recovery_client.get_protected_database.side_effect = [
        _response(SimpleNamespace(is_redo_logs_shipped=True)),
        _response(SimpleNamespace(is_redo_logs_shipped=False)),
        _response(SimpleNamespace(metrics=SimpleNamespace(is_redo_logs_enabled=True))),
    ]

    redo = server.summarize_protected_database_redo_status(
        compartment_id="compartment", region="us-ashburn-1"
    )
    # The fourth entry has no id, so its redo status cannot be read at all. It is
    # reported as unknown rather than dropped, which would have made a database
    # nobody could see look like one that simply is not counted. total counts the
    # databases in scope, so it includes that one; the scan ran to completion, so
    # nothing is flagged partial.
    assert redo.aggregated.model_dump(by_alias=True) == {
        "compartmentId": "compartment",
        "region": "us-ashburn-1",
        "enabled": 2,
        "disabled": 1,
        "unknown": 1,
        "total": 4,
        "partial": False,
    }
    assert redo.per_compartment[0].total == 4
    assert redo.per_compartment[0].unknown == 1

    recovery_client.list_protected_databases.return_value = _response(
        [
            SimpleNamespace(
                id="pd1",
                lifecycle_state="ACTIVE",
                metrics=SimpleNamespace(backup_space_used_in_gbs=2.5),
            ),
            SimpleNamespace(id="deleted", lifecycle_state="DELETED"),
            SimpleNamespace(id="pd2", lifecycle_state="DELETE_SCHEDULED"),
            SimpleNamespace(lifecycle_state="ACTIVE"),
            SimpleNamespace(id="pd3", lifecycle_state="ACTIVE"),
        ]
    )
    recovery_client.get_protected_database.side_effect = [
        RuntimeError("fall back to summary metrics"),
        _response(SimpleNamespace(metrics={"backupSpaceUsedInGbs": 3.5})),
        _response(SimpleNamespace(metrics={})),
    ]

    backup_space = server.summarize_backup_space_used(
        compartment_id="compartment", region="us-ashburn-1"
    )
    assert backup_space["aggregated"]["compartmentId"] == "compartment"
    assert backup_space["aggregated"]["totalDatabasesScanned"] == 3
    assert backup_space["aggregated"]["sumBackupSpaceUsedInGBs"] == 6.0
    assert backup_space["missingMetricsCount"] == 1


def test_summary_serialization_fallbacks_and_error_paths(monkeypatch):
    """
    An empty compartment still returns the full declared shape, so a client reads
    the same fields whether or not anything was found, while a failure from the
    service itself propagates instead of being reported as zero.
    """
    recovery_client = MagicMock()
    monkeypatch.setattr(
        clients,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        compartments,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )
    recovery_client.list_protected_databases.return_value = _response([])

    health = server.summarize_protected_database_health("compartment")
    assert isinstance(health, models.ProtectedDatabaseHealthSummary)
    assert health.aggregated.model_dump(by_alias=True) == {
        "compartmentId": "compartment",
        "region": None,
        "protected": 0,
        "warning": 0,
        "alert": 0,
        "unknown": 0,
        "total": 0,
        "partial": False,
    }

    redo = server.summarize_protected_database_redo_status("compartment")
    assert isinstance(redo, models.ProtectedDatabaseRedoSummary)
    assert redo.aggregated.model_dump(by_alias=True) == {
        "compartmentId": "compartment",
        "region": None,
        "enabled": 0,
        "disabled": 0,
        "unknown": 0,
        "total": 0,
        "partial": False,
    }

    recovery_client.list_protected_databases.side_effect = RuntimeError("service down")
    with pytest.raises(RuntimeError, match="service down"):
        server.summarize_backup_space_used("compartment")


def test_backup_tools_handle_manual_paging_errors_and_destination_variants(monkeypatch):
    """
    With aggregate_pages off, list_backups forwards the caller's limit and page and
    stops after one page, and a failed database lookup leaves the enrichment fields
    empty rather than failing the call. Calling it with neither database_id nor
    compartment_id is rejected, and get_backup reports the destination type for
    each variant.
    """
    db_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        clients,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(
        compartments,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )

    db_client.list_backups.return_value = _response(
        SimpleNamespace(
            items=[
                {
                    "id": "manual-backup",
                    "databaseId": "db1",
                    "retentionPeriodInYears": 2,
                }
            ]
        ),
        has_next_page=True,
        next_page="ignored-when-not-aggregating",
    )
    db_client.get_database.side_effect = RuntimeError("database lookup failed")
    backups = server.list_backups(
        database_id="db1",
        lifecycle_state="ACTIVE",
        type="FULL",
        limit=25,
        page="start",
        region="us-ashburn-1",
        aggregate_pages=False,
    )
    assert backups[0]["id"] == "manual-backup"
    assert backups[0]["retention-period-in-years"] == 2
    assert backups[0]["db_unique_name"] is None
    assert db_client.list_backups.call_args.kwargs == {
        "database_id": "db1",
        "lifecycle_state": "ACTIVE",
        "type": "FULL",
        "limit": 25,
        "page": "start",
    }

    with pytest.raises(ValueError, match="Provide database_id"):
        server.list_backups(region="us-ashburn-1")

    db_client.get_database.side_effect = None
    for destination_type, expected in (
        ("OBJECT_STORE", "OBJECT_STORE"),
        ("NFS", "NFS"),
    ):
        db_client.get_backup.return_value = _response(
            {"id": f"backup-{expected}", "databaseId": f"db-{expected}"}
        )
        db_client.get_database.return_value = _response(
            {
                "dbUniqueName": f"{expected}_UNQ",
                "backupDestinationDetails": [{"destinationType": destination_type}],
            }
        )
        backup = server.get_backup(f"backup-{expected}", region="us-ashburn-1")
        assert backup["backup-destination-type"] == expected
        assert backup["db_unique_name"] == f"{expected}_UNQ"


def test_backup_destination_summary_handles_object_store_paging_and_errors(monkeypatch):
    """
    The destination summary walks every database page, counts a database it cannot
    identify in the total but not in any group, reads the auto-backup flag from
    both the nested config and the top level, and propagates a listing failure.
    """
    db_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        clients,
        "get_database_client",
        lambda region=None, request_id=None: db_client,
    )
    monkeypatch.setattr(
        compartments,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )

    db_client.list_databases.side_effect = [
        _response(
            [
                {
                    "id": "db-object",
                    "dbName": "Object DB",
                    "dbBackupConfig": {
                        "isAutoBackupEnabled": True,
                        "backupDestinationDetails": [
                            {
                                "destinationType": "OBJECT_STORE",
                                "backupDestinationId": "dest-object",
                            }
                        ],
                    },
                }
            ],
            has_next_page=True,
            next_page="db-page-2",
        ),
        _response(
            [
                {
                    "id": "db-nfs",
                    "dbName": "NFS DB",
                    "autoBackupEnabled": True,
                    "backupDestinationDetails": [{"type": "NFS"}],
                },
                {"dbName": "Missing Id"},
            ]
        ),
    ]
    summary = server.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        db_home_id="home-explicit",
        include_last_backup_time=False,
    )
    assert summary.total_databases == 3
    assert summary.counts_by_destination_type == {"OBJECT_STORE": 1}
    assert summary.db_names_by_destination_type == {"OBJECT_STORE": ["Object DB"]}
    assert [item.database_id for item in summary.items] == ["db-object", "db-nfs"]
    assert db_client.list_databases.call_args_list[1].kwargs["page"] == "db-page-2"

    db_client.list_databases.side_effect = RuntimeError("list databases failed")
    with pytest.raises(RuntimeError, match="list databases failed"):
        server.summarize_protected_database_backup_destination(
            compartment_id="compartment",
            db_home_id="home-explicit",
        )


def test_summary_scans_stop_at_their_deadline_and_say_so(monkeypatch):
    """
    A scan that runs out of budget stops, reports only the compartments it
    finished, and marks itself truncated -- issuing no further per-database GETs.

    One request per protected database across every compartment in scope turns a
    single tool call into hundreds of sequential round trips on a large tenancy,
    long past the point where an MCP client has stopped waiting. Stopping and
    reporting partial counts beats never returning.
    """
    recovery_client = MagicMock()
    monkeypatch.setattr(
        clients, "get_recovery_client", lambda region=None, request_id=None: recovery_client
    )
    monkeypatch.setattr(
        compartments, "_resolve_compartment_id", lambda compartment_id, **_kwargs: compartment_id
    )
    monkeypatch.setattr(
        compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: ["c1", "c2", "c3"]
    )
    recovery_client.list_protected_databases.return_value = _response(
        [
            SimpleNamespace(id="pd1", health="PROTECTED"),
            SimpleNamespace(id="pd2", health="PROTECTED"),
        ]
    )
    recovery_client.get_protected_database.return_value = _response(
        SimpleNamespace(is_redo_logs_shipped=True, health="PROTECTED")
    )

    class _ExpiresAfterFirstItem:
        """Reports its budget as spent before the second item in one page."""

        def __init__(self, seconds=None):
            """Start unexpired, with no checks recorded."""
            self.expired = False
            self._checks = 0

        def reached(self):
            """Report the budget spent from the fourth check onward."""
            self._checks += 1
            # One check enters the first compartment, one enters its page loop,
            # and one admits the first item. The second item must not issue a GET.
            self.expired = self._checks > 3
            return self.expired

    monkeypatch.setattr(server, "_Deadline", _ExpiresAfterFirstItem)

    redo = server.summarize_protected_database_redo_status(compartment_id="root")
    assert redo.truncated is True
    assert redo.compartment_ids_scanned == ["c1"]
    assert len(redo.per_compartment) == 1
    assert recovery_client.get_protected_database.call_count == 1
    # c1 was entered but only half read: it holds two databases and only one was
    # fetched. Its counts stay in the report -- dropping them would hide the work
    # that was done -- but they are flagged, so a caller cannot mistake a
    # half-scanned compartment for one that really contains a single database.
    assert redo.per_compartment[0].partial is True
    assert redo.per_compartment[0].total == 1


def test_summary_scans_report_every_compartment_when_they_finish(monkeypatch):
    """
    A scan that completes within budget reports every compartment it was given and
    is not marked truncated.
    """
    recovery_client = MagicMock()
    monkeypatch.setattr(
        clients, "get_recovery_client", lambda region=None, request_id=None: recovery_client
    )
    monkeypatch.setattr(
        compartments, "_resolve_compartment_id", lambda compartment_id, **_kwargs: compartment_id
    )
    monkeypatch.setattr(
        compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: ["c1", "c2"]
    )
    recovery_client.list_protected_databases.return_value = _response(
        [SimpleNamespace(id="pd1", health="PROTECTED")]
    )
    recovery_client.get_protected_database.return_value = _response(
        SimpleNamespace(is_redo_logs_shipped=True, health="PROTECTED")
    )

    health = server.summarize_protected_database_health(compartment_id="root")
    assert health.truncated is False
    assert health.compartment_ids_scanned == ["c1", "c2"]
    assert [c.partial for c in health.per_compartment] == [False, False]
