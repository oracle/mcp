"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Constants shared by the OCI Full Stack Disaster Recovery MCP server.
"""

from __future__ import annotations

import os

DEFAULT_PROFILE_1: str = os.getenv("FSDR_PROFILE_1", "FSDR_REGION1")
DEFAULT_PROFILE_2: str = os.getenv("FSDR_PROFILE_2", "FSDR_REGION2")

DEFAULT_OCI_CONFIG_FILE: str = os.path.expanduser(
    os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
)
DEFAULT_OCI_AUTH_TYPE: str = os.getenv("OCI_AUTH_TYPE", "api_key").lower()

FSDR_OPERATION_NAMES: tuple[str, ...] = (
    "create_automatic_dr_configuration",
    "get_automatic_dr_configuration",
    "list_automatic_dr_configurations",
    "update_automatic_dr_configuration",
    "delete_automatic_dr_configuration",
    "create_dr_protection_group",
    "get_dr_protection_group",
    "list_dr_protection_groups",
    "update_dr_protection_group",
    "delete_dr_protection_group",
    "change_dr_protection_group_compartment",
    "update_dr_protection_group_role",
    "associate_dr_protection_group",
    "disassociate_dr_protection_group",
    "create_dr_plan",
    "get_dr_plan",
    "list_dr_plans",
    "update_dr_plan",
    "delete_dr_plan",
    "refresh_dr_plan",
    "verify_dr_plan",
    "create_dr_plan_execution",
    "get_dr_plan_execution",
    "list_dr_plan_executions",
    "update_dr_plan_execution",
    "cancel_dr_plan_execution",
    "pause_dr_plan_execution",
    "resume_dr_plan_execution",
    "retry_dr_plan_execution",
    "ignore_dr_plan_execution",
    "delete_dr_plan_execution",
    "get_work_request",
    "list_work_requests",
    "list_work_request_errors",
    "list_work_request_logs",
    "cancel_work_request",
)

ALLOWED_FSDR_OPERATIONS: frozenset[str] = frozenset(FSDR_OPERATION_NAMES)
