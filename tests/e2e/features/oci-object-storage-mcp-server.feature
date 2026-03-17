# Copyright (c) 2026, Oracle and/or its affiliates.
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

  Scenario: Get bucket details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my buckets, then get the details of the first bucket in the list"
    Then the response should contain the details of a bucket

  Scenario: List objects in a bucket
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list the objects in the bucket mcp-e2e-bucket"
    Then the response should contain a list of objects

  Scenario: List object versions in a bucket
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list the object versions in the bucket mcp-e2e-bucket"
    Then the response should contain a list of object versions

  # Commented out because of a bug in get_object
  # Scenario: Get a specific object from a bucket
  #   Given the MCP server is running with OCI tools
  #   And the ollama model with the tools is properly working
  #   When I send a request with the prompt "get the object file1.txt from the bucket mcp-e2e-bucket"
  #   Then the response should contain the details of an object
