"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

from typing import Any

import oci

from ..authentication.session_signer import session_config
from ..config.consts import MAX_OBJECT_STORAGE_LIST_PAGE_SIZE


def create_object_storage_client(*, profile: str | None = None, region: str | None = None):
    config, signer, _context = session_config(profile=profile, region=region)
    return oci.object_storage.ObjectStorageClient(config=config, signer=signer)


def call_put_object(
    client: Any,
    *,
    namespace: str,
    bucket: str,
    object_name: str,
    body: Any,
    content_length: int,
    content_type: str | None,
    metadata: dict[str, str] | None = None,
    request_id: str | None = None,
    overwrite: bool = False,
):
    kwargs: dict[str, Any] = {
        "content_length": content_length,
    }
    if content_type:
        kwargs["content_type"] = content_type
    if metadata:
        kwargs["opc_meta"] = metadata
    if request_id:
        kwargs["opc_client_request_id"] = request_id
    if not overwrite:
        kwargs["if_none_match"] = "*"

    return client.put_object(
        namespace_name=namespace,
        bucket_name=bucket,
        object_name=object_name,
        put_object_body=body,
        **kwargs,
    )


def call_list_objects(
    client: Any,
    *,
    namespace: str,
    bucket: str,
    prefix: str | None,
    delimiter: str | None,
    fields: str | None,
    start: str | None = None,
    limit: int = MAX_OBJECT_STORAGE_LIST_PAGE_SIZE,
    request_id: str | None = None,
):
    kwargs: dict[str, Any] = {
        "limit": limit,
    }
    if prefix is not None:
        kwargs["prefix"] = prefix
    if delimiter:
        kwargs["delimiter"] = delimiter
    if fields:
        kwargs["fields"] = fields
    if start:
        kwargs["start"] = start
    if request_id:
        kwargs["opc_client_request_id"] = request_id

    return client.list_objects(
        namespace_name=namespace,
        bucket_name=bucket,
        **kwargs,
    )


def call_get_object(
    client: Any,
    *,
    namespace: str,
    bucket: str,
    object_name: str,
    request_id: str | None = None,
):
    kwargs: dict[str, Any] = {}
    if request_id:
        kwargs["opc_client_request_id"] = request_id

    return client.get_object(
        namespace_name=namespace,
        bucket_name=bucket,
        object_name=object_name,
        **kwargs,
    )
