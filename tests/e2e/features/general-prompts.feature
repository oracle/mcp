# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI MCP Servers
  Scenario: List the tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What tools do you have? List all by name"
    Then the response should contain a list of tools available

  Scenario: List the instances in the root compartment
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my instances in the root compartment and limit to 5"
    Then the response should contain a list of instances

