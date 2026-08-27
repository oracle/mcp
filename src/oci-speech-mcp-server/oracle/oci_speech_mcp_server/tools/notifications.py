"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import json
import logging
from typing import Any, Literal

import oci
from fastmcp import FastMCP

from ..models import EventType, OperationResult
from ..utils.clients import get_clients
from ..utils.responses import raise_safe, response_header, to_dict

logger = logging.getLogger(__name__)

DEFAULT_EVENT_TYPES: list[EventType] = [
    "com.oraclecloud.aiservicespeech.completedtranscriptionjob",
    "com.oraclecloud.aiservicespeech.failedtranscriptionjob",
]


def setup_transcription_notifications(
    compartment_id: str,
    rule_display_name: str,
    topic_id: str | None = None,
    topic_name: str | None = None,
    topic_description: str | None = None,
    subscription_protocol: Literal[
        "EMAIL", "HTTPS", "PAGERDUTY", "SLACK", "ORACLE_FUNCTIONS"
    ]
    | None = None,
    subscription_endpoint: str | None = None,
    event_types: list[EventType] | None = None,
    transcription_job_id: str | None = None,
    rule_description: str | None = None,
    freeform_tags: dict[str, str] | None = None,
) -> OperationResult:
    """Create or reuse a topic and create an Events rule for Speech job events."""
    if (topic_id is None) == (topic_name is None):
        raise ValueError("Provide exactly one of topic_id or topic_name.")
    if (subscription_protocol is None) != (subscription_endpoint is None):
        raise ValueError(
            "subscription_protocol and subscription_endpoint must be provided together."
        )
    selected_events = DEFAULT_EVENT_TYPES if event_types is None else event_types
    if not selected_events:
        raise ValueError("event_types must not be empty.")
    created: dict[str, Any] = {}
    notes: list[str] = []
    try:
        clients = get_clients()
        resolved_topic_id = topic_id
        if topic_name:
            topic_response = clients.notifications.create_topic(
                oci.ons.models.CreateTopicDetails(
                    compartment_id=compartment_id,
                    name=topic_name,
                    description=topic_description,
                    freeform_tags=freeform_tags,
                )
            )
            resolved_topic_id = topic_response.data.topic_id
            created["topic"] = to_dict(topic_response.data)

        if subscription_protocol and subscription_endpoint:
            subscription_response = clients.subscriptions.create_subscription(
                oci.ons.models.CreateSubscriptionDetails(
                    compartment_id=compartment_id,
                    topic_id=resolved_topic_id,
                    protocol=subscription_protocol,
                    endpoint=subscription_endpoint,
                    freeform_tags=freeform_tags,
                )
            )
            created["subscription"] = to_dict(subscription_response.data)
            if subscription_protocol == "EMAIL":
                notes.append(
                    "The email subscription remains PENDING until the recipient confirms it."
                )

        condition: dict[str, Any] = {"eventType": selected_events}
        if transcription_job_id:
            condition["data"] = {"resourceId": transcription_job_id}
        rule_response = clients.events.create_rule(
            oci.events.models.CreateRuleDetails(
                display_name=rule_display_name,
                description=rule_description,
                is_enabled=True,
                compartment_id=compartment_id,
                condition=json.dumps(condition, separators=(",", ":")),
                actions=oci.events.models.ActionDetailsList(
                    actions=[
                        oci.events.models.CreateNotificationServiceActionDetails(
                            is_enabled=True,
                            topic_id=resolved_topic_id,
                        )
                    ]
                ),
                freeform_tags=freeform_tags,
            )
        )
        created["rule"] = to_dict(rule_response.data)
        notes.append(
            "Ensure the OCI Events service can publish to the selected Notifications topic."
        )
        return OperationResult(
            operation="setup_transcription_notifications",
            data=created,
            status=getattr(rule_response, "status", None),
            opc_request_id=response_header(rule_response, "opc-request-id"),
            notes=notes,
        )
    except Exception as error:
        if created:
            logger.warning(
                "Notification setup stopped after creating: %s", ", ".join(created)
            )
        raise_safe("setup_transcription_notifications", error)


def register_tools(mcp: FastMCP) -> None:
    mcp.tool()(setup_transcription_notifications)
