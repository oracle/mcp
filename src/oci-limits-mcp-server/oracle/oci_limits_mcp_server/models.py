"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import oci


# ----------------------------
# Mappers to stable dict shapes
# ----------------------------
def map_service_summary(svc: "oci.limits.models.ServiceSummary") -> dict:
    """Map OCI ServiceSummary to a stable dict shape used by our tools."""
    return {
        "name": getattr(svc, "name", None),
        "description": getattr(svc, "description", None),
        "supported_subscriptions": getattr(svc, "supported_subscriptions", None),
    }


def map_limit_definition_summary(
    defn: "oci.limits.models.LimitDefinitionSummary",
) -> dict:
    """Map OCI LimitDefinitionSummary to a stable dict shape used by our tools."""
    return {
        "name": getattr(defn, "name", None),
        "serviceName": getattr(defn, "service_name", None),
        "description": getattr(defn, "description", None),
        "scopeType": getattr(defn, "scope_type", None),
        "areQuotasSupported": getattr(defn, "are_quotas_supported", None),
        "isResourceAvailabilitySupported": getattr(
            defn, "is_resource_availability_supported", None
        ),
        "isDeprecated": getattr(defn, "is_deprecated", None),
        "isEligibleForLimitIncrease": getattr(
            defn, "is_eligible_for_limit_increase", None
        ),
        "isDynamic": getattr(defn, "is_dynamic", None),
        "externalLocationSupportedSubscriptions": getattr(
            defn, "external_location_supported_subscriptions", None
        ),
        "supportedSubscriptions": getattr(defn, "supported_subscriptions", None),
        "supportedQuotaFamilies": getattr(defn, "supported_quota_families", None),
    }


def map_limit_value_summary(val: "oci.limits.models.LimitValueSummary") -> dict:
    """Map OCI LimitValueSummary to a stable dict shape used by our tools."""
    return {
        "name": getattr(val, "name", None),
        "scopeType": getattr(val, "scope_type", None),
        "availabilityDomain": getattr(val, "availability_domain", None),
        "value": getattr(val, "value", None),
    }


def map_resource_availability(ra: "oci.limits.models.ResourceAvailability") -> dict:
    """Map OCI ResourceAvailability to a stable dict shape used by our tools."""
    return {
        "used": getattr(ra, "used", None),
        "available": getattr(ra, "available", None),
        "fractionalUsage": getattr(ra, "fractional_usage", None),
        "fractionalAvailability": getattr(ra, "fractional_availability", None),
        "effectiveQuotaValue": getattr(ra, "effective_quota_value", None),
    }


__all__ = [
    "map_service_summary",
    "map_limit_definition_summary",
    "map_limit_value_summary",
    "map_resource_availability",
]
