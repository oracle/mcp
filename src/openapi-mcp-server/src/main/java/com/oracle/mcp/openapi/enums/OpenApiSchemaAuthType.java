/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.enums;

import com.oracle.mcp.openapi.model.McpServerConfig;

/**
 * Represents the supported authentication types for the OpenAPI MCP server.
 * This enum provides a type-safe way to handle different authentication schemes.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public enum OpenApiSchemaAuthType {
    /**
     * Basic Authentication using a username and password.
     */
    BASIC,
    /**
     * Bearer Token Authentication using an opaque token.
     */
    BEARER,
    /**
     * API Key Authentication, where the key can be sent in a header or query parameter.
     */
    API_KEY,
    /**
     * Custom Authentication using a user-defined set of headers.
     */
    CUSTOM,
    /**
     * No authentication is required.
     */
    NONE;

    /**
     * Safely determines the {@code OpenApiSchemaAuthType} from the server configuration.
     * <p>
     * This method parses the raw authentication type string provided in the
     * {@link McpServerConfig}. It handles null, empty, or invalid strings by defaulting
     * to {@link #NONE}, preventing runtime exceptions.
     *
     * @param request The server configuration object containing the raw auth type string.
     * @return The corresponding {@code OpenApiSchemaAuthType} enum constant. Returns {@link #NONE}
     * if the provided auth type is null, empty, or does not match any known type.
     */
    public static OpenApiSchemaAuthType getType(McpServerConfig request) {
        String authType = request.getRawAuthType();
        if (authType == null || authType.isEmpty()) {
            return NONE;
        }
        try {
            return OpenApiSchemaAuthType.valueOf(authType.toUpperCase());
        } catch (IllegalArgumentException ex) {
            return NONE;
        }
    }
}
