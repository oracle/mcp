# Add Members to a DR Protection Group

Members are the OCI resources (compute instances, databases, etc.) that
FSDR will manage during DR operations.

## IMPORTANT
`update_dr_protection_group` REPLACES the entire member list. Always
retrieve current members first and merge your additions before calling it.

## How members are described

Each member is a dict with a `_type` discriminator naming the exact OCI SDK
model class, plus `member_id` and any type-specific fields required by that
class. The server does not hardcode the set of supported types — any class
under `oci.disaster_recovery.models` beginning with
`UpdateDrProtectionGroupMember...Details` is valid.

Common classes (non-exhaustive — check OCI SDK docs for the full list):

| _type | Resource |
|-------|----------|
| `UpdateDrProtectionGroupMemberComputeInstanceDetails` | Compute VM |
| `UpdateDrProtectionGroupMemberComputeInstanceMovableDetails` | Movable compute |
| `UpdateDrProtectionGroupMemberComputeInstanceNonMovableDetails` | Non-movable compute |
| `UpdateDrProtectionGroupMemberDatabaseDetails` | Oracle DB System |
| `UpdateDrProtectionGroupMemberAutonomousDatabaseDetails` | Autonomous Database |
| `UpdateDrProtectionGroupMemberAutonomousContainerDatabaseDetails` | Autonomous Container DB |
| `UpdateDrProtectionGroupMemberVolumeGroupDetails` | Block volume group |
| `UpdateDrProtectionGroupMemberFileSystemDetails` | File Storage |
| `UpdateDrProtectionGroupMemberLoadBalancerDetails` | Load Balancer |
| `UpdateDrProtectionGroupMemberNetworkLoadBalancerDetails` | Network Load Balancer |
| `UpdateDrProtectionGroupMemberOkeClusterDetails` | OKE cluster |
| `UpdateDrProtectionGroupMemberObjectStorageBucketDetails` | Object Storage bucket |

## Step-by-Step

### Step 1 — Get current members

```
get_dr_protection_group(dr_protection_group_id="<drpg-ocid>")
```

Extract the `members` array from the response data. Each existing member
already has a `member_type` field returned by the API; convert it to the
matching `Update...Details` class name when building the new list.

### Step 2 — Build the new member list

Merge existing members with your new additions. Every member dict must
include `_type` and `member_id`; additional fields depend on the specific
class (e.g. destination VCN, backup policy) — refer to the OCI SDK for
required fields per type.

### Step 3 — Show the payload to the user and ask for confirmation

Before calling any write operation, print the full payload (DRPG OCID,
new member count, member OCIDs and types) and wait for explicit approval.
The MCP server does not implement a preview mode — confirmation is the
caller's responsibility.

### Step 4 — Execute

```
fsdr_raw_call(
  operation="update_dr_protection_group",
  parameters={
    "dr_protection_group_id": "<drpg-ocid>",
    "update_dr_protection_group_details": {
      "members": [
        {
          "_type": "UpdateDrProtectionGroupMemberDatabaseDetails",
          "member_id": "ocid1.dbsystem.oc1.iad.xxx"
        },
        {
          "_type": "UpdateDrProtectionGroupMemberComputeInstanceMovableDetails",
          "member_id": "ocid1.instance.oc1.iad.yyy"
        }
      ]
    }
  }
)
```

### Step 5 — Verify

Re-run `get_dr_protection_group` and confirm the `members` array matches
the expected final state. If plans existed before the member change,
follow the `plan_refresh_workflow` prompt — plans do NOT auto-update.
