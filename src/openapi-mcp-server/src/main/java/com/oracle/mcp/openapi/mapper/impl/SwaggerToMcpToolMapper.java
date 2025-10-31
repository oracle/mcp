/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.mapper.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.mapper.McpToolMapper;
import com.oracle.mcp.openapi.model.override.ToolOverridesConfig;
import io.modelcontextprotocol.spec.McpSchema;
import io.swagger.models.Swagger;
import io.swagger.parser.SwaggerParser;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.parser.converter.SwaggerConverter;
import io.swagger.v3.parser.core.models.SwaggerParseResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

/**
 * Implementation of {@link McpToolMapper} that converts Swagger 2.0 specifications
 * into MCP-compliant tool definitions.
 */
public class SwaggerToMcpToolMapper implements McpToolMapper {

    private final McpServerCacheService mcpServerCacheService;
    private static final Logger LOGGER = LoggerFactory.getLogger(SwaggerToMcpToolMapper.class);

    public SwaggerToMcpToolMapper(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    @Override
    public List<McpSchema.Tool> convert(JsonNode swaggerNode, ToolOverridesConfig toolOverridesConfig)
            throws McpServerToolInitializeException {

        SwaggerConverter converter = new SwaggerConverter();
        SwaggerParseResult result = converter.readContents(swaggerNode.toString(), null, null);
        OpenAPI openAPI = result.getOpenAPI();
        return new OpenApiToMcpToolMapper(mcpServerCacheService).convert(openAPI,toolOverridesConfig);

    }

}
