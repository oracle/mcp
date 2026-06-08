# Run a Planned Switchover

A **Switchover** is a planned, graceful operation that reverses the PRIMARY/STANDBY roles between two regions.

**Key differences from Failover and Drill:**
- Both regions must be fully operational
- Data replication is quiesced before the switch — no data loss (RPO = 0)
- Roles reverse: PRIMARY becomes STANDBY, STANDBY becomes PRIMARY
- The standby region takes over immediately after completion
- Reverse replication must be confirmed operational before proceeding

---

## Confirmation is the caller's responsibility

`fsdr_raw_call` executes immediately. Before triggering a switchover,
print the full payload (plan OCID, display name, execution options) to
the user and wait for explicit approval.

---

## Pre-Switchover Checklist

Before executing, verify ALL of the following:

1. **Both DRPGs are ACTIVE**
   ```
   get_dr_protection_group(dr_protection_group_id="<primary-drpg-ocid>")
   get_dr_protection_group(dr_protection_group_id="<standby-drpg-ocid>")
   ```
   Both `lifecycle_state` must be `ACTIVE`.

2. **No drill is in progress**
   ```
   list_dr_plan_executions_for_protection_group(dr_protection_group_id="<primary-drpg-ocid>")
   ```
   No execution should be in `IN_PROGRESS` state. A drill in progress blocks switchover.
   Stop it first with a STOP_DRILL execution if needed.

3. **Replication is healthy**
   Verify data replication (Data Guard, Object Replication, etc.) is in sync.
   Check DB Data Guard apply lag is near zero.

4. **Maintenance window is active**
   Notify application teams — there will be a brief connectivity interruption.

5. **Locate the SWITCHOVER plan OCID**
   ```
   list_dr_plans_for_protection_group(dr_protection_group_id="<primary-drpg-ocid>", plan_type="SWITCHOVER")
   ```
   Copy the plan's `id` from the response.

---

## Step 1 — Execute the Switchover

```
fsdr_raw_call(
  operation="create_dr_plan_execution",
  parameters={
    "create_dr_plan_execution_details": {
      "plan_id": "<switchover-plan-ocid>",
      "display_name": "Switchover to Region2 <date>",
      "execution_options": {
        "_type": "SwitchoverExecutionOptionDetails",
        "are_prechecks_enabled": true,
        "are_warnings_ignored": false
      }
    }
  }
)
```

Note the returned `work_request_id` and the execution OCID from `data.id`.

---

## Step 2 — Monitor Progress

```
get_work_request(work_request_id="<wrq-ocid>")
get_dr_plan_execution(dr_plan_execution_id="<execution-ocid>")
```

Expected progression: `ACCEPTED` → `IN_PROGRESS` → `SUCCEEDED`

Typical switchover duration: 15–30 minutes depending on database size.

---

## Step 3 — Post-Switchover Validation

After `SUCCEEDED`:

1. **Verify roles have reversed**
   ```
   get_dr_protection_group(dr_protection_group_id="<old-primary-drpg-ocid>")
   ```
   `role` should now be `STANDBY`.

   ```
   get_dr_protection_group(dr_protection_group_id="<old-standby-drpg-ocid>")
   ```
   `role` should now be `PRIMARY`.

2. **Verify application connectivity** in the new primary region.

3. **Confirm reverse replication** is running (old primary → new standby direction).

4. **Refresh DR plans** in the new primary DRPG if member configuration has changed.

---

## Step 4 — Reverse Replication Setup

After switchover, the new standby region must replicate back to the new primary.
This is usually automatic for OCI-managed services but verify:
- Data Guard: primary/standby roles should auto-switch with the DRPG
- Object Storage replication: confirm replication policy direction
- File Storage: confirm replication direction

---

## Switching Back (Re-Switchover)

To return to the original configuration, run another SWITCHOVER — this time
initiating from the **new primary** DRPG (now in the old standby region):

```
list_dr_plans_for_protection_group(
  dr_protection_group_id="<new-primary-drpg-ocid>",
  plan_type="SWITCHOVER",
  profile="FSDR_REGION2"
)
```

Then execute its SWITCHOVER plan with the same `fsdr_raw_call` pattern as Step 1.

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Execution stays `IN_PROGRESS` > 60 min | `get_dr_plan_execution` to find the failing step |
| `FAILED` state | Review `group_executions` for error details; fix and re-run |
| Both DRPGs show PRIMARY after failure | Manual intervention needed — contact Oracle Support |
| Replication lag high before switchover | Wait for lag to drop before proceeding |
