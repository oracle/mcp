# OCI Fusion Applications (FAaaS) MCP Server

## Overview

This server provides tools for interacting with Oracle Cloud Infrastructure (OCI) Fusion Applications (FAaaS) via the OCI Python SDK `oci.fusion_apps.FusionApplicationsClient`.

## Running the server

```sh
uv run oracle.oci-faaas-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| list_fusion_environment_families | List Fusion Environment Families in a compartment |
| list_fusion_environments | List Fusion Environments in a compartment (optionally by family) |
| get_fusion_environment | Get details of a Fusion Environment by OCID |
| get_fusion_environment_status | Get status of a Fusion Environment by OCID |

Notes:
- All list tools handle pagination.
- Responses are converted to plain dictionaries using best-effort conversion of OCI SDK models.

⚠️ NOTE: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0 as shown at  
https://oss.oracle.com/licenses/upl/
