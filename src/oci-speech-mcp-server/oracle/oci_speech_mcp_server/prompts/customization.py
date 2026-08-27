"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP


def build_speech_customization_prompt(goal: str) -> str:
    return f"""Design an OCI Speech customization for: `{goal}`.
Read `speech://guides/customizations`. Extract candidate entity types, aliases,
entities, sounds-like forms, audio pronunciations, weights, and representative
reference sentences. Identify which lists should be newly populated and which
should reuse an existing customization by OCID or alias. Validate that every
reference placeholder matches an entity type. Present the proposed dataset and
expected reusable/contextual relationships for review before creating or
updating a customization, because that operation starts training."""


def register_prompts(mcp: FastMCP) -> None:
    mcp.prompt(
        name="build_speech_customization",
        description="Design a reviewed Speech customization dataset.",
    )(build_speech_customization_prompt)
