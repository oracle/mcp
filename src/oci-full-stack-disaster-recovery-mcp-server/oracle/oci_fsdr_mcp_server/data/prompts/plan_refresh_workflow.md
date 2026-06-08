# DR Plan Refresh Workflow

Run this workflow whenever you add, remove, or modify members in a DRPG.
DR plans do NOT auto-update — stale plans can cause execution failures.

## When to Refresh

- Added a new compute instance, database, or other member
- Removed a member from the DRPG
- Changed member configuration (e.g., VNIC mappings, destination subnet)
- After any infrastructure change in either region

## Confirmation is the caller's responsibility

`fsdr_raw_call` executes immediately. Before each write step below, print
the full payload to the user and wait for explicit approval.

## Step 1 — Confirm member changes are saved

```
get_dr_protection_group(dr_protection_group_id="<drpg-ocid>")
```

Review the `members` array — confirm all intended resources appear.
If members are missing, use the `add_members` prompt first.

## Step 2 — List existing plans

```
list_dr_plans_for_protection_group(dr_protection_group_id="<drpg-ocid>")
```

Note OCIDs for SWITCHOVER, FAILOVER, START_DRILL, and STOP_DRILL plans.
All active plans should be refreshed after member changes.

## Step 3 — Refresh each plan

OCI FSDR exposes a dedicated `refresh_dr_plan` API. Prefer it over
delete-and-recreate:

```
fsdr_raw_call(
  operation="refresh_dr_plan",
  parameters={"dr_plan_id": "<plan-ocid>"}
)
```

Repeat for each plan you need to refresh.

If `refresh_dr_plan` is not suitable (e.g. you also need to rename or
reorder plan groups), delete and recreate instead:

```
fsdr_raw_call(
  operation="delete_dr_plan",
  parameters={"dr_plan_id": "<old-plan-ocid>"}
)

fsdr_raw_call(
  operation="create_dr_plan",
  parameters={
    "create_dr_plan_details": {
      "dr_protection_group_id": "<drpg-ocid>",
      "display_name": "Switchover Plan v2",
      "type": "SWITCHOVER"
    }
  }
)
```

## Step 4 — Review new plan steps

```
get_dr_plan(dr_plan_id="<new-plan-ocid>")
```

Verify:
- All new members appear in the generated steps
- Step order is logical (databases before compute, etc.)
- No unexpected members from old configuration remain

## Step 5 — Verify plan health

```
list_dr_plans_for_protection_group(dr_protection_group_id="<drpg-ocid>")
```

All plans should show `lifecycle_state = ACTIVE` before you run any DR operation.

## Step 6 — Run a drill to validate

After refreshing plans following a significant member change, run a drill
to confirm the updated plan executes correctly — follow the `run_drill`
prompt.

## Important Notes

- Refreshing plans on the PRIMARY DRPG does NOT automatically refresh plans on the STANDBY DRPG
- Repeat this workflow on both DRPGs if you changed shared resources
- Do not execute a stale plan — it may skip new members or reference deleted resources
- After a Switchover, the new primary's plans may reference old configurations — refresh immediately
