# Copyright (c) 2026, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

Feature: OCI Networking MCP Server
  Scenario: List the networking tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What networking mcp tools do you have"
    Then the response should contain a list of networking tools available

  Scenario: List the virtual networks (VCNs)
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my vcns"
    Then the response should contain a list of vcns

  Scenario: Get virtual network (VCN) details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my vcns, then get the details of the first vcn in the list"
    Then the response should contain the details of a vcn

  Scenario: List the subnets
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my subnets"
    Then the response should contain a list of subnets

  Scenario: Get subnet details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my subnets, then get the details of the first subnet in the list"
    Then the response should contain the details of a subnet

  Scenario: List the security lists
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my security lists"
    Then the response should contain a list of security lists

  Scenario: Get security list details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my security lists, then get the details of the first security list in the list"
    Then the response should contain the details of a security list

  Scenario: List the network security groups
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network security groups"
    Then the response should contain a list of network security groups

  Scenario: Get network security group details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my network security groups, then get the details of the first network security group in the list"
    Then the response should contain the details of a network security group

  Scenario: Get vnic details by id
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "get the vnic details for ocid ocid1.vnic.oc1..mock-vnic"
    Then the response should contain the details of a vnic
