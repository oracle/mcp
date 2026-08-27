"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

NOTIFICATIONS_GUIDE = """# Job notifications

`setup_transcription_notifications` can create or reuse an OCI Notifications
topic, optionally add a subscription, and create an OCI Events rule targeting
the topic. The default event filter covers completed and failed transcription
jobs. Supply a job OCID to narrow the rule to one job, or omit it for all jobs
in the compartment.

Email subscriptions remain PENDING until the recipient confirms them. Keep the
Events rule in the same region as the Speech jobs and ensure the Events service
is allowed to publish to the topic. The tool returns every created resource so
partial setup can be inspected and completed safely.
"""


def notifications_guide() -> str:
    return NOTIFICATIONS_GUIDE


def register_resources(mcp: FastMCP) -> None:
    mcp.resource(
        "speech://guides/notifications",
        description="OCI Events and Notifications workflow for transcription jobs.",
    )(notifications_guide)

