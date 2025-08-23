package com.oracle.mcp.openapi.enums;

import com.oracle.mcp.openapi.model.McpServerConfig;

public enum OpenApiSchemaAuthType {
    BASIC, BEARER, API_KEY, CUSTOM, NONE;

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
