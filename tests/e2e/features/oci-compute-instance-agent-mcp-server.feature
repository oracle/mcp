# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

Feature: OCI Compute Instance Agent MCP Server
  Scenario: List instance agent command executions for an instance
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my instances, then list the instance agent command executions on the first instance in the list and limit to 2"
    Then the response should contain a list of instance agent command executions

  Scenario: Run an instance agent command and get execution details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my instances, then run an instance agent command 'echo Hello from agent' on the first instance in the list"
    Then the response should contain instance agent command execution details
