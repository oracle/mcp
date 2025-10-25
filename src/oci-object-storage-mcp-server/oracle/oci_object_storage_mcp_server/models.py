"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import oci.object_storage.models
from pydantic import BaseModel, Field


class Bucket(BaseModel):
    namespace: Optional[str] = Field(
        None,
        description=("The Object Storage namespace in which the bucket " "resides."),
    )
    name: Optional[str] = Field(
        None,
        description="The name of the bucket.",
    )
    compartment_id: Optional[str] = Field(
        None,
        description=("The compartment ID in which the bucket is " "authorized."),
    )
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description=("Arbitrary string keys and values for user-defined " "metadata."),
    )
    created_by: Optional[str] = Field(
        None,
        description="The OCID of the user who created the bucket.",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="The date and time the bucket was created.",
    )
    etag: Optional[str] = Field(
        None,
        description="The entity tag (ETag) for the bucket.",
    )
    public_access_type: Optional[str] = Field(
        None,
        description=("The type of public access enabled on this bucket."),
    )
    storage_tier: Optional[str] = Field(
        None,
        description="The storage tier type assigned to the bucket.",
    )
    object_events_enabled: Optional[bool] = Field(
        None,
        description=(
            "Whether or not events are emitted for object state "
            "changes in this bucket."
        ),
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Free-form tags for this resource.",
    )
    defined_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description="Defined tags for this resource.",
    )
    kms_key_id: Optional[str] = Field(
        None,
        description=(
            "The OCID of a master encryption key used to call "
            "the Key Management service."
        ),
    )
    object_lifecycle_policy_etag: Optional[str] = Field(
        None,
        description=(
            "The entity tag (ETag) for the live object lifecycle "
            "policy on the bucket."
        ),
    )
    approximate_count: Optional[int] = Field(
        None,
        description="The approximate number of objects in the bucket.",
    )
    approximate_size: Optional[int] = Field(
        None,
        description=(
            "The approximate total size in bytes of all objects " "in the bucket."
        ),
    )
    replication_enabled: Optional[bool] = Field(
        None,
        description="Whether or not this bucket is a replication source.",
    )
    is_read_only: Optional[bool] = Field(
        None,
        description="Whether or not this bucket is read only.",
    )
    id: Optional[str] = Field(
        None,
        description="The OCID of the bucket.",
    )
    versioning: Optional[str] = Field(
        None,
        description="The versioning status on the bucket.",
    )
    auto_tiering: Optional[str] = Field(
        None,
        description="The auto tiering status on the bucket.",
    )

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class NamespaceMetadata(BaseModel):
    """
    Pydantic model mirroring the fields of oci.object_storage.models.NamespaceMetadata.
    """

    namespace: str = Field(
        ...,
        description=("The Object Storage namespace to which the metadata " "belongs."),
    )
    default_s3_compartment_id: Optional[str] = Field(
        None,
        description=(
            "If set, specifies the default compartment assignment "
            "for the Amazon S3 Compatibility API."
        ),
    )
    default_swift_compartment_id: Optional[str] = Field(
        None,
        description=(
            "If set, specifies the default compartment assignment " "for the Swift API."
        ),
    )

    class Config:
        extra = "forbid"


class CreateBucketDetails(BaseModel):
    """
    Pydantic model mirroring the fields of
    oci.object_storage.models.CreateBucketDetails.
    """

    name: str = Field(
        ...,
        description="The name of the bucket.",
    )
    compartment_id: str = Field(
        ...,
        description=("The ID of the compartment in which to create the " "bucket."),
    )
    metadata: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Arbitrary string, up to 4KB, of keys and values for "
            "user-defined metadata."
        ),
    )
    public_access_type: Optional[str] = Field(
        None,
        description=("The type of public access enabled on this bucket."),
    )
    storage_tier: Optional[str] = Field(
        None,
        description="The type of storage tier of this bucket.",
    )
    object_events_enabled: Optional[bool] = Field(
        None,
        description=(
            "Whether or not events are emitted for object state "
            "changes in this bucket."
        ),
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Free-form tags for this resource.",
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource.",
    )
    kms_key_id: Optional[str] = Field(
        None,
        description=(
            "The OCID of a master encryption key used to call "
            "the Key Management service."
        ),
    )
    versioning: Optional[str] = Field(
        None,
        description="The versioning status on the bucket.",
    )
    auto_tiering: Optional[str] = Field(
        None,
        description="The auto tiering status on the bucket.",
    )

    class Config:
        extra = "forbid"


class BucketSummary(BaseModel):
    namespace: Optional[str] = Field(
        None,
        description=("The Object Storage namespace in which the bucket " "lives."),
    )
    name: Optional[str] = Field(
        None,
        description="The name of the bucket.",
    )
    compartment_id: Optional[str] = Field(
        None,
        description=("The compartment ID in which the bucket is " "authorized."),
    )
    created_by: Optional[str] = Field(
        None,
        description="The OCID of the user who created the bucket.",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="The date and time the bucket was created.",
    )
    etag: Optional[str] = Field(
        None,
        description="The entity tag (ETag) for the bucket.",
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None,
        description="Free-form tags for this resource.",
    )
    defined_tags: Optional[Dict[str, Dict[str, object]]] = Field(
        None,
        description="Defined tags for this resource.",
    )

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class ObjectSummary(BaseModel):
    name: Optional[str] = Field(
        None,
        description="The name of the object.",
    )
    size: Optional[int] = Field(
        None,
        description="Size of the object in bytes.",
    )
    md5: Optional[str] = Field(
        None,
        description="Base64-encoded MD5 hash of the object data.",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="The date and time the object was created.",
    )
    etag: Optional[str] = Field(
        None,
        description="The current entity tag (ETag) for the object.",
    )
    storage_tier: Optional[str] = Field(
        None,
        description="The storage tier that the object is stored in.",
    )
    archival_state: Optional[str] = Field(
        None,
        description="Archival state of an object.",
    )
    time_modified: Optional[datetime] = Field(
        None,
        description="The date and time the object was modified.",
    )

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class ListObjects(BaseModel):
    objects: Optional[List[ObjectSummary]] = Field(
        None,
        description="An array of object summaries.",
    )
    prefixes: Optional[List[str]] = Field(
        None,
        description=(
            "Prefixes that are common to the results returned "
            "by the request if the request specified a delimiter."
        ),
    )
    next_start_with: Optional[str] = Field(
        None,
        description=(
            "The name of the object to use in the `start` "
            "parameter to obtain the next page of a truncated "
            "ListObjects response."
        ),
    )

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True


class ObjectVersionSummary(BaseModel):
    name: Optional[str] = Field(
        None,
        description="The name of the object.",
    )
    size: Optional[int] = Field(
        None,
        description="Size of the object in bytes.",
    )
    md5: Optional[str] = Field(
        None,
        description="Base64-encoded MD5 hash of the object data.",
    )
    time_created: Optional[datetime] = Field(
        None,
        description="The date and time the object was created.",
    )
    time_modified: Optional[datetime] = Field(
        None,
        description="The date and time the object was modified.",
    )
    etag: Optional[str] = Field(
        None,
        description="The current entity tag (ETag) for the object.",
    )
    storage_tier: Optional[str] = Field(
        None,
        description="The storage tier that the object is stored in.",
    )
    archival_state: Optional[str] = Field(
        None,
        description="Archival state of an object.",
    )
    version_id: Optional[str] = Field(
        None,
        description="VersionId of the object.",
    )
    is_delete_marker: Optional[bool] = Field(
        None,
        description="This flag will indicate if the version is deleted or not.",
    )

    class Config:
        extra = "allow"
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class ObjectVersionCollection(BaseModel):
    """
    Pydantic model mirroring the fields of oci.object_storage.models.ObjectVersionCollection.
    """

    items: List[ObjectVersionSummary] = Field(
        ..., description="An array of object version summaries."
    )
    prefixes: Optional[List[str]] = Field(
        None,
        description=(
            "Prefixes that are common to the results returned by the request if the request "
            "specified a delimiter."
        ),
    )

    class Config:
        extra = "forbid"


def map_object_summary(obj: oci.object_storage.models.ObjectSummary) -> ObjectSummary:
    """
    Convert an oci.object_storage.models.ObjectSummary to an
    oracle.oci_object_storage_mcp_server.models.ObjectSummary, including all nested types
    """
    return ObjectSummary(
        name=obj.name,
        size=getattr(obj, "size", None),
        time_created=getattr(obj, "time_created", None),
        etag=getattr(obj, "etag", None),
        storage_tier=getattr(obj, "storage_tier", None),
        archival_state=getattr(obj, "archival_state", None),
        time_modified=getattr(obj, "time_modified", None),
    )


def map_bucket_summary(
    bucket: oci.object_storage.models.BucketSummary,
) -> BucketSummary:
    """
    Convert an oci.object_storage.models.BucketSummary to an
    oracle.oci_object_storage_mcp_server.models.BucketSummary, including all nested types
    """
    return BucketSummary(
        namespace=getattr(bucket, "namespace", None),
        name=getattr(bucket, "name", None),
        compartment_id=getattr(bucket, "compartment_id", None),
        created_by=getattr(bucket, "created_by", None),
        time_created=getattr(bucket, "time_created", None),
        etag=getattr(bucket, "etag", None),
        freeform_tags=getattr(bucket, "freeform_tags", None),
        defined_tags=getattr(bucket, "defined_tags", None),
    )


def map_bucket(bucket: oci.object_storage.models.Bucket) -> Bucket:
    """
    Convert an oci.object_storage.models.Bucket to an oracle.oci_object_storage_mcp_server.models.Bucket,
    including all nested types
    """
    return Bucket(
        namespace=getattr(bucket, "namespace", None),
        name=getattr(bucket, "name", None),
        compartment_id=getattr(bucket, "compartment_id", None),
        metadata=getattr(bucket, "metadata", None),
        created_by=getattr(bucket, "created_by", None),
        time_created=getattr(bucket, "time_created", None),
        etag=getattr(bucket, "etag", None),
        public_access_type=getattr(bucket, "public_access_type", None),
        storage_tier=getattr(bucket, "storage_tier", None),
        object_events_enabled=getattr(bucket, "object_events_enabled", None),
        freeform_tags=getattr(bucket, "freeform_tags", None),
        defined_tags=getattr(bucket, "defined_tags", None),
        kms_key_id=getattr(bucket, "kms_key_id", None),
        object_lifecycle_policy_etag=getattr(
            bucket, "object_lifecycle_policy_etag", None
        ),
        approximate_count=getattr(bucket, "approximate_count", None),
        approximate_size=getattr(bucket, "approximate_size", None),
        replication_enabled=getattr(bucket, "replication_enabled", None),
        is_read_only=getattr(bucket, "is_read_only", None),
        id=getattr(bucket, "id", None),
        versioning=getattr(bucket, "versioning", None),
        auto_tiering=getattr(bucket, "auto_tiering", None),
    )


def map_object_version_summary(obj: oci.object_storage.models.ObjectVersionSummary):
    return ObjectVersionSummary(
        name=obj.name,
        size=getattr(obj, "size", None),
        md5=getattr(obj, "md5", None),
        time_created=getattr(obj, "time_created", None),
        time_modified=getattr(obj, "time_modified", None),
        etag=getattr(obj, "etag", None),
        storage_tier=getattr(obj, "storage_tier", None),
        archival_state=getattr(obj, "archival_state", None),
        version_id=getattr(obj, "version_id", None),
        is_delete_marker=getattr(obj, "is_delete_marker", None),
    )
