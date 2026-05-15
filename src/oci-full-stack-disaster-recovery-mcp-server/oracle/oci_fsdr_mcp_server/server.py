"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

OCI Full Stack Disaster Recovery MCP Server

Exposes OCI FSDR operations as MCP tools for MCP-aware clients.

The server is intentionally schema-agnostic: read operations are thin wrappers
over paginated list/get APIs, and all write operations go through a single
generic passthrough (`fsdr_raw_call`). Polymorphic SDK models (members,
execution options, log locations) are resolved at call time via a `_type`
discriminator in the payload, so new member types or plan execution types
never require server changes.

Environment variables:
  OCI_AUTH_TYPE      : "api_key" (default) or "security_token"
  OCI_CONFIG_FILE    : path to OCI config file (default: ~/.oci/config)
  FSDR_PROFILE_1     : profile for region 1 (default: FSDR_REGION1)
  FSDR_PROFILE_2     : profile for region 2 (default: FSDR_REGION2)
"""

from __future__ import annotations

import logging
import sys
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import oci
from oci.util import to_dict
from fastmcp import FastMCP
from pydantic import Field

from .auth import get_dr_client
from .consts import ALLOWED_FSDR_OPERATIONS, DEFAULT_PROFILE_1, DEFAULT_PROFILE_2
from .models import (
    DrPlanExecutionLifecycleState,
    DrPlanType,
    DrProtectionGroupLifecycleState,
    FsdrOperation,
    ListResult,
    OciResponseResult,
    WriteResult,
)

# ---------------------------------------------------------------------------
# Logging (stderr only -- never stdout, which would corrupt the MCP stream)
# ---------------------------------------------------------------------------

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
)
log = logging.getLogger("oci_fsdr_mcp")

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

_PROMPTS_DIR = Path(__file__).parent / "data" / "prompts"
_PROFILE_DESCRIPTION = (
    "OCI config profile for the target FSDR region. "
    f"Defaults to '{DEFAULT_PROFILE_1}'. Common profiles are "
    f"'{DEFAULT_PROFILE_1}' for region 1 and '{DEFAULT_PROFILE_2}' for region 2."
)

mcp = FastMCP(
    name="oci-fsdr-mcp-server",
    instructions=(
        "Tools for OCI Full Stack Disaster Recovery (FSDR). "
        f"Two region profiles are available: '{DEFAULT_PROFILE_1}' (region 1) and "
        f"'{DEFAULT_PROFILE_2}' (region 2). "
        "All tools accept a 'profile' parameter to target the desired region -- "
        f"defaults to '{DEFAULT_PROFILE_1}' when omitted. "
        "Read tools (list_*/get_*) return data directly. "
        "All mutations go through `fsdr_raw_call`, which invokes any "
        "DisasterRecoveryClient method by name. For polymorphic payloads "
        "(DRPG members, execution options, log locations), include a `_type` "
        "key naming the exact SDK model class -- e.g. "
        "`_type`: 'UpdateDrProtectionGroupMemberDatabaseDetails'. "
        "Use the built-in prompts for guided workflows: "
        "check_dr_status, setup_drpg_pair, run_switchover, run_drill, "
        "run_failover, plan_refresh_workflow, add_members."
    ),
)

# ---------------------------------------------------------------------------
# Request tracking decorator
# ---------------------------------------------------------------------------


def _tool_logger(func: Callable) -> Callable:
    """Log each tool call with a short request ID for correlation."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        req_id = uuid.uuid4().hex[:8]
        log_context: Dict[str, Any] = {
            "operation": kwargs.get("operation"),
            "profile": kwargs.get("profile"),
            "kwargs": sorted(kwargs),
        }
        if isinstance(kwargs.get("parameters"), dict):
            log_context["parameter_keys"] = sorted(kwargs["parameters"])
        log.info("[%s] %s called context=%s", req_id, func.__name__, log_context)
        try:
            result = func(*args, **kwargs)
            log.info("[%s] %s succeeded", req_id, func.__name__)
            return result
        except Exception as exc:
            log.error("[%s] %s failed: %s", req_id, func.__name__, exc)
            raise
    return wrapper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _response_to_result(response: oci.response.Response) -> OciResponseResult:
    data = response.data
    return OciResponseResult(
        data=to_dict(data) if data is not None else None,
        status=response.status,
        headers=dict(response.headers or {}),
    )


def _resolve_model(value: Any) -> Any:
    """Recursively turn dicts carrying `_type` into OCI SDK model instances.

    A dict with a `_type: "SomeClassName"` entry is instantiated as
    `oci.disaster_recovery.models.SomeClassName(**rest)`. Dicts without
    `_type` and all other values are returned unchanged (but still recursed
    into). This lets callers describe polymorphic payloads -- e.g. DRPG
    members, execution options -- without the server needing to know any
    specific type.
    """
    if isinstance(value, dict):
        if "_type" in value:
            rest = {k: v for k, v in value.items() if k != "_type"}
            type_name = value["_type"]
            model_cls = getattr(oci.disaster_recovery.models, type_name, None)
            if model_cls is None:
                raise ValueError(
                    f"Unknown oci.disaster_recovery.models class: '{type_name}'"
                )
            return model_cls(**{k: _resolve_model(v) for k, v in rest.items()})
        return {k: _resolve_model(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_model(v) for v in value]
    return value

# ---------------------------------------------------------------------------
# Guided workflow prompts
# ---------------------------------------------------------------------------


def _load_prompt(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


@mcp.prompt()
def setup_drpg_pair() -> str:
    """Step-by-step guide to create and associate a PRIMARY/STANDBY DRPG pair across two regions."""
    return _load_prompt("setup_drpg_pair.md")


@mcp.prompt()
def check_dr_status() -> str:
    """Read-only guide to inspect DRPG state, plan health, execution history, and work requests."""
    return _load_prompt("check_dr_status.md")


@mcp.prompt()
def run_switchover() -> str:
    """Guide for a planned Switchover — reverses PRIMARY/STANDBY roles; both regions must be up."""
    return _load_prompt("run_switchover.md")


@mcp.prompt()
def run_drill() -> str:
    """Guide to run a DR Drill (START_DRILL then STOP_DRILL) — roles do NOT change, test only."""
    return _load_prompt("run_drill.md")


@mcp.prompt()
def run_failover() -> str:
    """Guide for an emergency Failover when primary is down, including mandatory post-failover reset."""
    return _load_prompt("run_failover.md")


@mcp.prompt()
def plan_refresh_workflow() -> str:
    """Guide to refresh DR plans after adding or removing DRPG members."""
    return _load_prompt("plan_refresh_workflow.md")


@mcp.prompt()
def add_members() -> str:
    """Guide to add compute, database, and other resources to a DRPG."""
    return _load_prompt("add_members.md")

# ---------------------------------------------------------------------------
# Read tools
# ---------------------------------------------------------------------------


@mcp.tool()
@_tool_logger
def list_dr_protection_groups(
    compartment_id: str = Field(
        ..., description="The OCID of the compartment containing DR Protection Groups."
    ),
    lifecycle_state: Optional[DrProtectionGroupLifecycleState] = Field(
        None, description="Optional DR Protection Group lifecycle state filter."
    ),
    limit: int = Field(
        50, description="Maximum number of DR Protection Groups to return.", ge=1, le=1000
    ),
    page: Optional[str] = Field(
        None, description="Opaque opc-next-page token returned by a previous list call."
    ),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> ListResult:
    """
    List DR Protection Groups (DRPGs) in a compartment.

    Args:
        compartment_id: OCID of the compartment.
        lifecycle_state: Optional filter e.g. "ACTIVE". If None, all states returned.
        limit: Max items per page (default 50).
        page: opc-next-page token for pagination.
        profile: OCI config profile for the target region. Defaults to FSDR_REGION1.

    Returns:
        { "items": [...], "opc_next_page": "...", "total_items": N }
    """
    resp = get_dr_client(profile).list_dr_protection_groups(
        compartment_id=compartment_id,
        lifecycle_state=lifecycle_state,
        limit=limit,
        page=page,
    )
    items = [to_dict(pg) for pg in resp.data.items]
    return ListResult.from_items(items, resp.headers.get("opc-next-page"))


@mcp.tool()
@_tool_logger
def list_dr_plans_for_protection_group(
    dr_protection_group_id: str = Field(
        ..., description="The OCID of the DR Protection Group that owns the plans."
    ),
    display_name: Optional[str] = Field(
        None, description="Optional display name filter for DR Plans."
    ),
    plan_type: Optional[DrPlanType] = Field(
        None,
        description="Optional DR Plan type filter, such as SWITCHOVER or FAILOVER.",
    ),
    limit: int = Field(
        50, description="Maximum number of DR Plans to return.", ge=1, le=1000
    ),
    page: Optional[str] = Field(
        None, description="Opaque opc-next-page token returned by a previous list call."
    ),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> ListResult:
    """
    List DR Plans for a DR Protection Group.

    Args:
        dr_protection_group_id: OCID of the DR Protection Group.
        display_name: Optional filter by display name.
        plan_type: Optional filter -- "SWITCHOVER", "FAILOVER", "START_DRILL", "STOP_DRILL".
        limit: Max items per page (default 50).
        page: opc-next-page token for pagination.
        profile: OCI config profile for the target region.

    Returns:
        { "items": [...], "opc_next_page": "...", "total_items": N }
    """
    resp = get_dr_client(profile).list_dr_plans(
        dr_protection_group_id=dr_protection_group_id,
        display_name=display_name,
        dr_plan_type=plan_type,
        limit=limit,
        page=page,
    )
    items = [to_dict(p) for p in resp.data.items]
    return ListResult.from_items(items, resp.headers.get("opc-next-page"))


@mcp.tool()
@_tool_logger
def list_dr_plan_executions_for_protection_group(
    dr_protection_group_id: str = Field(
        ...,
        description="The OCID of the DR Protection Group that owns the plan executions.",
    ),
    lifecycle_state: Optional[DrPlanExecutionLifecycleState] = Field(
        None, description="Optional DR Plan Execution lifecycle state filter."
    ),
    limit: int = Field(
        50, description="Maximum number of DR Plan Executions to return.", ge=1, le=1000
    ),
    page: Optional[str] = Field(
        None, description="Opaque opc-next-page token returned by a previous list call."
    ),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> ListResult:
    """
    List DR Plan Executions for a DR Protection Group.

    Args:
        dr_protection_group_id: OCID of the DR Protection Group.
        lifecycle_state: Optional lifecycle state filter.
        limit: Max items per page (default 50).
        page: opc-next-page token for pagination.
        profile: OCI config profile for the target region.

    Returns:
        { "items": [...], "opc_next_page": "...", "total_items": N }
    """
    resp = get_dr_client(profile).list_dr_plan_executions(
        dr_protection_group_id=dr_protection_group_id,
        lifecycle_state=lifecycle_state,
        limit=limit,
        page=page,
    )
    items = [to_dict(e) for e in resp.data.items]
    return ListResult.from_items(items, resp.headers.get("opc-next-page"))


@mcp.tool()
@_tool_logger
def get_dr_protection_group(
    dr_protection_group_id: str = Field(
        ..., description="The OCID of the DR Protection Group to retrieve."
    ),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> OciResponseResult:
    """
    Get details of a DR Protection Group.

    Args:
        dr_protection_group_id: OCID of the DR Protection Group.
        profile: OCI config profile for the target region.
    """
    resp = get_dr_client(profile).get_dr_protection_group(dr_protection_group_id)
    return _response_to_result(resp)


@mcp.tool()
@_tool_logger
def get_dr_plan(
    dr_plan_id: str = Field(..., description="The OCID of the DR Plan to retrieve."),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> OciResponseResult:
    """
    Get details of a DR Plan.

    Args:
        dr_plan_id: OCID of the DR Plan.
        profile: OCI config profile for the target region.
    """
    resp = get_dr_client(profile).get_dr_plan(dr_plan_id)
    return _response_to_result(resp)


@mcp.tool()
@_tool_logger
def get_dr_plan_execution(
    dr_plan_execution_id: str = Field(
        ..., description="The OCID of the DR Plan Execution to retrieve."
    ),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> OciResponseResult:
    """
    Get details of a DR Plan Execution.

    Args:
        dr_plan_execution_id: OCID of the DR Plan Execution.
        profile: OCI config profile for the target region.
    """
    resp = get_dr_client(profile).get_dr_plan_execution(dr_plan_execution_id)
    return _response_to_result(resp)


@mcp.tool()
@_tool_logger
def get_work_request(
    work_request_id: str = Field(
        ..., description="The OCID of the OCI work request to retrieve."
    ),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> OciResponseResult:
    """
    Get details of a Work Request (tracks async operations).

    Args:
        work_request_id: OCID of the Work Request.
        profile: OCI config profile for the target region.
    """
    resp = get_dr_client(profile).get_work_request(work_request_id)
    return _response_to_result(resp)

@mcp.tool()
@_tool_logger
def fsdr_raw_call(
    operation: FsdrOperation = Field(
        ...,
        description=(
            "Allowed DisasterRecoveryClient method name to invoke. Use read tools "
            "first, then call this for approved FSDR changes."
        ),
    ),
    parameters: Dict[str, Any] = Field(
        ...,
        description=(
            "Keyword arguments for the OCI SDK operation. Use *_details dicts for "
            "request bodies and `_type` for polymorphic nested OCI SDK models."
        ),
    ),
    profile: str = Field(DEFAULT_PROFILE_1, description=_PROFILE_DESCRIPTION),
) -> WriteResult:
    """
    Invoke any OCI Full Stack Disaster Recovery API by DisasterRecoveryClient
    method name. This is the single entry point for all mutations -- CREATE,
    UPDATE, DELETE, associate, execute, refresh, cancel, etc.

    WARNING: Live, potentially irreversible operations. The caller is
    responsible for previewing parameters with the user before invoking
    write operations -- this tool does not implement a dry-run mode.

    Parameter construction rules:

    1. Any `*_details` parameter whose value is a dict is converted to the
       matching SDK model class by naming convention -- e.g.
       `create_dr_protection_group_details` -> CreateDrProtectionGroupDetails.

    2. For polymorphic nested payloads (DRPG members, execution options,
       log locations, etc.) include a `_type` key naming the exact SDK
       model class. The tool recurses into dicts and lists and instantiates
       any dict with a `_type` key as that class. Examples:

         "members": [
           {"_type": "UpdateDrProtectionGroupMemberDatabaseDetails",
            "member_id": "ocid1.database..."},
           {"_type": "UpdateDrProtectionGroupMemberComputeInstanceMovableDetails",
            "member_id": "ocid1.instance..."}
         ]

         "execution_options": {
           "_type": "SwitchoverExecutionOptionDetails",
           "are_prechecks_enabled": true,
           "are_warnings_ignored": false
         }

         "log_location": {
           "_type": "CreateObjectStorageLogLocationDetails",
           "bucket": "dr-logs",
           "namespace": "mytenancy"
         }

       Refer to the `oci.disaster_recovery.models` module for the full set
       of available class names.

    Args:
        operation: DisasterRecoveryClient method name e.g.
            "create_dr_protection_group", "update_dr_protection_group",
            "associate_dr_protection_group", "create_dr_plan_execution".
        parameters: Keyword arguments for the SDK method.
        profile: OCI config profile for the target region. Defaults to FSDR_REGION1.

    Returns:
        {
          "data": ...,
          "status": 200,
          "headers": {...},
          "work_request_id": "..."  # present when the response carries one
        }
    """
    if operation not in ALLOWED_FSDR_OPERATIONS:
        raise ValueError(
            f"Unsupported operation '{operation}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_FSDR_OPERATIONS))}"
        )

    client = get_dr_client(profile)
    func = getattr(client, operation)

    converted: Dict[str, Any] = {}
    for key, value in parameters.items():
        resolved = _resolve_model(value)
        if key.endswith("_details") and isinstance(resolved, dict):
            parts = key.split("_")[:-1]
            class_name = "".join(p.capitalize() for p in parts) + "Details"
            model_cls = getattr(oci.disaster_recovery.models, class_name, None)
            if model_cls is not None:
                resolved = model_cls(**resolved)
        converted[key] = resolved

    resp = func(**converted)
    result = _response_to_result(resp)
    work_request_id = resp.headers.get("opc-work-request-id") if resp.headers else None
    return WriteResult(
        data=result.data,
        status=result.status,
        headers=result.headers,
        work_request_id=work_request_id,
    )

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for uvx / installed scripts.

    MCP stdio uses stdout for JSON-RPC messages. Application logs are
    configured above to use stderr so they do not corrupt the protocol stream.
    """
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
