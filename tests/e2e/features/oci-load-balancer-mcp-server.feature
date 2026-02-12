# Copyright (c) 2025, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at
# https://oss.oracle.com/licenses/upl.

# Feature: OCI Load Balancer MCP Server
#
#   Background:
#     Given the MCP server is running with OCI tools
#     And the ollama model with the tools is properly working
#
#   Scenario: List the load balancer tools available in the agent
#     When I send a request with the prompt "What load balancer mcp tools do you have"
#     Then the response should contain a list of load balancer tools available
#
#   Scenario: List the load balancers for a compartment
#     When I send a request with the prompt "list my load balancers"
#     Then the response should contain a list of load balancers
#
#   Scenario: Create a load balancer
#     When I send a request with the prompt "create a flexible load balancer named mock-lb in root compartment"
#     Then the response should confirm creation of a load balancer
#
#   Scenario: Get load balancer details
#     When I send a request with the prompt "get the details of load balancer mock-lb"
#     Then the response should contain the details of a load balancer
#
#   Scenario: Delete a load balancer
#     When I send a request with the prompt "delete the load balancer mock-lb in root compartment"
#     Then the response should confirm deletion of a load balancer
#
#   Scenario: List listeners for a load balancer
#     When I send a request with the prompt "list listeners for load balancer mock-lb"
#     Then the response should contain a list of listeners
#
#   Scenario: List backend sets and backends for a load balancer
#     When I send a request with the prompt "show backend sets and backends for load balancer mock-lb"
#     Then the response should contain a list of backend sets and backends
#
#   Scenario: List certificates and SSL cipher suites for a load balancer
#     When I send a request with the prompt "list certificates and ssl ciphers for load balancer mock-lb"
#     Then the response should contain a list of certificates and cipher suites
#
#   Scenario: List hostnames, rule sets, and routing policies for a load balancer
#     When I send a request with the prompt "list hostnames, rule sets, and routing policies for load balancer mock-lb"
#     Then the response should contain hostnames, rule sets, and routing policies
#
#   Scenario: Show health summaries and work requests for a load balancer
#     When I send a request with the prompt "show health and recent work requests for load balancer mock-lb"
#     Then the response should contain health summaries and work requests
#
#   # Expanded coverage scenarios
#   Scenario: Manage a listener lifecycle on a load balancer
#     When I send a request with the prompt "on load balancer mock-lb create a listener named lhttp on port 80 using HTTP with default backend set backendset1, then get listener lhttp, then update listener lhttp to use port 81, then delete listener lhttp"
#     Then the response should confirm listener operations
#
#   Scenario: Manage a backend set lifecycle on a load balancer
#     When I send a request with the prompt "on load balancer mock-lb create a backend set named bes2 with policy ROUND_ROBIN and http health check on /health, then get backend set bes2, then update backend set bes2 to use backend max connections 400, then delete backend set bes2"
#     Then the response should confirm backend set operations
#
#   Scenario: Manage a backend lifecycle in a backend set
#     When I send a request with the prompt "for load balancer mock-lb and backend set backendset1 add backend 10.0.0.5:8080 with weight 1, then get backend 10.0.0.5:8080, then update backend 10.0.0.5:8080 to be offline, then delete backend 10.0.0.5:8080"
#     Then the response should confirm backend operations
#
#   Scenario: Manage certificates on a load balancer
#     When I send a request with the prompt "for load balancer mock-lb create a certificate named cert2 with provided PEMs, then delete certificate cert2"
#     Then the response should confirm certificate operations
#
#   Scenario: Manage SSL cipher suites on a load balancer
#     When I send a request with the prompt "for load balancer mock-lb create ssl cipher suite suite2 with ciphers TLS_AES_256_GCM_SHA384, then get ssl cipher suite suite2, then update ssl cipher suite suite2 to include TLS_CHACHA20_POLY1305_SHA256, then delete ssl cipher suite suite2"
#     Then the response should confirm ssl cipher suite operations
#
#   Scenario: Manage hostnames on a load balancer
#     When I send a request with the prompt "for load balancer mock-lb create hostname host2 with value api.example.com, then get hostname host2, then update hostname host2 to value api2.example.com, then delete hostname host2"
#     Then the response should confirm hostname operations
#
#   Scenario: Manage rule sets on a load balancer
#     When I send a request with the prompt "for load balancer mock-lb create rule set rs2 with an ADD_HTTP_REQUEST_HEADER rule, then get rule set rs2, then update rule set rs2 to new items, then delete rule set rs2"
#     Then the response should confirm rule set operations
#
#   Scenario: Manage routing policies on a load balancer
#     When I send a request with the prompt "for load balancer mock-lb create routing policy rp2 with a forward rule to backendset1, then get routing policy rp2, then update routing policy rp2, then delete routing policy rp2"
#     Then the response should confirm routing policy operations
#
#   Scenario: Get detailed health for load balancer, backend set, and backend
#     When I send a request with the prompt "for load balancer mock-lb show the overall health, the health for backend set backendset1, and the health for backend 10.0.0.3:8080"
#     Then the response should contain load balancer health
#     And the response should contain backend set health
#     And the response should contain backend health
#
#   Scenario: Get work requests and details for a load balancer
#     When I send a request with the prompt "for load balancer mock-lb list work requests and then get the details of the first work request"
#     Then the response should contain work request details
#