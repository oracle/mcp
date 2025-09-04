/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.tool;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.constants.CommonConstant;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.rest.RestApiAuthHandler;
import com.oracle.mcp.openapi.rest.RestApiExecutionService;
import io.modelcontextprotocol.server.McpSyncServerExchange;
import io.modelcontextprotocol.spec.McpSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Executes OpenAPI-based MCP tools. This class translates MCP tool requests
 * into actual HTTP REST API calls, handling path parameters, query parameters,
 * authentication, and headers automatically.
 *
 * <p>
 * It supports multiple authentication mechanisms (NONE, BASIC, BEARER, API_KEY, CUSTOM)
 * and can dynamically substitute parameters based on the tool metadata.
 * </p>
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class OpenApiMcpToolExecutor {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiMcpToolExecutor.class);

    private final McpServerCacheService mcpServerCacheService;
    private final RestApiExecutionService restApiExecutionService;
    private final ObjectMapper jsonMapper;
    private final RestApiAuthHandler restApiAuthHandler;

    /**
     * Constructs a new {@code OpenApiMcpToolExecutor}.
     *
     * @param mcpServerCacheService     service for retrieving cached tool and server configurations
     * @param restApiExecutionService   service for executing REST API requests
     * @param jsonMapper                JSON object mapper for serializing request bodies
     */
    public OpenApiMcpToolExecutor(McpServerCacheService mcpServerCacheService,
                                  RestApiExecutionService restApiExecutionService,
                                  ObjectMapper jsonMapper, RestApiAuthHandler restApiAuthHandler) {
        this.mcpServerCacheService = mcpServerCacheService;
        this.restApiExecutionService = restApiExecutionService;
        this.jsonMapper = jsonMapper;
        this.restApiAuthHandler = restApiAuthHandler;
    }

    /**
     * Executes a tool request coming from a synchronous MCP server exchange.
     *
     * @param exchange    the MCP exchange context
     * @param callRequest the tool execution request
     * @return the result of executing the tool
     */
    public McpSchema.CallToolResult execute(McpSyncServerExchange exchange, McpSchema.CallToolRequest callRequest) {
        return execute(callRequest);
    }

    /**
     * Executes a tool request directly, without exchange context.
     *
     * <p>
     * Resolves path parameters, query parameters, headers, and authentication,
     * then executes the HTTP request and returns the response wrapped as structured content.
     * </p>
     *
     * @param callRequest the tool execution request
     * @return the result of executing the tool
     */
    public McpSchema.CallToolResult execute(McpSchema.CallToolRequest callRequest) {
        String response;
        try {
            McpSchema.Tool toolToExecute = mcpServerCacheService.getTool(callRequest.name());
            String httpMethod = toolToExecute.meta().get("httpMethod").toString().toUpperCase();
            String path = toolToExecute.meta().get(CommonConstant.PATH).toString();
            McpServerConfig config = mcpServerCacheService.getServerConfig();

            Map<String, Object> arguments = new HashMap<>(callRequest.arguments());

            // Resolve final URL with substituted path and query parameters
            String finalUrl = substitutePathParameters(config.getApiBaseUrl() + path, toolToExecute, arguments);
            finalUrl = appendQueryParameters(finalUrl, toolToExecute, arguments, config);

            // Prepare headers and request body
            Map<String, String> headers = restApiAuthHandler.extractAuthHeaders(config);
            String body = null;
            if (shouldHaveBody(httpMethod)) {
                body = jsonMapper.writeValueAsString(arguments);
                headers.put("Content-Type", "application/json");
            }

            LOGGER.debug("Executing {} request to URL: {}", httpMethod, finalUrl);
            response = restApiExecutionService.executeRequest(finalUrl, httpMethod, body, headers);
            LOGGER.info("Successfully executed tool '{}'.", callRequest.name());

        } catch (IOException | InterruptedException e) {
            LOGGER.error("Execution failed for tool '{}': {}", callRequest.name(), e.getMessage());
            throw new RuntimeException("Failed to execute tool: " + callRequest.name(), e);
        }
        Map<String, Object> wrappedResponse = new HashMap<>();
        wrappedResponse.put("response",response);
        return McpSchema.CallToolResult.builder()
                .structuredContent(wrappedResponse)
                .build();
    }

    /**
     * Substitutes path parameters (e.g., {@code /users/{id}}) in the URL with actual values
     * from the request arguments.
     *
     * @param url       the URL containing path placeholders
     * @param tool      the tool definition containing metadata
     * @param arguments the request arguments
     * @return the final URL with substituted path parameters
     */
    private String substitutePathParameters(String url, McpSchema.Tool tool, Map<String, Object> arguments) {
        Map<String, Object> pathParams = (Map<String, Object>) tool.meta().getOrDefault("pathParams", Collections.emptyMap());
        String finalUrl = url;
        for (String paramName : pathParams.keySet()) {
            if (arguments.containsKey(paramName)) {
                String value = String.valueOf(arguments.get(paramName));
                finalUrl = finalUrl.replace("{" + paramName + "}", URLEncoder.encode(value, StandardCharsets.UTF_8));
                arguments.remove(paramName);
            }
        }
        return finalUrl;
    }

    /**
     * Appends query parameters (including API key if configured) to the URL.
     *
     * @param url       the base URL
     * @param tool      the tool definition containing metadata
     * @param arguments the request arguments
     * @param config    the server configuration (used for API key handling)
     * @return the final URL with query parameters appended
     */
    private String appendQueryParameters(String url, McpSchema.Tool tool, Map<String, Object> arguments, McpServerConfig config) {
        Map<String, Object> queryParams = (Map<String, Object>) tool.meta().getOrDefault("queryParams", Collections.emptyMap());
        List<String> queryParts = new ArrayList<>();

        // Add regular query parameters
        queryParams.keySet().stream()
                .filter(arguments::containsKey)
                .map(paramName -> {
                    String key = URLEncoder.encode(paramName, StandardCharsets.UTF_8);
                    String value = URLEncoder.encode(String.valueOf(arguments.get(paramName)), StandardCharsets.UTF_8);
                    arguments.remove(paramName);
                    return key + "=" + value;
                })
                .forEach(queryParts::add);

        // Add API key if configured to go in query
        if (config.getAuthType() == OpenApiSchemaAuthType.API_KEY && "query".equalsIgnoreCase(config.getAuthApiKeyIn())) {
            String key = URLEncoder.encode(config.getAuthApiKeyName(), StandardCharsets.UTF_8);
            String value = URLEncoder.encode(new String(Objects.requireNonNull(config.getAuthApiKey())), StandardCharsets.UTF_8);
            queryParts.add(key + "=" + value);
        }

        if (queryParts.isEmpty()) {
            return url;
        }

        String queryPart = String.join("&", queryParts);
        return url + (url.contains("?") ? "&" : "?") + queryPart;
    }

    /**
     * Prepares HTTP headers, including authentication headers based on server configuration.
     *
     * @param config the server configuration
     * @return a map of HTTP headers
     */
    private Map<String, String> prepareHeaders(McpServerConfig config) {
        Map<String, String> headers = new HashMap<>();
        headers.put("Accept", "application/json");

        OpenApiSchemaAuthType authType = config.getAuthType();
        if (authType == null) {
            authType = OpenApiSchemaAuthType.NONE;
        }

        switch (authType) {
            case NONE:
                break;
            case BASIC:
                char[] passwordChars = config.getAuthPassword();
                assert passwordChars != null;
                String password = new String(passwordChars);
                String encoded = Base64.getEncoder().encodeToString(
                        (config.getAuthUsername() + ":" + password).getBytes(StandardCharsets.UTF_8)
                );
                headers.put("Authorization", "Basic " + encoded);
                Arrays.fill(passwordChars, ' ');
                break;
            case BEARER:
                char[] tokenChars = config.getAuthToken();
                assert tokenChars != null;
                String token = new String(tokenChars);
                headers.put("Authorization", "Bearer " + token);
                Arrays.fill(tokenChars, ' ');
                break;
            case API_KEY:
                if ("header".equalsIgnoreCase(config.getAuthApiKeyIn())) {
                    headers.put(config.getAuthApiKeyName(), new String(Objects.requireNonNull(config.getAuthApiKey())));
                }
                break;
            case CUSTOM:
                headers.putAll(config.getAuthCustomHeaders());
                break;
        }
        return headers;
    }

    /**
     * Determines whether the HTTP request should have a body.
     *
     * @param httpMethod the HTTP method (e.g., GET, POST, PUT, PATCH)
     * @return true if the method supports a request body, false otherwise
     */
    private boolean shouldHaveBody(String httpMethod) {
        return switch (httpMethod.toUpperCase()) {
            case "POST", "PUT", "PATCH" -> true;
            default -> false;
        };
    }
}
