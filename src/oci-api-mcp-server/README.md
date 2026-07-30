# OCI API MCP Server

## Overview

This server provides tools to run OCI CLI commands to interact with the OCI services.
It includes tools to help with OCI command execution and provide helpful information.

## Running the server

### STDIO transport mode

```sh
uvx oracle.oci-api-mcp-server
```

### HTTP streaming transport mode

`oracle.oci-api-mcp-server` supports `stdio` only.

## Tools

| Tool Name | Description |
| --- | --- |
| get_oci_command_help | Returns helpful instructions for running an OCI CLI command. Only provide the command after 'oci', do not include the string 'oci' in your command. |
| run_oci_command | Runs an OCI CLI command. This tool allows you to run OCI CLI commands on the user's behalf. Only provide the command after 'oci', do not include the string 'oci' in your command. |
| get_oci_commands (Resource) | Returns helpful information on various OCI services and related commands. |

⚠️ **NOTE**: All actions use the configured OCI CLI profile. `OCI_CLI_AUTH` is authoritative:
when it is set, `run_oci_command` adds no authentication override and lets the OCI CLI select
authentication. Otherwise, `run_oci_command` resolves `OCI_MCP_AUTH_TYPE` using
`oracle-mcp-common`. Supported values are `api_key`, `security_token`, `instance_principal`,
`resource_principal`, and `oke_workload_identity`. `auto` selects API-key or session-token
authentication from the selected profile's direct configuration. The server rejects unclassifiable
`auto` profiles and auth modes without OCI CLI equivalents (`identity_domain_upst`,
`instance_principal_delegation`, and `resource_principal_delegation`).

The server owns OCI CLI authentication and connection configuration. Commands cannot supply
global overrides such as `--auth`, `--profile`, `--config-file`, `--endpoint`, or `--proxy`.
Use least-privilege IAM and protect secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
