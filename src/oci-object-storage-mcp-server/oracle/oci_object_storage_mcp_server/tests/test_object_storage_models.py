"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from oracle.oci_object_storage_mcp_server.models import (
    Bucket,
    BucketSummary,
    CreateBucketDetails,
    ListObjects,
    NamespaceMetadata,
    ObjectSummary,
    ObjectVersionCollection,
    ObjectVersionSummary,
    map_bucket,
    map_bucket_summary,
    map_object_summary,
    map_object_version_summary,
)
from pydantic import ValidationError


class TestModelMapping:
    def test_map_object_summary_from_oci_like_object(self):
        # Use a simple namespace to emulate the OCI SDK object with attributes
        src = SimpleNamespace(
            name="obj1",
            size=123,
            time_created=datetime(2021, 1, 1, tzinfo=timezone.utc),
            etag="etag-1",
            storage_tier="STANDARD",
            archival_state="ARCHIVED",
            time_modified=datetime(2021, 1, 2, tzinfo=timezone.utc),
        )

        mapped = map_object_summary(src)
        assert isinstance(mapped, ObjectSummary)
        assert mapped.name == "obj1"
        assert mapped.size == 123
        assert mapped.storage_tier == "STANDARD"
        # json encodes datetimes using isoformat
        json_text = mapped.json()
        assert "2021-01-01T00:00:00" in json_text
        assert "2021-01-02T00:00:00" in json_text

    def test_map_bucket_summary_from_oci_like_object(self):
        src = SimpleNamespace(
            namespace="ns1",
            name="bucket1",
            compartment_id="ocid1.compartment.oc1..xyz",
            created_by="ocid1.user.oc1..abc",
            time_created=datetime(2021, 1, 1, tzinfo=timezone.utc),
            etag="etag-bkt",
            freeform_tags={"env": "dev"},
            defined_tags={"ns": {"k": "v"}},
        )

        mapped = map_bucket_summary(src)
        assert isinstance(mapped, BucketSummary)
        assert mapped.name == "bucket1"
        assert mapped.namespace == "ns1"
        assert mapped.freeform_tags == {"env": "dev"}

    def test_map_bucket_from_oci_like_object(self):
        src = SimpleNamespace(
            namespace="ns1",
            name="bucket1",
            compartment_id="ocid1.compartment.oc1..xyz",
            metadata={"a": "b"},
            created_by="ocid1.user.oc1..abc",
            time_created=datetime(2021, 1, 1, tzinfo=timezone.utc),
            etag="etag-bkt",
            public_access_type="NoPublicAccess",
            storage_tier="Standard",
            object_events_enabled=False,
            freeform_tags={"env": "dev"},
            defined_tags={"ns": {"k": "v"}},
            kms_key_id="ocid1.key.oc1..key",
            object_lifecycle_policy_etag="olp-etag",
            approximate_count=10,
            approximate_size=2048,
            replication_enabled=False,
            is_read_only=False,
            id="ocid1.bucket.oc1..bucket",
            versioning="Enabled",
            auto_tiering="InfrequentAccess",
        )

        mapped = map_bucket(src)
        assert isinstance(mapped, Bucket)
        assert mapped.name == "bucket1"
        assert mapped.approximate_size == 2048
        assert mapped.versioning == "Enabled"

    def test_map_object_version_summary_from_oci_like_object(self):
        src = SimpleNamespace(
            name="obj1",
            size=123,
            md5="md5==",
            time_created=datetime(2021, 1, 1, tzinfo=timezone.utc),
            time_modified=datetime(2021, 1, 2, tzinfo=timezone.utc),
            etag="etag-1",
            storage_tier="STANDARD",
            archival_state="ARCHIVED",
            version_id="ver-1",
            is_delete_marker=False,
        )

        mapped = map_object_version_summary(src)
        assert isinstance(mapped, ObjectVersionSummary)
        assert mapped.version_id == "ver-1"
        assert mapped.is_delete_marker is False


class TestModelValidation:
    def test_namespace_metadata_forbids_extra_fields(self):
        with pytest.raises(ValidationError):
            NamespaceMetadata(namespace="ns", unknown="x")

    def test_create_bucket_details_forbids_extra_fields(self):
        with pytest.raises(ValidationError):
            CreateBucketDetails(name="b", compartment_id="c", unknown="x")

    def test_object_version_collection_forbids_extra_fields(self):
        items = [ObjectVersionSummary(name="o")]  # minimal valid item
        with pytest.raises(ValidationError):
            ObjectVersionCollection(items=items, unknown="x")

    def test_list_objects_allows_extra_fields(self):
        lo = ListObjects(objects=[ObjectSummary(name="a")], prefixes=["p"], extra=1)
        # extra field should be preserved due to extra="allow"
        assert getattr(lo, "extra") == 1

    def test_bucket_model_allows_extra_fields(self):
        b = Bucket(name="bkt", extra_field="ok")
        assert getattr(b, "extra_field") == "ok"
