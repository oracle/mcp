# End-to-End Tests for OCI MCP Servers

## Introduction

This directory contains end-to-end tests for the OCI MCP Servers using the Behave framework.

## Prerequisites

1. Ensure you have the necessary OCI configuration set up on your system.

## Configuration

1. In the e2e directory, copy `.env.template` to `.env`.
2. Fill in the required environment variables in `.env`:
   - TENANCY_OCID: Your Oracle Cloud tenancy OCID.
   - TENANCY_NAME: Your Oracle Cloud tenancy name.
   - COMPARTMENT_OCID: The OCID of the compartment to test against (defaults to TENANCY_OCID if not set).
   - USER_OCID: Your Oracle Cloud user OCID.
   - USER_NAME: Your Oracle Cloud user name.
   - REGION: Your home region name (defaults to us-ashburn-1 if not set)
   - MODEL: LLM model that you are running (defaults to got-oss:20b if not set)
   
   You can copy the following into a `.env` file
   ```bash
   TENANCY_OCID=
   TENANCY_NAME=
   COMPARTMENT_OCID=
   USER_OCID=
   USER_NAME=
   REGION=
   MODEL=

## Running the Tests

1. Ensure the `ollama` is installed and started. 
2. Following the instructions in the [Getting Started - MCPHost](https://github.com/shrug-labs/oci-mcp#mcphost) section.
2. Run the tests using the command:
   ```bash
   cd tests/e2e
   behave

## Notes

- The tests use the configuration from the `.env` file.
- The `mcphost.json` file is used to configure the MCP server.


----
<small>Copyright (c) 2025, Oracle and/or its affiliates. Licensed under the [Universal Permissive License v1.0](https://oss.oracle.com/licenses/upl).</small>

