#!/usr/bin/env python3
"""
test4.py - Simple test harness for the OCI MCP server tools.

Usage (from C:\oci-mcp-main):
    C:\Python314\python.exe test4.py

This does NOT use the MCP protocol; it just imports server.py and calls the
tool functions directly to verify connectivity and logic.
"""

from __future__ import annotations

import os
import traceback
from pprint import pprint

# Import the tool functions and helper from your server module
from server import (  # type: ignore[import]
    list_compartments,
    list_databases_using_recovery_service,
    get_tenancy_cost_summary,
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
        comp = os.getenv("TEST_COMPARTMENT_OCID") or _default_compartment()
        if not comp:
            print(
                "No compartment OCID available. Set TEST_COMPARTMENT_OCID or "
                "DEFAULT_COMPARTMENT_OCID or ensure tenancy OCID is in the OCI config."
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


def test_get_tenancy_cost_summary() -> None:
    print("\n=== 3) Testing get_tenancy_cost_summary() ===")
    try:
        # Let the function use its default of last 7 days, DAILY
        summary = get_tenancy_cost_summary()

        print("Cost summary window:")
        print(f"  start      : {summary.start}")
        print(f"  end        : {summary.end}")
        print(f"  granularity: {summary.granularity}")
        print(f"  total cost : {summary.total_c_
