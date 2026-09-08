"""
Copyright (c) 2025, 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

The tenancy's subscribed regions, read from IAM on every call.

Deliberately not cached. Whether a caller may list region subscriptions is
decided by their own OCI IAM policy, and the only place that decision is made is
the IAM call itself -- so a cache that answered ahead of it would be answering an
authorization question it is not entitled to answer. This served exactly one
thin tool, so there was nothing to weigh against that.
"""

from . import auth, clients


def _iam_subscribed_regions_with_status(*, request_id: str) -> list[dict]:
    """
    Returns the tenancy's subscribed regions from IAM (IdentityClient.list_region_subscriptions).
    Output items are: {"region": "<region_name>", "status": "<READY|...>"}.

    Goes to IAM every time, so the caller's current permissions decide the answer.
    """
    tenancy_id = auth.get_tenancy()
    identity = clients.get_identity_client(request_id=request_id)
    resp = identity.list_region_subscriptions(tenancy_id=tenancy_id)
    subs = getattr(resp, "data", None) or []

    out: list[dict] = []
    for sub in subs:
        region_name = getattr(sub, "region_name", None) or getattr(sub, "regionName", None)
        status = getattr(sub, "status", None)
        if region_name:
            out.append({"region": region_name, "status": status})

    return sorted(out, key=lambda x: x.get("region") or "")
