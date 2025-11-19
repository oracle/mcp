# OCI Recovery Service MCP Server

## Overview

This server provides tools to interact with the OCI Recovery Service resources.
It includes tools to help with viewing Recovery Service configurations.

## Running the server

```sh
uv run oracle.oci-recovery-service-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_databases_using_recovery_service | Lists the databases using the Recovery Service along with their detail |
| list_compartments | List compartments available. listing protected databases requires a compartment |
| get_tenancy_cost_summary | List tenancy usage for recovery service only |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.

