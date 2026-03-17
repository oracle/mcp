# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Usage MCP Server
  Scenario: List the usage tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What usage mcp tools do you have"
    Then the response should contain a list of usage tools available

  Scenario: Get summarized usage
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "Get the summarized usage for tenant ocid1.tenancy.oc1..mock from 2025-01-01T00:00:00Z to 2025-01-03T00:00:00Z"
    Then the response should contain a list of usage summaries