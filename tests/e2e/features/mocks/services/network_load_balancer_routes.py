"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from network_load_balancer_data import NETWORK_LOAD_BALANCERS

# OCI NLB API version base path (per docs)
network_load_balancer_bp = Blueprint(
    "network_load_balancer", __name__, url_prefix="/20200501"
)


def _apply_limit(items):
    try:
        limit = request.args.get("limit")
        if limit is not None:
            lim = int(limit)
            if lim >= 0:
                return items[:lim]
    except Exception:
        pass
    return items


def _find_nlb(nlb_id):
    return next((n for n in NETWORK_LOAD_BALANCERS if n.get("id") == nlb_id), None)


@network_load_balancer_bp.route("/networkLoadBalancers", methods=["GET"])
def list_network_load_balancers():
    items = NETWORK_LOAD_BALANCERS

    # Optional filters
    comp = request.args.get("compartmentId")
    if comp:
        items = [i for i in items if i.get("compartmentId") == comp]

    lifecycle_state = request.args.get("lifecycleState")
    if lifecycle_state:
        items = [i for i in items if i.get("lifecycleState") == lifecycle_state]

    items = _apply_limit(items)

    # Shape should be a collection with items
    return oci_res({"items": items})


@network_load_balancer_bp.route("/networkLoadBalancers/<nlb_id>", methods=["GET"])
def get_network_load_balancer(nlb_id):
    nlb = _find_nlb(nlb_id)
    if not nlb:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(nlb)


@network_load_balancer_bp.route(
    "/networkLoadBalancers/<nlb_id>/listeners", methods=["GET"]
)
def list_listeners(nlb_id):
    nlb = _find_nlb(nlb_id)
    if not nlb:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    listeners_map = nlb.get("listeners", {}) or {}
    items = list(listeners_map.values())
    items = _apply_limit(items)
    return oci_res({"items": items})


@network_load_balancer_bp.route(
    "/networkLoadBalancers/<nlb_id>/listeners/<listener_name>", methods=["GET"]
)
def get_listener(nlb_id, listener_name):
    nlb = _find_nlb(nlb_id)
    if not nlb:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    listener = (nlb.get("listeners", {}) or {}).get(listener_name)
    if not listener:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(listener)


@network_load_balancer_bp.route(
    "/networkLoadBalancers/<nlb_id>/backendSets", methods=["GET"]
)
def list_backend_sets(nlb_id):
    nlb = _find_nlb(nlb_id)
    if not nlb:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    backend_sets_map = nlb.get("backendSets", {}) or {}
    items = list(backend_sets_map.values())
    items = _apply_limit(items)
    return oci_res({"items": items})


@network_load_balancer_bp.route(
    "/networkLoadBalancers/<nlb_id>/backendSets/<backend_set_name>", methods=["GET"]
)
def get_backend_set(nlb_id, backend_set_name):
    nlb = _find_nlb(nlb_id)
    if not nlb:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    backend_set = (nlb.get("backendSets", {}) or {}).get(backend_set_name)
    if not backend_set:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(backend_set)


@network_load_balancer_bp.route(
    "/networkLoadBalancers/<nlb_id>/backendSets/<backend_set_name>/backends",
    methods=["GET"],
)
def list_backends(nlb_id, backend_set_name):
    nlb = _find_nlb(nlb_id)
    if not nlb:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    backend_set = (nlb.get("backendSets", {}) or {}).get(backend_set_name) or {}
    items = backend_set.get("backends", [])
    items = _apply_limit(items)
    return oci_res({"items": items})


@network_load_balancer_bp.route(
    "/networkLoadBalancers/<nlb_id>/backendSets/<backend_set_name>/backends/<backend_name>",
    methods=["GET"],
)
def get_backend(nlb_id, backend_set_name, backend_name):
    nlb = _find_nlb(nlb_id)
    if not nlb:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    backend_set = (nlb.get("backendSets", {}) or {}).get(backend_set_name) or {}
    backend = next(
        (b for b in backend_set.get("backends", []) if b.get("name") == backend_name),
        None,
    )
    if not backend:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(backend)
