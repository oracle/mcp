"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from _common import oci_res
from flask import Blueprint, jsonify, request
from jms_data import (
    FLEET_ADVANCED_FEATURE_CONFIGURATIONS,
    FLEET_AGENT_CONFIGURATIONS,
    FLEETS,
    INSTALLATION_SITES,
    JMS_PLUGINS,
    MANAGED_INSTANCE_USAGE,
    RESOURCE_INVENTORY,
)

jms_bp = Blueprint("jms", __name__, url_prefix="/20210610")


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


def _find_fleet(fleet_id):
    return next((fleet for fleet in FLEETS if fleet.get("id") == fleet_id), None)


def _find_plugin(plugin_id):
    return next((plugin for plugin in JMS_PLUGINS if plugin.get("id") == plugin_id), None)


@jms_bp.route("/fleets", methods=["GET"])
def list_fleets():
    items = FLEETS

    compartment_id = request.args.get("compartmentId")
    if compartment_id:
        items = [item for item in items if item.get("compartmentId") == compartment_id]

    fleet_id = request.args.get("id")
    if fleet_id:
        items = [item for item in items if item.get("id") == fleet_id]

    lifecycle_state = request.args.get("lifecycleState")
    if lifecycle_state:
        items = [item for item in items if item.get("lifecycleState") == lifecycle_state]

    display_name = request.args.get("displayName")
    if display_name:
        items = [item for item in items if item.get("displayName") == display_name]

    display_name_contains = request.args.get("displayNameContains")
    if display_name_contains:
        needle = display_name_contains.lower()
        items = [item for item in items if needle in item.get("displayName", "").lower()]

    return oci_res({"items": _apply_limit(items)})


@jms_bp.route("/fleets/<fleet_id>", methods=["GET"])
def get_fleet(fleet_id):
    fleet = _find_fleet(fleet_id)
    if not fleet:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(fleet)


@jms_bp.route("/jmsPlugins", methods=["GET"])
def list_jms_plugins():
    items = JMS_PLUGINS

    compartment_id = request.args.get("compartmentId")
    if compartment_id:
        items = [item for item in items if item.get("compartmentId") == compartment_id]

    fleet_id = request.args.get("fleetId")
    if fleet_id:
        items = [item for item in items if item.get("fleetId") == fleet_id]

    plugin_id = request.args.get("id")
    if plugin_id:
        items = [item for item in items if item.get("id") == plugin_id]

    lifecycle_state = request.args.get("lifecycleState")
    if lifecycle_state:
        items = [item for item in items if item.get("lifecycleState") == lifecycle_state]

    hostname_contains = request.args.get("hostnameContains")
    if hostname_contains:
        needle = hostname_contains.lower()
        items = [item for item in items if needle in item.get("hostname", "").lower()]

    return oci_res({"items": _apply_limit(items)})


@jms_bp.route("/jmsPlugins/<jms_plugin_id>", methods=["GET"])
def get_jms_plugin(jms_plugin_id):
    plugin = _find_plugin(jms_plugin_id)
    if not plugin:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(plugin)


@jms_bp.route("/fleets/<fleet_id>/installationSites", methods=["GET"])
def list_installation_sites(fleet_id):
    if not _find_fleet(fleet_id):
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404

    items = INSTALLATION_SITES.get(fleet_id, [])

    managed_instance_id = request.args.get("managedInstanceId")
    if managed_instance_id:
        items = [item for item in items if item.get("managedInstanceId") == managed_instance_id]

    path_contains = request.args.get("pathContains")
    if path_contains:
        needle = path_contains.lower()
        items = [item for item in items if needle in item.get("path", "").lower()]

    jre_version = request.args.get("jreVersion")
    if jre_version:
        items = [item for item in items if item.get("jre", {}).get("version") == jre_version]

    return oci_res({"items": _apply_limit(items)})


@jms_bp.route("/fleets/<fleet_id>/agentConfiguration", methods=["GET"])
def get_fleet_agent_configuration(fleet_id):
    if not _find_fleet(fleet_id):
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    config = FLEET_AGENT_CONFIGURATIONS.get(fleet_id)
    if not config:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(config)


@jms_bp.route("/fleets/<fleet_id>/advancedFeatureConfiguration", methods=["GET"])
def get_fleet_advanced_feature_configuration(fleet_id):
    if not _find_fleet(fleet_id):
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    config = FLEET_ADVANCED_FEATURE_CONFIGURATIONS.get(fleet_id)
    if not config:
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404
    return oci_res(config)


@jms_bp.route("/summarizeResourceInventory", methods=["GET"])
def summarize_resource_inventory():
    compartment_id = request.args.get("compartmentId")
    if compartment_id and compartment_id != "ocid1.tenancy.oc1..mock":
        return oci_res(
            {
                "activeFleetCount": 0,
                "managedInstanceCount": 0,
                "jreCount": 0,
                "installationCount": 0,
                "applicationCount": 0,
            }
        )
    return oci_res(RESOURCE_INVENTORY)


@jms_bp.route("/fleets/<fleet_id>/actions/summarizeManagedInstanceUsage", methods=["GET"])
def summarize_managed_instance_usage(fleet_id):
    if not _find_fleet(fleet_id):
        return jsonify({"code": "NotAuthorizedOrNotFound"}), 404

    items = MANAGED_INSTANCE_USAGE.get(fleet_id, [])

    managed_instance_id = request.args.get("managedInstanceId")
    if managed_instance_id:
        items = [item for item in items if item.get("managedInstanceId") == managed_instance_id]

    hostname_contains = request.args.get("hostnameContains")
    if hostname_contains:
        needle = hostname_contains.lower()
        items = [item for item in items if needle in item.get("hostname", "").lower()]

    return oci_res({"items": _apply_limit(items)})
