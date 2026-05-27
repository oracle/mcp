# Run a DR Drill (START_DRILL / STOP_DRILL)

A **Drill** tests your DR plan without changing PRIMARY/STANDBY roles and without impacting production.

**Key differences from Switchover and Failover:**
- Roles do NOT change — PRIMARY stays PRIMARY
- Production is NOT affected
- The standby enters a special "drill state" during the test
- You MUST stop the drill (STOP_DRILL) before any real switchover or failover
- Cannot run SWITCHOVER or FAILOVER while a drill is in progress

---

## Confirmation is the caller's responsibility

`fsdr_raw_call` executes immediately. Before each START_DRILL or
STOP_DRILL below, print the full payload to the user and wait for
explicit approval.

---

## Pre-Drill Checklist

1. **Both DRPGs are ACTIVE**
   ```
   get_dr_protection_group(dr_protection_group_id="<drpg-ocid>")
   ```

2. **No active drill already running**
   ```
   list_dr_plan_executions_for_protection_group(dr_protection_group_id="<drpg-ocid>")
   ```
   No execution in `IN_PROGRESS` state.

3. **Maintenance window** — notify teams that standby resources will be tested.

4. **Locate START_DRILL and STOP_DRILL plan OCIDs**
   ```
   list_dr_plans_for_protection_group(dr_protection_group_id="<drpg-ocid>")
   ```
   Note OCIDs for both `START_DRILL` and `STOP_DRILL` plan types.

---

## Phase 1 — Start the Drill

```
fsdr_raw_call(
  operation="create_dr_plan_execution",
  parameters={
    "create_dr_plan_execution_details": {
      "plan_id": "<start-drill-plan-ocid>",
      "display_name": "DR Drill <date>",
      "execution_options": {
        "_type": "StartDrillExecutionOptionDetails",
        "are_prechecks_enabled": true,
        "are_warnings_ignored": false
      }
    }
  }
)
```

Note the returned `work_request_id` and execution OCID.

### Monitor

```
get_dr_plan_execution(dr_plan_execution_id="<execution-ocid>")
```

Wait for `lifecycle_state = SUCCEEDED` before proceeding to validation.

---

## Phase 2 — Validate DR Environment

Once the drill is running, perform your validation tests:

- Verify compute instances are accessible in the standby region
- Test application connectivity and health checks
- Verify database is accessible (read/write if applicable)
- Check network routing and load balancer configurations
- Document any issues found for remediation

**Important:** During the drill, the standby DRPG is in DRILL state.
You cannot run a real SWITCHOVER or FAILOVER until the drill is stopped.

---

## Phase 3 — Stop the Drill

```
fsdr_raw_call(
  operation="create_dr_plan_execution",
  parameters={
    "create_dr_plan_execution_details": {
      "plan_id": "<stop-drill-plan-ocid>",
      "display_name": "Stop DR Drill <date>",
      "execution_options": {
        "_type": "StopDrillExecutionOptionDetails"
      }
    }
  }
)
```

Note that `StopDrillExecutionOptionDetails` does not accept precheck or
warning flags — those are ignored for STOP_DRILL.

### Monitor

```
get_dr_plan_execution(dr_plan_execution_id="<stop-execution-ocid>")
```

Wait for `lifecycle_state = SUCCEEDED`.

---

## Post-Drill Checklist

After STOP_DRILL succeeds:

1. **Verify DRPG state returned to normal**
   ```
   get_dr_protection_group(dr_protection_group_id="<drpg-ocid>")
   ```
   `lifecycle_state` = `ACTIVE`, `role` unchanged.

2. **Verify standby resources are back in standby state**
   (Databases back in standby mode, compute instances stopped, etc.)

3. **Document findings** — note execution durations, any failures, and RTO measurement.

4. **Check execution history**
   ```
   list_dr_plan_executions_for_protection_group(dr_protection_group_id="<drpg-ocid>")
   ```
   Both START_DRILL and STOP_DRILL executions should show `SUCCEEDED`.

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| START_DRILL fails | Check `group_executions` for step details; fix and retry |
| Drill stuck IN_PROGRESS | Do not attempt switchover/failover; wait or contact support |
| STOP_DRILL fails | Critical — resources may be in inconsistent state; escalate |
| Cannot find STOP_DRILL plan | Run `list_dr_plans_for_protection_group` filtering for `plan_type = STOP_DRILL` |

## Important Restriction

While a drill is in progress (standby in DRILL state):
- `SWITCHOVER` plan execution will be **rejected**
- `FAILOVER` plan execution will be **rejected**
- You MUST run STOP_DRILL first, even in an emergency
