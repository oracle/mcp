Feature: OCI IoT MCP server high-value flows

  Scenario: Invoke a raw command and wait for an observed outcome
    Given the OCI IoT MCP server package is installed
    And the OCI IoT e2e environment is configured
    When I invoke "invoke_raw_command_and_wait" for the configured digital twin
    Then the response should have "ok" equal to true
    And the response data should include "request_id"

  Scenario: List recent raw commands for a configured twin
    Given the OCI IoT MCP server package is installed
    And the OCI IoT e2e environment is configured
    When I invoke "list_recent_raw_commands_for_twin" for the configured digital twin
    Then the response should have "ok" equal to true
    And the response data should be a list

  Scenario: Explain twin platform context for a configured twin
    Given the OCI IoT MCP server package is installed
    And the OCI IoT e2e environment is configured
    When I invoke "get_twin_platform_context" for the configured digital twin
    Then the response should have "ok" equal to true
    And the IoT platform context response should include "domain_context"

  Scenario: Report latest twin state for a configured twin
    Given the OCI IoT MCP server package is installed
    And the OCI IoT e2e environment is configured
    When I invoke "get_latest_twin_state" for the configured digital twin
    Then the response should have "ok" equal to true
    And the latest twin state response should include "observed_timestamps"

  Scenario: Validate passive readiness for a configured twin
    Given the OCI IoT MCP server package is installed
    And the OCI IoT e2e environment is configured
    When I invoke "validate_twin_readiness" for the configured digital twin
    Then the response should have "ok" equal to true
    And the readiness response should include at least one check
