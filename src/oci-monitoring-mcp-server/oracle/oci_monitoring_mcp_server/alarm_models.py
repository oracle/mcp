"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import oci
from pydantic import BaseModel, Field

SeverityType = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "UNKNOWN_ENUM_VALUE"]


class Suppression(BaseModel):
    """
    Pydantic model mirroring oci.monitoring.models.Suppression.
    """

    description: Optional[str] = Field(None, description="Human-readable description of the suppression.")
    time_suppress_from: Optional[datetime] = Field(
        None, description="The start time for the suppression (RFC3339)."
    )
    time_suppress_until: Optional[datetime] = Field(
        None, description="The end time for the suppression (RFC3339)."
    )


def map_suppression(s: oci.monitoring.models.Suppression | None) -> Suppression | None:
    if not s:
        return None
    return Suppression(
        description=getattr(s, "description", None),
        time_suppress_from=getattr(s, "time_suppress_from", None) or getattr(s, "timeSuppressFrom", None),
        time_suppress_until=getattr(s, "time_suppress_until", None) or getattr(s, "timeSuppressUntil", None),
    )


class AlarmOverride(BaseModel):
    """
    Pydantic model mirroring (a subset of) oci.monitoring.models.AlarmOverride.
    Each override can specify values for query, severity, body, and pending duration.
    """

    rule_name: Optional[str] = Field(
        None,
        description="Identifier of the alarm's base/override values. Default is 'BASE'.",
    )
    query: Optional[str] = Field(None, description="MQL expression override for this rule.")
    severity: Optional[SeverityType] = Field(None, description="Severity override for this rule.")
    body: Optional[str] = Field(None, description="Message body override (alarm body).")
    pending_duration: Optional[str] = Field(
        None,
        description="Override for pending duration as ISO 8601 duration (e.g., 'PT5M').",
    )


def map_alarm_override(
    o: oci.monitoring.models.AlarmOverride | None,
) -> AlarmOverride | None:
    if not o:
        return None
    return AlarmOverride(
        rule_name=getattr(o, "rule_name", None) or getattr(o, "ruleName", None),
        query=getattr(o, "query", None),
        severity=getattr(o, "severity", None),
        body=getattr(o, "body", None),
        pending_duration=getattr(o, "pending_duration", None) or getattr(o, "pendingDuration", None),
    )


def map_alarm_overrides(items) -> list[AlarmOverride] | None:
    if not items:
        return None
    result: list[AlarmOverride] = []
    for it in items:
        mapped = map_alarm_override(it)
        if mapped is not None:
            result.append(mapped)
    return result if result else None


class AlarmSummary(BaseModel):
    """
    Pydantic model mirroring (a subset of) oci.monitoring.models.AlarmSummary.
    """

    id: Optional[str] = Field(None, description="The OCID of the alarm.")
    display_name: Optional[str] = Field(
        None,
        description="A user-friendly name for the alarm; used as title in notifications.",
    )
    compartment_id: Optional[str] = Field(
        None, description="The OCID of the compartment containing the alarm."
    )
    metric_compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the metric evaluated by the alarm.",
    )
    namespace: Optional[str] = Field(None, description="The source service/application emitting the metric.")
    query: Optional[str] = Field(
        None,
        description="The Monitoring Query Language (MQL) expression to evaluate for the alarm.",
    )
    severity: Optional[SeverityType] = Field(
        None,
        description="The perceived type of response required when the alarm is FIRING.",
    )
    destinations: Optional[List[str]] = Field(
        None,
        description="List of destination OCIDs for alarm notifications (e.g., NotificationTopic).",
    )
    suppression: Optional[Suppression] = Field(
        None, description="Configuration details for suppressing an alarm."
    )
    is_enabled: Optional[bool] = Field(None, description="Whether the alarm is enabled.")
    is_notifications_per_metric_dimension_enabled: Optional[bool] = Field(
        None,
        description="Whether the alarm sends a separate message for each metric stream.",
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Simple key/value pair tags applied without predefined names."
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None, description="Defined tags for this resource, scoped to namespaces."
    )
    lifecycle_state: Optional[str] = Field(None, description="The current lifecycle state of the alarm.")
    overrides: Optional[List[AlarmOverride]] = Field(
        None,
        description="Overrides controlling alarm evaluations (query, severity, body, pending duration).",
    )
    rule_name: Optional[str] = Field(
        None,
        description="Identifier of the alarm’s base values when overrides are present; default 'BASE'.",
    )
    notification_version: Optional[str] = Field(
        None,
        description="Version of the alarm notification to be delivered (e.g., '1.X').",
    )
    notification_title: Optional[str] = Field(
        None,
        description="Customizable notification title used as subject/title in messages.",
    )
    evaluation_slack_duration: Optional[str] = Field(
        None,
        description="Slack period for metric ingestion before evaluating the alarm, ISO 8601 (e.g., 'PT3M').",
    )
    alarm_summary: Optional[str] = Field(
        None,
        description="Customizable alarm summary (message body) with optional dynamic variables.",
    )
    resource_group: Optional[str] = Field(
        None,
        description="Resource group to match for metrics used by this alarm.",
    )


def map_alarm_summary(
    alarm: oci.monitoring.models.AlarmSummary,
) -> AlarmSummary:
    """
    Convert an oci.monitoring.models.AlarmSummary to
    oracle.oci_monitoring_mcp_server.alarms.models.AlarmSummary, including nested types.
    """
    return AlarmSummary(
        id=getattr(alarm, "id", None),
        display_name=getattr(alarm, "display_name", None) or getattr(alarm, "displayName", None),
        compartment_id=getattr(alarm, "compartment_id", None) or getattr(alarm, "compartmentId", None),
        metric_compartment_id=getattr(alarm, "metric_compartment_id", None)
        or getattr(alarm, "metricCompartmentId", None),
        namespace=getattr(alarm, "namespace", None),
        query=getattr(alarm, "query", None),
        severity=getattr(alarm, "severity", None),
        destinations=getattr(alarm, "destinations", None),
        suppression=map_suppression(getattr(alarm, "suppression", None)),
        is_enabled=getattr(alarm, "is_enabled", None) or getattr(alarm, "isEnabled", None),
        is_notifications_per_metric_dimension_enabled=getattr(
            alarm, "is_notifications_per_metric_dimension_enabled", None
        )
        or getattr(alarm, "isNotificationsPerMetricDimensionEnabled", None),
        freeform_tags=getattr(alarm, "freeform_tags", None) or getattr(alarm, "freeformTags", None),
        defined_tags=getattr(alarm, "defined_tags", None) or getattr(alarm, "definedTags", None),
        lifecycle_state=getattr(alarm, "lifecycle_state", None) or getattr(alarm, "lifecycleState", None),
        overrides=map_alarm_overrides(getattr(alarm, "overrides", None)),
        rule_name=getattr(alarm, "rule_name", None) or getattr(alarm, "ruleName", None),
        notification_version=getattr(alarm, "notification_version", None)
        or getattr(alarm, "notificationVersion", None),
        notification_title=getattr(alarm, "notification_title", None)
        or getattr(alarm, "notificationTitle", None),
        evaluation_slack_duration=getattr(alarm, "evaluation_slack_duration", None)
        or getattr(alarm, "evaluationSlackDuration", None),
        alarm_summary=getattr(alarm, "alarm_summary", None) or getattr(alarm, "alarmSummary", None),
        resource_group=getattr(alarm, "resource_group", None) or getattr(alarm, "resourceGroup", None),
    )
