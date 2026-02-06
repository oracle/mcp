# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

Feature: OCI Network Load Balancer MCP Server
  Scenario: List the network load balancer tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What network load balancer mcp tools do you have"
    Then the response should contain a list of network load balancer tools available

  Scenario: List the network load balancers
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network load balancers"
    Then the response should contain a list of network load balancers

  Scenario: Get network load balancer details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network load balancers, then get the details of the first network load balancer in the list"
    Then the response should contain the details of a network load balancer

  Scenario: List the listeners on the first network load balancer
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network load balancers and list the listeners on the first network load balancer in the list"
    Then the response should contain a list of listeners

  Scenario: Get listener details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network load balancers and list the listeners on the first network load balancer in the list, then fetch the details of the first listener in that list"
    Then the response should contain the details of a listener

  Scenario: List the backend sets on the first network load balancer
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network load balancers and list the backend sets on the first network load balancer in the list"
    Then the response should contain a list of backend sets

  Scenario: Get backend set details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network load balancers and list the backend sets on the first network load balancer in the list, then fetch the details of the first backend set in that list"
    Then the response should contain the details of a backend set

  Scenario: List the backends in the first backend set
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network load balancers and list the backend sets on the first network load balancer in the list, then list the backends in the first backend set"
    Then the response should contain a list of backends
