# Run an Emergency Failover

A **Failover** is an emergency operation used when the primary region is unavailable or severely degraded.

**Key differences from Switchover and Drill:**
- Primary region does NOT need to be available
- Data loss is possible (RPO > 0) — last replicated state is used
- Roles change: STANDBY becomes the new PRIMARY
- The old primary does NOT automatically become STANDBY
- Manual reset is REQUIRED after the failover to restore the DR pair
- This is a one-way operation — cannot be automatically reversed

---

## Confirmation is the caller's responsibility

`fsdr_raw_call` executes immediately. A failover is potentially
irreversible and involves data loss — before calling it, print the full
payload to the user and obtain explicit approval.

---

## When to Use Failover vs Switchover

| Criteria | Use Failover | Use Switchover |
|----------|-------------|----------------|
| Primary region is down | YES | NO |
| Planned maintenance | NO | YES |
| Both regions must be up | NO | YES |
| Data loss acceptable | YES (if needed) | NO |
| Roles auto-reverse | NO | YES |

---

## Pre-Failover Checklist

1. **Confirm primary is truly unavailable** — avoid accidental failovers due to monitoring glitches.

2. **Assess data loss risk** — check replication lag from last known sync.

3. **Notify stakeholders** — failover has significant operational impact.

4. **Confirm standby DRPG is ACTIVE**
   ```
   get_dr_protection_group(dr_protection_group_id="<standby-drpg-ocid>", profile="FSDR_REGION2")
   ```
   `lifecycle_state` must be `ACTIVE`.

5. **No drill in progress**
   ```
   list_dr_plan_executions_for_protection_group(dr_protection_group_id="<standby-drpg-ocid>", profile="FSDR_REGION2")
   ```
   No IN_PROGRESS drill execution. Stop drill first if one is running.

6. **Locate FAILOVER plan OCID on the STANDBY DRPG**
   ```
   list_dr_plans_for_protection_group(
     dr_protection_group_id="<standby-drpg-ocid>",
     plan_type="FAILOVER",
     profile="FSDR_REGION2"
   )
   ```
   The failover plan lives on the **standby** DRPG.

---

## Step 1 — Execute Failover

```
fsdr_raw_call(
  operation="create_dr_plan_execution",
  profile="FSDR_REGION2",
  parameters={
    "create_dr_plan_execution_details": {
      "plan_id": "<failover-plan-ocid>",
      "display_name": "Emergency Failover <date>",
      "execution_options": {
        "_type": "FailoverExecutionOptionDetails",
        "are_prechecks_enabled": true,
        "are_warnings_ignored": false
      }
    }
  }
)
```

Note the returned `work_request_id` and execution OCID.

---

## Step 2 — Monitor Progress

```
get_work_request(work_request_id="<wrq-ocid>", profile="FSDR_REGION2")
get_dr_plan_execution(dr_plan_execution_id="<execution-ocid>", profile="FSDR_REGION2")
```

Expected: `ACCEPTED` → `IN_PROGRESS` → `SUCCEEDED`

---

## Step 3 — Post-Failover Validation

After `SUCCEEDED`:

1. **Verify new primary role**
   ```
   get_dr_protection_group(dr_protection_group_id="<old-standby-drpg-ocid>", profile="FSDR_REGION2")
   ```
   `role` = `PRIMARY`.

2. **Verify application is running** in the new primary region.

3. **Verify databases** are open in read/write mode.

4. **Check network/DNS routing** — update DNS or traffic manager to point to new primary.

---

## Step 4 — Manual Reset After Failover (REQUIRED)

The old primary region must be manually reset before the DR pair can be used again.
**Do not skip this step — without it, you have no DR protection.**

### 4a — Restore the old primary region
- Bring up failed compute instances
- Start databases and verify data consistency
- Resolve whatever caused the original failure

### 4b — Disassociate and delete the old primary DRPG

The old primary DRPG is now orphaned. Disassociate it first, then delete:

```
fsdr_raw_call(
  operation="disassociate_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={"dr_protection_group_id": "<old-primary-drpg-ocid>"}
)

fsdr_raw_call(
  operation="delete_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={"dr_protection_group_id": "<old-primary-drpg-ocid>"}
)
```

### 4c — Create a new DRPG in the old primary region (now acting as standby)

```
fsdr_raw_call(
  operation="create_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={
    "create_dr_protection_group_details": {
      "compartment_id": "<compartment-ocid>",
      "display_name": "DR Standby - <region1>",
      "log_location": {
        "_type": "CreateObjectStorageLogLocationDetails",
        "bucket": "<bucket-name>",
        "namespace": "<namespace>"
      }
    }
  }
)
```

### 4d — Associate the new DRPG as STANDBY

Call from the new STANDBY region (old primary region):

```
fsdr_raw_call(
  operation="associate_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={
    "dr_protection_group_id": "<new-standby-drpg-ocid>",
    "associate_dr_protection_group_details": {
      "peer_id": "<current-primary-drpg-ocid>",
      "peer_region": "<current-primary-region>",
      "role": "STANDBY"
    }
  }
)
```

### 4e — Add members to the new standby DRPG

Follow the `add_members` prompt to re-add all resources.

### 4f — Create DR Plans on the new primary

```
fsdr_raw_call(
  operation="create_dr_plan",
  profile="FSDR_REGION2",
  parameters={
    "create_dr_plan_details": {
      "dr_protection_group_id": "<new-primary-drpg-ocid>",
      "display_name": "Switchover Plan",
      "type": "SWITCHOVER"
    }
  }
)
```

Repeat for `FAILOVER`, `START_DRILL`, and `STOP_DRILL`.

### 4g — Verify DR topology is healthy

Run the `check_dr_status` prompt to confirm both DRPGs are active and paired.

---

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Failover FAILED | Check `group_executions` for step details |
| New primary stuck NEEDS_ATTENTION | Check OCI Console events |
| Application won't start | Check security lists, route tables, DNS in new primary region |
| DB in mount/restrict mode | Manually open with `ALTER DATABASE OPEN` if Data Guard |
| Old primary came back up as PRIMARY | Shut it down immediately to prevent split-brain; perform disassociation |
