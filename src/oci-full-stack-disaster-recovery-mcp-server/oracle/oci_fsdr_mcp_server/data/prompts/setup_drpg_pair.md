# Setup DR Protection Group Pair

Use this workflow to create and associate a PRIMARY and STANDBY DR Protection
Group (DRPG) across two OCI regions.

## Prerequisites
- Two OCI regions configured as `FSDR_REGION1` (primary) and `FSDR_REGION2` (standby)
- Object Storage buckets for DR logs in each region (recommended)
- Compartment OCID where DRPGs will be created

## Important: confirmation is the caller's responsibility

All mutations go through `fsdr_raw_call` and execute immediately. Before
every write below, print the full payload to the user and wait for
explicit approval. There is no built-in preview/dry-run mode.

## Step-by-Step

### Step 1 — Create PRIMARY DRPG in Region 1

```
fsdr_raw_call(
  operation="create_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={
    "create_dr_protection_group_details": {
      "compartment_id": "<compartment-ocid>",
      "display_name": "MyApp-Primary-IAD",
      "log_location": {
        "_type": "CreateObjectStorageLogLocationDetails",
        "bucket": "<bucket-name>",
        "namespace": "<namespace>"
      }
    }
  }
)
```

Note: role (PRIMARY/STANDBY) is not set at creation — it is assigned via
`associate_dr_protection_group` in Step 3.

Track the returned `work_request_id` with `get_work_request` and wait for
SUCCEEDED before proceeding. Capture the new DRPG's OCID from the work
request's `resources` array (or by calling `list_dr_protection_groups`).

### Step 2 — Create STANDBY DRPG in Region 2

```
fsdr_raw_call(
  operation="create_dr_protection_group",
  profile="FSDR_REGION2",
  parameters={
    "create_dr_protection_group_details": {
      "compartment_id": "<compartment-ocid>",
      "display_name": "MyApp-Standby-PHX",
      "log_location": {
        "_type": "CreateObjectStorageLogLocationDetails",
        "bucket": "<bucket-name>",
        "namespace": "<namespace>"
      }
    }
  }
)
```

Again, wait for the work request to reach SUCCEEDED and capture the new
DRPG's OCID.

### Step 3 — Associate the DRPGs

Call from the PRIMARY region. Association sets the PRIMARY role on the
local DRPG and STANDBY on the peer.

```
fsdr_raw_call(
  operation="associate_dr_protection_group",
  profile="FSDR_REGION1",
  parameters={
    "dr_protection_group_id": "<primary-drpg-ocid>",
    "associate_dr_protection_group_details": {
      "peer_id": "<standby-drpg-ocid>",
      "peer_region": "us-phoenix-1",
      "role": "PRIMARY"
    }
  }
)
```

This triggers a work request — poll `get_work_request` until status is
SUCCEEDED.

### Step 4 — Verify

```
get_dr_protection_group(dr_protection_group_id="<primary-drpg-ocid>", profile="FSDR_REGION1")
get_dr_protection_group(dr_protection_group_id="<standby-drpg-ocid>", profile="FSDR_REGION2")
```

Confirm:
- Region 1 DRPG: `role` = PRIMARY, `lifecycle_state` = ACTIVE
- Region 2 DRPG: `role` = STANDBY, `lifecycle_state` = ACTIVE
- Both show `peer_id` and `peer_region` populated

## Next Steps

Once the pair is active, proceed to:
- Add members — follow the `add_members` prompt
- Create DR plans — call `fsdr_raw_call` with `operation="create_dr_plan"`
  (SWITCHOVER / FAILOVER / START_DRILL / STOP_DRILL)
