"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP


def plan_speech_policies_prompt(group_name: str, compartment_name: str) -> str:
    return f"""Prepare least-privilege OCI Speech policy guidance for
group `{group_name}` and compartment `{compartment_name}`. Read
`speech://guides/policies` and `speech://guides/service-limits`. Determine whether
the user needs transcription/customizations, Object Storage local workflows,
text-to-speech only, defined tags, or Events and Notifications. Produce only the
policy statements required for those capabilities, explain where an
administrator should create the policy, and leave all policy application to the
administrator. Do not use tenancy-wide or any-user scope unless the user
explicitly requests and acknowledges it."""


def register_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        name="plan_speech_policies",
        description="Prepare least-privilege Speech IAM policy statements for review.",
    )(plan_speech_policies_prompt)
