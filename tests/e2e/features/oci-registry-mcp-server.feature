# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Registry MCP Server
  Scenario: List the registry tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What registry mcp tools do you have"
    Then the response should contain a list of registry tools available

  Scenario: List container repositories
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my container repositories and limit to 5"
    Then the response should contain a list of container repositories

  Scenario: Get container repository details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my container repositories and limit to 5, then get the details of the first repository in the list"
    Then the response should contain the details of a container repository
