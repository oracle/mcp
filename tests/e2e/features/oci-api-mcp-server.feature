# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI API MCP Server
  Scenario: List the tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What tools do you have"
    Then the response should contain a list of tools available

  Scenario: List the instances in the root compartment
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my instances and limit to 2"
    Then the response should contain a list of all instances

  Scenario: Generate Terraform for Stable Diffusion GPU infrastructure
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "Create TF for me to create and configure all resources needed to run stable diffusion in a webUI on an OCI GPU. I want to make sure i'm using OCI Gen AI services as much as possible"
    Then the response should contain terraform configuration
    And the response should mention GPU instances
    And the response should mention OCI Gen AI services