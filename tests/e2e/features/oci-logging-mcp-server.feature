# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Logging MCP Server
  Scenario: List the logging tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What logging mcp tools do you have"
    Then the response should contain a list of logging tools available

  Scenario: List log groups
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my log groups"
    Then the response should contain a list of log groups

  Scenario: Get log group details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my log groups, then get the details of the first log group in the list"
    Then the response should contain the details of a log group

  Scenario: List logs in a log group
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my log groups and list the logs for the first log group"
    Then the response should contain a list of logs

  Scenario: Get log details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my log groups and list the logs for the first log group, then fetch the details of the first log in that list"
    Then the response should contain the details of a log
