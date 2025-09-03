/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.enums;

import com.oracle.mcp.openapi.model.McpServerConfig;

/**
 * Represents the source type of OpenAPI specification.
 * <p>
 * This enum distinguishes between specifications loaded from a remote URL and
 * those read from a local file system path.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public enum OpenApiSchemaSourceType {
    /**
     * The specification is located at a remote URL
     */
    URL,
    /**
     * The specification is located at a path on the local file system.
     */
    FILE;

    /**
     * Determines the source type of the OpenAPI specification from the server configuration.
     * <p>
     * This method inspects the specification location string provided in the
     * {@link McpServerConfig}. It returns {@link #URL} if the string starts
     * with "http://" or "https://", and {@link #FILE} otherwise.
     *
     * @param request The server configuration containing the API specification location.
     * @return The determined {@code OpenApiSchemaSourceType} (either {@link #URL} or {@link #FILE}).
     * @throws IllegalArgumentException if the API specification location is null or empty in the configuration.
     */
    public static OpenApiSchemaSourceType getType(McpServerConfig request) {
        // Backward compatibility: prefer specUrl if set
        String specUrl = request.getApiSpec();
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
