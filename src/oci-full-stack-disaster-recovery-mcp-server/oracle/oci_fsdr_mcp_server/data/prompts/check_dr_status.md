# Check DR Status (Read-Only Operations)

Use these steps to inspect the current state of your DR topology without making any changes.

## 1 — List DR Protection Groups

```
list_dr_protection_groups(compartment_id="<ocid>")
```

Key fields to review:
- `role` — PRIMARY or STANDBY
- `lifecycle_state` — ACTIVE = healthy, NEEDS_ATTENTION = investigate
- `peer_id` / `peer_region` — confirm the pair is linked

Run this against both region profiles to see the full picture:
- `profile="FSDR_REGION1"` (primary region)
- `profile="FSDR_REGION2"` (standby region)

## 2 — Inspect a Specific DRPG

```
get_dr_protection_group(dr_protection_group_id="ocid1.drprotectiongroup.oc1..xxx")
```

Review:
- `members` array — verify all expected resources are listed
- `association_status` — must be ASSOCIATED before any DR operation
- `lifecycle_state` — ACTIVE is required

## 3 — List DR Plans

```
list_dr_plans_for_protection_group(dr_protection_group_id="<drpg-ocid>")
```

Plan types:
| type | Purpose |
|------|---------|
| SWITCHOVER | Planned role reversal (both regions must be up) |
| FAILOVER | Emergency failover (standby takes over unilaterally) |
| START_DRILL | Begin a test drill |
| STOP_DRILL | End a test drill |

Check `lifecycle_state` — ACTIVE plans are ready to execute.

## 4 — List Plan Executions

```
list_dr_plan_executions_for_protection_group(dr_protection_group_id="<drpg-ocid>")
```

Execution states:
| state | Meaning |
|-------|---------|
| ACCEPTED | Queued, not started |
| IN_PROGRESS | Running |
| SUCCEEDED | Completed successfully |
| FAILED | Failed — review log groups |
| PAUSED | Waiting for manual step |
| CANCELED | User-canceled |

## 5 — Get a Specific Execution

```
get_dr_plan_execution(dr_plan_execution_id="ocid1.drplanexecution.oc1..xxx")
```

Check `group_executions` for per-step detail.
`execution_duration_in_sec` shows elapsed time.

## 6 — Check Work Request Status

After any write operation, a `work_request_id` is returned.

```
get_work_request(work_request_id="ocid1.workrequest.oc1..xxx")
```

- `percent_complete` — 0–100
- `status` — IN_PROGRESS / SUCCEEDED / FAILED
- `resources` — lists affected resource OCIDs

## 7 — Steady-State Health Check (Full Sequence)

Run this periodically to confirm your DR topology is healthy:

1. `list_dr_protection_groups` on both profiles → both ACTIVE, correct roles
2. `get_dr_protection_group` on primary DRPG → members list is complete
3. `list_dr_plans_for_protection_group` on primary DRPG → SWITCHOVER + FAILOVER + STOP_DRILL plans exist and are ACTIVE
4. `list_dr_plan_executions_for_protection_group` on primary DRPG → no IN_PROGRESS or FAILED executions
5. If last execution FAILED → `get_dr_plan_execution` to review step details

## Warning Signs

- `lifecycle_state = NEEDS_ATTENTION` on a DRPG → open OCI Console for details
- No STANDBY plan on the standby DRPG → re-associate or create plans
- Both DRPGs showing role PRIMARY → association is broken
- Drill execution in IN_PROGRESS state → cannot run SWITCHOVER or FAILOVER until drill is stopped
