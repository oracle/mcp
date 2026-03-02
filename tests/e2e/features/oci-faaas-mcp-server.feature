# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Fusion Applications (FaaS) MCP Server
  Scenario: List the FaaS tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What fusion applications (faaas) mcp tools do you have"
    Then the response should contain a list of faaas tools available

  Scenario: List Fusion Environment Families
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list fusion environment families"
    Then the response should contain a list of fusion environment families

  Scenario: List Fusion Environments
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list fusion environments"
    Then the response should contain a list of fusion environments

  Scenario: Get Fusion Environment details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list fusion environments and then get the details of the first one"
    Then the response should contain the details of a fusion environment

  Scenario: Get Fusion Environment status
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "get the status of the first fusion environment"
    Then the response should contain the status of a fusion environment
