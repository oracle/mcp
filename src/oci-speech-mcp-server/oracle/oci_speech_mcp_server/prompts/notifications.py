"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP


def setup_job_notifications_prompt(compartment_id: str) -> str:
    return f"""Set up notifications for OCI Speech jobs in compartment
`{compartment_id}`. Read `speech://guides/notifications`. Prefer an existing topic
when its OCID is supplied; otherwise create a clearly named topic. Create a
subscription only when both protocol and endpoint are explicit. Default to
completed and failed events, then report any confirmation or IAM follow-up."""


def register_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        name="setup_job_notifications",
        description="Set up completion and failure notifications.",
    )(setup_job_notifications_prompt)
