# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.


Feature: OCI Compute MCP Server
  Scenario: List the compute tools available in the agent
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "What compute mcp tools do you have"
    Then the response should contain a list of compute tools available

  Scenario: List the compute instances
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my instances"
    Then the response should contain a list of running instances

  Scenario: Get compute instance details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my instances, then get the details of the first instance in the list"
    Then the response should contain the details of an instance

  Scenario: List the images
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list the possible compute images and limit to 5"
    Then the response should contain a list of images

  Scenario: Get image details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list the possible compute images and limit to 5, then get the details of the first image in the list"
    Then the response should contain the details of an image

  Scenario: List the vnic attachments
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my running instances and list the vnics attachments on the first instance in the list"
    Then the response should contain a list of vnic attachments

  Scenario: Get vnic attachment details
    Given the MCP server is running with OCI tools
    And the ollama model with the tools is properly working
    When I send a request with the prompt "list my running instances and list the vnics attachments on the first instance in the list, then fetch the details of the first vnic attachment in that list"
    Then the response should contain the details of a vnic attachment

  # Scenario: Security review of compute instances in specific region
  #   Given the MCP server is running with OCI tools
  #   And the ollama model with the tools is properly working
  #   When I send a request with the prompt "Can you review the security configuration of my compute instances in Ashburn and let me know if there are any recommended improvements or best practices to strengthen their security posture?"
  #   Then the response should contain security analysis
  #   And the response should mention security best practices
  #   And the response should reference regional considerations
