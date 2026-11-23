# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI MCP Servers
  Scenario: List the tools available in the agent
    Given the mock OCI services are running
    And the Codex CLI is configured with OCI tools
    When I send a request with the prompt "What tools do you have? List all by name"
    Then the response should contain a list of tools available

