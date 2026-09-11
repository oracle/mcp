"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from oracle.oci_db_observability_mcp_server import metric_catalog


def _catalog() -> metric_catalog.MetricCatalog:
    records = [
        {
            "namespace": "oracle_oci_database",
            "name": "ApplyLag",
            "description": "Apply lag during replication",
            "dimensions": ["dbRole", "databaseId"],
        },
        {
            "namespace": "oracle_oci_database",
            "name": "CpuUtilization",
            "description": "Database CPU utilization",
            "dimensions": ["databaseId"],
        },
    ]
    return metric_catalog.MetricCatalog("test-catalog", "1", tuple(metric_catalog._freeze(record) for record in records))


def test_search_ranks_matches_and_validates_input() -> None:
    catalog = _catalog()

    result = catalog.search("apply lags", namespace="oracle_oci_database", limit=1)

    assert result["items"][0]["key"] == {"namespace": "oracle_oci_database", "name": "ApplyLag"}
    assert result["items"][0]["matchedFields"] == ["name", "description"]
    assert metric_catalog._stem("categories") == "category"
    assert metric_catalog._stem("running") == "run"
    assert metric_catalog._stem("updated") == "updat"
    assert metric_catalog._stem("alarms") == "alarm"
    with pytest.raises(metric_catalog.MetricCatalogError, match="non-empty"):
        catalog.search(" ")
    with pytest.raises(metric_catalog.MetricCatalogError, match="between"):
        catalog.search("apply", limit=0)


def test_get_and_list_validate_and_page_catalog_records() -> None:
    catalog = _catalog()

    assert catalog.get([{"namespace": "oracle_oci_database", "name": "ApplyLag"}])["items"][0]["name"] == "ApplyLag"
    with pytest.raises(metric_catalog.MetricCatalogError, match="at least one"):
        catalog.get([])
    with pytest.raises(metric_catalog.MetricCatalogError, match="non-empty"):
        catalog.get([{"namespace": "", "name": "ApplyLag"}])
    with pytest.raises(metric_catalog.MetricCatalogError, match="between"):
        catalog.list(limit=101)
    with pytest.raises(metric_catalog.MetricCatalogError, match="non-negative"):
        catalog.list(cursor="not-a-number")
    with pytest.raises(metric_catalog.MetricCatalogError, match="non-negative"):
        catalog.list(cursor="-1")

    first_page = catalog.list(limit=1)
    assert first_page["nextCursor"] == "1"
    assert first_page["items"][0]["name"] == "ApplyLag"
    assert catalog.list(limit=1, cursor=first_page["nextCursor"])["nextCursor"] is None


def test_packaged_catalog_exposes_collection_interval() -> None:
    catalog = metric_catalog.load_metric_catalog()

    assert all("collectionInterval" in record and "collectionInternal" not in record for record in catalog.records)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ("{", "Unable to load metric catalog"),
        (json.dumps({"catalogId": "test", "version": "1", "records": "not-a-list"}), "invalid metadata"),
        (json.dumps({"catalogId": "test", "version": "1", "records": ["not-an-object"]}), "records must be objects"),
    ],
)
def test_load_metric_catalog_rejects_invalid_packaged_data(monkeypatch, payload, error) -> None:
    resource = SimpleNamespace(read_text=lambda **_kwargs: payload)
    monkeypatch.setattr(metric_catalog, "files", lambda _package: SimpleNamespace(joinpath=lambda *_parts: resource))
    metric_catalog.load_metric_catalog.cache_clear()

    with pytest.raises(metric_catalog.MetricCatalogError, match=error):
        metric_catalog.load_metric_catalog()

    metric_catalog.load_metric_catalog.cache_clear()
