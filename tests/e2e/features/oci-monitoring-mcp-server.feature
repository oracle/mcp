# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

Feature: OCI Monitoring MCP Server
  Scenario: List the monitoring tools available in the agent
    Given the mock OCI services are running
    And the Codex CLI is configured with OCI tools
    When I send a request with the prompt "What monitoring mcp tools do you have"
    Then the response should contain a list of monitoring tools available

  Scenario: List alarms
    Given the mock OCI services are running
    And the Codex CLI is configured with OCI tools
    When I send a request with the prompt "list the alarms in my compartment"
    Then the response should contain a list of alarms

  Scenario: List metric definitions
    Given the mock OCI services are running
    And the Codex CLI is configured with OCI tools
    When I send a request with the prompt "list the metric definitions for namespace oci_computeagent"
    Then the response should contain a list of metric definitions

  Scenario: Get metrics data
    Given the mock OCI services are running
    And the Codex CLI is configured with OCI tools
    When I send a request with the prompt "get the CpuUtilization metrics data for the last hour"
    Then the response should contain aggregated metric data