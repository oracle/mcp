"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from datetime import UTC, datetime

import oci

from oracle.oci_oracle_db_observability.v1.response_mapping import map_response_data


def _database_insight(suffix: str) -> oci.opsi.models.DatabaseInsight:
    return oci.opsi.models.DatabaseInsight(
        entity_source="AUTONOMOUS_DATABASE",
        id=f"ocid1.opsidatabaseinsight.oc1..{suffix}",
        compartment_id="ocid1.compartment.oc1..example",
        status="ENABLED",
        freeform_tags={},
        defined_tags={},
        time_created=datetime(2026, 1, 1, tzinfo=UTC),
        lifecycle_state="ACTIVE",
    )


def test_shared_mapper_preserves_none_and_scalars() -> None:
    assert map_response_data(None) is None
    assert map_response_data("plain report content") == "plain report content"
    assert map_response_data(42) == 42
    assert map_response_data(False) is False


def test_shared_mapper_maps_sdk_model_to_plain_dict() -> None:
    result = map_response_data(_database_insight("one"))

    assert isinstance(result, dict)
    assert result["id"] == "ocid1.opsidatabaseinsight.oc1..one"


def test_shared_mapper_recursively_maps_lists() -> None:
    result = map_response_data([_database_insight("one"), _database_insight("two")])

    assert [item["id"] for item in result] == [
        "ocid1.opsidatabaseinsight.oc1..one",
        "ocid1.opsidatabaseinsight.oc1..two",
    ]
    assert all(isinstance(item, dict) for item in result)


def test_shared_mapper_falls_back_to_plain_data() -> None:
    assert map_response_data({"id": "example", "count": 1}) == {
        "id": "example",
        "count": 1,
    }
