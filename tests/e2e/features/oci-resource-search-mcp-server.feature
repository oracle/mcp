# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Resource Search MCP Server
  Scenario: List the resource search tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What resource search mcp tools do you have"
    Then the response should contain a list of resource search tools available

  Scenario: List supported resource types
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list the resource search resource types and limit to 5"
    Then the response should contain a list of resource types

  Scenario: List all resources in a compartment
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list all resources for tenant ocid1.tenancy.oc1..mock in compartment ocid1.tenancy.oc1..mock and limit to 10"
    Then the response should contain a list of resources

  Scenario: Search resources by display name
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "search for resources in compartment ocid1.tenancy.oc1..mock for tenant ocid1.tenancy.oc1..mock with display name Mock-Server-1"
    Then the response should contain resources matching the display name search

  Scenario: Free-form search for resources
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "free text search for resources for tenant ocid1.tenancy.oc1..mock containing the text mock"
    Then the response should contain resources matching the free-text search

  Scenario: Search resources by type
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "search for resources by type subnet for tenant ocid1.tenancy.oc1..mock in compartment ocid1.tenancy.oc1..mock"
    Then the response should contain resources of the specified type
