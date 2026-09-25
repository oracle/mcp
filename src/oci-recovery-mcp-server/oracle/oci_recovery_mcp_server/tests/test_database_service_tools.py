"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Database Service tools: databases, DB homes, DB systems, and their
compartment-subtree and error paths.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from _helpers import _response
import oracle.oci_recovery_mcp_server.models as models
from oracle.oci_recovery_mcp_server import auth
from oracle.oci_recovery_mcp_server import summarise_tools
from oracle.oci_recovery_mcp_server import recovery_tools
from oracle.oci_recovery_mcp_server import prompt_tools
from oracle.oci_recovery_mcp_server import database_tools
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import compartments


def test_database_tools_resolve_compartment_paths_and_enrich_backups(monkeypatch):
    """
    The Database-service tools discover DB Homes from a compartment, enrich each
    result from a follow-up lookup -- backup config and protection policy on
    databases, unique name and destination type on backups -- and follow the paging
    token across responses shaped as a bare list and as an items collection.
    """
    db_client = MagicMock()
    recovery_client = MagicMock()
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
        clients,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        compartments,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: compartment_id or "tenancy",
    )
    monkeypatch.setattr(
        compartments,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: ["home1"],
    )

    recovery_client.list_protected_databases.return_value = _response(
        SimpleNamespace(items=[{"databaseId": "db1", "protectionPolicyId": "policy1"}])
    )
    db_client.list_databases.return_value = _response(
        SimpleNamespace(items=[SimpleNamespace(id="db1", db_name="DB1")])
    )
    db_client.get_database.return_value = _response(
        {
            "id": "db1",
            "compartmentId": "compartment",
            "dbBackupConfig": {"isAutoBackupEnabled": True},
        }
    )

    databases = database_tools.list_databases(
        compartment_id="compartment",
        system_id="system1",
        limit=10,
        page="page",
        sort_by="DBNAME",
        sort_order="ASC",
        lifecycle_state="AVAILABLE",
        db_name="DB1",
        region="us-ashburn-1",
    )
    assert databases[0].id == "db1"
    assert databases[0].db_backup_config.is_auto_backup_enabled is True
    assert databases[0].protection_policy_id == "policy1"
    assert db_client.list_databases.call_args.kwargs["db_home_id"] == "home1"

    db_client.get_database.return_value = _response(
        {"id": "db1", "compartmentId": "compartment"}
    )
    recovery_client.list_protected_databases.return_value = _response(
        [{"databaseId": "db1", "protectionPolicyId": "policy2"}]
    )
    database = database_tools.get_database("db1", region="us-ashburn-1")
    assert database.id == "db1"
    assert database.protection_policy_id == "policy2"

    db_client.list_databases.return_value = _response(
        SimpleNamespace(
            items=[
                {
                    "id": "db1",
                    "dbUniqueName": "DB1_UNQ",
                    "dbBackupConfig": {"isAutoBackupEnabled": True},
                }
            ]
        )
    )
    db_client.list_backups.side_effect = [
        _response(
            SimpleNamespace(
                items=[
                    SimpleNamespace(
                        id="backup1",
                        database_id="db1",
                        backup_destination_type="DBRS",
                    )
                ]
            ),
            has_next_page=True,
            next_page="backup-page-2",
        ),
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "backup2",
                        "databaseId": "db1",
                        "databaseSizeInGbs": 11,
                    }
                ]
            )
        ),
    ]

    backups = recovery_tools.list_backups(
        compartment_id="compartment",
        lifecycle_state="ACTIVE",
        type="FULL",
        region="us-ashburn-1",
    )
    assert [backup["id"] for backup in backups] == ["backup1", "backup2"]
    assert backups[0]["db_unique_name"] == "DB1_UNQ"
    assert backups[1]["database-size-in-gbs"] == 11
    assert db_client.list_backups.call_args_list[1].kwargs["page"] == "backup-page-2"

    db_client.get_backup.return_value = _response(
        SimpleNamespace(
            id="backup1",
            database_id="db1",
            database_size_in_gbs=8,
            retention_period_in_days=30,
        )
    )
    db_client.get_database.return_value = _response(
        {
            "dbUniqueName": "DB1_UNQ",
            "dbBackupConfig": {
                "backupDestinationDetails": [{"type": "RECOVERY_SERVICE"}]
            },
        }
    )
    backup = recovery_tools.get_backup("backup1", region="us-ashburn-1")
    assert backup["database-size-in-gbs"] == 8
    assert backup["backup-destination-type"] == "DBRS"
    assert backup["db_unique_name"] == "DB1_UNQ"

    db_client.list_databases.return_value = _response(
        [
            {
                "id": "db1",
                "dbName": "DB1",
                "dbBackupConfig": {
                    "isAutoBackupEnabled": True,
                    "backupDestinationDetails": [
                        {"type": "RECOVERY_SERVICE", "id": "dest1"}
                    ],
                },
            },
            {"id": "db2", "dbName": "DB2"},
        ]
    )
    db_client.get_database.return_value = _response(
        {
            "id": "db2",
            "dbName": "DB2",
            "dbBackupConfig": {"isAutoBackupEnabled": False},
        }
    )
    db_client.list_backups.side_effect = None
    db_client.list_backups.return_value = _response(
        [SimpleNamespace(time_ended="2024-01-02T00:00:00Z")]
    )
    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="compartment",
        region="us-ashburn-1",
        include_last_backup_time=True,
        db_name="DB",
        limit_per_home=50,
        max_db_homes=1,
        max_total_databases=2,
    )
    assert summary.total_databases == 2
    assert summary.counts_by_destination_type == {"DBRS": 1}
    assert summary.unconfigured_count == 1
    assert [item.database_id for item in summary.items] == ["db1", "db2"]
    assert summary.items[0].last_backup_time.isoformat() == "2024-01-02T00:00:00+00:00"


def test_database_child_scope_tools_deduplicate_results(monkeypatch):
    """
    Every subtree-scoped Database-service tool de-duplicates by OCID, so a resource
    visible from two compartments is returned once. The destination summary is the
    exception: it still counts each sighting in its total, then de-duplicates the
    per-database items.
    """
    db_client = MagicMock()
    recovery_client = MagicMock()
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
        clients,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        compartments, "_resolve_compartment_id", lambda value, **_kwargs: value
    )
    monkeypatch.setattr(
        compartments,
        "_compartment_ids_for_tool",
        lambda compartment_id, fetch_for_child_compartment, request_id=None: [
            "compartment-a",
            "compartment-b",
        ],
    )
    monkeypatch.setattr(
        compartments,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: ["home1"],
    )
    recovery_client.list_protected_databases.return_value = _response([])

    db_client.list_databases.side_effect = [
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db1",
                        "dbName": "DB1",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    }
                ]
            )
        ),
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db1",
                        "dbName": "DB1 Duplicate",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    },
                    {
                        "id": "db2",
                        "dbName": "DB2",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    },
                ]
            )
        ),
    ]
    databases = database_tools.list_databases(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [database.id for database in databases] == ["db1", "db2"]

    db_client.reset_mock()
    db_client.list_databases.side_effect = [
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db1",
                        "dbUniqueName": "DB1_UNQ",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    }
                ]
            )
        ),
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "db2",
                        "dbUniqueName": "DB2_UNQ",
                        "dbBackupConfig": {"isAutoBackupEnabled": True},
                    }
                ]
            )
        ),
    ]
    db_client.list_backups.side_effect = [
        _response(SimpleNamespace(items=[{"id": "backup1", "databaseId": "db1"}])),
        _response(
            SimpleNamespace(
                items=[
                    {"id": "backup1", "databaseId": "db2"},
                    {"id": "backup2", "databaseId": "db2"},
                ]
            )
        ),
    ]
    backups = recovery_tools.list_backups(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [backup["id"] for backup in backups] == ["backup1", "backup2"]

    db_client.reset_mock()
    db_client.list_databases.side_effect = [
        _response(
            [
                {
                    "id": "db1",
                    "dbName": "DB1",
                    "dbBackupConfig": {
                        "isAutoBackupEnabled": True,
                        "backupDestinationDetails": [
                            {"type": "RECOVERY_SERVICE", "id": "dest1"}
                        ],
                    },
                }
            ]
        ),
        _response(
            [
                {
                    "id": "db1",
                    "dbName": "DB1 Duplicate",
                    "dbBackupConfig": {
                        "isAutoBackupEnabled": True,
                        "backupDestinationDetails": [
                            {"type": "RECOVERY_SERVICE", "id": "dest1"}
                        ],
                    },
                },
                {
                    "id": "db2",
                    "dbName": "DB2",
                    "dbBackupConfig": {"isAutoBackupEnabled": False},
                },
            ]
        ),
    ]
    summary = summarise_tools.summarize_protected_database_backup_destination(
        compartment_id="root",
        fetch_for_child_compartment=True,
        db_home_id="home1",
        include_last_backup_time=False,
    )
    assert [item.database_id for item in summary.items] == ["db1", "db2"]
    # The repeated database is dropped before anything counts it, so the total matches
    # the list beside it rather than the raw number of rows the scan fetched.
    assert summary.total_databases == 2

    db_client.reset_mock()
    db_client.list_db_homes.side_effect = [
        _response([SimpleNamespace(id="home1")]),
        _response([SimpleNamespace(id="home1"), SimpleNamespace(id="home2")]),
    ]
    homes = database_tools.list_db_homes(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [home.id for home in homes] == ["home1", "home2"]

    db_client.reset_mock()
    db_client.list_db_systems.side_effect = [
        _response([SimpleNamespace(id="system1")]),
        _response([SimpleNamespace(id="system1"), SimpleNamespace(id="system2")]),
    ]
    systems = database_tools.list_db_systems(
        compartment_id="root",
        fetch_for_child_compartment=True,
    )
    assert [system.id for system in systems] == ["system1", "system2"]


def test_database_home_and_system_tools_apply_pagination_and_defaults(monkeypatch):
    """
    The DB Home and DB System tools default to the tenancy when given no
    compartment, forward their filters, and walk every page.
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
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")
    monkeypatch.setattr(
        compartments,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: f"resolved-{compartment_id}",
    )

    db_client.list_db_homes.side_effect = [
        _response(
            SimpleNamespace(items=[SimpleNamespace(id="home1", display_name="Home 1")]),
            has_next_page=True,
            next_page="home-page-2",
        ),
        _response([SimpleNamespace(id="home2", display_name="Home 2")]),
    ]
    homes = database_tools.list_db_homes(
        compartment_id=None,
        db_system_id=None,
        limit=1,
        page="home-page-1",
        region="us-ashburn-1",
    )
    assert [home.id for home in homes] == ["home1", "home2"]
    assert (
        db_client.list_db_homes.call_args_list[0].kwargs["compartment_id"]
        == "resolved-tenancy"
    )
    assert db_client.list_db_homes.call_args_list[1].kwargs["page"] == "home-page-2"

    db_client.get_db_home.return_value = _response(
        SimpleNamespace(id="home1", display_name="Home 1")
    )
    assert database_tools.get_db_home("home1", region="us-ashburn-1").id == "home1"

    db_client.list_db_systems.side_effect = [
        _response(
            [SimpleNamespace(id="system1", display_name="System 1")],
            has_next_page=True,
            next_page="system-page-2",
        ),
        _response(SimpleNamespace(items=[SimpleNamespace(id="system2")])),
    ]
    systems = database_tools.list_db_systems(
        compartment_id="compartment",
        lifecycle_state="AVAILABLE",
        limit=1,
        page="system-page-1",
        region="us-ashburn-1",
    )
    assert [system.id for system in systems] == ["system1", "system2"]
    assert (
        db_client.list_db_systems.call_args_list[0].kwargs["lifecycle_state"]
        == "AVAILABLE"
    )
    assert db_client.list_db_systems.call_args_list[1].kwargs["page"] == "system-page-2"

    db_client.get_db_system.return_value = _response(
        SimpleNamespace(id="system1", display_name="System 1")
    )
    assert database_tools.get_db_system("system1", region="us-ashburn-1").id == "system1"


def test_database_list_branches_and_tool_error_paths(monkeypatch):
    """
    list_databases rejects a call with neither starting point, returns empty when a
    compartment has no DB Homes, and degrades rather than fails when enrichment is
    unavailable -- leaving the policy or backup config unset. Failures from the
    services themselves propagate out of every tool, and the guidance tools return
    their prompt text directly.
    """
    db_client = MagicMock()
    recovery_client = MagicMock()
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

    with pytest.raises(ValueError, match="Either db_home_id"):
        database_tools.list_databases()

    monkeypatch.setattr(
        compartments,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: [],
    )
    assert database_tools.list_databases(compartment_id="compartment") == []

    monkeypatch.setattr(
        compartments,
        "_fetch_db_home_ids_for_compartment",
        lambda compartment_id, region=None: ["home1"],
    )
    recovery_client.list_protected_databases.side_effect = RuntimeError(
        "recovery unavailable"
    )
    db_client.list_databases.return_value = _response(
        [
            {
                "id": "db1",
                "dbName": "DB1",
                "dbBackupConfig": {"isAutoBackupEnabled": True},
            }
        ]
    )
    databases = database_tools.list_databases(compartment_id="compartment")
    assert databases[0].protection_policy_id is None

    db_client.list_databases.return_value = _response([{"id": "db2", "dbName": "DB2"}])
    db_client.get_database.side_effect = RuntimeError("backup config unavailable")
    databases = database_tools.list_databases(compartment_id="compartment", db_home_id="home1")
    assert databases[0].id == "db2"
    assert databases[0].db_backup_config is None

    db_client.reset_mock()
    db_client.get_database.side_effect = RuntimeError("backup config unavailable")
    databases = database_tools.list_databases(db_home_id="home1")
    assert databases[0].id == "db2"
    assert db_client.list_databases.call_args.kwargs == {"db_home_id": "home1"}

    error_cases = [
        (
            recovery_tools.list_protection_policies,
            {"compartment_id": "compartment"},
            "list_protection_policies",
        ),
        (
            recovery_tools.get_protection_policy,
            {"protection_policy_id": "policy1"},
            "get_protection_policy",
        ),
        (
            recovery_tools.list_recovery_service_subnets,
            {"compartment_id": "compartment"},
            "list_recovery_service_subnets",
        ),
        (
            recovery_tools.get_recovery_service_subnet,
            {"recovery_service_subnet_id": "rss1"},
            "get_recovery_service_subnet",
        ),
    ]
    for tool, kwargs, method_name in error_cases:
        getattr(recovery_client, method_name).side_effect = RuntimeError(
            f"{method_name} failed"
        )
        with pytest.raises(RuntimeError, match=f"{method_name} failed"):
            tool(**kwargs)
        getattr(recovery_client, method_name).side_effect = None

    db_error_cases = [
        (database_tools.get_database, {"database_id": "db1"}, "get_database"),
        (recovery_tools.get_backup, {"backup_id": "backup1"}, "get_backup"),
        (database_tools.list_db_homes, {"compartment_id": "compartment"}, "list_db_homes"),
        (database_tools.get_db_home, {"db_home_id": "home1"}, "get_db_home"),
        (database_tools.list_db_systems, {"compartment_id": "compartment"}, "list_db_systems"),
        (database_tools.get_db_system, {"db_system_id": "system1"}, "get_db_system"),
    ]
    for tool, kwargs, method_name in db_error_cases:
        getattr(db_client, method_name).side_effect = RuntimeError(
            f"{method_name} failed"
        )
        with pytest.raises(RuntimeError, match=f"{method_name} failed"):
            tool(**kwargs)
        getattr(db_client, method_name).side_effect = None

    # Guidance tools return the prompt text directly so clients without prompt
    # support can call them as ordinary tools.
    assert (
        prompt_tools.oci_recovery_service_dashboard_prompt()
        == prompt_tools.OCI_RECOVERY_SERVICE_DASHBOARD_PROMPT
    )
    assert (
        prompt_tools.onboard_database_to_recovery_service()
        == prompt_tools.ONBOARD_DATABASE_TO_RECOVERY_SERVICE_PROMPT
    )
    assert (
        prompt_tools.diagnose_recovery_service_issue()
        == prompt_tools.DIAGNOSE_RECOVERY_SERVICE_ISSUE_PROMPT
    )


def test_policy_correlation_survives_an_unreadable_compartment(monkeypatch):
    """
    One compartment the caller cannot read does not strip the policy link from the
    rest of the subtree.

    Such a caller gets a 404 there. Discarding the whole correlation would strip
    the policy link off every database in every readable compartment too, which
    reads as "no protection policy" rather than "could not check".
    """
    recovery_client = MagicMock()
    database_client = MagicMock()

    def list_protected_databases(compartment_id=None, page=None):
        """Serve one protected database per compartment, refusing the denied one."""
        if compartment_id == "denied":
            raise RuntimeError("NotAuthorizedOrNotFound")
        return _response(
            SimpleNamespace(
                items=[{"databaseId": "db-in-" + compartment_id, "protectionPolicyId": "pol-" + compartment_id}]
            )
        )

    recovery_client.list_protected_databases.side_effect = list_protected_databases
    database_client.list_db_homes.return_value = _response([SimpleNamespace(id="home1")])
    database_client.list_databases.return_value = _response(
        [
            SimpleNamespace(id="db-in-readable", db_name="OPEN", lifecycle_state="AVAILABLE"),
            SimpleNamespace(id="db-in-denied", db_name="HIDDEN", lifecycle_state="AVAILABLE"),
        ]
    )

    monkeypatch.setattr(clients, "get_recovery_client", lambda *a, **k: recovery_client)
    monkeypatch.setattr(clients, "get_database_client", lambda *a, **k: database_client)
    monkeypatch.setattr(
        compartments, "_compartment_ids_for_tool", lambda cid, **k: ["readable", "denied"]
    )
    monkeypatch.setattr(compartments, "_resolve_compartment_id", lambda c, **k: c)

    databases = database_tools.list_databases(
        compartment_id="root", fetch_for_child_compartment=True
    )

    policies = {d.id: d.protection_policy_id for d in databases}
    # The readable compartment's correlation survives the other one's failure.
    assert policies.get("db-in-readable") == "pol-readable"
    # And the unreadable one is simply unlinked, not fabricated.
    assert policies.get("db-in-denied") is None
