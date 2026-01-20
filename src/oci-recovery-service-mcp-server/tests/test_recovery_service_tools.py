#!/usr/bin/env python3
r"""
test_recovery_service_tools.py - Local test harness for the OCI MCP server tools.

Usage (from C:\mcp-main\mcp-main\src\oci-recovery-service-mcp-server\oracle\oci_recovery_service_mcp_server\tests):
    C:\Python314\python.exe test_recovery_service_tools.py
"""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
from pprint import pprint

# --- ensure we can import server.py no matter where we run this from ---

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1]  # .../oci_recovery_service_mcp_server
sys.path.insert(0, str(PACKAGE_ROOT))



# Import the tool functions and helper from your server module
from server import (  # type: ignore[import]
    list_compartments,
    list_databases_using_recovery_service,
    get_tenancy_cost_summary,
    list_recovery_service_subnets,
    _default_compartment,
)


def test_list_compartments() -> None:
    print("\n=== 1) Testing list_compartments() ===")
    try:
        comps = list_compartments()
        print(f"Retrieved {len(comps)} compartments.")
        for c in comps[:10]:  # show at most 10 for brevity
            print(
                f"- {c.name} "
                f"(ocid={c.compartment_ocid}) "
                f"state={c.lifecycle_state} "
                f"accessible={c.is_accessible}"
            )
        if len(comps) > 10:
            print(f"... ({len(comps) - 10} more not shown)")
    except Exception:
        print("Error while calling list_compartments():")
        traceback.print_exc()


def test_list_databases_using_recovery_service() -> None:
    print("\n=== 2) Testing list_databases_using_recovery_service() ===")
    try:
        # Prefer an explicit test compartment if set
        comp = os.getenv("TEST_COMPARTMENT_OCID") or _default_compartment()
        if not comp:
            print(
                "No compartment OCID available.\n"
                "Set TEST_COMPARTMENT_OCID or DEFAULT_COMPARTMENT_OCID or ensure\n"
                "your tenancy OCID is present in the OCI config used by server.py."
            )
            return

        print(f"Using compartment_ocid = {comp}")
        dbs = list_databases_using_recovery_service(compartment_ocid=comp)

        print(f"Retrieved {len(dbs)} protected databases.")
        for d in dbs[:10]:
            print(
                f"- {d.display_name or d.db_unique_name or d.protected_database_id} "
                f"(protected_database_id={d.protected_database_id}, "
                f"database_id={d.database_id}, "
                f"health={d.health}, "
                f"lifecycle_state={d.lifecycle_state})"
            )
        if len(dbs) > 10:
            print(f"... ({len(dbs) - 10} more not shown)")
    except Exception:
        print("Error while calling list_databases_using_recovery_service():")
        traceback.print_exc()


def test_list_recovery_service_subnets() -> None:
    print("\n=== 2) Testing list_recovery_service_subnets() ===")
    try:
        # Prefer an explicit test compartment if set
        comp = os.getenv("TEST_COMPARTMENT_OCID") or _default_compartment()
        if not comp:
            print(
                "No compartment OCID available.\n"
                "Set TEST_COMPARTMENT_OCID or DEFAULT_COMPARTMENT_OCID or ensure\n"
                "your tenancy OCID is present in the OCI config used by server.py."
            )
            return

        print(f"Using compartment_ocid = {comp}")
        dbs = list_list_recovery_service_subnets(compartment_ocid=comp)

        print(f"Retrieved {len(rsss)} recovery service subnets.")
        for s in rsss[:10]:
            print(
                f"- {s.display_name } "
                f"(recovery_service_id={s.recovery_service_id}, "
                f"health={d.health}, "
                f"lifecycle_state={d.lifecycle_state})"
            )
        if len(rsss) > 10:
            print(f"... ({len(rsss) - 10} more not shown)")
    except Exception:
        print("Error while calling list_list_recovery_service_subnets():")
        traceback.print_exc()


def test_get_tenancy_cost_summary() -> None:
    print("\n=== 3) Testing get_tenancy_cost_summary() ===")
    try:
        # Let the function use its default of last 7 days, DAILY
        summary = get_tenancy_cost_summary()

        print("Cost summary window:")
        print(f"  start      : {summary.start}")
        print(f"  end        : {summary.end}")
        print(f"  granularity: {summary.granularity}")
        print(f"  total cost : {summary.total_computed_amount}")
        print(f"  total usage: {summary.total_computed_usage}")
        print(f"  items      : {len(summary.items)} summarized rows")

        # Show first few raw rows for inspection
        for row in summary.items[:5]:
            print("  - row:")
            pprint(row)
        if len(summary.items) > 5:
            print(f"... ({len(summary.items) - 5} more rows not shown)")
    except Exception:
        print("Error while calling get_tenancy_cost_summary():")
        traceback.print_exc()


def main() -> None:
    print("=== OCI MCP Server Local Test (test_recovery_service_tools.py) ===")
    print("Using environment / OCI config from server.py (dotenv + OCI config).")

    test_list_compartments()
    test_list_databases_using_recovery_service()
    test_get_tenancy_cost_summary()

    print("\n=== Done ===")


if __name__ == "__main__":
    main()