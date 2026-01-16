# End-to-End Tests for OCI MCP Servers

## Introduction

This directory contains end-to-end tests for the OCI MCP Servers using the [Behave framework](https://behave.readthedocs.io/en/latest/).

## Prerequisites

1. Ensure that you have `uv` installed from the [Quick Start](https://github.com/oracle/mcp#quick-start) section of the main README.
2. Ensure that you have your local development environment set up from the [Local development](https://github.com/oracle/mcp#local-development) section of the main README.
3. Ensure that you have downloaded `ollama`, started the `ollama` server, and fetched a large language model (e.g. gpt-oss:20b) from the [Client configuration - MCPHost](https://github.com/oracle/mcp#mcphost) section of the main README.
   1. When following the instructions in the step above, there is no need to start `mcphost` for these E2E tests. You only need to install and start `ollama` for running these tests.

## Configuration

1. In the `tests/e2e/features` directory, copy `.env.template` to `.env`.
2. Fill in the required environment variables in `.env`:
   - MCP_HOST_FILE: The .json configuration file holding your MCP server configurations. Defaults to the absolute path of the existing tests/e2e/features/mcphost.json file.
   - URL: The URL to send the LLM prompts to. Defaults to http://localhost:8000/api/chat (Ollama's chat endpoint).
   - MODEL: LLM model that you are running. This should be the model that you fetched in the prerequisites section. Defaults to gpt-oss:20b.

   You can copy the following into a `.env` file
   ```bash
   MCP_HOST_FILE=
   URL=
   MODEL=
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

