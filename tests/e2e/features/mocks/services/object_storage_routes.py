"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from object_storage_data import (
    BUCKET_DETAILS,
    BUCKETS,
    NAMESPACE,
    OBJECT_VERSIONS,
    OBJECTS,
)

# OCI Object Storage endpoints style
# Base prefix is /n to match real API shape
object_storage_bp = Blueprint("object_storage", __name__)


@object_storage_bp.route("/n", methods=["GET"])
def get_namespace():
    # compartmentId is accepted but not used for the mock
    return oci_res(NAMESPACE)


@object_storage_bp.route("/n/<namespace>/b", methods=["GET"])
def list_buckets(namespace):
    _limit = request.args.get("limit", type=int)

    items = BUCKETS if namespace == NAMESPACE else []
    if _limit is not None:
        items = items[:_limit]
    return oci_res(items)


@object_storage_bp.route("/n/<namespace>/b/<bucket_name>", methods=["GET"])
def get_bucket(namespace, bucket_name):
    if namespace != NAMESPACE:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    details = BUCKET_DETAILS.get(bucket_name)
    if not details:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(details)


@object_storage_bp.route("/n/<namespace>/b/<bucket_name>/o", methods=["GET"])
def list_objects(namespace, bucket_name):
    if namespace != NAMESPACE:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404

    data = OBJECTS.get(
        bucket_name, {"objects": [], "prefixes": [], "nextStartWith": None}
    )

    prefix = request.args.get("prefix", default="")
    objects = data.get("objects", [])
    if prefix:
        objects = [o for o in objects if o.get("name", "").startswith(prefix)]

    # Basic prefix derivation for the filtered set
    prefixes = sorted(
        {o["name"].split("/", 1)[0] + "/" for o in objects if "/" in o["name"]}
    )

    return oci_res(
        {
            "objects": objects,
            "prefixes": prefixes,
            "nextStartWith": None,
        }
    )


@object_storage_bp.route(
    "/n/<namespace>/b/<bucket_name>/objectversions", methods=["GET"]
)
def list_object_versions(namespace, bucket_name):
    if namespace != NAMESPACE:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404

    data = OBJECT_VERSIONS.get(bucket_name, {"items": [], "prefixes": []})
    prefix = request.args.get("prefix", default="")
    limit = request.args.get("limit", type=int)
    items = data.get("items", [])
    if prefix:
        items = [o for o in items if o.get("name", "").startswith(prefix)]

    prefixes = sorted(
        {i["name"].split("/", 1)[0] + "/" for i in items if "/" in i["name"]}
    )

    if limit is not None:
        items = items[:limit]

    return oci_res(
        {
            "items": items,
            "prefixes": prefixes,
        }
    )


@object_storage_bp.route(
    "/n/<namespace>/b/<bucket_name>/o/<path:object_name>",
    methods=["GET", "PUT", "HEAD", "DELETE"],
)
def get_or_put_object(namespace, bucket_name, object_name):
    if namespace != NAMESPACE:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404

    if request.method in ["GET", "HEAD"]:
        bucket = OBJECTS.get(bucket_name, {"objects": []})
        obj = next(
            (o for o in bucket.get("objects", []) if o.get("name") == object_name), None
        )
        if not obj:
            return jsonify({"code": "NotAuthorizedOrNotFound"}), 404

        if request.method == "HEAD":
            resp = jsonify({})
            resp.headers["Content-Length"] = obj.get("size", 0)
            resp.headers["ETag"] = obj.get("etag", "mock-etag")
            return resp

        # GET returns content
        return f"Content of {object_name}", 200

    if request.method == "DELETE":
        bucket = OBJECTS.get(bucket_name)
        if bucket:
            bucket["objects"] = [
                o for o in bucket["objects"] if o.get("name") != object_name
            ]
        return "", 204

    # PUT upload: accept and return simple ack
    return oci_res({"message": "Object uploaded successfully"})
