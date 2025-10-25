# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Object Storage MCP Server
  Scenario: Get the namespace
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "get my namespace"
    Then the response should contain a the tenancy namespace

  Scenario: List buckets
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my buckets"
    Then the response should contain a list of buckets available

