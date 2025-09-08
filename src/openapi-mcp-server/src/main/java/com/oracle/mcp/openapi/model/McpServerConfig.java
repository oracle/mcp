/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.model;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.constants.ErrorMessage;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.model.override.ToolOverridesConfig;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * Represents parsed command-line arguments for the MCP OpenAPI server.
 * Immutable once constructed.
 * Secrets (token, password, api-key) are stored in char arrays
 * and should be cleared by the consumer after use.
 * Environment variables override CLI arguments if both are present.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public final class McpServerConfig {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    // Specification source
    private final String apiName;
    private final String apiBaseUrl;
    private final String apiSpec;

    // Authentication details
    private final String authType; // raw string
    private final char[] authToken;
    private final String authUsername;
    private final char[] authPassword;
    private final char[] authApiKey;
    private final String authApiKeyName;
    private final String authApiKeyIn;
    private final Map<String, String> authCustomHeaders;

    // Network configs
    private final String connectTimeout;
    private final String responseTimeout;
    private final String httpVersion;
    private final String redirectPolicy;
    private final String proxyHost;
    private final Integer proxyPort;
    private final String toolOverridesJson;

    public McpServerConfig(Builder builder) {
        this.apiName = builder.apiName;
        this.apiBaseUrl = builder.apiBaseUrl;
        this.apiSpec = builder.apiSpec;
        this.authType = builder.authType;
        this.authToken = builder.authToken != null ? builder.authToken.clone() : null;
        this.authUsername = builder.authUsername;
        this.authPassword = builder.authPassword != null ? builder.authPassword.clone() : null;
        this.authApiKey = builder.authApiKey != null ? builder.authApiKey.clone() : null;
        this.authApiKeyName = builder.authApiKeyName;
        this.authApiKeyIn = builder.authApiKeyIn;
        this.authCustomHeaders = builder.authCustomHeaders != null ? Map.copyOf(builder.authCustomHeaders) : Collections.emptyMap();
        this.connectTimeout = builder.connectTimeout;
        this.responseTimeout = builder.responseTimeout;
        this.httpVersion = builder.httpVersion;
        this.redirectPolicy = builder.redirectPolicy;
        this.proxyHost = builder.proxyHost;
        this.proxyPort = builder.proxyPort;
        this.toolOverridesJson = builder.toolOverridesJson;
    }

    // ----------------- GETTERS -----------------
    public String getApiName() {
        return apiName;
    }

    public String getApiBaseUrl() {
        return apiBaseUrl;
    }

    public String getRawAuthType() {
        return authType;
    }

    public OpenApiSchemaAuthType getAuthType() {
        return OpenApiSchemaAuthType.getType(this);
    }

    public String getAuthUsername() {
        return authUsername;
    }

    public char[] getAuthToken() {
        return authToken != null ? authToken.clone() : null;
    }

    public char[] getAuthPassword() {
        return authPassword != null ? authPassword.clone() : null;
    }

    public char[] getAuthApiKey() {
        return authApiKey != null ? authApiKey.clone() : null;
    }

    public String getAuthApiKeyName() {
        return authApiKeyName;
    }

    public String getAuthApiKeyIn() {
        return authApiKeyIn;
    }

    public Map<String, String> getAuthCustomHeaders() {
        return authCustomHeaders;
    }

    public String getApiSpec() {
        return apiSpec;
    }

    public long getConnectTimeoutMs() {
        try {
            return Long.parseLong(connectTimeout);
        } catch (NumberFormatException e) {
            System.err.printf("Invalid connect timeout value: %s. Using default 10000ms.%n", connectTimeout);
            return 10_000L;
        }
    }

    public long getResponseTimeoutMs() {
        try {
            return Long.parseLong(responseTimeout);
        } catch (NumberFormatException e) {
            System.err.printf("Invalid response timeout value: %s. Using default 30000ms.%n", responseTimeout);
            return 30_000L;
        }
    }

    public String getConnectTimeout() {
        return connectTimeout;
    }

    public String getResponseTimeout() {
        return responseTimeout;
    }

    public String getHttpVersion() {
        return httpVersion;
    }

    public String getRedirectPolicy() {
        return redirectPolicy;
    }

    public String getProxyHost() {
        return proxyHost;
    }

    public Integer getProxyPort() {
        return proxyPort;
    }

    public String getToolOverridesJson() {
        return toolOverridesJson;
    }

    public ToolOverridesConfig getToolOverridesConfig() throws JsonProcessingException {
        String toolOverridesJson = getToolOverridesJson();
        if(toolOverridesJson==null){
            return ToolOverridesConfig.EMPTY_TOOL_OVERRIDE_CONFIG;
        }
        return OBJECT_MAPPER.readValue(toolOverridesJson,ToolOverridesConfig.class);
    }

    // ----------------- BUILDER -----------------
    public static class Builder {
        private String apiName;
        private String apiBaseUrl;
        private String apiSpec;
        private String authType;
        private char[] authToken;
        private String authUsername;
        private char[] authPassword;
        private char[] authApiKey;
        private String authApiKeyName;
        private String authApiKeyIn;
        private Map<String, String> authCustomHeaders = Collections.emptyMap();
        private String connectTimeout;
        private String responseTimeout;
        private String httpVersion;
        private String redirectPolicy;
        private String proxyHost;
        private Integer proxyPort;
        private String toolOverridesJson;

        public Builder apiName(String apiName) {
            this.apiName = apiName;
            return this;
        }

        public Builder apiBaseUrl(String apiBaseUrl) {
            this.apiBaseUrl = apiBaseUrl;
            return this;
        }

        public Builder apiSpec(String apiSpec) {
            this.apiSpec = apiSpec;
            return this;
        }

        public Builder authType(String authType) {
            this.authType = authType;
            return this;
        }

        public Builder authToken(char[] authToken) {
            this.authToken = authToken;
            return this;
        }

        public Builder authUsername(String authUsername) {
            this.authUsername = authUsername;
            return this;
        }

        public Builder authPassword(char[] authPassword) {
            this.authPassword = authPassword;
            return this;
        }

        public Builder authApiKey(char[] authApiKey) {
            this.authApiKey = authApiKey;
            return this;
        }

        public Builder authApiKeyName(String authApiKeyName) {
            this.authApiKeyName = authApiKeyName;
            return this;
        }

        public Builder authApiKeyIn(String authApiKeyIn) {
            this.authApiKeyIn = authApiKeyIn;
            return this;
        }

        public Builder authCustomHeaders(Map<String, String> headers) {
            this.authCustomHeaders = headers;
            return this;
        }

        public Builder connectTimeout(String connectTimeout) {
            this.connectTimeout = connectTimeout;
            return this;
        }

        public Builder responseTimeout(String responseTimeout) {
            this.responseTimeout = responseTimeout;
            return this;
        }

        public Builder httpVersion(String httpVersion) {
            this.httpVersion = httpVersion;
            return this;
        }

        public Builder redirectPolicy(String redirectPolicy) {
            this.redirectPolicy = redirectPolicy;
            return this;
        }

        public Builder proxyHost(String proxyHost) {
            this.proxyHost = proxyHost;
            return this;
        }

        public Builder proxyPort(Integer proxyPort) {
            this.proxyPort = proxyPort;
            return this;
        }

        public Builder toolOverridesJson(String toolOverridesJson) {
            this.toolOverridesJson = toolOverridesJson;
            return this;
        }



        public McpServerConfig build() {
            return new McpServerConfig(this);
        }
    }

    public static Builder builder() {
        return new Builder();
    }

    // ----------------- FACTORY METHOD -----------------
    public static McpServerConfig fromArgs(String[] args) throws McpServerToolInitializeException {
        Map<String, String> argMap = toMap(args);

        // API info
        String apiName = getStringValue(argMap.get("--api-name"), "API_NAME");
        String apiBaseUrl = getStringValue(argMap.get("--api-base-url"), "API_BASE_URL");
        if (apiBaseUrl == null) throw new McpServerToolInitializeException(ErrorMessage.MISSING_API_BASE_URL);

        String apiSpec = getStringValue(argMap.get("--api-spec"), "API_SPEC");
        if (apiSpec == null) throw new McpServerToolInitializeException(ErrorMessage.MISSING_API_SPEC);

        // Authentication
        String authType = getStringValue(argMap.get("--auth-type"), "AUTH_TYPE");
        char[] authToken = getCharValue(argMap.get("--auth-token"), "AUTH_TOKEN");
        String authUsername = getStringValue(argMap.get("--auth-username"), "AUTH_USERNAME");
        char[] authPassword = getCharValue(argMap.get("--auth-password"), "AUTH_PASSWORD");
        char[] authApiKey = getCharValue(argMap.get("--auth-api-key"), "AUTH_API_KEY");
        String authApiKeyName = getStringValue(argMap.get("--auth-api-key-name"), "API_API_KEY_NAME");
        String authApiKeyIn = getStringValue(argMap.get("--auth-api-key-in"), "API_API_KEY_IN");

        String toolOverridesJson = getStringValue(argMap.get("--tool-overrides"), "MCP_TOOL_OVERRIDES");

        // Validation for API key
        if ("API_KEY".equalsIgnoreCase(authType)) {
            if (authApiKey == null || authApiKey.length == 0) {
                throw new McpServerToolInitializeException("Missing API Key value for auth type API_KEY");
            }
            if (authApiKeyName == null || authApiKeyName.isBlank()) {
                throw new McpServerToolInitializeException("Missing API Key name (--auth-api-key-name) for auth type API_KEY");
            }
            if (authApiKeyIn == null ||
                    !(authApiKeyIn.equalsIgnoreCase("header") || authApiKeyIn.equalsIgnoreCase("query"))) {
                throw new McpServerToolInitializeException("Invalid or missing API Key location (--auth-api-key-in). Must be 'header' or 'query'.");
            }
        }

        // Validation for Basic auth
        if ("BASIC".equalsIgnoreCase(authType)) {
            if (authUsername == null || authUsername.isBlank()) {
                throw new McpServerToolInitializeException("Missing username for BASIC auth");
            }
            if (authPassword == null || authPassword.length == 0) {
                throw new McpServerToolInitializeException("Missing password for BASIC auth");
            }
        }

        // Validation for Bearer token
        if ("BEARER".equalsIgnoreCase(authType)) {
            if (authToken == null || authToken.length == 0) {
                throw new McpServerToolInitializeException("Missing bearer token for BEARER auth");
            }
        }

        // Parse custom headers JSON
        String customHeadersJson = getStringValue(argMap.get("--auth-custom-headers"), "AUTH_CUSTOM_HEADERS");
        Map<String, String> authCustomHeaders = Collections.emptyMap();
        if (customHeadersJson != null && !customHeadersJson.isEmpty()) {
            try {
                authCustomHeaders = OBJECT_MAPPER.readValue(customHeadersJson, new TypeReference<>() {
                });
            } catch (JsonProcessingException e) {
                throw new McpServerToolInitializeException("Invalid JSON format for --auth-custom-headers: " + e.getMessage());
            }
        }

        // Network configs
        String connectTimeout = getStringValue(argMap.getOrDefault("--connect-timeout", "10000"), "API_HTTP_CONNECT_TIMEOUT");
        String responseTimeout = getStringValue(argMap.getOrDefault("--response-timeout", "30000"), "API_HTTP_RESPONSE_TIMEOUT");
        String httpVersion = getStringValue(argMap.getOrDefault("--http-version", "HTTP_2"), "API_HTTP_VERSION");
        String redirectPolicy = getStringValue(argMap.getOrDefault("--http-redirect", "NORMAL"), "API_HTTP_REDIRECT");
        String proxyHost = getStringValue(argMap.get("--proxy-host"), "API_HTTP_PROXY_HOST");
        Integer proxyPort = getIntOrNull(argMap.get("--proxy-port"), "API_HTTP_PROXY_PORT");

        // Build config using builder
        return McpServerConfig.builder()
                .apiName(apiName)
                .apiBaseUrl(apiBaseUrl)
                .apiSpec(apiSpec)
                .authType(authType)
                .authToken(authToken)
                .authUsername(authUsername)
                .authPassword(authPassword)
                .authApiKey(authApiKey)
                .authApiKeyName(authApiKeyName)
                .authApiKeyIn(authApiKeyIn)
                .authCustomHeaders(authCustomHeaders)
                .connectTimeout(connectTimeout)
                .responseTimeout(responseTimeout)
                .httpVersion(httpVersion)
                .redirectPolicy(redirectPolicy)
                .proxyHost(proxyHost)
                .proxyPort(proxyPort)
                .toolOverridesJson(toolOverridesJson)
                .build();
    }

    // ----------------- HELPERS -----------------
    private static char[] getCharValue(String cliValue, String envVarName) {
        String envValue = System.getenv(envVarName);
        String secret = envValue != null ? envValue : cliValue;
        return secret != null ? secret.toCharArray() : null;
    }

    private static String getStringValue(String cliValue, String envVarName) {
        String envValue = System.getenv(envVarName);
        return envValue != null ? envValue : cliValue;
    }

    private static Integer getIntOrNull(String cliValue, String envVarName) {
        String value = getStringValue(cliValue, envVarName);
        if (value != null) {
            try {
                return Integer.parseInt(value);
            } catch (NumberFormatException e) {
                System.err.printf("Invalid integer for %s: %s. Ignoring.%n", envVarName, value);
            }
        }
        return null;
    }

    private static Map<String, String> toMap(String[] args) {
        Map<String, String> map = new HashMap<>();
        if (args == null) return map;
        for (int i = 0; i < args.length; i++) {
            String key = args[i];
            if (key.startsWith("--")) {
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    map.put(key, args[++i]);
                } else {
                    map.put(key, ""); // Use empty string for flags without values
                }
            } else {
                System.err.println("Warning: Unexpected argument format, ignoring: " + key);
            }
        }
        return map;
    }
}
