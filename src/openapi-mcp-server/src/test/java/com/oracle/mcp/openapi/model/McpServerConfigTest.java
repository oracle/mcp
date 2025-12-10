/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.model;

import com.oracle.mcp.openapi.constants.ErrorMessage;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Unit tests for {@link McpServerConfig}.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
class McpServerConfigTest {

    @Test
    void fromArgs_whenAllCliArgsProvided_thenConfigIsCreatedCorrectly() throws McpServerToolInitializeException {
        String[] args = {
                "--api-name", "MyTestApi",
                "--api-base-url", "https://api.example.com",
                "--api-spec", "path/to/spec.json",
                "--auth-type", "CUSTOM",
                "--auth-custom-headers", "{\"X-Custom-Auth\":\"secret-value\"}",
                "--connect-timeout", "5000",
                "--response-timeout", "15000",
                "--http-version", "HTTP_1_1",
                "--http-redirect", "ALWAYS",
                "--proxy-host", "proxy.example.com",
                "--proxy-port", "8080"
        };

        McpServerConfig config = McpServerConfig.fromArgs(args);

        assertThat(config.getApiName()).isEqualTo("MyTestApi");
        assertThat(config.getApiBaseUrl()).isEqualTo("https://api.example.com");
        assertThat(config.getApiSpec()).isEqualTo("path/to/spec.json");
        assertThat(config.getRawAuthType()).isEqualTo("CUSTOM");
        assertThat(config.getAuthCustomHeaders()).isEqualTo(Map.of("X-Custom-Auth", "secret-value"));
        assertThat(config.getConnectTimeout()).isEqualTo("5000");
        assertThat(config.getConnectTimeoutMs()).isEqualTo(5000L);
        assertThat(config.getResponseTimeout()).isEqualTo("15000");
        assertThat(config.getResponseTimeoutMs()).isEqualTo(15000L);
        assertThat(config.getHttpVersion()).isEqualTo("HTTP_1_1");
        assertThat(config.getRedirectPolicy()).isEqualTo("ALWAYS");
        assertThat(config.getProxyHost()).isEqualTo("proxy.example.com");
        assertThat(config.getProxyPort()).isEqualTo(8080);
    }

    @Test
    void fromArgs_whenOptionalNetworkArgsAreMissing_thenDefaultsAreUsed() throws McpServerToolInitializeException {
        String[] args = {
                "--api-base-url", "https://api.example.com",
                "--api-spec", "spec.json"
        };

        McpServerConfig config = McpServerConfig.fromArgs(args);

        assertThat(config.getConnectTimeout()).isEqualTo("10000");
        assertThat(config.getResponseTimeout()).isEqualTo("30000");
        assertThat(config.getHttpVersion()).isEqualTo("HTTP_2");
        assertThat(config.getRedirectPolicy()).isEqualTo("NORMAL");
        assertThat(config.getProxyHost()).isNull();
        assertThat(config.getProxyPort()).isNull();
    }

    @Test
    void fromArgs_whenNoArgsProvided_thenThrowsException() {
        String[] args = {};
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage(ErrorMessage.MISSING_API_BASE_URL);
    }

    @Test
    void fromArgs_whenMissingApiBaseUrl_thenThrowsException() {
        String[] args = {"--api-spec", "spec.json"};

        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage(ErrorMessage.MISSING_API_BASE_URL);
    }

    @Test
    void fromArgs_whenMissingApiSpec_thenThrowsException() {
        String[] args = {"--api-base-url", "https://api.example.com"};

        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage(ErrorMessage.MISSING_API_SPEC);
    }

    @Test
    void fromArgs_whenAuthTypeApiKeyButMissingKey_thenThrowsException() {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--auth-type", "API_KEY",
                "--auth-api-key-name", "X-API-KEY",
                "--auth-api-key-in", "header"
        };
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage("Missing API Key value for auth type API_KEY");
    }

    @Test
    void fromArgs_whenAuthTypeApiKeyButMissingKeyName_thenThrowsException() {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--auth-type", "API_KEY",
                "--auth-api-key", "secretkey",
                "--auth-api-key-in", "header"
        };
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage("Missing API Key name (--auth-api-key-name) for auth type API_KEY");
    }

    @Test
    void fromArgs_whenAuthTypeApiKeyButInvalidLocation_thenThrowsException() {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--auth-type", "API_KEY",
                "--auth-api-key", "secretkey",
                "--auth-api-key-name", "X-API-KEY",
                "--auth-api-key-in", "cookie" // Invalid location
        };
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage("Invalid or missing API Key location (--auth-api-key-in). Must be 'header' or 'query'.");
    }

    @Test
    void fromArgs_whenAuthTypeBasicButMissingUsername_thenThrowsException() {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--auth-type", "BASIC",
                "--auth-password", "secretpass"
        };
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage("Missing username for BASIC auth");
    }

    @Test
    void fromArgs_whenAuthTypeBasicButMissingPassword_thenThrowsException() {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--auth-type", "BASIC",
                "--auth-username", "user"
        };
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage("Missing password for BASIC auth");
    }

    @Test
    void fromArgs_whenAuthTypeBearerButMissingToken_thenThrowsException() {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--auth-type", "BEARER"
        };
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessage("Missing bearer token for BEARER auth");
    }

    @Test
    void fromArgs_whenCustomHeadersAreInvalidJson_thenThrowsException() {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--auth-type", "CUSTOM",
                "--auth-custom-headers", "{not-valid-json}"
        };
        assertThatThrownBy(() -> McpServerConfig.fromArgs(args))
                .isInstanceOf(McpServerToolInitializeException.class)
                .hasMessageStartingWith("Invalid JSON format for --auth-custom-headers:");
    }

    @Test
    void getTimeoutMs_whenValueIsInvalid_returnsDefaultValue() {
        McpServerConfig config = McpServerConfig.builder()
                .connectTimeout("invalid")
                .responseTimeout("not-a-number")
                .build();

        assertThat(config.getConnectTimeoutMs()).isEqualTo(10_000L);
        assertThat(config.getResponseTimeoutMs()).isEqualTo(30_000L);
    }

    @Test
    void getProxyPort_whenValueIsInvalid_returnsNull() throws McpServerToolInitializeException {
        String[] args = {
                "--api-base-url", "url", "--api-spec", "spec",
                "--proxy-port", "not-an-integer"
        };

        McpServerConfig config = McpServerConfig.fromArgs(args);
        assertThat(config.getProxyPort()).isNull();
    }

    @Test
    void builder_whenSecretsAreSet_clonesTheCharArrays() {
        char[] originalToken = {'t', 'o', 'k', 'e', 'n'};
        McpServerConfig config = McpServerConfig.builder()
                .authToken(originalToken)
                .build();

        // Modify the original array after building
        originalToken[0] = 'X';

        // The config should hold the original, unmodified value
        assertThat(config.getAuthToken()).isEqualTo(new char[]{'t', 'o', 'k', 'e', 'n'});
    }
}

