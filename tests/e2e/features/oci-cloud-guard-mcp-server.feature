# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Cloud Guard MCP Server
  Scenario: List the Cloud Guard tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What cloud guard mcp tools do you have"
    Then the response should contain a list of cloud guard tools available

  Scenario: List Cloud Guard problems
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my cloud guard problems for the past 30 days"
    Then the response should contain a list of cloud guard problems

  Scenario: Get Cloud Guard problem details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my cloud guard problems for the past 30 days, then get the details of the first problem in the list"
    Then the response should contain the details of a cloud guard problem
