package com.oracle.mcp.openapi.model;

import com.oracle.mcp.openapi.constants.ErrorMessage;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;

import java.util.HashMap;
import java.util.Map;

/**
 * Represents parsed command-line arguments for the MCP OpenAPI server.
 * Immutable once constructed.
 * Secrets (token, password, api-key) are stored in char arrays
 * and should be cleared by the consumer after use.
 * Environment variables override CLI arguments if both are present.
 */
public final class McpServerConfig {

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

    // Network configs
    private final String connectTimeout;
    private final String responseTimeout;
    private final String httpVersion;
    private final String redirectPolicy;
    private final String proxyHost;
    private final Integer proxyPort;

    private McpServerConfig(String apiName, String apiBaseUrl,
                            String authType, char[] authToken, String authUsername,
                            char[] authPassword, char[] authApiKey, String authApiKeyName,
                            String authApiKeyIn, String apiSpec,
                            String connectTimeout, String responseTimeout,
                            String httpVersion, String redirectPolicy,
                            String proxyHost, Integer proxyPort) {
        this.apiName = apiName;
        this.apiBaseUrl = apiBaseUrl;
        this.authType = authType;
        this.authToken = authToken != null ? authToken.clone() : null;
        this.authUsername = authUsername;
        this.authPassword = authPassword != null ? authPassword.clone() : null;
        this.authApiKey = authApiKey != null ? authApiKey.clone() : null;
        this.authApiKeyName = authApiKeyName;
        this.authApiKeyIn = authApiKeyIn;
        this.apiSpec = apiSpec;
        this.connectTimeout = connectTimeout;
        this.responseTimeout = responseTimeout;
        this.httpVersion = httpVersion;
        this.redirectPolicy = redirectPolicy;
        this.proxyHost = proxyHost;
        this.proxyPort = proxyPort;
    }

    // ----------------- GETTERS -----------------
    public String getApiName() { return apiName; }
    public String getApiBaseUrl() { return apiBaseUrl; }
    public String getRawAuthType() { return authType; }
    public OpenApiSchemaAuthType getAuthType() { return OpenApiSchemaAuthType.getType(this); }
    public String getAuthUsername() { return authUsername; }
    public String getAuthToken() { return authToken != null ? new String(authToken) : null; }

    public char[] getAuthPassword() {
        return authPassword;
    }
    public char[] getAuthApiKey() { return authApiKey != null ? authApiKey.clone() : null; }
    public String getAuthApiKeyName() { return authApiKeyName; }
    public String getAuthApiKeyIn() { return authApiKeyIn; }
    public String getApiSpec() { return apiSpec; }

    // Timeouts as long
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

    // Original string getters
    public String getConnectTimeout() { return connectTimeout; }
    public String getResponseTimeout() { return responseTimeout; }

    public String getHttpVersion() { return httpVersion; }
    public String getRedirectPolicy() { return redirectPolicy; }
    public String getProxyHost() { return proxyHost; }
    public Integer getProxyPort() { return proxyPort; }

    // ----------------- FACTORY METHOD -----------------
    public static McpServerConfig fromArgs(String[] args) throws McpServerToolInitializeException {
        Map<String, String> argMap = toMap(args);

        // ----------------- API info -----------------
        String apiName = getStringValue(argMap.get("--api-name"), "API_NAME");
        String apiBaseUrl = getStringValue(argMap.get("--api-base-url"), "API_BASE_URL");
        String apiSpec = getStringValue(argMap.get("--api-spec"), "API_SPEC");

        if (apiSpec == null) {
            throw new McpServerToolInitializeException(ErrorMessage.MISSING_API_SPEC);
        }
        // ----------------- Authentication -----------------
        String authType = getStringValue(argMap.get("--auth-type"), "AUTH_TYPE");
        char[] authToken = getCharValue(argMap.get("--auth-token"), "AUTH_TOKEN");
        String authUsername = getStringValue(argMap.get("--auth-username"), "AUTH_USERNAME");
        char[] authPassword = getCharValue(argMap.get("--auth-password"), "AUTH_PASSWORD");
        char[] authApiKey = getCharValue(argMap.get("--auth-api-key"), "AUTH_API_KEY");
        String authApiKeyName = getStringValue(argMap.get("--auth-api-key-name"), "AUTH_API_KEY_NAME");
        String authApiKeyIn = getStringValue(argMap.get("--auth-api-key-in"), "AUTH_API_KEY_IN");

        // ----------------- Network configs -----------------
        String connectTimeout = getStringValue(argMap.get("--connect-timeout"), "API_HTTP_CONNECT_TIMEOUT");
        if (connectTimeout == null) connectTimeout = "10000"; // default 10s in ms

        String responseTimeout = getStringValue(argMap.get("--response-timeout"), "API_HTTP_RESPONSE_TIMEOUT");
        if (responseTimeout == null) responseTimeout = "30000"; // default 30s in ms

        String httpVersion = getStringValue(argMap.get("--http-version"), "API_HTTP_VERSION");
        if (httpVersion == null) httpVersion = "HTTP_2";

        String redirectPolicy = getStringValue(argMap.get("--http-redirect"), "API_HTTP_REDIRECT");
        if (redirectPolicy == null) redirectPolicy = "NORMAL";

        String proxyHost = getStringValue(argMap.get("--proxy-host"), "API_HTTP_PROXY_HOST");
        Integer proxyPort = getIntOrNull(argMap.get("--proxy-port"), "API_HTTP_PROXY_PORT");

        return new McpServerConfig(apiName, apiBaseUrl,
                authType, authToken, authUsername, authPassword, authApiKey,
                authApiKeyName, authApiKeyIn, apiSpec,
                connectTimeout, responseTimeout,
                httpVersion, redirectPolicy, proxyHost, proxyPort);
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
        String envValue = System.getenv(envVarName);
        String value = envValue != null ? envValue : cliValue;
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
