"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from logging import Logger
from typing import Annotated, List

import oci
from fastmcp import FastMCP
from oracle.mcp_common import with_oci_client
from oracle.oci_object_storage_mcp_server.models import (
    Bucket,
    BucketSummary,
    ListObjects,
    ObjectSummary,
    ObjectVersionCollection,
    map_bucket,
    map_bucket_summary,
    map_object_summary,
    map_object_version_summary,
)

from . import __project__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


# Object storage namespace
@with_oci_client(oci.object_storage.ObjectStorageClient)
def get_object_storage_namespace(
    compartment_id: str, *, client: oci.object_storage.ObjectStorageClient
):
    namespace = client.get_namespace(compartment_id=compartment_id)
    return namespace.data


@mcp.tool(description="Get the object storage namespace for the tenancy")
@with_oci_client(oci.object_storage.ObjectStorageClient)
def get_namespace(
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    *,
    client: oci.object_storage.ObjectStorageClient,
):
    return get_object_storage_namespace(compartment_id, client=client)


# Buckets
@mcp.tool(description="List object storage buckets")
@with_oci_client(oci.object_storage.ObjectStorageClient)
def list_buckets(
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    *,
    client: oci.object_storage.ObjectStorageClient,
) -> List[BucketSummary]:
    namespace_name = get_object_storage_namespace(compartment_id, client=client)
    buckets = client.list_buckets(namespace_name, compartment_id).data
    return [map_bucket_summary(bucket) for bucket in buckets]


@mcp.tool(description="Get details for a specific object storage bucket")
@with_oci_client(oci.object_storage.ObjectStorageClient)
def get_bucket_details(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    *,
    client: oci.object_storage.ObjectStorageClient,
) -> Bucket:
    namespace_name = get_object_storage_namespace(compartment_id, client=client)
    bucket_details = client.get_bucket(
        namespace_name,
        bucket_name,
        fields=[
            "approximateSize",
            "approximateCount",
            "autoTiering",
        ],
    ).data

    return map_bucket(bucket_details)


# Objects
@mcp.tool(description="List objects in a given object storage bucket")
@with_oci_client(oci.object_storage.ObjectStorageClient)
def list_objects(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    prefix: Annotated[str, "Optional prefix to filter objects"] = "",
    *,
    client: oci.object_storage.ObjectStorageClient,
) -> ListObjects:
    namespace_name = get_object_storage_namespace(compartment_id, client=client)
    list_objects = client.list_objects(
        namespace_name,
        bucket_name,
        prefix=prefix,
        fields="name,size,timeModified,archivalState,storageTier",
    ).data

    objects = [map_object_summary(obj) for obj in list_objects.objects]
    prefixes = list_objects.prefixes if list_objects.prefixes else []
    return ListObjects(objects=objects, prefixes=prefixes)


@mcp.tool(description="List object versions in a given object storage bucket")
@with_oci_client(oci.object_storage.ObjectStorageClient)
def list_object_versions(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    prefix: Annotated[str, "Optional prefix to filter object versions"] = "",
    *,
    client: oci.object_storage.ObjectStorageClient,
) -> ObjectVersionCollection:
    namespace_name = get_object_storage_namespace(compartment_id, client=client)
    list_object_versions = client.list_object_versions(
        namespace_name,
        bucket_name,
        prefix=prefix,
        limit=25,
        fields="timeModified",
    ).data

    versioned_objects = [
        map_object_version_summary(obj) for obj in list_object_versions.items
    ]
    prefixes = list_object_versions.prefixes if list_object_versions.prefixes else []
    return ObjectVersionCollection(items=versioned_objects, prefixes=prefixes)


@mcp.tool(description="Get a specific object from an object storage bucket")
@with_oci_client(oci.object_storage.ObjectStorageClient)
def get_object(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    object_name: Annotated[str, "The name of the object"],
    version_id: Annotated[str, "Optional version ID of the object"] = "",
    *,
    client: oci.object_storage.ObjectStorageClient,
) -> ObjectSummary:
    namespace_name = get_object_storage_namespace(compartment_id, client=client)
    obj = client.get_object(
        namespace_name,
        bucket_name,
        object_name,
        version_id=version_id,
    ).data

    return map_object_summary(obj)


@mcp.tool(description="Upload an object to an object storage bucket")
@with_oci_client(oci.object_storage.ObjectStorageClient)
def upload_object(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    file_path: Annotated[str, "The path to the file to upload"],
    object_name: Annotated[
        str,
        "Optional name of the object to upload"
        "If the object name is not provided, use the file name as the object name",
    ] = "",
    *,
    client: oci.object_storage.ObjectStorageClient,
):
    namespace_name = get_object_storage_namespace(compartment_id, client=client)
    logger.info("Got Namespace: %s", namespace_name)
    logger.info("Checking file at path: %s", file_path)
    try:
        with open(file_path, "rb") as file:
            client.put_object(namespace_name, bucket_name, object_name, file)
        return {"message": "Object uploaded successfully"}
    except Exception as e:
        return {"error": str(e)}


def main():

    host = os.getenv("ORACLE_MCP_HOST")
    port = os.getenv("ORACLE_MCP_PORT")

    if host and port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
