"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

SDK-to-Pydantic model mapping: nested and variant fields, unusual iterable
and attribute sources, and the conversion fallbacks.
"""

from types import SimpleNamespace
import inspect

import oracle.oci_recovery_mcp_server.models as models


def test_model_conversion_helpers_handle_fallback_paths(monkeypatch):
    """
    The shared conversion helpers degrade rather than raise: a failed
    ``oci.util.to_dict`` falls back to the object's public attributes, an
    un-iterable value maps to None, and an object with neither yields None.
    """
    assert models._oci_to_dict(None) is None
    assert models._first_not_none(None, False, "fallback") is False
    assert models._map_list([1, 2], lambda value: value * 2) == [2, 4]

    class BadIterable:
        """A value that raises the moment anything tries to iterate it."""

        def __iter__(self):
            """Fail every iteration attempt."""
            raise RuntimeError("cannot iterate")

    assert models._map_list(BadIterable(), lambda value: value) is None

    def raising_to_dict(_sdk_obj):
        """Stand in for oci.util.to_dict and fail, forcing the fallback path."""
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(models.oci.util, "to_dict", raising_to_dict)

    class MinimalObject:
        """An object with one public and one private attribute."""

        def __init__(self):
            """Set the public and private attributes the fallback should distinguish."""
            self.id = "obj1"
            self._private = "hidden"

    assert models._oci_to_dict({"id": "dict1"}) == {"id": "dict1"}
    assert models._oci_to_dict(MinimalObject()) == {"id": "obj1"}
    assert models._oci_to_dict(object()) is None


def test_generated_model_mappers_handle_none_and_sdk_conversion_fallback(monkeypatch):
    """
    Every ``map_*`` in the module returns None for None, and survives an empty
    object with the SDK conversion broken -- swept across the module by
    reflection so a newly added mapper is covered without editing this test.
    """

    def raising_to_dict(_sdk_obj):
        """Stand in for oci.util.to_dict and fail, forcing the fallback path."""
        raise RuntimeError("conversion failed")

    monkeypatch.setattr(models.oci.util, "to_dict", raising_to_dict)

    for mapper_name, mapper in inspect.getmembers(models, inspect.isfunction):
        if not mapper_name.startswith("map_"):
            continue

        assert mapper(None) is None, mapper_name
        mapped = mapper(SimpleNamespace())
        assert mapped is None or isinstance(mapped, models.OCIBaseModel), mapper_name


def test_model_mappers_capture_nested_and_variant_fields():
    """
    Mappers read camelCase input, flatten subnet objects to OCIDs, keep
    unmodeled destination fields in ``extras``, and populate nested metrics,
    backup config and work request models.
    """
    rss = models.map_recovery_service_subnet(
        {
            "id": "rss1",
            "nsgIds": ("nsg1", "nsg2"),
            "subnets": [{"subnetId": "subnet1"}, {"id": "subnet2"}],
        }
    )
    assert rss.id == "rss1"
    assert rss.nsg_ids == ["nsg1", "nsg2"]
    assert rss.subnets == ["subnet1", "subnet2"]

    backup_config = models.map_db_backup_config(
        {
            "isAutoBackupEnabled": True,
            "backupDestinationDetails": [
                {
                    "destinationType": "OBJECT_STORE",
                    "bucketName": "bucket",
                    "customField": "preserved",
                }
            ],
        }
    )
    assert backup_config.is_auto_backup_enabled is True
    assert backup_config.backup_destination_details[0].type == "OBJECT_STORE"
    assert backup_config.backup_destination_details[0].extras == {
        "customField": "preserved"
    }

    metrics = models.map_metrics(
        {
            "backupSpaceUsedInGbs": 5.5,
            "isRedoLogsEnabled": False,
            "retentionPeriodInDays": 14,
        }
    )
    assert metrics.backup_space_used_in_gbs == 5.5
    assert metrics.is_redo_logs_enabled is False
    assert metrics.retention_period_in_days == 14

    work_request = models.map_work_request(
        {
            "id": "wr1",
            "compartmentId": "compartment",
            "operationType": "RESTORE_DATABASE",
            "percentComplete": 75.5,
            "resourceId": "db1",
        }
    )
    assert work_request.id == "wr1"
    assert work_request.operation_type == "RESTORE_DATABASE"
    assert work_request.percent_complete == 75.5
    assert work_request.resource_id == "db1"


def test_model_mappers_handle_unusual_iterables_and_attribute_sources(monkeypatch):
    """
    A list field that raises on iteration becomes None rather than failing the
    mapper, a bare OCID string maps as a subnet detail, and a dict-like whose
    ``get`` never returns anything still yields a model with no ``extras``.
    """

    class BadIterable:
        """A value that raises the moment anything tries to iterate it."""

        def __iter__(self):
            """Fail every iteration attempt."""
            raise RuntimeError("cannot iterate")

    rss = models.map_recovery_service_subnet(
        {"id": "rss1", "nsgIds": BadIterable(), "subnets": BadIterable()}
    )
    assert rss.id == "rss1"
    assert rss.nsg_ids is None
    assert rss.subnets is None

    assert models.map_recovery_service_subnet_details("rss-id").id == "rss-id"
    assert (
        models.map_recovery_service_subnet_details(
            {"id": "rss-detail", "nsgIds": BadIterable()}
        ).nsg_ids
        is None
    )
    assert (
        models.map_recovery_service_subnet_input(
            {"displayName": "input", "nsgIds": BadIterable()}
        ).nsg_ids
        is None
    )
    assert (
        models.map_recovery_service_subnet_summary(
            {"id": "rss-summary", "nsgIds": BadIterable()}
        ).nsg_ids
        is None
    )

    class GetWithoutItems:
        """A dict-like that answers every lookup with the default and exposes no items."""

        def get(self, _key, default=None):
            """Return the default for any key."""
            return default

    monkeypatch.setattr(models, "_oci_to_dict", lambda _obj: GetWithoutItems())
    backup_destination = models.map_backup_destination_details(
        SimpleNamespace(type="NFS")
    )
    assert backup_destination.type == "NFS"
    assert backup_destination.extras is None
    backup_config = models.map_db_backup_config(
        SimpleNamespace(is_auto_backup_enabled=True)
    )
    assert backup_config.is_auto_backup_enabled is True
    assert backup_config.extras is None
