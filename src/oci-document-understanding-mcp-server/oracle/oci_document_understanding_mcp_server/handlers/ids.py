"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import base64
import hashlib

from oracle.oci_document_understanding_mcp_server.models import DocumentSource


def document_id_from_base64(document: str, mime_type: str) -> str:
    """Creates a stable document id from the MIME type and decoded content."""
    digest = hashlib.sha256()
    digest.update(mime_type.encode("utf-8"))
    digest.update(b"\0")
    digest.update(base64.b64decode(document, validate=True))
    return "doc_" + digest.hexdigest()[:32]


def document_id_from_source(source: DocumentSource) -> str:
    """Creates a stable document id for either inline or Object Storage document sources."""
    if source.source_type == "INLINE_BASE64":
        if source.document is None or source.mime_type is None:
            raise ValueError("INLINE_BASE64 document source requires document and mime_type")
        return document_id_from_base64(source.document, source.mime_type)

    digest = hashlib.sha256()
    digest.update(b"OBJECT_STORAGE")
    digest.update(b"\0")
    digest.update((source.namespace_name or "").encode("utf-8"))
    digest.update(b"\0")
    digest.update((source.bucket_name or "").encode("utf-8"))
    digest.update(b"\0")
    digest.update((source.object_name or "").encode("utf-8"))
    return "doc_" + digest.hexdigest()[:32]
