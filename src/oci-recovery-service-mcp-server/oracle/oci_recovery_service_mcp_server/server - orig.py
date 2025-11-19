#!/usr/bin/env python3
"""
OCI MCP Server
- Tools for Compute / DB / Object Storage discovery and simple actions
- Resource providers (e.g., compartments)
- A prompt for summarizing findings

Transports: stdio (default)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# MCP (official Python SDK)
from mcp.server.fastmcp import FastMCP

# OCI SDK
import oci
from oci.util import to_dict

# Local models
from models import Compartment, ProtectedDatabase, TenancyCostSummary

# ---------- Logging & env ----------
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("oci-mcp")


# ---------- OCI helper ----------

class OCIManager:
    """Simple manager to create OCI clients using ~/.oci/config or env-based auth."""

    def __init__(self) -> None:
        self.config = self._load_config()
        self.signer = None  # for instance principals etc.

    def _load_config(self) -> Dict[str, Any]:
        # Prefer config file if present
        cfg_file = os.getenv("OCI_CONFIG_FILE", os.path.expanduser("~/.oci/config"))
        profile = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
        if os.path.exists(cfg_file):
            log.info(f"Using OCI config file: {cfg_file} [{profile}]")
            return oci.config.from_file(cfg_file, profile_name=profile)

        # Else try explicit env vars
        env_keys = (
            "OCI_USER_OCID",
            "OCI_FINGERPRINT",
            "OCI_TENANCY_OCID",
            "OCI_REGION",
            "OCI_KEY_FILE",
        )
        if all(os.getenv(k) for k in env_keys):
            cfg = {
                "user": os.environ["OCI_USER_OCID"],
                "fingerprint": os.environ["OCI_FINGERPRINT"],
                "tenancy": os.environ["OCI_TENANCY_OCID"],
                "region": os.environ["OCI_REGION"],
                "key_file": os.environ["OCI_KEY_FILE"],
            }
            log.info("Using explicit OCI env var configuration")
            return cfg

        # Finally, try instance principals (for servers running on OCI)
        try:
            self.signer = oci.auth.signers.get_resource_principals_signer()
            region = os.getenv("OCI_REGION", "ap-ashburn-1")
            cfg = {"region": region, "tenancy": os.getenv("OCI_TENANCY_OCID", "")}
            log.info("Using instance/resource principals signer")
            return cfg
        except Exception:
            raise RuntimeError(
                "No OCI credentials found. Run `oci setup config` or set env vars "
                "(OCI_USER_OCID, OCI_FINGERPRINT, OCI_TENANCY_OCID, OCI_REGION, OCI_KEY_FILE)."
            )

    def get_client(self, service: str):
        """Return an OCI service client bound to configured region/signer."""
        service = service.lower()
        kwargs: Dict[str, Any] = {}
        if self.signer:
            kwargs["signer"] = self.signer

        if service in ("identity", "iam"):
            return oci.identity.IdentityClient(self.config, **kwargs)
        if service in ("recovery", "ars", "rcv", "zrcv"):
            return oci.recovery.DatabaseRecoveryClient(self.config, **kwargs)
        if service in ("usage", "usage_api", "cost"):
            try:
                return oci.usage_api.UsageapiClient(self.config, **kwargs)  # type: ignore[attr-defined]
            except Exception as e:
                raise RuntimeError(
                    "Usage API client not available; check OCI SDK version."
                ) from e

        raise ValueError(f"Unknown OCI service: {service}")


oci_manager = OCIManager()


# ---------- Utility helpers ----------

def _default_compartment() -> Optional[str]:
    """Return default compartment (env override or tenancy OCID)."""
    return os.getenv("DEFAULT_COMPARTMENT_OCID") or oci_manager.config.get("tenancy")


def _to_clean_dict(x: Any) -> Any:
    """Safe dict conversion for OCI models/collections."""
    try:
        return to_dict(x)
    except Exception:
        return json.loads(json.dumps(x, default=str))


# ---------- MCP server ----------

mcp = FastMCP("oci-mcp-server")


@mcp.tool()
def list_compartments() -> List[Compartment]:
    """List accessible compartments in the tenancy (including subtrees)."""
    identity = oci_manager.get_client("identity")
    tenancy_id = oci_manager.config["tenancy"]
    comps = oci.pagination.list_call_get_all_results(
        identity.list_compartments,
        compartment_id=tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ACCESSIBLE",
    ).data

    return [
        Compartment(
            compartment_ocid=c.id,
            name=c.name,
            lifecycle_state=getattr(c, "lifecycle_state", None),
            is_accessible=getattr(c, "is_accessible", None),
        )
        for c in comps
    ]


@mcp.tool()
def list_databases_using_recovery_service(
    compartment_ocid: str,
    lifecycle_state: Optional[str] = None,
) -> List[ProtectedDatabase]:
    """List databases that are protected by Autonomous Recovery Service (ARS).

    Args:
        compartment_ocid: Compartment OCID (defaults to tenancy if omitted)
        lifecycle_state: Optional filter (e.g., ACTIVE, CREATING, DELETING, DELETED, FAILED)
    """
    comp = compartment_ocid or _default_compartment()
    assert comp, "No compartment OCID available"

    recovery = oci_manager.get_client("recovery")

    # 1) Fetch protected databases
    protected = oci.pagination.list_call_get_all_results(
        recovery.list_protected_databases,
        compartment_id=comp,
    ).data

    # Optional lifecycle filter (case-insensitive)
    if lifecycle_state:
        want = lifecycle_state.upper()
        protected = [
            p
            for p in protected
            if getattr(p, "lifecycle_state", "").upper() == want
        ]

    # 2) Collect unique policy IDs so we can resolve their names once
    policy_ids = {getattr(p, "protection_policy_id", None) for p in protected}
    policy_ids.discard(None)

    policy_name_by_id: Dict[str, str] = {}
    for pid in policy_ids:
        try:
            pol = recovery.get_protection_policy(pid).data
            pname = (
                getattr(pol, "display_name", None)
                or getattr(pol, "name", None)
                or pid
            )
            policy_name_by_id[pid] = pname
        except Exception:
            policy_name_by_id[pid] = pid  # still useful

    # 3) Normalize output into ProtectedDatabase models
    items: List[ProtectedDatabase] = []
    for p in protected:
        metrics = getattr(p, "metrics", None)

        item = ProtectedDatabase(
            protected_database_id=getattr(p, "id", None),
            display_name=getattr(p, "display_name", None),
            db_unique_name=getattr(p, "db_unique_name", None),
            database_id=getattr(p, "database_id", None),
            compartment_id=getattr(p, "compartment_id", None),
            health=getattr(p, "health", None),
            health_details=getattr(p, "health_details", None),
            lifecycle_state=getattr(p, "lifecycle_state", None),
            time_created=getattr(p, "time_created", None),
            database_size_in_gbs=getattr(metrics, "db_size_in_gbs", None),
            backup_space_used_in_gbs=getattr(metrics, "backup_space_used_in_gbs", None),
            minimum_recovery_needed=getattr(
                metrics, "minimum_recovery_needed_in_days", None
            ),
            unprotected_window_in_seconds=getattr(
                metrics, "unprotected_window_in_seconds", None
            ),
            retention_period_in_days=getattr(
                metrics, "retention_period_in_days", None
            ),
            current_retention_period_in_seconds=getattr(
                metrics, "current_retention_period_in_seconds", None
            ),
            backup_space_estimate_in_gbs=getattr(
                metrics, "backup_space_estimate_in_gbs", None
            ),
            protection_policy_id=getattr(p, "protection_policy_id", None),
            policy_locked_date_time=getattr(p, "policy_locked_date_time", None),
            protection_policy_name=policy_name_by_id.get(
                getattr(p, "protection_policy_id", None)
            ),
            recovery_service_vault_id=getattr(p, "recovery_service_vault_id", None),
            is_redo_transmission_enabled=getattr(
                p, "is_redo_transmission_enabled", None
            ),
            description=getattr(p, "description", None),
            is_redo_logs_enabled=getattr(p, "is_redo_logs_enabled", None),
        )
        items.append(item)

    return items


@mcp.tool()
def get_tenancy_cost_summary(
    start_time_iso: Optional[str] = None,
    end_time_iso: Optional[str] = None,
    granularity: str = "DAILY",
) -> TenancyCostSummary:
    """Summarize tenancy costs using Usage API (requires permissions).

    Args:
        start_time_iso: ISO8601 start (defaults: now-7d)
        end_time_iso: ISO8601 end (defaults: now)
        granularity: DAILY or MONTHLY
    """
    try:
        usage = oci_manager.get_client("usage_api")
    except Exception as e:
        raise RuntimeError(
            "Usage API not available; upgrade OCI SDK and permissions."
        ) from e

    if not end_time_iso:
        end = datetime.utcnow()
    else:
        end = datetime.fromisoformat(end_time_iso.replace("Z", ""))

    if not start_time_iso:
        start = end - timedelta(days=7)
    else:
        start = datetime.fromisoformat(start_time_iso.replace("Z", ""))

    tenant_id = oci_manager.config["tenancy"]
    details = oci.usage_api.models.RequestSummarizedUsagesDetails(
        tenant_id=tenant_id,
        time_usage_started=start,
        time_usage_ended=end,
        granularity=granularity,
        query_type="USAGE",
        filter={
            "operator": "AND",
            "dimensions": [{"key": "service", "value": "AUTONOMOUS_RECOVERY"}],
        },
        group_by=["resourceId"],
    )

    resp = usage.request_summarized_usages(
        request_summarized_usages_details=details
    )
    rows = (
        [to_dict(x) for x in resp.data.items]
        if getattr(resp.data, "items", None)
        else []
    )

    total_cost = sum((r.get("computed_amount", 0) or 0) for r in rows)
    total_usage = sum((r.get("computed_quantity", 0) or 0) for r in rows)

    return TenancyCostSummary(
        start=start.isoformat() + "Z",
        end=end.isoformat() + "Z",
        granularity=granularity,
        total_computed_amount=total_cost,
        total_computed_usage=total_usage,
        items=rows,
    )


# ----------- Resources -----------

@mcp.resource("oci://compartments")
def resource_compartments() -> Dict[str, Any]:
    """Resource listing compartments (compartment_ocid, name)."""
    comps = [c.dict() for c in list_compartments()]
    return {"compartments": comps}


# ----------- Prompts -----------

@mcp.prompt("oci_analysis_prompt")
def oci_analysis_prompt() -> str:
    """A helper prompt to analyze OCI state returned by the tools."""
    return (
        "You are an expert Oracle Cloud architect. Given the JSON outputs from tools like "
        "`list_compartments`, `list_databases_using_recovery_service`, and `get_tenancy_cost_summary`, "
        "produce a concise assessment covering cost, usage, backup protection and reliability. "
        "Highlight RPO and RTO for databases and note any missing monitoring/alerts."
    )


def main() -> None:
    # Start stdio transport
    mcp.run()


if __name__ == "__main__":
    main()
