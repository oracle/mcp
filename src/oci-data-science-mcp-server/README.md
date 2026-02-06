# OCI Data Science MCP Server

## Overview

This server provides tools to interact with the OCI Data Science resources.
It includes tools to help with common tasks with OCI Data Science.

## Running the server

```sh
uv run oracle.oci-data-science-mcp-server
```

## Tools

| Tool Name | Description |
| --- | --- |
| get_compartment_id | Get a list of Compartment OCID by Compartment name for use with other tools. |
| project_count | Get count of OCI Data Science Projects |
| create_project | Create new OCI Data Science Project with project name and description. |
| model_count | Returns number of models saved to model catalog in OCI Data Science for a given compartment |
| list_projects | returns a list of OCI Data Science Projects by Project Name, Project ID and Project Description as a dictionary |
| create_notebook_session | Creates a managed Notebook Session on OCI Data Science in a given Project and Compartment. |
| list_model_version_set_attributes | List attributes of a Model Version Set. |
| list_model_version_sets | List all Model Version Sets in a compartment with their IDs and names. |
| download_model_artefact | Download model artifact from the catalog. |
| create_job_from_script | Create a job from a script. Currently only implemented to support service_conda runtimes. |
| list_models | List models in the model catalog. |
| list_jobs | List all jobs in a compartment with their IDs and names. |
| job_details_by_id | List jobs information for a job based on its Job ID. |
| list_pipelines | List all pipelines in a compartment with their IDs and names. |
| pipelines_details_by_id | List pipeline details by Pipeline ID. |
| start_job_run | Start a job run. |
| start_pipeline_run | Start a pipeline run. Use list_pipelines to find the pipeline_id by name. give the run a meaningful name if possible. |
| create_job_from_container_image | Create a job from a container image. |
| delete_project | Delete an OCI Data Science Project. Find the Project ID by calling List Projects and finding the Project ID associated with a Project Name. |
| activate_notebook_session | Activates a notebook session. Use list_notebook_sessions to find a notebook session id by name. |
| delete_notebook_session | Delete a notebook session. |
| stop_notebook_session | Stop (deactivate) a notebook session. |
| delete_job | Delete a job. |
| delete_pipeline | Delete a pipeline. |
| deploy_model | Deploy a model from the catalog as a model deployment. Only works for Conda based runtimes currently. Assumes you have already saved the model to the model catalog separately |
| activate_model_deployment | Activate an existing model deployment. |
| deactivate_model_deployment | Deactivate (stop) a running model deployment. |
| list_notebook_sessions | List all notebook sessions in a compartment with their IDs, names, and statuses. |
| update_project | Update an existing project's details such as name or description. |
| list_model_deployments | List all model deployments in a compartment with their IDs, names, and statuses. |
| get_pipeline_run_status | Get the status and details of the most recent pipeline run for a given pipeline. This tool can be used to: - get the current status - get the started, accepted or finished date and time |
| get_job_run_status | Get the status and details of the most recent job run for a given job. This tool can be used to: - get the current status - get the started, accepted or finished date and time |
| list_job_runs | List all runs for a specific job, including their statuses and details. |
| cancel_job_run | Cancel a currently running job run. |
| list_pipeline_runs | List all runs for a specific pipeline, including statuses and details. |
| delete_model_deployment | Delete a model deployment. |


⚠️ **NOTE**: All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.
