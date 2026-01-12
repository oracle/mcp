# End-to-End Tests for OCI MCP Servers

## Introduction

This directory contains end-to-end tests for the OCI MCP Servers using the [Behave framework](https://behave.readthedocs.io/en/latest/).

## Prerequisites

1. Ensure that you have `uv` installed from the [Quick Start](https://github.com/oracle/mcp#quick-start) section of the main README.
2. Ensure that you have your OCI profile set up from the [Authentication](https://github.com/oracle/mcp#authentication) section of the main README.
3. Ensure that you have your local development environment set up from the [Local development](https://github.com/oracle/mcp#local-development) section of the main README.
4. Ensure that you have downloaded `ollama`, started the `ollama` server, and fetched a large language model from the [Client configuration - MCPHost](https://github.com/oracle/mcp#mcphost) section of the main README.
   1. When following the instructions in the step above, there is no need to start `mcphost` for these E2E tests. You only need to install and start `ollama` for running these tests.

## Configuration

1. In the `tests/e2e/features` directory, copy `.env.template` to `.env`.
2. Fill in the required environment variables in `.env`:
   - TENANCY_OCID: Your Oracle Cloud tenancy OCID.
   - TENANCY_NAME: Your Oracle Cloud tenancy name.
   - COMPARTMENT_OCID: The OCID of the compartment to test against (defaults to TENANCY_OCID if not set).
   - USER_OCID: Your Oracle Cloud user OCID.
   - USER_NAME: Your Oracle Cloud user name.
   - REGION: Your home region name (defaults to us-ashburn-1 if not set)
   - MODEL: LLM model that you are running (defaults to gpt-oss:20b if not set). This should be the model that you fetched in the prerequisites section.
   - OCI_CONFIG_PROFILE: The name of your OCI profile set up in the prerequisites section (defaults to DEFAULT if not set).
   
   You can copy the following into a `.env` file
   ```bash
   TENANCY_OCID=
   TENANCY_NAME=
   COMPARTMENT_OCID=
   USER_OCID=
   USER_NAME=
   REGION=
   MODEL=
   OCI_CONFIG_PROFILE=
   ```

## Running the Tests

1. If you have not already activated your virtual environment from the [Local development](https://github.com/oracle/mcp#local-development) section, please do so.
2. In the `tests` directory, install the test dependencies using this command: `uv pip install .`
3. In the `tests/e2e` directory, run all of the tests by using this command: `behave`
   1. Run specific features by using this command: `behave features/<name of your feature file>`. Example: `behave features/oci-compute-mcp-server.feature`
   2. Run specific scenarios by using this command: `behave -n "Name of your scenario"`. Example: `behave -n "OCI Compute MCP Server"`

## Notes

- The tests use the configuration from the `.env` file.
- The `mcphost.json` file is used to configure the MCP server.

----
<small>Copyright (c) 2025, Oracle and/or its affiliates. Licensed under the [Universal Permissive License v1.0](https://oss.oracle.com/licenses/upl).</small>

