package com.oracle.mcp.openapi.model;

import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;

import java.util.HashMap;
import java.util.Map;

/**
 * Represents parsed command-line arguments for the MCP OpenAPI server.
 * Immutable once constructed.
 * Secrets (token, password, api-key) are stored in char arrays
 * and should be cleared by the consumer after use.
 *
 * Environment variables override CLI arguments if both are present.
 */
public final class McpServerConfig {

    // Specification source
    private final String apiName;
    private final String apiBaseUrl;
    private final String specUrl;
    private final String specPath;

    // Authentication details
    private final String authType; // raw string
    private final char[] authToken;
    private final String authUsername;
    private final char[] authPassword;
    private final char[] authApiKey;
    private final String authApiKeyName;
    private final String authApiKeyIn;

    private McpServerConfig(String apiName, String apiBaseUrl, String specUrl, String specPath,
                            String authType, char[] authToken, String authUsername,
                            char[] authPassword, char[] authApiKey, String authApiKeyName,
                            String authApiKeyIn) {
        this.apiName = apiName;
        this.apiBaseUrl = apiBaseUrl;
        this.specUrl = specUrl;
        this.specPath = specPath;
        this.authType = authType;
        this.authToken = authToken != null ? authToken.clone() : null;
        this.authUsername = authUsername;
        this.authPassword = authPassword != null ? authPassword.clone() : null;
        this.authApiKey = authApiKey != null ? authApiKey.clone() : null;
        this.authApiKeyName = authApiKeyName;
        this.authApiKeyIn = authApiKeyIn;
    }

    // ----------------- GETTERS -----------------

    public String getApiName() { return apiName; }
    public String getApiBaseUrl() { return apiBaseUrl; }
    public String getSpecUrl() { return specUrl; }
    public String getSpecPath() { return specPath; }
    public String getRawAuthType() { return authType; }
    public OpenApiSchemaAuthType getAuthType() { return OpenApiSchemaAuthType.getType(this); }
    public String getAuthUsername() { return authUsername; }
    public char[] getAuthToken() { return authToken != null ? authToken.clone() : null; }
    public String getAuthPassword() { return authPassword != null ? new String(authPassword) : null; }
    public char[] getAuthApiKey() { return authApiKey != null ? authApiKey.clone() : null; }
    public String getAuthApiKeyName() { return authApiKeyName; }
    public String getAuthApiKeyIn() { return authApiKeyIn; }

    // ----------------- FACTORY METHOD -----------------

    public static McpServerConfig fromArgs(String[] args) {
        Map<String, String> argMap = toMap(args);

        // ----------------- API info -----------------
        String apiName = getStringValue(argMap.get("--api-name"), "API_NAME");
        String apiBaseUrl = getStringValue(argMap.get("--api-base-url"), "API_BASE_URL");
        String specUrl = getStringValue(argMap.get("--spec-url"), "API_SPEC_URL");
        String specPath = getStringValue(argMap.get("--spec-path"), "API_SPEC_PATH");

        if (specUrl == null && specPath == null) {
            throw new IllegalArgumentException("Either --spec-url or --spec-path is required.");
        }
        if (specUrl != null && specPath != null) {
            throw new IllegalArgumentException("Provide either --spec-url or --spec-path, but not both.");
        }

        // ----------------- Authentication -----------------
        String authType = getStringValue(argMap.get("--auth-type"), "AUTH_TYPE");
        char[] authToken = getCharValue(argMap.get("--auth-token"), "AUTH_TOKEN");
        String authUsername = getStringValue(argMap.get("--auth-username"), "AUTH_USERNAME");
        char[] authPassword = getCharValue(argMap.get("--auth-password"), "AUTH_PASSWORD");
        char[] authApiKey = getCharValue(argMap.get("--auth-api-key"), "AUTH_API_KEY");
        String authApiKeyName = getStringValue(argMap.get("--auth-api-key-name"), "AUTH_API_KEY_NAME");
        String authApiKeyIn = getStringValue(argMap.get("--auth-api-key-in"), "AUTH_API_KEY_IN");

        return new McpServerConfig(apiName, apiBaseUrl, specUrl, specPath,
                authType, authToken, authUsername, authPassword, authApiKey,
                authApiKeyName, authApiKeyIn);
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

    private static Map<String, String> toMap(String[] args) {
        Map<String, String> map = new HashMap<>();
        for (int i = 0; i < args.length; i++) {
            String key = args[i];
            if (key.startsWith("--")) {
                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    map.put(key, args[++i]);
                } else {
                    map.put(key, null); // flag with no value
                }
            } else {
                throw new IllegalArgumentException("Unexpected argument: " + key);
            }
        }
        return map;
    }
}
