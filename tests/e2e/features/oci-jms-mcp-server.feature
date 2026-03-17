# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

Feature: OCI JMS MCP Server
  Scenario: List the JMS tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What JMS mcp tools do you have"
    Then the response should contain a list of JMS tools available

  Scenario: List JMS fleets
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my JMS fleets"
    Then the response should contain a list of JMS fleets

  Scenario: Get fleet details and fleet configuration
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my JMS fleets, then get the details of the first JMS fleet in the list, then get the fleet agent configuration and advanced feature configuration for that fleet"
    Then the response should contain fleet configuration details

  Scenario: List JMS plugins and get the first plugin
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my JMS fleets, then list the JMS plugins in the first fleet, then get the details of the first JMS plugin"
    Then the response should contain JMS plugin details

  Scenario: List installation sites and summarize managed instance usage
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my JMS fleets, then list the installation sites in the first JMS fleet, then summarize managed instance usage for that same fleet"
    Then the response should contain installation site and managed instance usage details

  Scenario: Summarize JMS resource inventory
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "summarize my JMS resource inventory"
    Then the response should contain JMS resource inventory details
