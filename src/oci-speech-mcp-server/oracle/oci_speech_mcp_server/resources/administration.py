"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from fastmcp import FastMCP

INDEX_GUIDE = """# OCI Speech MCP guide

Available guides:
- `speech://guides/prerequisites`: authentication, IAM, regions, and local roots.
- `speech://guides/policies`: step-by-step Speech, Object Storage, and TTS IAM policy setup.
- `speech://guides/service-limits`: file, job, TTS, Realtime, retention, and region limits.
- `speech://guides/transcription`: job, task, local-file, and result workflows.
- `speech://guides/text-to-speech`: voices, models, SSML, and output formats.
- `speech://guides/ssml`: supported tags, constraints, safe composition, and examples.
- `speech://guides/customizations`: entity lists, pronunciations, reference examples, and datasets.
- `speech://guides/notifications`: OCI Events and Notifications setup.
- `speech://guides/realtime`: safe client-side Realtime Speech integration.

Prefer a workflow prompt when the user has an outcome rather than a single API operation.
"""

PREREQUISITES_GUIDE = """# Prerequisites

1. Configure an OCI SDK credential mode supported by `oracle-mcp-common` (API key,
   security token, instance principal, resource principal, workload identity, or
   a supported delegation mode). Never pass credentials as tool arguments.
2. Read `speech://guides/policies`. Transcription and customization require
   access to `ai-service-speech-family`; local workflows also require access to
   the selected Object Storage buckets. Notification setup additionally
   requires Notifications topics/subscriptions and Events rules.
3. Text-to-speech currently runs in `us-phoenix-1`; the server safely routes only
   text-to-speech calls there. Other calls use the configured OCI region.
4. For local transcription, set `OCI_SPEECH_INPUT_ROOT` to the only directory
   the server may read. Optionally set `OCI_SPEECH_OUTPUT_ROOT`; otherwise output
   goes to `~/.oci-speech-mcp/outputs`.
5. Read `speech://guides/service-limits` before planning bulk, long-running,
   realtime, or text-to-speech workloads.
"""

POLICIES_GUIDE = """# OCI Speech IAM policy setup

Only members of the tenancy Administrators group have Speech access by default.
For other users, an administrator must create a policy in the tenancy or in a
parent compartment that governs the target compartment. Replace the placeholder
names below; do not paste angle brackets into the final policy.

## Standard Speech and Object Storage workflow

For transcription jobs, customizations, and their CRUDL operations in one
compartment, grant the user group the aggregate Speech resource. Local-file and
Object Storage transcription also needs object access:

```text
allow group <group-name> to manage ai-service-speech-family in compartment <compartment-name>
allow group <group-name> to manage object-family in compartment <compartment-name>
```

Use `in tenancy` instead of `in compartment ...` only when tenancy-wide access
is deliberate. Scope Object Storage more narrowly with IAM conditions when your
governance model requires access to specific buckets. The MCP server cannot
create IAM policies; a tenancy administrator must review and apply them.

## Text-to-speech-only users

When a group needs synthesis but not transcription/customization management,
the Speech policy reference exposes these individual resource types:

```text
allow group <group-name> to manage ai-service-speech-synthesize-voice in compartment <compartment-name>
allow group <group-name> to manage ai-service-speech-synthesize in compartment <compartment-name>
```

## Tags and notification setup

If requests use defined tags, add only the tag namespace permissions required
by your tagging policy. The official Speech examples use read and inspect access
to tag namespaces. The notification setup tool also needs permission to manage
Notifications topics/subscriptions and Events rules, plus permission for the
Events service to publish to the selected topic; see
`speech://guides/notifications`.

## Troubleshooting authorization

1. Confirm the authenticated principal is a member of the intended group or
   dynamic group and that the policy was created in the correct parent scope.
2. Confirm the configured Speech region and resource compartment match the
   policy target.
3. For local transcription, check both Speech and Object Storage permissions;
   upload, job creation, output write, and result download are separate calls.
4. Record the tool's OCI request ID when asking an administrator or Oracle
   Support to investigate an authorization failure. Never share credentials or
   signed request headers.

Official policy reference:
https://docs.oracle.com/en-us/iaas/Content/speech/using/policies.htm
"""

SERVICE_LIMITS_GUIDE = """# OCI Speech service limits

Current documented limits for every enabled region are:

- Media file size: at most 2 GB.
- Media duration: at most four hours.
- Transcription job: at most 100 tasks.
- Job metadata retention: 90 days.
- Text-to-speech input: at most 10,000 characters per request, including SSML
  markup when SSML is used.
- Live Transcribe: at most 10 concurrent sessions per tenancy. Request a limit
  increase through Oracle Support before designing for greater concurrency.
- Text-to-speech availability: the service is currently limited to the
  `us-phoenix-1` commercial region.

The local-file tool validates supported suffix, local containment, and the 2 GB
size limit. It does not decode media to prove duration or audio format, so the
caller must verify the four-hour limit and that the media bytes match a supported
codec. Split larger workloads before submission and keep every job at or below
100 objects. Export results you need to retain beyond the service's 90-day job
metadata window.

Limits can change. For production capacity planning, verify the current service
documentation:
https://docs.oracle.com/en-us/iaas/Content/speech/using/speech.htm#ser-limits
"""


def index_guide() -> str:
    return INDEX_GUIDE


def prerequisites_guide() -> str:
    return PREREQUISITES_GUIDE


def policies_guide() -> str:
    return POLICIES_GUIDE


def service_limits_guide() -> str:
    return SERVICE_LIMITS_GUIDE


def register_resources(mcp: FastMCP) -> None:
    mcp.resource(
        "speech://guides/index",
        description="Index of OCI Speech MCP guides.",
    )(index_guide)
    mcp.resource(
        "speech://guides/prerequisites",
        description="OCI Speech authentication, IAM, region, and local-root prerequisites.",
    )(prerequisites_guide)
    mcp.resource(
        "speech://guides/policies",
        description="Step-by-step OCI IAM policies for Speech and related workflows.",
    )(policies_guide)
    mcp.resource(
        "speech://guides/service-limits",
        description="OCI Speech file, job, TTS, Realtime, retention, and region limits.",
    )(service_limits_guide)

