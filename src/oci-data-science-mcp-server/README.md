# OCI Data Science MCP Server

## Overview

This server provides tools to interact with the OCI Data Science resources.
It includes tools to help with common tasks with OCI Data Science.

## Installing dependencies
```sh

# cd to path you cloned the oci-data-science-mcp-server
cd /path/to/oci-data-science-mcp-server

# Create a new venv
uv venv .venv

# sync dependencies
uv sync
```

## Running the server manually

```sh
uv run oracle.oci-data-science-mcp-server
```

## Example MCP Config JSON
```
{
  "mcpServers": {
    "oracle-oci-data-science-mcp-server": {
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "oracle.oci-data-science-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "VIRTUAL_ENV": "/path/to/mcp/.venv",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| oci_ds_compartments | List OCI compartments in the tenancy (including sub-compartments). Use this tool when the user provides a compartment *name* and you need the compartment OCID. |
| data_science_projects | Manage OCI Data Science Projects. Supports create, list, update, delete, and count. Use 'list' to discover project OCIDs. |
| data_science_model_catalog | Manage the OCI Data Science Model Catalog. Supports listing models, counting, downloading model artifacts, and interacting with Model Version Sets. |
| data_science_jobs | Manage OCI Data Science Jobs. Supports creating jobs from scripts or container images, listing jobs, retrieving details, updating, and deleting jobs. |
| data_science_job_runs | Manage OCI Data Science Job Runs. Supports starting runs, listing runs, getting status, and cancelling runs. |
| data_science_notebook_sessions | Manage OCI Data Science Notebook Sessions. Supports create, activate, stop, delete, and list. Notebook session URLs can be used to open the session in the OCI console. |
| data_science_pipelines | Manage OCI Data Science Pipelines. Supports list, details, and delete. |
| data_science_pipeline_runs | Manage OCI Data Science Pipeline Runs. Supports starting runs, listing runs, and retrieving status. |
| data_science_model_deployments | Manage OCI Data Science Model Deployments. Supports deploy, list, activate, deactivate, and delete. Deploy uses ADS GenericModel.deploy for conda-based deployments. |

⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
