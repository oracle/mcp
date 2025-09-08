/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.tool;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.constants.CommonConstant;
import com.oracle.mcp.openapi.constants.ErrorMessage;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.exception.UnsupportedApiDefinitionException;
import com.oracle.mcp.openapi.mapper.impl.OpenApiToMcpToolMapper;
import com.oracle.mcp.openapi.mapper.impl.SwaggerToMcpToolMapper;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.model.override.ToolOverridesConfig;
import io.modelcontextprotocol.spec.McpSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;


/**
 * Initializes and extracts {@link McpSchema.Tool} objects from OpenAPI or Swagger specifications.
 * <p>
 * This class detects whether the provided API definition is OpenAPI (v3) or Swagger (v2),
 * maps the specification into {@link McpSchema.Tool} objects, and updates the
 * {@link McpServerCacheService} with the extracted tools for later use.
 * </p>
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class OpenApiMcpToolInitializer {

    private final McpServerCacheService mcpServerCacheService;
    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiMcpToolInitializer.class);

    /**
     * Creates a new {@code OpenApiMcpToolInitializer}.
     *
     * @param mcpServerCacheService the cache service for storing and retrieving tool definitions
     */
    public OpenApiMcpToolInitializer(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    /**
     * Extracts tools from the given OpenAPI/Swagger JSON definition.
     * <p>
     * Determines the API specification type (OpenAPI or Swagger),
     * maps it to {@link McpSchema.Tool} objects, caches them,
     * and returns the list of tools.
     * </p>
     *
     * @param openApiJson the JSON representation of the OpenAPI or Swagger specification
     * @return a list of {@link McpSchema.Tool} created from the API definition
     * @throws IllegalArgumentException           if {@code openApiJson} is {@code null}
     * @throws UnsupportedApiDefinitionException if the API definition is not recognized
     */
    public List<McpSchema.Tool> extractTools(McpServerConfig serverConfig,JsonNode openApiJson) throws McpServerToolInitializeException {
        LOGGER.debug("Parsing OpenAPI JsonNode to OpenAPI object...");
        List<McpSchema.Tool> mcpTools = parseApi(serverConfig,openApiJson);
        LOGGER.debug("Conversion complete. Total tools created: {}", mcpTools.size());
        updateToolsToCache(mcpTools);
        return mcpTools;
    }

    /**
     * Updates the {@link McpServerCacheService} with the given tools.
     *
     * @param tools the tools to cache
     */
    private void updateToolsToCache(List<McpSchema.Tool> tools) {
        for (McpSchema.Tool tool : tools) {
            mcpServerCacheService.putTool(tool.name(), tool);
        }
    }

    /**
     * Parses the given JSON node into a list of {@link McpSchema.Tool} objects.
     * <p>
     * Detects the specification type:
     * <ul>
     *     <li>If {@code openapi} field exists, assumes OpenAPI 3.x</li>
     *     <li>If {@code swagger} field exists, assumes Swagger 2.x</li>
     *     <li>Otherwise, throws {@link UnsupportedApiDefinitionException}</li>
     * </ul>
     * </p>
     *
     * @param jsonNode the JSON representation of the API definition
     * @return a list of mapped {@link McpSchema.Tool} objects
     * @throws IllegalArgumentException           if {@code jsonNode} is {@code null}
     * @throws UnsupportedApiDefinitionException if the specification type is unsupported
     */
    private List<McpSchema.Tool> parseApi(McpServerConfig serverConfig,JsonNode jsonNode) throws McpServerToolInitializeException {
        if (jsonNode == null) {
            throw new IllegalArgumentException("jsonNode cannot be null");
        }
        ToolOverridesConfig toolOverridesJson = null;
        try {
            toolOverridesJson = serverConfig.getToolOverridesConfig();
        } catch (JsonProcessingException e) {
            LOGGER.warn("Failed to parse tool overrides JSON: {}", e.getMessage());
        }
        // Detect version
        if (jsonNode.has(CommonConstant.OPEN_API)) {
            return new OpenApiToMcpToolMapper(mcpServerCacheService).convert(jsonNode,toolOverridesJson);
        } else if (jsonNode.has(CommonConstant.SWAGGER)) {
            return new SwaggerToMcpToolMapper(mcpServerCacheService).convert(jsonNode,toolOverridesJson);
        } else {
            throw new McpServerToolInitializeException(ErrorMessage.INVALID_SPEC_DEFINITION);
        }

    }
}
