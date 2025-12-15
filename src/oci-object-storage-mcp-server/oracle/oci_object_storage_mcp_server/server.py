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

from . import __project__, __version__

logger = Logger(__name__, level="INFO")

mcp = FastMCP(name=__project__)


def get_object_storage_client():
    config = oci.config.from_file(
        profile_name=os.getenv("OCI_CONFIG_PROFILE", oci.config.DEFAULT_PROFILE)
    )
    user_agent_name = __project__.split("oracle.", 1)[1].split("-server", 1)[0]
    config["additional_user_agent"] = f"{user_agent_name}/{__version__}"

    private_key = oci.signer.load_private_key_from_file(config["key_file"])
    token_file = config["security_token_file"]
    token = None
    with open(token_file, "r") as f:
        token = f.read()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    return oci.object_storage.ObjectStorageClient(config, signer=signer)


# Object storage namespace
def get_object_storage_namespace(compartment_id: str):
    object_storage_client = get_object_storage_client()
    namespace = object_storage_client.get_namespace(compartment_id=compartment_id)
    return namespace.data


@mcp.tool(description="Get the object storage namespace for the tenancy")
def get_namespace(
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
):
    return get_object_storage_namespace(compartment_id)


# Buckets
@mcp.tool(description="List object storage buckets")
def list_buckets(
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
) -> List[BucketSummary]:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    buckets = object_storage_client.list_buckets(namespace_name, compartment_id).data
    return [map_bucket_summary(bucket) for bucket in buckets]


@mcp.tool(description="Get details for a specific object storage bucket")
def get_bucket_details(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
) -> Bucket:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    bucket_details = object_storage_client.get_bucket(
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
def list_objects(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    prefix: Annotated[str, "Optional prefix to filter objects"] = "",
) -> ListObjects:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    list_objects = object_storage_client.list_objects(
        namespace_name,
        bucket_name,
        prefix=prefix,
        fields="name,size,timeModified,archivalState,storageTier",
    ).data

    objects = [map_object_summary(obj) for obj in list_objects.objects]
    prefixes = list_objects.prefixes if list_objects.prefixes else []
    return ListObjects(objects=objects, prefixes=prefixes)


@mcp.tool(description="List object versions in a given object storage bucket")
def list_object_versions(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    prefix: Annotated[str, "Optional prefix to filter object versions"] = "",
) -> ObjectVersionCollection:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    list_object_versions = object_storage_client.list_object_versions(
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
def get_object(
    bucket_name: Annotated[str, "The name of the bucket"],
    compartment_id: Annotated[
        str,
        "The OCID of the compartment."
        "If compartment id is not provided, use the root compartment id or the tenancy id",
    ],
    object_name: Annotated[str, "The name of the object"],
    version_id: Annotated[str, "Optional version ID of the object"] = "",
) -> ObjectSummary:
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    obj = object_storage_client.get_object(
        namespace_name,
        bucket_name,
        object_name,
        version_id=version_id,
    ).data

    return map_object_summary(obj)


@mcp.tool(description="Upload an object to an object storage bucket")
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
):
    object_storage_client = get_object_storage_client()
    namespace_name = get_object_storage_namespace(compartment_id)
    logger.info("Got Namespace: %s", namespace_name)
    logger.info("Checking file at path: %s", file_path)
    try:
        with open(file_path, "rb") as file:
            object_storage_client.put_object(
                namespace_name, bucket_name, object_name, file
            )
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
