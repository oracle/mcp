"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Compartment resolution and the compartment-subtree scope: the child compartment
cache, its crawl, and the tools that aggregate across it.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from _helpers import _paged, _raise, _response
import oracle.oci_recovery_mcp_server.models as models
from oracle.oci_recovery_mcp_server import auth
from oracle.oci_recovery_mcp_server import recovery_tools
from oracle.oci_recovery_mcp_server import app
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import compartments
from oracle.oci_recovery_mcp_server import telemetry


def test_compartment_and_database_home_helpers_resolve_ids(monkeypatch):
    """
    Compartment listing walks every page and appends the root tenancy, name lookup
    is case-insensitive, and _resolve_compartment_id passes OCIDs through while
    resolving names -- raising a distinct error for missing, blank, unknown and
    unresolvable input. DB Home discovery reads ids from both object and dict
    items, skips entries without one, and returns empty rather than raising when
    the Database service is unavailable.
    """
    accessible = [
        SimpleNamespace(id="compartment-a", name="Dev"),
        SimpleNamespace(id="compartment-b", name="Prod"),
    ]
    root = SimpleNamespace(id="tenancy", name="Root")
    identity_client = MagicMock()
    identity_client.list_compartments.side_effect = [
        _response([accessible[0]], has_next_page=True, next_page="next"),
        _response([accessible[1]]),
    ]
    identity_client.get_compartment.return_value = _response(root)
    monkeypatch.setattr(clients, "get_identity_client", lambda: identity_client)
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")

    assert compartments.list_all_compartments_internal(True, limit=25) == [
        accessible[0],
        root,
    ]
    identity_client.list_compartments.reset_mock()
    identity_client.list_compartments.side_effect = [
        _response([accessible[0]], has_next_page=True, next_page="next"),
        _response([accessible[1]]),
    ]
    all_compartments = compartments.list_all_compartments_internal(False, limit=25)
    assert [compartment.id for compartment in all_compartments] == [
        "compartment-a",
        "tenancy",
        "compartment-b",
    ]

    monkeypatch.setattr(
        compartments,
        "list_all_compartments_internal",
        lambda _only_one_page: accessible + [root],
    )
    assert compartments.get_compartment_by_name("prod").id == "compartment-b"
    assert compartments.get_compartment_by_name("missing") is None
    assert compartments._looks_like_ocid(" ocid1.compartment.oc1..abc ")
    assert not compartments._looks_like_ocid("Dev")
    assert compartments._resolve_compartment_id("ocid1.compartment.oc1..abc") == (
        "ocid1.compartment.oc1..abc"
    )
    assert compartments._resolve_compartment_id("Dev") == "compartment-a"
    assert compartments._resolve_compartment_id(None, default_to_tenancy=True) == "tenancy"
    with pytest.raises(ValueError, match="required"):
        compartments._resolve_compartment_id(None)
    with pytest.raises(ValueError, match="cannot be empty"):
        compartments._resolve_compartment_id(" ")
    with pytest.raises(ValueError, match="not found"):
        compartments._resolve_compartment_id("Missing")
    monkeypatch.setattr(
        compartments, "get_compartment_by_name", lambda _name: SimpleNamespace(name="NoId")
    )
    with pytest.raises(ValueError, match="Unable to resolve"):
        compartments._resolve_compartment_id("NoId")

    db_client = MagicMock()
    db_client.list_db_homes.return_value = _response(
        SimpleNamespace(
            items=[
                SimpleNamespace(id="home1"),
                {"id": "home2"},
                SimpleNamespace(display_name="missing-id"),
            ]
        )
    )
    monkeypatch.setattr(clients, "get_database_client", lambda region=None: db_client)
    assert compartments._fetch_db_home_ids_for_compartment("compartment-a") == [
        "home1",
        "home2",
    ]
    db_client.list_db_homes.side_effect = RuntimeError("service unavailable")
    assert compartments._fetch_db_home_ids_for_compartment("compartment-a") == []


def test_child_compartment_helpers_use_cache_fast_path_and_fallback(monkeypatch):
    """
    The compartment list is de-duplicated, has the root appended, and is cached by
    identity so a second call reuses it. The children index skips compartments
    with no parent, subtree expansion returns the root alone when children are not
    requested, and falls back to crawling Identity page by page when the cache is
    empty. If expansion fails outright, the tool still scopes to the one resolved
    compartment rather than failing the call, but records the result as partial so
    the root alone is not presented as the whole subtree.
    """
    monkeypatch.setattr(app.time, "time", lambda: 100.0)
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")
    monkeypatch.setattr(
        compartments,
        "list_all_compartments_internal",
        lambda _only_one_page: [
            SimpleNamespace(id="child", compartment_id="tenancy"),
            SimpleNamespace(id="child", compartment_id="tenancy"),
            SimpleNamespace(name="missing id"),
        ],
    )
    identity_client = MagicMock()
    identity_client.get_compartment.return_value = _response(
        SimpleNamespace(id="tenancy", name="Root")
    )
    monkeypatch.setattr(
        clients, "get_identity_client", lambda request_id=None: identity_client
    )

    cached = compartments._list_all_compartments_cached(request_id="rid")
    assert [compartment.id for compartment in cached] == ["child", "tenancy"]
    assert compartments._list_all_compartments_cached(request_id="rid2") is cached

    tree = [
        SimpleNamespace(id="root", compartment_id="tenancy"),
        SimpleNamespace(id="child", compartment_id="root"),
        SimpleNamespace(id="grandchild", compartmentId="child"),
        SimpleNamespace(id="orphan"),
    ]
    assert compartments._build_children_index(tree) == {
        "tenancy": ["root"],
        "root": ["child"],
        "child": ["grandchild"],
    }
    monkeypatch.setattr(
        compartments,
        "_list_all_compartments_cached",
        lambda request_id=None: tree,
    )
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "child", "grandchild"], True)
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=False
    ) == (["root"], True)

    fallback_identity = MagicMock()
    fallback_identity.list_compartments.side_effect = [
        _response([SimpleNamespace(id="child")], has_next_page=True, next_page="p2"),
        _response([SimpleNamespace(id="sibling")]),
        _response([]),
        _response([]),
    ]
    monkeypatch.setattr(compartments, "_list_all_compartments_cached", lambda **_: [])
    monkeypatch.setattr(
        clients, "get_identity_client", lambda request_id=None: fallback_identity
    )
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "child", "sibling"], True)

    monkeypatch.setattr(
        compartments, "_resolve_compartment_id", lambda value, **_kwargs: f"resolved-{value}"
    )
    monkeypatch.setattr(
        compartments,
        "_expand_compartment_scope",
        MagicMock(side_effect=RuntimeError("identity unavailable")),
    )
    reasons_token = telemetry._MCP_PARTIAL_RESULT_CONTEXT.set([])
    try:
        assert compartments._compartment_ids_for_tool("Dev", fetch_for_child_compartment=True) == [
            "resolved-Dev"
        ]
        assert "Identity could not list it" in telemetry._MCP_PARTIAL_RESULT_CONTEXT.get()[0]
    finally:
        telemetry._MCP_PARTIAL_RESULT_CONTEXT.reset(reasons_token)
    # The root alone stands in for a subtree that was never read, so it is not
    # reported as complete.
    assert compartments._compartment_scope_for_tool(
        "Dev", fetch_for_child_compartment=True
    ) == (["resolved-Dev"], False)


def test_subtree_expansion_reports_when_the_cap_drops_compartments(monkeypatch):
    """
    A subtree larger than ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE is cut to the cap and
    reported incomplete, on both the cached path and the Identity crawl. A subtree
    of exactly the cap loses nothing and is reported complete.
    """
    tree = [SimpleNamespace(id=f"c{i}", compartment_id="root") for i in range(4)]
    monkeypatch.setattr(compartments, "_list_all_compartments_cached", lambda **_: tree)

    monkeypatch.setenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", "3")
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "c0", "c1"], False)

    monkeypatch.setenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", "5")
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "c0", "c1", "c2", "c3"], True)

    identity_client = MagicMock()
    identity_client.list_compartments.side_effect = [
        _response([SimpleNamespace(id="a"), SimpleNamespace(id="b")]),
        _response([]),
    ]
    monkeypatch.setattr(compartments, "_list_all_compartments_cached", lambda **_: [])
    monkeypatch.setattr(clients, "get_identity_client", lambda request_id=None: identity_client)
    monkeypatch.setenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", "2")
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "a"], False)


def test_subtree_expansion_is_incomplete_when_identity_cannot_be_read(monkeypatch):
    """
    When neither the cached listing nor the Identity crawl can be read, the root is
    returned alone and marked incomplete: whether it has children is unknown, and a
    root-only scope must not pass for a leaf compartment. A crawl that fails part-way
    keeps what it found. A genuine leaf, where the crawl succeeds, stays complete.
    """
    monkeypatch.setattr(
        compartments,
        "_list_all_compartments_cached",
        MagicMock(side_effect=RuntimeError("identity unavailable")),
    )
    monkeypatch.setattr(
        clients,
        "get_identity_client",
        MagicMock(side_effect=RuntimeError("identity unavailable")),
    )
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root"], False)

    identity_client = MagicMock()
    identity_client.list_compartments.side_effect = [
        _response([SimpleNamespace(id="child")]),
        RuntimeError("throttled"),
    ]
    monkeypatch.setattr(clients, "get_identity_client", lambda request_id=None: identity_client)
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "child"], False)

    identity_client.list_compartments.side_effect = [_response([])]
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root"], True)


def test_deadline_stops_full_subtree_pagination_without_caching_partial_results(monkeypatch):
    """An Identity page that spends the budget stops discovery and is not cached."""

    class Deadline:
        expired = False

        def reached(self):
            return self.expired

    deadline = Deadline()
    identity_client = MagicMock()

    def list_compartments(**_kwargs):
        deadline.expired = True
        return _response([SimpleNamespace(id="child", compartment_id="root")], has_next_page=True)

    identity_client.list_compartments.side_effect = list_compartments
    compartments._STORE.clear()
    monkeypatch.setattr(clients, "get_identity_client", lambda **_kwargs: identity_client)
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")

    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True, deadline=deadline
    ) == (["root"], False)
    identity_client.list_compartments.assert_called_once()
    identity_client.get_compartment.assert_not_called()
    assert len(compartments._STORE) == 0


def test_deadline_stops_direct_child_crawl(monkeypatch):
    """The restricted-IAM fallback stops after an in-flight Identity request."""

    class Deadline:
        expired = False

        def reached(self):
            return self.expired

    deadline = Deadline()
    identity_client = MagicMock()

    def list_compartments(**_kwargs):
        deadline.expired = True
        return _response([SimpleNamespace(id="child")], has_next_page=True)

    identity_client.list_compartments.side_effect = list_compartments
    monkeypatch.setattr(
        compartments,
        "_list_all_compartments_until_deadline",
        lambda *_args, **_kwargs: ([], True),
    )
    monkeypatch.setattr(clients, "get_identity_client", lambda **_kwargs: identity_client)

    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True, deadline=deadline
    ) == (["root"], False)
    identity_client.list_compartments.assert_called_once()


def test_name_resolution_timeout_returns_incomplete_scope(monkeypatch):
    """A display name not found before timeout is partial scope, not a false 404."""

    class Deadline:
        def reached(self):
            return True

    assert compartments._compartment_scope_for_tool(
        "Dev", fetch_for_child_compartment=False, deadline=Deadline()
    ) == ([], False)

    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True, deadline=Deadline()
    ) == (["root"], False)
    assert compartments._compartment_scope_for_tool(
        "ocid1.compartment.oc1..root",
        fetch_for_child_compartment=False,
        deadline=Deadline(),
    ) == (["ocid1.compartment.oc1..root"], False)


def test_deadline_scope_stops_before_fallback_requests(monkeypatch):
    """Expiry during local expansion or before a fallback request returns a partial scope."""

    class ExpiresOnCheck:
        def __init__(self, expiry_check):
            self.checks = 0
            self.expiry_check = expiry_check

        def reached(self):
            self.checks += 1
            return self.checks >= self.expiry_check

    monkeypatch.setattr(
        compartments,
        "_list_all_compartments_until_deadline",
        lambda *_a, **_k: (
            [SimpleNamespace(id="child", compartment_id="root")], True
        ),
    )
    deadline = ExpiresOnCheck(3)
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True, deadline=deadline
    ) == (["root"], False)

    monkeypatch.setattr(
        compartments,
        "_list_all_compartments_until_deadline",
        lambda *_a, **_k: ([], True),
    )
    identity_client = MagicMock()
    monkeypatch.setattr(clients, "get_identity_client", lambda **_kwargs: identity_client)
    for expiry_check in (4, 5, 6):
        deadline = ExpiresOnCheck(expiry_check)
        assert compartments._expand_compartment_scope(
            "root", include_child_compartments=True, deadline=deadline
        ) == (["root"], False)
        identity_client.list_compartments.assert_not_called()
        identity_client.reset_mock()


def test_deadline_listing_reports_complete_and_failed_scans(monkeypatch):
    """Only a complete Identity listing is returned as complete."""

    class Deadline:
        def reached(self):
            return False

    tree = [SimpleNamespace(id="root")]
    monkeypatch.setattr(compartments, "_fetch_all_compartments", lambda **_kwargs: tree)
    assert compartments._list_all_compartments_until_deadline(Deadline()) == (tree, True)

    monkeypatch.setattr(
        compartments,
        "_fetch_all_compartments",
        lambda **_kwargs: _raise(RuntimeError("identity unavailable")),
    )
    assert compartments._list_all_compartments_until_deadline(Deadline()) == ([], False)


def test_name_resolution_still_errors_when_scope_is_not_found_before_deadline(monkeypatch):
    """A live deadline does not hide an actual missing-compartment error."""

    class Deadline:
        def reached(self):
            return False

    monkeypatch.setattr(compartments, "get_compartment_by_name", lambda *_a, **_k: None)
    with pytest.raises(ValueError, match="not found"):
        compartments._compartment_scope_for_tool(
            "Missing", fetch_for_child_compartment=False, deadline=Deadline()
        )


def test_compartment_helpers_handle_malformed_items_and_empty_fallbacks(monkeypatch):
    """Malformed SDK shapes and empty expansion results keep safe scope behavior."""

    class BrokenCompartment:
        @property
        def id(self):
            raise RuntimeError("bad identity model")

    monkeypatch.setattr(compartments, "list_all_compartments_internal", lambda *_a: [BrokenCompartment()])
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")
    identity_client = MagicMock()
    identity_client.get_compartment.side_effect = RuntimeError("tenancy not readable")
    monkeypatch.setattr(clients, "get_identity_client", lambda **_kwargs: identity_client)

    assert compartments._fetch_all_compartments.__wrapped__(request_id="rid") == []
    assert compartments._build_children_index([BrokenCompartment()]) == {}
    assert compartments._resolve_compartment_id(" ", default_to_tenancy=True) == "tenancy"

    monkeypatch.setattr(compartments, "_list_all_compartments_cached", lambda **_kwargs: [
        SimpleNamespace(id="root", compartment_id="root"),
        SimpleNamespace(id="child", compartment_id="root"),
        SimpleNamespace(id="child", compartment_id="root"),
    ])
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "child"], True)

    monkeypatch.setattr(compartments, "_list_all_compartments_cached", lambda **_kwargs: [])
    identity_client.list_compartments.side_effect = [
        _response(
            [
                SimpleNamespace(id="root"),
                SimpleNamespace(id="child"),
                SimpleNamespace(id="child"),
            ]
        ),
        _response([SimpleNamespace(id="root")]),
    ]
    assert compartments._expand_compartment_scope(
        "root", include_child_compartments=True
    ) == (["root", "child"], True)

    monkeypatch.setattr(compartments, "_resolve_compartment_id", lambda value: value)
    monkeypatch.setattr(compartments, "_expand_compartment_scope", lambda *_a, **_k: ([], True))
    assert compartments._compartment_scope_for_tool(
        "root", fetch_for_child_compartment=True
    ) == (["root"], False)

    db_client = MagicMock()
    db_client.list_db_homes.return_value = _response([SimpleNamespace(display_name="no id")])
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)
    monkeypatch.setattr(compartments.oci.util, "to_dict", lambda _obj: _raise(RuntimeError("no mapping")))
    assert compartments._fetch_db_home_ids_for_compartment("root") == []
    with pytest.raises(RuntimeError, match="listing failed"):
        db_client.list_db_homes.side_effect = RuntimeError("listing failed")
        compartments._fetch_db_home_ids_for_compartment("root", raise_errors=True)


def test_child_scope_tools_deduplicate_and_forward_filter_kwargs(monkeypatch):
    """
    Every subtree-scoped tool de-duplicates resources seen in more than one
    compartment, keeps the summary when an optional full lookup fails, tags metric
    series with the compartment they came from, and forwards only kwargs the SDK
    actually accepts.
    """
    recovery_client = MagicMock()
    monitoring_client = MagicMock()
    work_request_client = MagicMock()
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
        clients,
        "get_monitoring_client",
        lambda request_id=None: monitoring_client,
    )
    monkeypatch.setattr(
        clients,
        "get_work_request_client",
        lambda region=None, request_id=None: work_request_client,
    )
    monkeypatch.setattr(
        compartments,
        "_compartment_ids_for_tool",
        lambda compartment_id, fetch_for_child_compartment, request_id=None: [
            "compartment-a",
            "compartment-b",
        ],
    )

    recovery_client.list_protected_databases.side_effect = [
        _response([SimpleNamespace(id="pd1", display_name="PD 1")]),
        _response([SimpleNamespace(id="pd1", display_name="PD 1 duplicate")]),
    ]
    recovery_client.get_protected_database.return_value = _response(
        SimpleNamespace(
            metrics=SimpleNamespace(backup_space_used_in_gbs=1.5),
            is_redo_logs_shipped=True,
        )
    )
    protected_databases = recovery_tools.list_protected_databases(
        "root", fetch_for_child_compartment=True
    )
    assert [pd["id"] for pd in protected_databases] == ["pd1"]

    recovery_client.list_protection_policies.side_effect = [
        _response([SimpleNamespace(id="policy1")]),
        _response([SimpleNamespace(id="policy1"), SimpleNamespace(id="policy2")]),
    ]
    policies = recovery_tools.list_protection_policies(
        "root", fetch_for_child_compartment=True
    )
    assert [policy.id for policy in policies] == ["policy1", "policy2"]

    recovery_client.list_recovery_service_subnets.side_effect = [
        _response([SimpleNamespace(id="rss1", subnet_id="subnet1")]),
        _response([SimpleNamespace(id="rss1"), SimpleNamespace(id="rss2")]),
    ]
    recovery_client.get_recovery_service_subnet.side_effect = RuntimeError(
        "optional full lookup failed"
    )
    subnets = recovery_tools.list_recovery_service_subnets(
        "root", fetch_for_child_compartment=True
    )
    assert [subnet.id for subnet in subnets] == ["rss1", "rss2"]
    assert subnets[0].subnets == ["subnet1"]

    series_a = SimpleNamespace(
        dimensions={"resourceId": "pd1"},
        aggregated_datapoints=[SimpleNamespace(timestamp="t1", value=1)],
    )
    series_b = SimpleNamespace(
        dimensions={"resourceId": "pd2"},
        aggregated_datapoints=[SimpleNamespace(timestamp="t2", value=2)],
    )
    monitoring_client.summarize_metrics_data.side_effect = [
        _response([series_a]),
        _response([series_b]),
    ]
    metrics = recovery_tools.get_recovery_service_metrics(
        compartment_id="root",
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-01T01:00:00Z",
        fetch_for_child_compartment=True,
        metricName="DataLossExposure",
        resolution="5m",
        aggregation="sum",
        protected_database_id="ocid1.protecteddatabase.oc1.iad.pd1",
    )
    assert [item["compartmentId"] for item in metrics] == [
        "compartment-a",
        "compartment-b",
    ]
    details = monitoring_client.summarize_metrics_data.call_args_list[0].kwargs[
        "summarize_metrics_data_details"
    ]
    assert details.query == 'DataLossExposure[5m]{resourceId="ocid1.protecteddatabase.oc1.iad.pd1"}.sum()'

    # The real client raises on unknown kwargs; a permissive mock is what let a
    # tool ship advertising parameters the SDK call rejects.
    _WORK_REQUEST_KWARGS = {"compartment_id", "resource_id", "limit", "page", "opc_request_id"}

    def _strict_work_requests(pages):
        """
        Build a list_work_requests stub that rejects unknown kwargs.

        The real client raises on kwargs it does not accept; a permissive mock is what
        let a tool ship advertising parameters the SDK call rejects.
        """
        responses = iter(pages)

        def call(**kwargs):
            """Return the next canned page, first refusing any unexpected kwarg."""
            extra = sorted(k for k in kwargs if k not in _WORK_REQUEST_KWARGS)
            if extra:
                raise ValueError(f"list_work_requests got unknown kwargs: {extra!r}")
            return next(responses)

        return call

    work_request_client.list_work_requests.side_effect = _strict_work_requests([
        _response(
            SimpleNamespace(
                items=[
                    {
                        "id": "wr1",
                        "operationType": "RESTORE_DATABASE",
                        "status": "IN_PROGRESS",
                    },
                    {"id": "skip", "operationType": "Create Backup"},
                ]
            ),
            has_next_page=True,
            next_page="wr-page-2",
        ),
        _response(
            [{"id": "wr1", "operation_type": "Restore Database", "status": "IN_PROGRESS"}]
        ),
        _response(
            [{"id": "wr2", "operation_type": "restore-database", "status": "IN_PROGRESS"}]
        ),
    ])
    restore_requests = recovery_tools.list_restore(
        "root",
        fetch_for_child_compartment=True,
        resource_id="db1",
        status="IN_PROGRESS",
        limit=2,
        page="wr-page-1",
        sort_order="DESC",
        sort_by="timeAccepted",
        opc_request_id="opc",
        region="us-ashburn-1",
    )
    assert [request.id for request in restore_requests] == ["wr1", "wr2"]
    first_restore_call = work_request_client.list_work_requests.call_args_list[0].kwargs
    # status/sort_by/sort_order are applied to the results, never forwarded: the
    # Work Requests API rejects them outright as unknown kwargs.
    assert first_restore_call == {
        "compartment_id": "compartment-a",
        "resource_id": "db1",
        "opc_request_id": "opc",
        "limit": 2,
        "page": "wr-page-1",
    }
    assert (
        work_request_client.list_work_requests.call_args_list[1].kwargs["page"]
        == "wr-page-2"
    )


def test_a_failed_compartment_scan_is_not_served_from_the_cache(monkeypatch):
    """
    A failed Identity scan must not be cached: the next call retries.

    The scan fails for any number of transient reasons, and this listing decides the
    scope of 14 tools. Were the empty result cached, one blip would answer "you have
    no compartments" for the whole TTL, and every one of those tools would quietly
    return nothing while OCI was healthy again.
    """
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")
    monkeypatch.setattr(auth, "_serving_http", lambda: False)

    identity_client = MagicMock()
    identity_client.get_compartment.return_value = _response(
        SimpleNamespace(id="tenancy", compartment_id=None)
    )
    monkeypatch.setattr(clients, "get_identity_client", lambda **_kwargs: identity_client)

    calls: list[str] = []

    def scan(_only_one_page):
        """Fail once, then succeed -- the shape of a transient Identity outage."""
        calls.append("scan")
        if len(calls) == 1:
            raise RuntimeError("Identity unavailable")
        return [SimpleNamespace(id="child", compartment_id="tenancy")]

    monkeypatch.setattr(compartments, "list_all_compartments_internal", scan)

    assert compartments._list_all_compartments_cached(request_id="rid") == []
    # The retry is the whole point: a cached [] would make this return [] as well.
    recovered = compartments._list_all_compartments_cached(request_id="rid")
    assert [getattr(c, "id", None) for c in recovered] == ["child", "tenancy"]
    assert calls == ["scan", "scan"]

    # And the good listing *is* cached -- a third call does not scan again.
    assert compartments._list_all_compartments_cached(request_id="rid") == recovered
    assert calls == ["scan", "scan"]


def test_db_home_discovery_reads_every_page(monkeypatch):
    """
    DB Home discovery follows the paging token under the same compartment scope, so
    homes that appear only on later pages -- including after an empty first page --
    are part of the set callers treat as complete. A later page that fails raises
    when the caller asked for errors, and a reached deadline stops paging.
    """
    db_client = MagicMock()
    db_client.list_db_homes.side_effect = _paged(
        [[], [SimpleNamespace(id="home-first")], [SimpleNamespace(id="home-second")]]
    )
    monkeypatch.setattr(clients, "get_database_client", lambda *_a, **_k: db_client)

    assert compartments._fetch_db_home_ids_for_compartment("compartment-a") == ["home-first", "home-second"]
    assert db_client.list_db_homes.call_count == 3
    assert all(c.kwargs["compartment_id"] == "compartment-a" for c in db_client.list_db_homes.call_args_list)

    deadline = SimpleNamespace(reached=lambda: True)
    db_client.list_db_homes.reset_mock()
    assert compartments._fetch_db_home_ids_for_compartment("compartment-a", deadline=deadline) == []
    assert db_client.list_db_homes.call_count == 1

    first = _paged([[SimpleNamespace(id="home-first")], []])
    db_client.list_db_homes.side_effect = lambda **kw: (
        _raise(RuntimeError("page two failed")) if kw.get("page") else first(**kw)
    )
    with pytest.raises(RuntimeError, match="page two failed"):
        compartments._fetch_db_home_ids_for_compartment("compartment-a", raise_errors=True)


def test_list_tool_scope_reports_a_capped_subtree_as_partial(monkeypatch):
    """
    The cap defaults to 200. A list tool keeps returning what it scanned when the cap
    drops compartments, but the call is recorded as partial so the client is told;
    a subtree that fits records nothing.
    """
    monkeypatch.delenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", raising=False)
    assert compartments._max_compartments_in_scope() == 200

    tree = [SimpleNamespace(id=f"c{i}", compartment_id="root") for i in range(3)]
    monkeypatch.setattr(compartments, "_resolve_compartment_id", lambda value, **_kwargs: value)
    monkeypatch.setattr(compartments, "_list_all_compartments_cached", lambda **_kwargs: tree)
    reasons_token = telemetry._MCP_PARTIAL_RESULT_CONTEXT.set([])
    try:
        assert compartments._compartment_ids_for_tool("root", fetch_for_child_compartment=True) == [
            "root",
            "c0",
            "c1",
            "c2",
        ]
        assert telemetry._MCP_PARTIAL_RESULT_CONTEXT.get() == []

        monkeypatch.setenv("ORACLE_MCP_MAX_COMPARTMENTS_IN_SCOPE", "2")
        assert compartments._compartment_ids_for_tool("root", fetch_for_child_compartment=True) == [
            "root",
            "c0",
        ]
        assert "(2)" in telemetry._MCP_PARTIAL_RESULT_CONTEXT.get()[0]
    finally:
        telemetry._MCP_PARTIAL_RESULT_CONTEXT.reset(reasons_token)
    # Outside a tool call there is nowhere to report to, so noting is a no-op.
    telemetry._note_partial_result("ignored")
