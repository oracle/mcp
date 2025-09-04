/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.rest;

import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.model.McpServerConfig;

import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * Handler for preparing authentication headers for REST API requests
 * based on server configuration.
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class RestApiAuthHandler {

    /**
     * Prepares HTTP headers, including authentication headers based on server configuration.
     *
     * @param config the server configuration
     * @return a map of HTTP headers
     */
    public Map<String, String> extractAuthHeaders(McpServerConfig config) {
        Map<String, String> headers = new HashMap<>();
        //headers.put("Accept", "application/json");

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
}
