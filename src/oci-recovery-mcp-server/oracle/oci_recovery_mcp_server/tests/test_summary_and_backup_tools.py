"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Summary tools and backup tools: health, redo status, space used, and the backup
destination summaries built from object-store listings.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from _helpers import _response
import oracle.oci_recovery_mcp_server.models as models
from oracle.oci_recovery_mcp_server import app
from oracle.oci_recovery_mcp_server import auth
from oracle.oci_recovery_mcp_server import summarise_tools
from oracle.oci_recovery_mcp_server import recovery_tools
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import compartments


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

    health = summarise_tools.summarize_protected_database_health(
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

    redo = summarise_tools.summarize_protected_database_redo_status(
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

    backup_space = summarise_tools.summarize_backup_space_used(
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

    health = summarise_tools.summarize_protected_database_health("compartment")
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

    redo = summarise_tools.summarize_protected_database_redo_status("compartment")
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
        summarise_tools.summarize_backup_space_used("compartment")


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
    backups = recovery_tools.list_backups(
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
        recovery_tools.list_backups(region="us-ashburn-1")

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
        backup = recovery_tools.get_backup(f"backup-{expected}", region="us-ashburn-1")
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
    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        db_home_id="home-explicit",
        include_last_backup_time=False,
    )
    assert summary.total_databases == 2
    assert summary.counts_by_destination_type == {"OBJECT_STORE": 1}
    assert summary.db_names_by_destination_type == {"OBJECT_STORE": ["Object DB"]}
    assert [item.database_id for item in summary.items] == ["db-object", "db-nfs"]
    assert db_client.list_databases.call_args_list[1].kwargs["page"] == "db-page-2"

    db_client.list_databases.side_effect = RuntimeError("list databases failed")
    with pytest.raises(RuntimeError, match="list databases failed"):
        summarise_tools.summarize_protected_database_backup_destination(
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

    monkeypatch.setattr(app, "_Deadline", _ExpiresAfterFirstItem)

    redo = summarise_tools.summarize_protected_database_redo_status(compartment_id="root")
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
    # The tenancy-wide totals are built separately from the per-compartment rows,
    # and were left unflagged: truncated=True above an aggregate claiming to be whole.
    assert redo.aggregated.partial is True

    health = summarise_tools.summarize_protected_database_health(compartment_id="root")
    assert health.truncated is True
    assert health.compartment_ids_scanned == ["c1"]
    assert health.per_compartment[0].partial is True
    assert health.aggregated.partial is True


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

    health = summarise_tools.summarize_protected_database_health(compartment_id="root")
    assert health.truncated is False
    assert health.compartment_ids_scanned == ["c1", "c2"]
    assert [c.partial for c in health.per_compartment] == [False, False]
    assert health.aggregated.partial is False


def _backup_destination_db(index: int) -> dict:
    """One AVAILABLE database row with auto-backup on, as list_databases returns it."""
    return {
        "id": f"db{index}",
        "dbName": f"DB{index}",
        "dbBackupConfig": {
            "isAutoBackupEnabled": True,
            "backupDestinationDetails": [{"destinationType": "OBJECT_STORE"}],
        },
    }


def test_backup_destination_scan_stops_at_max_total_databases(monkeypatch):
    """
    max_total_databases bounds the whole scan, not one DB Home's share of it.

    The cap was tested inside the pagination loop and broke only out of that, so the
    next DB Home resumed appending and the next compartment after it -- a cap of 2
    across three homes returned six. That is the opposite of what a caller sets a cap
    for: the tool fans out over a whole compartment subtree, and the cap is the only
    thing standing between a large tenancy and a very long call.
    """
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: [cid])
    monkeypatch.setattr(
        compartments,
        "_fetch_db_home_ids_for_compartment",
        lambda *_args, **_kwargs: ["home1", "home2", "home3"],
    )
    db_client = MagicMock()
    # Every home has two databases, so an unbounded scan would return six.
    db_client.list_databases.side_effect = lambda **kwargs: _response(
        [_backup_destination_db(1), _backup_destination_db(2)]
    )
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        include_last_backup_time=False,
        max_total_databases=2,
    )
    assert db_client.list_databases.call_count == 1  # stopped after the first home
    assert summary.total_databases == 2


def test_backup_destination_reports_which_databases_have_backups(monkeypatch):
    """
    has_backups_db_names names the databases a backup was actually returned for.

    The list was declared, sorted and returned but never appended to, so the field was
    an empty list on every response the tool has ever produced -- a caller reading it
    would conclude nothing was backed up. It is filled only when
    include_last_backup_time is set, since that is the flag that queries backups at all.
    """
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: [cid])
    monkeypatch.setattr(
        compartments, "_fetch_db_home_ids_for_compartment", lambda *_a, **_k: ["home1"]
    )
    db_client = MagicMock()
    db_client.list_databases.return_value = _response(
        [_backup_destination_db(1), _backup_destination_db(2)]
    )
    db_client.get_database.return_value = _response(_backup_destination_db(1))
    # db1 has a backup; db2 has none.
    db_client.list_backups.side_effect = lambda database_id, **_kwargs: _response(
        [SimpleNamespace(time_ended="2026-09-01T00:00:00Z")] if database_id == "db1" else []
    )
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        include_last_backup_time=True,
    )
    assert summary.has_backups_db_names == ["DB1"]


def test_backup_destination_counts_add_up_when_a_database_cannot_be_read(monkeypatch):
    """
    A database whose config cannot be read is left out of every count, total included.

    It used to be marked seen before the read, so a failed GET still counted toward
    total_databases while appearing in no list or per-type count beside it -- the
    same mismatch the de-dupe exists to prevent -- and a duplicate of it later in
    the scan was skipped rather than retried.
    """
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: [cid])
    monkeypatch.setattr(
        compartments, "_fetch_db_home_ids_for_compartment", lambda *_a, **_k: ["home1"]
    )
    # No backup config on the rows, so each one needs a GET.
    rows = [{"id": "db1", "dbName": "DB1"}, {"id": "db2", "dbName": "DB2"}, {"id": "db2", "dbName": "DB2"}]
    db_client = MagicMock()
    db_client.list_databases.return_value = _response(rows)
    calls = {"db2": 0}

    def _get_database(database_id, **_kwargs):
        """db1 reads fine; db2 fails on its first read and succeeds on the retry."""
        if database_id == "db2":
            calls["db2"] += 1
            if calls["db2"] == 1:
                raise RuntimeError("database lookup failed")
            return _response(_backup_destination_db(2))
        return _response(_backup_destination_db(1))

    db_client.get_database.side_effect = _get_database
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        include_last_backup_time=False,
    )
    assert calls["db2"] == 2  # the duplicate row was retried, not skipped
    assert [it.database_id for it in summary.items] == ["db1", "db2"]
    assert summary.total_databases == len(summary.items)
    assert (
        sum(summary.counts_by_destination_type.values()) + summary.unconfigured_count
        == summary.total_databases
    )

    # When the database never reads, it is absent everywhere rather than only from the lists.
    db_client.get_database.side_effect = lambda database_id, **_kwargs: (
        (_ for _ in ()).throw(RuntimeError("database lookup failed"))
        if database_id == "db2"
        else _response(_backup_destination_db(1))
    )
    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        include_last_backup_time=False,
    )
    assert [it.database_id for it in summary.items] == ["db1"]
    assert summary.total_databases == 1


def test_last_backup_time_compares_instants_not_their_text(monkeypatch):
    """
    The newest backup wins even when the SDK reports times in different shapes.

    The comparison was `str(t) > str(best)`, and the two shapes do not order against
    each other as text: str() renders a datetime with a space separator while an
    ISO-8601 string keeps its "T", and " " sorts below "T". So a datetime lost to any
    string regardless of when it happened. Here the datetime is the newer of the two,
    which the old comparison would have discarded.
    """
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: [cid])
    monkeypatch.setattr(
        compartments, "_fetch_db_home_ids_for_compartment", lambda *_a, **_k: ["home1"]
    )
    # Same calendar day, so the separator is what the text comparison ends up deciding
    # on: str(newer) is "2026-09-08 12:00:00+00:00" and " " < "T", so as plain text the
    # newer value sorts *below* the older one.
    newer = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
    older = "2026-09-08T00:00:00Z"
    db_client = MagicMock()
    db_client.list_databases.return_value = _response([_backup_destination_db(1)])
    db_client.get_database.return_value = _response(_backup_destination_db(1))
    db_client.list_backups.return_value = _response(
        [SimpleNamespace(time_ended=older), SimpleNamespace(time_ended=newer)]
    )
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        include_last_backup_time=True,
    )
    assert summary.items[0].last_backup_time == newer


def test_scan_skips_the_per_database_get_when_the_listing_already_has_the_config():
    """
    The per-database GET is made only when the list response omits the backup config.

    On a DB Home of any size that is the difference between one call and one call per
    database, and the list response usually carries the config already.
    """
    get_database = MagicMock()
    with_config = {
        "id": "db1",
        "dbBackupConfig": {"backupDestinationDetails": [{"destinationType": "DBRS"}]},
    }
    record, types, ids = summarise_tools._backup_destinations_for(
        with_config, get_database=get_database
    )
    assert types == ["DBRS"]
    get_database.assert_not_called()

    # Without it, the full record is fetched and read instead.
    get_database.return_value = _response(
        {"id": "db2", "dbBackupConfig": {"backupDestinationDetails": [{"type": "NFS"}]}}
    )
    record, types, ids = summarise_tools._backup_destinations_for(
        {"id": "db2"}, get_database=get_database
    )
    assert get_database.call_args.kwargs == {"database_id": "db2"}
    assert record["id"] == "db2"


def test_a_database_backed_up_to_both_services_is_reported_as_dbrs():
    """
    DBRS wins when a database has both destinations, and unrelated types are dropped.

    The tool answers "what protects this database", and the presence of Recovery
    Service is that answer whenever it is configured -- counting such a database under
    OBJECT_STORE as well would double it in counts_by_destination_type.
    """
    both = {
        "id": "db1",
        "dbBackupConfig": {
            "backupDestinationDetails": [
                {"destinationType": "OBJECT_STORE", "id": "dest-object"},
                {"destinationType": "DBRS", "id": "dest-dbrs"},
                {"destinationType": "NFS", "id": "dest-nfs"},
            ]
        },
    }
    _record, types, ids = summarise_tools._backup_destinations_for(
        both, get_database=MagicMock()
    )
    assert types == ["DBRS"]
    # Every id is still reported, including the one whose type was not counted.
    assert ids == ["dest-object", "dest-dbrs", "dest-nfs"]


def test_scan_stops_at_the_cap_across_compartments_homes_and_pages():
    """
    max_total_databases bounds the scan at every level, including mid-pagination.

    Each of the three loops can run past the cap on its own, and the page loop is the
    one the cap is tested in -- so this drives all three at once: two compartments,
    two homes each, and a home that pages.
    """
    db_client = MagicMock()
    db_client.list_databases.side_effect = lambda **_kwargs: _response(
        [{"id": "a"}, {"id": "b"}], has_next_page=True, next_page="next"
    )
    found = summarise_tools._scan_available_databases(
        db_client,
        {"comp1": ["home1", "home2"], "comp2": ["home3", "home4"]},
        max_total_databases=3,
    )
    assert len(found) == 3
    # Two rows per page, so the cap is reached on the second call and nothing follows.
    assert db_client.list_databases.call_count == 2


def test_scan_passes_the_per_home_filters_and_omits_the_ones_not_set():
    """
    Optional filters reach the SDK only when set.

    Passing db_name=None or limit=None through would not mean "no filter" to the
    Database API; it would be a filter on None.
    """
    db_client = MagicMock()
    db_client.list_databases.return_value = _response([{"id": "a"}])
    summarise_tools._scan_available_databases(db_client, {"comp1": ["home1"]})
    assert db_client.list_databases.call_args.kwargs == {
        "compartment_id": "comp1",
        "db_home_id": "home1",
        "lifecycle_state": "AVAILABLE",
    }

    db_client.list_databases.reset_mock()
    summarise_tools._scan_available_databases(
        db_client, {"comp1": ["home1", "home2"]}, db_name="DB1", limit_per_home=5, max_db_homes=1
    )
    assert db_client.list_databases.call_args.kwargs["db_name"] == "DB1"
    assert db_client.list_databases.call_args.kwargs["limit"] == 5
    assert db_client.list_databases.call_count == 1  # max_db_homes stopped the second home


class _ExpiresAfter:
    """A budget that lasts a fixed number of checks, then reports itself spent."""

    def __init__(self, checks: int):
        self._left = checks
        self.expired = False

    def reached(self) -> bool:
        """Spend one check; latch expired once the allowance runs out."""
        if self._left <= 0:
            self.expired = True
        self._left -= 1
        return self.expired


def test_backup_space_summary_stops_at_its_deadline_and_says_so(monkeypatch):
    """
    The backup-space scan stops at the deadline and reports what it actually covered.

    It reads one metric per protected database across every compartment in scope, the
    same unbounded fan-out the health and redo summaries were already budgeted for --
    this one had no budget at all. The response has to distinguish the compartments
    scanned from those in scope: a total covering half a tenancy, presented as a whole
    one, is worse than an answer that admits it is partial.
    """
    monkeypatch.setattr(
        compartments, "_resolve_compartment_id", lambda cid, **_k: cid
    )
    monkeypatch.setattr(
        compartments, "_compartment_ids_for_tool", lambda cid, **_k: ["c1", "c2", "c3"]
    )
    monkeypatch.setattr(app, "_Deadline", lambda *_a, **_k: _ExpiresAfter(1))
    client = MagicMock()
    client.list_protected_databases.return_value = _response([])
    monkeypatch.setattr(clients, "get_recovery_client", lambda *_a, **_k: client)

    out = summarise_tools.summarize_backup_space_used(compartment_id="c1")
    assert out["truncated"] is True
    assert out["compartmentIdsInScope"] == ["c1", "c2", "c3"]
    # Stopped before covering them all, and says which it did cover.
    assert len(out["compartmentIdsScanned"]) < 3


def test_backup_destination_summary_stops_at_its_deadline(monkeypatch):
    """
    The destination summary stops at the deadline, in the scan and in the per-DB pass.

    It is the heaviest of the four summaries -- a compartment/home/page walk, then up
    to two more calls for every database it finds -- and it had no budget either. The
    scanner takes it so the walk stops between requests rather than after all of them.
    """
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_k: ["c1"])
    monkeypatch.setattr(
        compartments, "_fetch_db_home_ids_for_compartment", lambda *_a, **_k: ["h1", "h2", "h3"]
    )
    monkeypatch.setattr(app, "_Deadline", lambda *_a, **_k: _ExpiresAfter(1))
    db_client = MagicMock()
    db_client.list_databases.return_value = _response([_backup_destination_db(1)])
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="c1", region="us-ashburn-1", include_last_backup_time=False
    )
    assert summary.truncated is True
    # It did not walk all three homes before noticing the budget was spent.
    assert db_client.list_databases.call_count < 3


def test_summary_deadlines_start_before_discovery(monkeypatch):
    """
    The budget starts when the tool does, so discovery is charged against it.

    It used to start only after compartment expansion and, for the destination
    summary, after one list_db_homes call per compartment in scope -- up to 200 calls
    in a row the deadline never saw. Here the budget is spent before discovery, so
    no DB Home lookup may be made and the result must say it is truncated.
    """
    order = []
    monkeypatch.setattr(
        compartments,
        "_compartment_ids_for_tool",
        lambda cid, **_k: order.append("expand") or ["c1", "c2", "c3"],
    )
    fetch_homes = MagicMock(return_value=["h1"])
    monkeypatch.setattr(compartments, "_fetch_db_home_ids_for_compartment", fetch_homes)
    monkeypatch.setattr(
        app, "_Deadline", lambda *_a, **_k: order.append("deadline") or _ExpiresAfter(0)
    )
    db_client = MagicMock()
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="c1", region="us-ashburn-1", include_last_backup_time=False
    )
    assert order == ["deadline", "expand"]
    fetch_homes.assert_not_called()
    db_client.list_databases.assert_not_called()
    assert summary.truncated is True

    recovery_client = MagicMock()
    monkeypatch.setattr(clients, "get_recovery_client", lambda *_a, **_k: recovery_client)
    monkeypatch.setattr(compartments, "_resolve_compartment_id", lambda cid, **_k: cid)
    for tool in (
        summarise_tools.summarize_protected_database_health,
        summarise_tools.summarize_protected_database_redo_status,
        summarise_tools.summarize_backup_space_used,
    ):
        order.clear()
        tool(compartment_id="c1")
        assert order == ["deadline", "expand"], tool.__name__


def test_backup_destination_retries_its_per_database_reads_within_a_bound(monkeypatch):
    """
    get_database and list_backups are called with a short, bounded retry strategy.

    Neither retries by default in the OCI SDK, so a single throttled or transient 5xx
    response dropped that database from the summary. The SDK's own default strategy
    is not a substitute: it retries for up to ten minutes, far past the tool deadline.
    """
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_k: [cid])
    monkeypatch.setattr(
        compartments, "_fetch_db_home_ids_for_compartment", lambda *_a, **_k: ["home1"]
    )
    db_client = MagicMock()
    db_client.list_databases.return_value = _response([{"id": "db1", "dbName": "DB1"}])
    db_client.get_database.return_value = _response(_backup_destination_db(1))
    db_client.list_backups.return_value = _response([])
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="c1", region="us-ashburn-1", include_last_backup_time=True
    )
    strategy = summarise_tools._PER_DATABASE_RETRY_STRATEGY
    assert db_client.get_database.call_args.kwargs["retry_strategy"] is strategy
    assert db_client.list_backups.call_args.kwargs["retry_strategy"] is strategy
    limits = {
        type(checker).__name__: checker for checker in strategy.checkers.checkers
    }
    assert limits["LimitBasedRetryChecker"].max_attempts == 3
    assert limits["TotalTimeExceededRetryChecker"].time_limit_seconds == 10


def test_the_scanner_stops_between_requests_not_after_all_of_them():
    """
    _scan_available_databases checks the budget before each call, not after the walk.

    Checking afterwards would make the deadline decorative: the cost being bounded is
    the round trips themselves, so a budget that only trims the result has already
    spent everything it was meant to save.
    """
    db_client = MagicMock()
    db_client.list_databases.return_value = _response([{"id": "a"}])
    found = summarise_tools._scan_available_databases(
        db_client,
        {"c1": ["h1", "h2"], "c2": ["h3", "h4"]},
        deadline=_ExpiresAfter(2),
    )
    assert db_client.list_databases.call_count <= 2
    assert len(found) <= 2
