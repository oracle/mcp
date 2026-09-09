"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Recovery Service resource tools: protected databases, protection policies, and
Recovery Service subnets.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from _helpers import _response
import oracle.oci_recovery_mcp_server.models as models
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import compartments
from oracle.oci_recovery_mcp_server import recovery_tools


def test_recovery_resource_tools_apply_filters_pagination_and_enrichment(monkeypatch):
    """
    Each Recovery Service resource tool forwards its filters under the SDK's own
    names, follows the paging token across responses shaped as a bare list and as
    an items collection, and enriches results -- protected databases with their
    metrics and expanded subnets, subnets with their full detail, falling back to
    the summary's own subnet id when the full lookup fails. Fields the model does
    not declare are dropped rather than passed through.
    """
    recovery_client = MagicMock()
    monkeypatch.setattr(
        models.oci.util,
        "to_dict",
        lambda obj: obj if isinstance(obj, dict) else getattr(obj, "__dict__", obj),
    )
    monkeypatch.setattr(
        clients,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        compartments,
        "_resolve_compartment_id",
        lambda compartment_id, **_kwargs: f"resolved-{compartment_id}",
    )

    recovery_client.list_protected_databases.side_effect = [
        _response(
            [
                SimpleNamespace(
                    id="pd1",
                    display_name="Protected 1",
                    lifecycle_state="ACTIVE",
                    recovery_service_subnets=[SimpleNamespace(id="rss1")],
                )
            ],
            has_next_page=True,
            next_page="page-2",
        ),
        _response(
            SimpleNamespace(
                items=[
                    SimpleNamespace(
                        id="pd2",
                        display_name="Protected 2",
                        lifecycle_state="ACTIVE",
                    )
                ]
            )
        ),
    ]
    recovery_client.get_recovery_service_subnet.return_value = _response(
        SimpleNamespace(
            id="rss1",
            display_name="Subnet 1",
            compartment_id="compartment",
            vcn_id="vcn",
            subnet_id="subnet",
            lifecycle_details="drop-me",
        )
    )
    recovery_client.get_protected_database.side_effect = [
        _response(
            SimpleNamespace(
                metrics=SimpleNamespace(
                    backup_space_used_in_gbs=9.5,
                    database_size_in_gbs=42,
                    is_redo_logs_enabled=True,
                )
            )
        ),
        _response(SimpleNamespace(metrics={"backupSpaceUsedInGbs": 2.5})),
    ]

    protected_databases = recovery_tools.list_protected_databases(
        compartment_id="compartment",
        lifecycle_state="ACTIVE",
        display_name="Protected 1",
        id="pd1",
        protection_policy_id="policy1",
        recovery_service_subnet_id="rss1",
        limit=1,
        page="page-1",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="opc",
        region="us-ashburn-1",
    )

    assert [item["id"] for item in protected_databases] == ["pd1", "pd2"]
    assert protected_databases[0]["recovery_service_subnets"][0]["vcn_id"] == "vcn"
    assert (
        "lifecycle_details" not in protected_databases[0]["recovery_service_subnets"][0]
    )
    assert protected_databases[0]["metrics"]["backup-space-used-in-gbs"] == 9.5
    assert recovery_client.list_protected_databases.call_args_list[0].kwargs == {
        "compartment_id": "resolved-compartment",
        "page": "page-1",
        "lifecycle_state": "ACTIVE",
        "display_name": "Protected 1",
        "id": "pd1",
        "protection_policy_id": "policy1",
        "recovery_service_subnet_id": "rss1",
        "limit": 1,
        "sort_order": "ASC",
        "sort_by": "displayName",
        "opc_request_id": "opc",
    }
    assert (
        recovery_client.list_protected_databases.call_args_list[1].kwargs["page"]
        == "page-2"
    )

    recovery_client.get_protected_database.side_effect = None
    recovery_client.get_protected_database.return_value = _response(
        SimpleNamespace(
            id="pd3",
            display_name="Protected 3",
            change_rate=1.2,
            compression_ratio=3.4,
            recovery_service_subnets=[SimpleNamespace(id="rss2")],
            metrics=SimpleNamespace(
                backup_space_used_in_gbs=7,
                database_size_in_gbs=70,
                is_redo_logs_enabled=False,
            ),
        )
    )
    recovery_client.get_recovery_service_subnet.return_value = _response(
        SimpleNamespace(
            id="rss2",
            display_name="Subnet 2",
            compartment_id="compartment",
            vcn_id="vcn2",
            subnet_id="subnet2",
            freeform_tags={"drop": "me"},
        )
    )

    protected_database = recovery_tools.get_protected_database(
        "pd3", opc_request_id="opc", region="us-ashburn-1"
    )
    assert protected_database["id"] == "pd3"
    assert "change_rate" not in protected_database
    assert protected_database["recovery_service_subnets"][0]["subnet_id"] == "subnet2"
    assert "freeform_tags" not in protected_database["recovery_service_subnets"][0]
    assert protected_database["metrics"]["db-size-in-gbs"] == 70

    recovery_client.list_protection_policies.side_effect = [
        _response(
            [SimpleNamespace(id="policy1", display_name="Policy 1")],
            has_next_page=True,
            next_page="next-policy",
        ),
        _response(SimpleNamespace(items=[SimpleNamespace(id="policy2")])),
    ]
    policies = recovery_tools.list_protection_policies(
        "compartment",
        lifecycle_state="ACTIVE",
        display_name="Policy 1",
        id="policy1",
        limit=5,
        page="first",
        sort_order="DESC",
        sort_by="timeCreated",
        opc_request_id="opc",
        region="us-ashburn-1",
    )
    assert [policy.id for policy in policies] == ["policy1", "policy2"]
    assert (
        recovery_client.list_protection_policies.call_args_list[0].kwargs["limit"] == 5
    )

    recovery_client.get_protection_policy.return_value = _response(
        SimpleNamespace(id="policy1", display_name="Policy 1")
    )
    assert recovery_tools.get_protection_policy("policy1", opc_request_id="opc").id == "policy1"

    recovery_client.list_recovery_service_subnets.return_value = _response(
        [
            SimpleNamespace(id="rss-list-1", display_name="RSS 1"),
            SimpleNamespace(
                id="rss-list-2", display_name="RSS 2", subnet_id="subnet-fallback"
            ),
        ]
    )
    recovery_client.get_recovery_service_subnet.side_effect = [
        _response(
            SimpleNamespace(
                id="rss-list-1",
                display_name="RSS 1",
                subnets=["subnet-full"],
            )
        ),
        RuntimeError("full subnet lookup failed"),
    ]
    subnets = recovery_tools.list_recovery_service_subnets(
        "compartment",
        lifecycle_state="ACTIVE",
        display_name="RSS 1",
        id="rss-list-1",
        vcn_id="vcn",
        limit=2,
        page="page",
        sort_order="ASC",
        sort_by="displayName",
        opc_request_id="opc",
        region="us-ashburn-1",
    )
    assert subnets[0].subnets == ["subnet-full"]
    assert subnets[1].subnets == ["subnet-fallback"]

    recovery_client.get_recovery_service_subnet.side_effect = None
    recovery_client.get_recovery_service_subnet.return_value = _response(
        SimpleNamespace(id="rss-single", subnet_id="subnet-single")
    )
    assert recovery_tools.get_recovery_service_subnet("rss-single").subnets == ["subnet-single"]


def test_protected_database_tools_fall_back_on_serialization_errors(monkeypatch):
    """
    When a mapped model cannot be serialized by any route, the tools fall back to
    reading its attributes directly: an unmappable item is skipped, a failed subnet
    or metrics lookup leaves those fields empty, and the metrics block still comes
    back with every declared key rather than missing.
    """
    recovery_client = MagicMock()
    monkeypatch.setattr(
        clients,
        "get_recovery_client",
        lambda region=None, request_id=None: recovery_client,
    )
    monkeypatch.setattr(
        compartments, "_resolve_compartment_id", lambda value, **_kwargs: value
    )

    class FallbackSummary:
        """A mapped summary that refuses every serialization route."""

        def __init__(self):
            """Expose the attributes the fallback path has to read directly."""
            self.id = "pd-fallback"
            self.recovery_service_subnets = [SimpleNamespace(id="rss-fallback")]

        def model_dump(self, **_kwargs):
            """Fail, forcing the caller past the pydantic route."""
            raise RuntimeError("model dump unavailable")

        def dict(self, **_kwargs):
            """Fail, forcing the caller past the legacy pydantic route."""
            raise RuntimeError("dict unavailable")

    monkeypatch.setattr(
        recovery_tools,
        "map_protected_database_summary",
        MagicMock(side_effect=[None, FallbackSummary()]),
    )
    recovery_client.list_protected_databases.return_value = _response(
        [object(), object()]
    )
    recovery_client.get_recovery_service_subnet.side_effect = RuntimeError(
        "subnet lookup failed"
    )
    recovery_client.get_protected_database.side_effect = RuntimeError(
        "metrics lookup failed"
    )

    protected_databases = recovery_tools.list_protected_databases("compartment")
    assert protected_databases == [
        {
            "id": "pd-fallback",
            "policyLockedDateTime": None,
            "recovery_service_subnets": [{"id": "rss-fallback"}],
        }
    ]

    class BadMetrics:
        """A metrics object that refuses every serialization route."""

        def model_dump(self, **_kwargs):
            """Fail, forcing the caller past the pydantic route."""
            raise RuntimeError("model dump unavailable")

        def dict(self, **_kwargs):
            """Fail, forcing the caller past the legacy pydantic route."""
            raise RuntimeError("dict unavailable")

    class FallbackProtectedDatabase:
        """A mapped protected database that refuses every serialization route."""

        def __init__(self):
            """Expose the attributes the fallback path has to read directly."""
            self.id = "pd1"
            self.change_rate = 2.0
            self.compression_ratio = 3.0
            self.recovery_service_subnets = [SimpleNamespace(id="rss-partial")]
            self.metrics = BadMetrics()

        def model_dump(self, **_kwargs):
            """Fail, forcing the caller past the pydantic route."""
            raise RuntimeError("model dump unavailable")

        def dict(self, **_kwargs):
            """Fail, forcing the caller past the legacy pydantic route."""
            raise RuntimeError("dict unavailable")

    monkeypatch.setattr(
        recovery_tools,
        "map_protected_database",
        MagicMock(return_value=FallbackProtectedDatabase()),
    )
    recovery_client.get_protected_database.side_effect = None
    recovery_client.get_protected_database.return_value = _response(object())
    recovery_client.get_recovery_service_subnet.side_effect = RuntimeError(
        "subnet lookup failed"
    )

    protected_database = recovery_tools.get_protected_database("pd1")
    assert protected_database["id"] == "pd1"
    assert "change_rate" not in protected_database
    assert "compression_ratio" not in protected_database
    assert protected_database["recovery_service_subnets"] == [{"id": "rss-partial"}]
    assert protected_database["metrics"] == {
        "backup-space-estimate-in-gbs": None,
        "backup-space-used-in-gbs": None,
        "current-retention-period-in-seconds": None,
        "db-size-in-gbs": None,
        "is-redo-logs-enabled": None,
        "minimum-recovery-needed-in-days": None,
        "retention-period-in-days": None,
        "unprotected-window-in-seconds": None,
    }


def _strict_client(method_name, allowed, items):
    """
    Build a client whose listing method rejects any kwarg outside ``allowed``.

    The OCI SDK rejects unknown keyword arguments outright, so a parameter a tool
    advertises but cannot forward is a hard failure at call time, not a silently
    ignored filter. These stand-ins mirror that behaviour.
    """
    client = MagicMock()

    def call(compartment_id=None, **kwargs):
        """Record the kwargs and return the canned items, refusing anything unexpected."""
        extra = [k for k in kwargs if k not in allowed]
        if extra:
            raise ValueError(f"{method_name} got unknown kwargs: {extra!r}")
        call.seen = dict(kwargs)
        return SimpleNamespace(
            data=SimpleNamespace(items=items), has_next_page=False, next_page=None
        )

    call.seen = {}
    getattr(client, method_name).side_effect = call
    return client, call


def test_list_restore_applies_status_and_sort_without_forwarding_them(monkeypatch):
    """
    Status and sort are applied to the results, never forwarded.

    oci.work_requests.WorkRequestClient.list_work_requests accepts only
    resource_id, limit, page and opc_request_id, so sending it sort_by, sort_order
    or status would fail the call. Non-restore work requests stay excluded whatever
    the filters, work requests with no timestamp sort last, and an unknown sort
    field or order is rejected up front.
    """
    items = [
        SimpleNamespace(
            id="wr1",
            operation_type="Restore Database",
            status="SUCCEEDED",
            time_accepted="2026-01-01T00:00:00Z",
        ),
        SimpleNamespace(
            id="wr2",
            operation_type="Restore Database",
            status="FAILED",
            time_accepted="2026-03-01T00:00:00Z",
        ),
        SimpleNamespace(
            id="wr3",
            operation_type="Create Protected Database",
            status="SUCCEEDED",
            time_accepted="2026-02-01T00:00:00Z",
        ),
        SimpleNamespace(
            id="wr4",
            operation_type="Restore Database",
            status="ACCEPTED",
            time_accepted=None,
        ),
    ]
    client, call = _strict_client(
        "list_work_requests", {"resource_id", "limit", "page", "opc_request_id"}, items
    )
    monkeypatch.setattr(clients, "get_work_request_client", lambda *a, **k: client)
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **k: [cid])
    compartment = "ocid1.compartment.oc1..c"

    newest_first = recovery_tools.list_restore(
        compartment_id=compartment, sort_by="timeAccepted", sort_order="DESC"
    )
    assert [w.id for w in newest_first] == ["wr2", "wr1", "wr4"]
    assert "sort_by" not in call.seen and "sort_order" not in call.seen

    oldest_first = recovery_tools.list_restore(
        compartment_id=compartment, sort_by="timeAccepted", sort_order="ASC"
    )
    assert [w.id for w in oldest_first] == ["wr1", "wr2", "wr4"]

    failed = recovery_tools.list_restore(compartment_id=compartment, status="failed")
    assert [w.id for w in failed] == ["wr2"]
    assert "status" not in call.seen

    # Non-restore work requests stay excluded regardless of the filters.
    assert [w.id for w in recovery_tools.list_restore(compartment_id=compartment)] == [
        "wr1",
        "wr2",
        "wr4",
    ]

    for field, value in (("sort_by", "bogus"), ("sort_order", "sideways")):
        with pytest.raises(ValueError, match=field):
            recovery_tools.list_restore(compartment_id=compartment, **{field: value})


def test_list_protection_policies_sends_the_id_filter_under_its_sdk_name(monkeypatch):
    """
    The tool's ``id`` filter reaches the SDK as ``protection_policy_id``, the name
    the call actually accepts.
    """
    client, call = _strict_client(
        "list_protection_policies",
        {
            "lifecycle_state",
            "display_name",
            "protection_policy_id",
            "owner",
            "limit",
            "page",
            "sort_order",
            "sort_by",
            "opc_request_id",
        },
        [SimpleNamespace(id="policy1", display_name="Policy 1")],
    )
    monkeypatch.setattr(clients, "get_recovery_client", lambda *a, **k: client)
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **k: [cid])

    policies = recovery_tools.list_protection_policies(
        compartment_id="ocid1.compartment.oc1..c", id="ocid1.protectionpolicy.oc1..p"
    )
    assert [p.id for p in policies] == ["policy1"]
    assert call.seen["protection_policy_id"] == "ocid1.protectionpolicy.oc1..p"
    assert "id" not in call.seen
