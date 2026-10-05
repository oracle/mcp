"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Tenancy region subscriptions and Recovery Service limit tools.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest

from _helpers import _raise, _response
from oracle.oci_recovery_mcp_server import auth
from oracle.oci_recovery_mcp_server import recovery_tools
from oracle.oci_recovery_mcp_server import clients
from oracle.oci_recovery_mcp_server import compartments
from oracle.oci_recovery_mcp_server import regions


def test_region_subscription_and_limit_tools_return_current_contracts(monkeypatch):
    """
    Subscribed regions are read through IAM, normalized across the snake_case and
    camelCase attribute spellings, and sorted -- re-querying every call, since the
    caller's own IAM policy decides whether they may read them at all. The limits
    tool then reports both Recovery Service limits for the resolved region, reading
    them from an SDK object and a plain dict alike, and passes the caller's
    opc_request_id through to every call.
    """
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")

    identity_client = MagicMock()
    identity_client.list_region_subscriptions.return_value = _response(
        [
            SimpleNamespace(region_name="us-phoenix-1", status="READY"),
            SimpleNamespace(regionName="us-ashburn-1", status="READY"),
            SimpleNamespace(status="IGNORED"),
        ]
    )
    monkeypatch.setattr(
        clients, "get_identity_client", lambda request_id=None: identity_client
    )

    subscribed = regions._iam_subscribed_regions_with_status(request_id="rid")
    assert subscribed == [
        {"region": "us-ashburn-1", "status": "READY"},
        {"region": "us-phoenix-1", "status": "READY"},
    ]
    assert regions._iam_subscribed_regions_with_status(request_id="rid2") == subscribed
    assert recovery_tools.fetch_regions_subscribed()["total"] == 2
    # Every one of those three lookups went back to IAM.
    assert identity_client.list_region_subscriptions.call_args_list == [
        call(tenancy_id="tenancy")
    ] * 3

    limits_client = MagicMock()
    monkeypatch.setattr(
        recovery_tools.oci.util,
        "to_dict",
        lambda _obj: _raise(RuntimeError("no SDK conversion")),
    )
    limits_client.get_resource_availability.side_effect = [
        _response(
            SimpleNamespace(
                scope_type="REGION",
                available=90,
                used=10,
                fractional_availability=0.9,
                fractional_usage=0.1,
                effective_quota_value=100,
                policy_name="storage-policy",
            )
        ),
        _response(
            {
                "scope_type": "AD",
                "available": 4,
                "used": 1,
                "fractional_availability": 0.8,
                "fractional_usage": 0.2,
                "effective_quota_value": 5,
                "policy_name": "count-policy",
            }
        ),
    ]
    monkeypatch.setattr(
        auth,
        "_load_oci_config_for_server",
        lambda: {"region": "us-phoenix-1"},
    )
    monkeypatch.setattr(
        clients,
        "get_limits_client",
        lambda region, request_id=None: limits_client,
    )

    # No region argument: the server's configured region is used.
    limits = recovery_tools.check_recovery_service_limits(
        compartment_id="ignored",
        opc_request_id="opc",
    )
    assert limits["compartmentId"] == "tenancy"
    assert limits["region"] == "us-phoenix-1"
    assert limits["limits"]["protectedDatabaseBackupStorageGb"]["available"] == 90
    assert limits["limits"]["protectedDatabaseCount"]["policyName"] == "count-policy"
    assert [
        call.kwargs["limit_name"]
        for call in limits_client.get_resource_availability.call_args_list
    ] == [
        "protected-database-backup-storage-gb",
        "protected-database-count",
    ]
    assert all(
        call.kwargs["opc_request_id"] == "opc"
        for call in limits_client.get_resource_availability.call_args_list
    )


def test_metric_query_parts_are_validated_before_interpolation(monkeypatch):
    """
    Every caller-supplied part of the MQL query is validated before it is
    interpolated.

    The query is assembled by string interpolation, so without this a caller could
    reshape it or break out of the quoted resourceId filter, and an ordinary typo
    would come back as an opaque service-side parse error.
    """
    captured = {}
    monitoring_client = MagicMock()

    def summarize(compartment_id, summarize_metrics_data_details):
        """Capture the assembled query instead of calling Monitoring."""
        captured["query"] = summarize_metrics_data_details.query
        captured["resolution"] = summarize_metrics_data_details.resolution
        return _response([])

    monitoring_client.summarize_metrics_data.side_effect = summarize
    monkeypatch.setattr(clients, "get_monitoring_client", lambda **_kwargs: monitoring_client)
    monkeypatch.setattr(compartments, "_compartment_ids_for_tool", lambda cid, **_kwargs: [cid])

    valid = dict(
        compartment_id="ocid1.compartment.oc1..c",
        start_time="2026-01-01T00:00:00Z",
        end_time="2026-01-02T00:00:00Z",
    )

    recovery_tools.get_recovery_service_metrics(**valid)
    assert captured["query"] == "SpaceUsedForRecoveryWindow[1h].max()"

    recovery_tools.get_recovery_service_metrics(
        **valid,
        metricName="ProtectedDatabaseSize",
        resolution="1d",
        aggregation="mean",
        protected_database_id="ocid1.protecteddatabase.oc1.iad.abc123",
    )
    assert (
        captured["query"]
        == 'ProtectedDatabaseSize[1d]{resourceId="ocid1.protecteddatabase.oc1.iad.abc123"}.mean()'
    )
    assert captured["resolution"] == "1d"

    rejected = {
        "metricName": "CpuUtilization[1m].max() -- ",
        "resolution": "99z",
        "aggregation": "grouping(1)",
        "protected_database_id": 'x"} or {resourceId=~".*"',
    }
    for field, value in rejected.items():
        with pytest.raises(ValueError, match=field):
            recovery_tools.get_recovery_service_metrics(**valid, **{field: value})


def test_limit_lookups_honor_the_requested_region_and_refuse_to_guess_one(monkeypatch):
    """
    `region` selects the region the limits are read from, and an unresolvable region is
    an error rather than a default.

    Limits differ per region, so both halves matter: the argument used to be accepted
    and silently discarded, which answered for the configured region while the caller
    believed they had asked about another, and the fallback used to be a hard-coded
    us-ashburn-1, which reported one region's numbers as another's on a server whose
    region could not be resolved. A wrong number is actionable; that is what makes it
    worse than no number.
    """
    monkeypatch.setattr(auth, "get_tenancy", lambda: "tenancy")
    limits_client = MagicMock()
    limits_client.get_resource_availability.return_value = _response(
        {"scope_type": "REGION", "available": 1, "used": 0}
    )
    built_for: list[str] = []

    def limits_factory(region, request_id=None):
        """Record the region each client is built for."""
        built_for.append(region)
        return limits_client

    monkeypatch.setattr(clients, "get_limits_client", limits_factory)
    monkeypatch.setattr(auth, "_load_oci_config_for_server", lambda: {"region": "us-phoenix-1"})

    # The argument wins over the server's configured region.
    assert recovery_tools.check_recovery_service_limits(region="eu-frankfurt-1")["region"] == (
        "eu-frankfurt-1"
    )
    assert built_for == ["eu-frankfurt-1"]

    # A blank argument is not an answer: it falls through to the configured region.
    built_for.clear()
    assert recovery_tools.check_recovery_service_limits(region="   ")["region"] == "us-phoenix-1"
    assert built_for == ["us-phoenix-1"]

    # With no region anywhere, the tool says so instead of picking one.
    monkeypatch.setattr(auth, "_effective_region", lambda default=None: None)
    with pytest.raises(ValueError, match="No OCI region could be determined"):
        recovery_tools.check_recovery_service_limits()
    with pytest.raises(ValueError, match="No OCI region could be determined"):
        recovery_tools.check_recovery_service_limits(region="   ")
