# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Identity MCP Server
  Scenario: List the identity tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What identity mcp tools do you have"
    Then the response should contain a list of identity tools available

  Scenario: List compartments
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my compartments"
    Then the response should contain a list of compartments

  Scenario: Get tenancy details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "get my tenancy details"
    Then the response should contain the details of a tenancy

  Scenario: List availability domains
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list availability domains"
    Then the response should contain a list of availability domains

  Scenario: Get current user
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "show me my user details"
    Then the response should contain the details of a user

  Scenario: List subscribed regions
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my subscribed regions"
    Then the response should contain a list of regions
