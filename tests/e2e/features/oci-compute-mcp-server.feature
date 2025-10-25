# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Compute MCP Server
  Scenario: List the tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What tools do you have"
    Then the response should contain a list of compute tools available

  Scenario: Security review of compute instances in specific region
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "Can you review the security configuration of my compute instances in San Jose and let me know if there are any recommended improvements or best practices to strengthen their security posture?"
    Then the response should contain security analysis
    And the response should mention security best practices
    And the response should reference regional considerations