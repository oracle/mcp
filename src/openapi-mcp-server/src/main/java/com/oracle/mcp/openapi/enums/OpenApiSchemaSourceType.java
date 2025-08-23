package com.oracle.mcp.openapi.enums;

import com.oracle.mcp.openapi.model.McpServerConfig;

public enum OpenApiSchemaSourceType {
    URL, FILE;

    public static OpenApiSchemaSourceType getType(McpServerConfig request) {
        // Backward compatibility: prefer specUrl if set
        String specUrl = request.getSpecUrl();
        if (specUrl != null && !specUrl.trim().isEmpty()) {
            return URL;
        }

        String specLocation = request.getApiSpec();
        if (specLocation == null || specLocation.trim().isEmpty()) {
            throw new IllegalArgumentException("No specUrl or specLocation defined in McpServerConfig.");
        }

        if (specLocation.startsWith("http://") || specLocation.startsWith("https://")) {
            return URL;
        }
        return FILE;
    }
}
