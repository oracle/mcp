"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from datetime import datetime, timezone

# CamelCase keys as required

# Stored commands created via the mock
INSTANCE_AGENT_COMMANDS = []

# Pre-populated command executions (summaries). Tests can list these even
# before creating new ones.
INSTANCE_AGENT_EXECUTIONS = [
    {
        "instanceAgentCommandId": "ocid1.instanceagentcommand.oc1..mock-cmd-1",
        "instanceId": "ocid1.instance.oc1..mock-uuid-1",
        "deliveryState": "VISIBLE",
        "lifecycleState": "SUCCEEDED",
        "timeCreated": "2026-01-13T10:00:00Z",
        "timeUpdated": "2026-01-13T10:00:10Z",
        "sequenceNumber": 100,
        "displayName": "echo-hello",
        "content": {
            "outputType": "TEXT",
            "exitCode": 0,
            "message": "Execution successful",
            "text": "hello",
            "textSha256": "abc123",
        },
    }
]


def now_rfc3339():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
