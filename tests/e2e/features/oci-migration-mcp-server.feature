# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Migration MCP Server
  Scenario: List the migration tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What migration mcp tools do you have"
    Then the response should contain a list of migration tools available

  Scenario: List migrations in a compartment
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my migrations"
    Then the response should contain a list of migrations

  Scenario: Get a migration by OCID
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my migrations, then get the details of the first migration in the list"
    Then the response should contain the details of a migration
