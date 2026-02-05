"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from load_balancer_data import (  # BACKENDS,; TENANCY_ID,
    BACKEND_HEALTH,
    BACKEND_SET_HEALTH,
    BACKEND_SETS,
    CERTIFICATES,
    HEALTH_SUMMARIES,
    HOSTNAMES,
    LB_ID,
    LOAD_BALANCER_HEALTH,
    LOAD_BALANCER_OBJ,
    LOAD_BALANCERS,
    ROUTING_POLICIES,
    RULE_SETS,
    SSL_CIPHER_SUITES,
    WORK_REQUESTS,
)

load_balancer_bp = Blueprint("load_balancer", __name__, url_prefix="/20170115")


# Helpers


def _find_backend_set(name: str):
    return next((b for b in BACKEND_SETS if b.get("name") == name), None)


def _find_backend(backend_set_name: str, backend_name: str):
    bs = _find_backend_set(backend_set_name)
    if not bs:
        return None
    return next(
        (b for b in bs.get("backends", []) if b.get("name") == backend_name), None
    )


def _find_ssl_cipher_suite(name: str):
    return next((s for s in SSL_CIPHER_SUITES if s.get("name") == name), None)


def _find_hostname(name: str):
    return next((h for h in HOSTNAMES if h.get("name") == name), None)


def _find_rule_set(name: str):
    return next((r for r in RULE_SETS if r.get("name") == name), None)


def _find_routing_policy(name: str):
    return next((r for r in ROUTING_POLICIES if r.get("name") == name), None)


def _find_certificate(name: str):
    return next((c for c in CERTIFICATES if c.get("certificateName") == name), None)


# Load Balancers


@load_balancer_bp.route("/loadBalancers", methods=["GET"])
def list_load_balancers():
    compartment_id = request.args.get("compartmentId")
    display_name = request.args.get("displayName")
    items = LOAD_BALANCERS
    if compartment_id:
        items = [i for i in items if i.get("compartmentId") == compartment_id]
    if display_name:
        items = [i for i in items if i.get("displayName") == display_name]
    return oci_res(items)


@load_balancer_bp.route("/loadBalancers", methods=["POST"])
def create_load_balancer():
    # Return 204 accepted with opc-work-request-id semantics
    return "", 204


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>", methods=["GET"])
def get_load_balancer(load_balancer_id):
    # Accept either the OCID or the display name for convenience in E2E flows
    if load_balancer_id not in (LB_ID, LOAD_BALANCER_OBJ.get("displayName")):
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(LOAD_BALANCER_OBJ)


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>", methods=["PUT"])
def update_load_balancer(load_balancer_id):
    return "", 204


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>", methods=["DELETE"])
def delete_load_balancer(load_balancer_id):
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/updateShape", methods=["PUT"]
)
def update_shape(load_balancer_id):
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/networkSecurityGroups", methods=["PUT"]
)
def update_nsgs(load_balancer_id):
    return "", 204


# Listeners


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>/listeners", methods=["POST"])
def create_listener(load_balancer_id):
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("name")
    if name:
        # Store/minimally normalize into LB object so subsequent GET works
        listener = {
            "name": name,
            "defaultBackendSetName": body.get("defaultBackendSetName"),
            "port": body.get("port"),
            "protocol": body.get("protocol"),
            "hostnameNames": body.get("hostnameNames", []),
            "pathRouteSetName": body.get("pathRouteSetName"),
            "sslConfiguration": body.get("sslConfiguration"),
            "connectionConfiguration": body.get("connectionConfiguration"),
            "ruleSetNames": body.get("ruleSetNames", []),
            "routingPolicyName": body.get("routingPolicyName"),
        }
        LOAD_BALANCER_OBJ.setdefault("listeners", {})[name] = listener
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/listeners/<listener_name>", methods=["PUT"]
)
def update_listener(load_balancer_id, listener_name):
    body = request.get_json(force=True, silent=True) or {}
    lmap = LOAD_BALANCER_OBJ.setdefault("listeners", {})
    if listener_name in lmap:
        listener = lmap[listener_name]
        # Update only provided fields
        for key, target_key in [
            ("defaultBackendSetName", "defaultBackendSetName"),
            ("port", "port"),
            ("protocol", "protocol"),
            ("hostnameNames", "hostnameNames"),
            ("pathRouteSetName", "pathRouteSetName"),
            ("sslConfiguration", "sslConfiguration"),
            ("connectionConfiguration", "connectionConfiguration"),
            ("ruleSetNames", "ruleSetNames"),
            ("routingPolicyName", "routingPolicyName"),
        ]:
            if key in body:
                listener[target_key] = body.get(key)
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/listeners/<listener_name>", methods=["DELETE"]
)
def delete_listener(load_balancer_id, listener_name):
    LOAD_BALANCER_OBJ.setdefault("listeners", {}).pop(listener_name, None)
    return "", 204


# Backend sets


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets", methods=["GET"]
)
def list_backend_sets(load_balancer_id):
    items = list(LOAD_BALANCER_OBJ.get("backendSets", {}).values())
    return oci_res(items)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets", methods=["POST"]
)
def create_backend_set(load_balancer_id):
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("name")
    if name:
        bs = {
            "name": name,
            "policy": body.get("policy"),
            "backends": body.get("backends", []),
            "backendMaxConnections": body.get("backendMaxConnections"),
            "healthChecker": body.get("healthChecker"),
            "sslConfiguration": body.get("sslConfiguration"),
            "sessionPersistenceConfiguration": body.get(
                "sessionPersistenceConfiguration"
            ),
            "lbCookieSessionPersistenceConfiguration": body.get(
                "lbCookieSessionPersistenceConfiguration"
            ),
        }
        # Update both dict map and list view
        LOAD_BALANCER_OBJ.setdefault("backendSets", {})[name] = bs
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>", methods=["GET"]
)
def get_backend_set(load_balancer_id, backend_set_name):
    bs = _find_backend_set(backend_set_name)
    if not bs:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(bs)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>", methods=["PUT"]
)
def update_backend_set(load_balancer_id, backend_set_name):
    body = request.get_json(force=True, silent=True) or {}
    bs = _find_backend_set(backend_set_name)
    if bs:
        for key in [
            "policy",
            "backends",
            "backendMaxConnections",
            "healthChecker",
            "sslConfiguration",
            "sessionPersistenceConfiguration",
            "lbCookieSessionPersistenceConfiguration",
        ]:
            if key in body:
                bs[key] = body.get(key)
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>",
    methods=["DELETE"],
)
def delete_backend_set(load_balancer_id, backend_set_name):
    # Remove from LB map
    LOAD_BALANCER_OBJ.setdefault("backendSets", {}).pop(backend_set_name, None)
    return "", 204


# Backends


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>/backends",
    methods=["GET"],
)
def list_backends(load_balancer_id, backend_set_name):
    bs = _find_backend_set(backend_set_name)
    items = (bs or {}).get("backends", [])
    return oci_res(items)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>/backends",
    methods=["POST"],
)
def create_backend(load_balancer_id, backend_set_name):
    body = request.get_json(force=True, silent=True) or {}
    bs = _find_backend_set(backend_set_name)
    if bs is not None:
        ip = body.get("ipAddress")
        port = body.get("port")
        backend = {
            "name": f"{ip}:{port}",
            "ipAddress": ip,
            "port": port,
            "weight": body.get("weight"),
            "maxConnections": body.get("maxConnections"),
            "backup": body.get("backup", False),
            "drain": body.get("drain", False),
            "offline": body.get("offline", False),
        }
        bs.setdefault("backends", []).append(backend)
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>/backends/<backend_name>",
    methods=["GET"],
)
def get_backend(load_balancer_id, backend_set_name, backend_name):
    b = _find_backend(backend_set_name, backend_name)
    if not b:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(b)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>/backends/<backend_name>",
    methods=["PUT"],
)
def update_backend(load_balancer_id, backend_set_name, backend_name):
    body = request.get_json(force=True, silent=True) or {}
    b = _find_backend(backend_set_name, backend_name)
    if b:
        for key in ["weight", "maxConnections", "backup", "drain", "offline"]:
            if key in body:
                b[key] = body.get(key)
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>/backends/<backend_name>",
    methods=["DELETE"],
)
def delete_backend(load_balancer_id, backend_set_name, backend_name):
    bs = _find_backend_set(backend_set_name)
    if bs is not None:
        bs["backends"] = [
            b for b in bs.get("backends", []) if b.get("name") != backend_name
        ]
    return "", 204


# Certificates


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/certificates", methods=["GET"]
)
def list_certificates(load_balancer_id):
    return oci_res(CERTIFICATES)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/certificates", methods=["POST"]
)
def create_certificate(load_balancer_id):
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("certificateName")
    if name:
        CERTIFICATES.append(
            {
                "certificateName": name,
                "publicCertificate": body.get("publicCertificate", "---PUBLIC---"),
                "caCertificate": body.get("caCertificate", "---CA---"),
            }
        )
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/certificates/<certificate_name>",
    methods=["DELETE"],
)
def delete_certificate(load_balancer_id, certificate_name):
    global CERTIFICATES
    CERTIFICATES = [
        c for c in CERTIFICATES if c.get("certificateName") != certificate_name
    ]
    return "", 204


# SSL Cipher Suites


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/sslCipherSuites", methods=["GET"]
)
def list_ssl_cipher_suites(load_balancer_id):
    return oci_res(SSL_CIPHER_SUITES)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/sslCipherSuites", methods=["POST"]
)
def create_ssl_cipher_suite(load_balancer_id):
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("name")
    if name and not _find_ssl_cipher_suite(name):
        SSL_CIPHER_SUITES.append({"name": name, "ciphers": body.get("ciphers", [])})
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/sslCipherSuites/<name>", methods=["GET"]
)
def get_ssl_cipher_suite(load_balancer_id, name):
    s = _find_ssl_cipher_suite(name)
    if not s:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(s)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/sslCipherSuites/<name>", methods=["PUT"]
)
def update_ssl_cipher_suite(load_balancer_id, name):
    body = request.get_json(force=True, silent=True) or {}
    s = _find_ssl_cipher_suite(name)
    if s:
        if "ciphers" in body:
            s["ciphers"] = body.get("ciphers")
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/sslCipherSuites/<name>", methods=["DELETE"]
)
def delete_ssl_cipher_suite(load_balancer_id, name):
    global SSL_CIPHER_SUITES
    SSL_CIPHER_SUITES = [s for s in SSL_CIPHER_SUITES if s.get("name") != name]
    return "", 204


# Hostnames


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>/hostnames", methods=["GET"])
def list_hostnames(load_balancer_id):
    return oci_res(HOSTNAMES)


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>/hostnames", methods=["POST"])
def create_hostname(load_balancer_id):
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("name")
    hostname = body.get("hostname")
    if name and hostname:
        HOSTNAMES.append({"name": name, "hostname": hostname})
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/hostnames/<name>", methods=["GET"]
)
def get_hostname(load_balancer_id, name):
    h = _find_hostname(name)
    if not h:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(h)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/hostnames/<name>", methods=["PUT"]
)
def update_hostname(load_balancer_id, name):
    body = request.get_json(force=True, silent=True) or {}
    h = _find_hostname(name)
    if h and "hostname" in body:
        h["hostname"] = body.get("hostname")
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/hostnames/<name>", methods=["DELETE"]
)
def delete_hostname(load_balancer_id, name):
    global HOSTNAMES
    HOSTNAMES = [h for h in HOSTNAMES if h.get("name") != name]
    return "", 204


# Rule sets


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>/ruleSets", methods=["GET"])
def list_rule_sets(load_balancer_id):
    return oci_res(RULE_SETS)


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>/ruleSets", methods=["POST"])
def create_rule_set(load_balancer_id):
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("name")
    if name and not _find_rule_set(name):
        RULE_SETS.append({"name": name, "items": body.get("items", [])})
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/ruleSets/<name>", methods=["GET"]
)
def get_rule_set(load_balancer_id, name):
    r = _find_rule_set(name)
    if not r:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(r)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/ruleSets/<name>", methods=["PUT"]
)
def update_rule_set(load_balancer_id, name):
    body = request.get_json(force=True, silent=True) or {}
    r = _find_rule_set(name)
    if r and "items" in body:
        r["items"] = body.get("items")
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/ruleSets/<name>", methods=["DELETE"]
)
def delete_rule_set(load_balancer_id, name):
    global RULE_SETS
    RULE_SETS = [r for r in RULE_SETS if r.get("name") != name]
    return "", 204


# Routing Policies


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/routingPolicies", methods=["GET"]
)
def list_routing_policies(load_balancer_id):
    return oci_res(ROUTING_POLICIES)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/routingPolicies", methods=["POST"]
)
def create_routing_policy(load_balancer_id):
    body = request.get_json(force=True, silent=True) or {}
    name = body.get("name")
    if name and not _find_routing_policy(name):
        ROUTING_POLICIES.append(
            {
                "name": name,
                "conditionLanguageVersion": body.get("conditionLanguageVersion", "V1"),
                "rules": body.get("rules", []),
            }
        )
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/routingPolicies/<name>", methods=["GET"]
)
def get_routing_policy(load_balancer_id, name):
    r = _find_routing_policy(name)
    if not r:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(r)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/routingPolicies/<name>", methods=["PUT"]
)
def update_routing_policy(load_balancer_id, name):
    body = request.get_json(force=True, silent=True) or {}
    r = _find_routing_policy(name)
    if r:
        if "conditionLanguageVersion" in body:
            r["conditionLanguageVersion"] = body.get("conditionLanguageVersion")
        if "rules" in body:
            r["rules"] = body.get("rules")
    return "", 204


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/routingPolicies/<name>", methods=["DELETE"]
)
def delete_routing_policy(load_balancer_id, name):
    global ROUTING_POLICIES
    ROUTING_POLICIES = [r for r in ROUTING_POLICIES if r.get("name") != name]
    return "", 204


# Health endpoints


@load_balancer_bp.route("/loadBalancers/<load_balancer_id>/health", methods=["GET"])
def get_load_balancer_health(load_balancer_id):
    return oci_res(LOAD_BALANCER_HEALTH)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>/health",
    methods=["GET"],
)
def get_backend_set_health(load_balancer_id, backend_set_name):
    return oci_res(BACKEND_SET_HEALTH)


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/backendSets/<backend_set_name>/backends/<backend_name>/health",
    methods=["GET"],
)
def get_backend_health(load_balancer_id, backend_set_name, backend_name):
    return oci_res(BACKEND_HEALTH)


@load_balancer_bp.route("/loadBalancerHealths", methods=["GET"])
def list_lb_healths():
    compartment_id = request.args.get("compartmentId")
    items = HEALTH_SUMMARIES
    if compartment_id:
        items = [i for i in items if LB_ID]
    return oci_res(items)


# Work Requests


@load_balancer_bp.route(
    "/loadBalancers/<load_balancer_id>/workRequests", methods=["GET"]
)
def list_work_requests(load_balancer_id):
    return oci_res(WORK_REQUESTS)


@load_balancer_bp.route("/loadBalancerWorkRequests/<work_request_id>", methods=["GET"])
def get_work_request(work_request_id):
    wr = next((w for w in WORK_REQUESTS if w.get("id") == work_request_id), None)
    if not wr:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(wr)
