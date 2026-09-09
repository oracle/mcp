"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

The three guidance tools. They return static prompt text read from the ``prompts``
directory at import and never reach the network -- which is what
``_LOCAL_GUIDANCE_TOOL`` tells an MCP host.
"""

from pathlib import Path


# Database Service models and mappers

from . import (
    telemetry,
)
from .app import mcp, _LOCAL_GUIDANCE_TOOL


_PROMPTS_DIR = Path(__file__).parent / "data" / "prompts"


OCI_RECOVERY_SERVICE_DASHBOARD_PROMPT = (
    _PROMPTS_DIR / "oci_recovery_service_dashboard.txt"
).read_text(encoding="utf-8")


ONBOARD_DATABASE_TO_RECOVERY_SERVICE_PROMPT = (
    _PROMPTS_DIR / "onboard_database_to_recovery_service.txt"
).read_text(encoding="utf-8")


DIAGNOSE_RECOVERY_SERVICE_ISSUE_PROMPT = (
    _PROMPTS_DIR / "diagnose_recovery_service_issue.txt"
).read_text(encoding="utf-8")


@mcp.tool(
    annotations=_LOCAL_GUIDANCE_TOOL,
    description=(
        "Returns dashboard-generation guidance for OCI Recovery Service, including "
        "cloud-protected databases."
    )
)
@telemetry._tool_logger("oci_recovery_service_dashboard_prompt")
def oci_recovery_service_dashboard_prompt() -> str:
    """Return dashboard-generation guidance as a tool for clients without prompt support."""
    return OCI_RECOVERY_SERVICE_DASHBOARD_PROMPT


@mcp.tool(
    annotations=_LOCAL_GUIDANCE_TOOL,
    description=(
        "Always call this tool first when a user asks to onboard, protect, enable Recovery Service backups for, or register a database to Recovery Service. The tool first determines and verifies whether the target database is OCI DBaaS or purely on-premises, retrieves the latest Oracle requirements, and performs only the read-only prerequisite checks appropriate for that deployment type. For OCI DBaaS, it configures DBRS automatic backups using the current UpdateDatabase / DbBackupConfig contract, then independently verifies the protected database, assigned policy, health status, and initial backup. For on-premises databases, it proceeds with the Cloud Protect workflow only after the deployment type has been verified and the required approval has been obtained."
    )
)
@telemetry._tool_logger("onboard_database_to_recovery_service")
def onboard_database_to_recovery_service() -> str:
    """Return database onboarding guidance as a tool for clients without prompt support."""
    return ONBOARD_DATABASE_TO_RECOVERY_SERVICE_PROMPT


@mcp.tool(
    annotations=_LOCAL_GUIDANCE_TOOL,
    description=(
        "Use this tool first whenever the user's underlying goal is to investigate, explain, or assess the health of Oracle Database backup, protection, or recoverability in an environment using Recovery Service. This includes explicit failures as well as implicit concerns such as unexpected backup behavior, stale or missing backups, protection lag, missing recovery points, restore/PITR problems, policy or retention behavior, RMAN issues, or questions about whether a protected database is healthy and recoverable. Also use it when the user asks whether anything is wrong with the protection environment, even without reporting an error. The tool provides an evidence-driven, access-first diagnostic workflow that traces the actual execution path, acquires relevant evidence, tests competing root-cause hypotheses, independently assesses recoverability, and guides safe remediation and verification. Do not use it for general database questions unrelated to backup, recovery, protection, or recoverability."
    )
)
@telemetry._tool_logger("diagnose_recovery_service_issue")
def diagnose_recovery_service_issue() -> str:
    """Return Recovery Service diagnostic guidance as a tool for clients without prompt support."""
    return DIAGNOSE_RECOVERY_SERVICE_ISSUE_PROMPT
