/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.mapper;

import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.model.override.ToolOverridesConfig;
import com.oracle.mcp.openapi.util.McpServerUtil;
import io.modelcontextprotocol.spec.McpSchema;

import java.util.Collections;
import java.util.List;
import java.util.Set;

/**
 * Mapper interface for converting OpenAPI specifications into
 * {@link McpSchema.Tool} representations.
 * <p>
 * Implementations of this interface are responsible for reading a parsed
 * API specification (as a Jackson {@link JsonNode}) and mapping it into
 * a list of tool definitions that conform to the MCP schema.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public interface McpToolMapper {

    /**
     * Converts an OpenAPI specification into a list of MCP tools.
     *
     * @param toolOverridesConfig the tool overrides configuration.
     * @param apiSpec the OpenAPI specification represented as a {@link JsonNode};
     *                must not be {@code null}.
     * @return a list of {@link McpSchema.Tool} objects derived from the given API specification;
     *         never {@code null}, but may be empty if no tools are found.
     */
    List<McpSchema.Tool> convert(JsonNode apiSpec,ToolOverridesConfig toolOverridesConfig) throws McpServerToolInitializeException;

    default String generateToolName(
            String method,
            String path,
            String operationId,
            Set<String> existingNames) {

        String baseName;

        if (operationId != null && !operationId.isEmpty()) {
            baseName = operationId;
        } else {
            StringBuilder name = new StringBuilder(method.toLowerCase());
            for (String segment : path.split("/")) {
                if (segment.isEmpty()){
                    continue;
                }

                if (segment.startsWith("{") && segment.endsWith("}")) {
                    String varName = segment.substring(1, segment.length() - 1);
                    name.append("By").append(McpServerUtil.capitalize(varName));
                } else {
                    name.append(McpServerUtil.capitalize(segment));
                }
            }
            baseName = name.toString();
        }

        String uniqueName = baseName;

        // Resolve clash: add HTTP method if already taken
        if (existingNames.contains(uniqueName)) {
            // Append method suffix if not already included
            String methodSuffix = McpServerUtil.capitalize(method.toLowerCase());
            if (!uniqueName.endsWith(methodSuffix)) {
                uniqueName = baseName + methodSuffix;
            }
            // In the rare case it's STILL a clash, append last path segment
            if (existingNames.contains(uniqueName)) {
                String lastSegment = getLastPathSegment(path);
                uniqueName = baseName + McpServerUtil.capitalize(method.toLowerCase()) + McpServerUtil.capitalize(lastSegment);
            }
        }

        existingNames.add(uniqueName);
        return uniqueName;
    }


    default String getLastPathSegment(String path) {
        String[] segments = path.split("/");
        for (int i = segments.length - 1; i >= 0; i--) {
            if (!segments[i].isEmpty() && !segments[i].startsWith("{")) {
                return segments[i];
            }
        }
        return "Endpoint";
    }

    default boolean skipTool(String toolName, ToolOverridesConfig config) {
        if (config == null) {
            return false;
        }

        Set<String> includeOnly = config.getIncludeOnly() == null
                ? Collections.emptySet()
                : config.getIncludeOnly();

        Set<String> exclude = config.getExclude() == null
                ? Collections.emptySet()
                : config.getExclude();

        // Apply filtering: Exclude wins
        return (!includeOnly.isEmpty() && !includeOnly.contains(toolName))
                || exclude.contains(toolName);
    }
}
