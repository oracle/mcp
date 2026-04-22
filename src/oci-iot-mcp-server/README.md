# OCI IoT Platform MCP Server

## Overview

This server provides MCP tools for interacting with the Oracle Cloud Infrastructure (OCI) IoT Platform
service. It includes:

- OCI IoT management tools backed by the Python SDK
- OCI IoT Data API tools backed by the OCI Internet of Things Platform Data API
- Operator-friendly wrappers for friendly identifier lookup, ORDS token minting, and polling workflows

## Running the server

```sh
uv run oracle.oci-iot-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| get_digital_twin_adapter | Retrieves a specific digital twin adapter by its identifier |
| get_digital_twin_adapter_full | Returns the full mapped digital twin adapter payload for debugging and migration workflows |
| get_digital_twin_instance | Retrieves a specific digital twin instance by its identifier |
| get_digital_twin_instance_content | Retrieves the content of a specific digital twin instance by its identifier |
| get_digital_twin_model | Retrieves a specific digital twin model by its identifier |
| get_digital_twin_model_spec | Retrieves the specification of a specific digital twin model by its identifier |
| create_digital_twin_model | Creates a new digital twin model in a specified IoT domain |
| create_digital_twin_adapter | Creates a new digital twin adapter in a specified IoT domain |
| create_digital_twin_instance | Creates a new digital twin instance in a specified IoT domain |
| create_digital_twin_relationship | Creates a new digital twin relationship in a specified IoT domain |
| get_digital_twin_relationship | Retrieves a specific digital twin relationship by its identifier |
| delete_digital_twin_adapter | Deletes a specific digital twin adapter by its identifier |
| delete_digital_twin_instance | Deletes a specific digital twin instance by its identifier |
| delete_digital_twin_model | Deletes a specific digital twin model by its identifier |
| delete_digital_twin_relationship | Deletes a specific digital twin relationship by its identifier |
| update_digital_twin_adapter | Updates a specific digital twin adapter by its identifier |
| update_digital_twin_instance | Updates a specific digital twin instance by its identifier |
| update_digital_twin_model | Updates a specific digital twin model by its identifier |
| update_digital_twin_relationship | Updates a specific digital twin relationship by its identifier |
| derive_domain_context | Derives normalized IoT domain context for ORDS and operator workflows |
| get_data_api_token | Mints and returns an IoT Data API bearer token plus the resolved domain context |
| get_raw_command_by_request_id | Fetches the raw command detail record for an ORDS request ID |
| create_iot_domain | Creates a new IoT domain in a specified IoT domain group |
| create_iot_domain_group | Creates a new IoT domain group in a specified compartment |
| change_iot_domain_compartment | Moves a specific IoT domain to a different compartment |
| change_iot_domain_data_retention_period | Changes the data retention period configuration for a specific IoT domain |
| change_iot_domain_group_compartment | Moves a specific IoT domain group to a different compartment |
| configure_iot_domain_data_access | Configures data access for a specific IoT domain |
| configure_iot_domain_group_data_access | Configures data access for a specific IoT domain group |
| update_iot_domain | Updates a specific IoT domain by its identifier |
| update_iot_domain_group | Updates a specific IoT domain group by its identifier |
| delete_iot_domain | Deletes a specific IoT domain by its identifier |
| delete_iot_domain_group | Deletes a specific IoT domain group by its identifier |
| invoke_raw_command | Invokes a raw command on a specific digital twin instance |
| invoke_raw_command_and_wait | Invokes a raw command on a digital twin instance and waits for a terminal data-plane result |
| get_iot_domain | Retrieves a specific IoT domain by its identifier |
| get_iot_domain_group | Retrieves a specific IoT domain group by its identifier |
| get_work_request | Retrieves a specific work request by its identifier |
| list_digital_twin_adapters | Lists digital twin adapters in a specified IoT domain |
| list_digital_twin_models | Lists digital twin models in a specified IoT domain |
| list_digital_twin_instances | Lists digital twin instances in a specified IoT domain |
| list_digital_twin_relationships | Lists digital twin relationships in a specified IoT domain |
| list_iot_domain_groups | Lists IoT domain groups in a specified compartment |
| list_iot_domains | Lists IoT domains in a specified compartment |
| list_work_request_errors | Lists errors for a specific work request |
| list_work_request_logs | Lists logs for a specific work request |
| list_work_requests | Lists work requests in a specified compartment |
| list_compartments | Lists all OCI compartments that the current user has access to |
| list_raw_data | Lists raw data records from the Oracle IoT Data API for a specific IoT domain |
| get_raw_data | Gets a raw data record by identifier from the Oracle IoT Data API for a specific IoT domain |
| list_rejected_data | Lists rejected data records from the Oracle IoT Data API for a specific IoT domain |
| get_rejected_data | Gets a rejected data record by identifier from the Oracle IoT Data API for a specific IoT domain |
| list_snapshot_data | Lists snapshot data records from the Oracle IoT Data API for a specific IoT domain |
| list_historized_data | Lists historized data records from the Oracle IoT Data API for a specific IoT domain |
| get_historized_data | Gets a historized data record by identifier from the Oracle IoT Data API for a specific IoT domain |
| list_raw_command_data | Lists raw command data records from the Oracle IoT Data API for a specific IoT domain |
| get_raw_command_data | Gets a raw command data record by identifier from the Oracle IoT Data API for a specific IoT domain |
| get_twin_platform_context | Returns the control-plane and domain-context resources that explain how a twin is wired into OCI IoT |
| get_latest_twin_state | Returns the latest observed snapshot, historized, raw-command, and rejected-data records for a twin |
| validate_twin_readiness | Passively validates whether a twin is reporting snapshot data |
| list_recent_raw_commands_for_twin | Lists recent raw command records for a digital twin instance |
| list_recent_rejected_data_for_twin | Lists recent rejected ingest records for a digital twin instance |
| wait_for_twin_update | Waits for a twin snapshot update after a given timestamp |
| health_check | Health check endpoint for the OCI IoT MCP server |

## Configuration

The server supports multiple OCI SDK authentication modes through `OCI_IOT_AUTH_TYPE`.

Supported values:

- `auto`
- `security_token`
- `api_key`
- `instance_principal`
- `resource_principal`
- `instance_principal_delegation`
- `resource_principal_delegation`
- `oke_workload_identity`

If `OCI_IOT_AUTH_TYPE` is not set, the server defaults to `auto`.

`auto` uses the OCI configuration profile specified by `OCI_CONFIG_PROFILE` and behaves as follows:

1. If the selected profile has a usable `security_token_file`, the server uses session-token auth.
2. Otherwise, it falls back to standard API-key auth from the same profile.

`OCI_CONFIG_PROFILE` still applies to `auto`, `security_token`, and `api_key`. If not set, it defaults to
`DEFAULT`.

`instance_principal` is intended for code running on OCI compute instances with instance principal access.

`resource_principal` is intended for OCI runtime environments that expose resource principal credentials.

`instance_principal_delegation` and `resource_principal_delegation` require
`OCI_IOT_DELEGATION_TOKEN`.

`oke_workload_identity` is intended for OKE workload identity environments. You can optionally override the
service account token source with either:

- `OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN`
- `OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN_PATH`

If both are set, `OCI_IOT_OKE_SERVICE_ACCOUNT_TOKEN` takes precedence.

Identity-scoped paths that need an explicit tenancy OCID, such as `list_compartments`, may also require:

- `OCI_IOT_TENANCY_ID_OVERRIDE`

`auto` still only covers profile-backed security-token and API-key flows. It does not auto-detect
delegation-token or OKE workload-identity auth.

For the direct OCI IoT Data API tools, you can also provide a bearer token through the
`OCI_IOT_DATA_API_ACCESS_TOKEN` environment variable.

For ORDS-backed operator tools, set:

- `OCI_IOT_ORDS_CLIENT_ID`
- `OCI_IOT_ORDS_CLIENT_SECRET`
- `OCI_IOT_ORDS_USERNAME`
- `OCI_IOT_ORDS_PASSWORD`

## Usage Notes

- `get_digital_twin_instance_content` supports `should_include_metadata=true` to include digital twin
  instance metadata in the response payload.
- List-style SDK tools return a structured payload with a `result` field containing the list of items.
- Custom operator tools return stable `{ "ok": true, "data": ... }` or `{ "ok": false, "error": ... }`
  envelopes.
- String-returning tools such as `get_digital_twin_instance_content` and `get_digital_twin_model_spec`
  return plain text content.

## Agent Workflow Guidance

- `get_twin_platform_context` is the best first call when an agent needs to understand how a twin maps to
  its domain, domain group, adapter, model, and ORDS/Data API context.
- `get_latest_twin_state` is the best current-state call when an agent needs the newest observed
  snapshot, historized, raw-command, and rejected-data records without manually querying each collection.
- `validate_twin_readiness` is the passive health check when an agent needs to confirm selector
  resolution, domain context, ORDS credential presence, token minting, and whether snapshot data is
  actually arriving.
- These tools intentionally return structured teaching payloads rather than raw ORDS collection pages so
  an agent can reason about topology and state with fewer follow-up calls.

## Friendly Identifier Rules

- `digital_twin_instance_id` and `iot_domain_id` work directly.
- Domain display-name lookup and `domain_short_id` lookup require `compartment_id` so the server
  can scope the control-plane search before returning a short identifier.
- Twin display-name lookup requires the IoT domain selector to resolve first; the twin lookup never
  runs without an identified domain context.
- Ambiguous friendly matches fail with `ambiguous_identifier` and list candidate identifiers so
  the caller can prompt for a retry with a specific choice.
- Short IDs are derived from the control-plane resources instead of being memorized; helpers such as
  `get_data_api_token` and `derive_domain_context` can surface those identifiers once the related
  domain context is resolved.

## ORDS Credentials And Token Behavior

- `get_data_api_token` returns a live bearer token and expiry metadata to the MCP caller.
- Treat the returned bearer token as a secret and do not log, persist, or echo it beyond the intended
  caller.
- Tokens are minted in-memory per call, are not cached across tool invocations, and must never be
  logged.
- `get_twin_platform_context`, `get_latest_twin_state`, `validate_twin_readiness`,
  `invoke_raw_command_and_wait`, `get_raw_command_by_request_id`, `list_recent_raw_commands_for_twin`,
  `list_recent_rejected_data_for_twin`, and `wait_for_twin_update` resolve ORDS access automatically
  from the provided domain and twin selectors.
- When the ORDS credentials (`OCI_IOT_ORDS_CLIENT_ID`, `OCI_IOT_ORDS_CLIENT_SECRET`, `OCI_IOT_ORDS_USERNAME`,
  and `OCI_IOT_ORDS_PASSWORD`) are configured, `get_data_api_token`, `get_latest_twin_state`, and
  `validate_twin_readiness` can mint tokens on the caller’s behalf without an explicit bearer token
  input. Callers can still supply a pre-minted token via `access_token` if they prefer to reuse it.
- `list_recent_raw_commands_for_twin` and `list_recent_rejected_data_for_twin` enforce a `limit` in the
  range `1` to `100`; values outside that range result in validation failures.
- `wait_for_twin_update` always requires the `since` argument and the value must be a valid RFC 3339
  timestamp so the helper can poll after the specified cursor.

## IoT Data API Notes

- These tools target the **OCI Internet of Things Platform Data API**, not the older Oracle Internet of
  Things Cloud Service product.
- Direct Data API tools require `iot_domain_group_short_id` and `iot_domain_short_id`.
- Direct list/get raw, snapshot, historized, rejected, and rawCommand helpers also require an
  `access_token` parameter unless the `OCI_IOT_DATA_API_ACCESS_TOKEN` environment variable is set.
- The Data API also requires a bearer token. Pass it with the `access_token` parameter or set
  `OCI_IOT_DATA_API_ACCESS_TOKEN`.
- If `region` is omitted, the tools default to the region in the configured OCI profile.
- List-style Data API tools accept optional `query_params` as an object or JSON string and pass them
  through to the API query string.
- The Data API base URL format is:

```text
https://{iot_domain_group_short_id}.data.iot.{region}.oci.oraclecloud.com/ords/{iot_domain_short_id}
```

## Examples

Get digital twin instance content with metadata:

```json
{
  "tool": "get_digital_twin_instance_content",
  "arguments": {
    "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..example",
    "should_include_metadata": true
  }
}
```

Resolve a domain context and mint a Data API token for operator workflows:

```json
{
  "tool": "get_data_api_token",
  "arguments": {
    "iot_domain_id": "ocid1.iotdomain.oc1..example"
  }
}
```

Explain how a configured twin is wired into OCI IoT:

```json
{
  "tool": "get_twin_platform_context",
  "arguments": {
    "digital_twin_instance_name": "pump-17",
    "iot_domain_id": "ocid1.iotdomain.oc1..example"
  }
}
```

Get the latest observed records for a twin:

```json
{
  "tool": "get_latest_twin_state",
  "arguments": {
    "digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..example"
  }
}
```

Passively validate whether a twin is reporting snapshot data:

```json
{
  "tool": "validate_twin_readiness",
  "arguments": {
    "digital_twin_instance_name": "pump-17",
    "iot_domain_id": "ocid1.iotdomain.oc1..example"
  }
}
```

List raw data from the OCI IoT Data API:

```json
{
  "tool": "list_raw_data",
  "arguments": {
    "iot_domain_group_short_id": "exampleDomainGroupShortId",
    "iot_domain_short_id": "exampleDomainShortId",
    "query_params": {
      "limit": 50
    }
  }
}
```

Invoke a raw command and wait for the resulting data-plane record by friendly twin name:

```json
{
  "tool": "invoke_raw_command_and_wait",
  "arguments": {
    "digital_twin_instance_name": "pump-17",
    "iot_domain_id": "ocid1.iotdomain.oc1..example",
    "request_endpoint": "/commands/reboot",
    "request_data_format": "JSON",
    "request_data": {
      "force": true
    }
  }
}
```

## Security

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile or Data API
bearer token. We advise least-privilege IAM setup, secure credential management, safe network practices,
secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining
and providing all required licenses and copyright notices for the third-party code used in order to
ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model
selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at
<https://oss.oracle.com/licenses/upl/>.
