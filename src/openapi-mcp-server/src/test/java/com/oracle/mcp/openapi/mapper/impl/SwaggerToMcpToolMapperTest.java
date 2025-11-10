/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.mapper.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.constants.ErrorMessage;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.model.override.ToolOverridesConfig;
import io.modelcontextprotocol.spec.McpSchema;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class SwaggerToMcpToolMapperTest {

    private SwaggerToMcpToolMapper swaggerMapper;
    private McpServerCacheService cacheService;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        cacheService = mock(McpServerCacheService.class);
        swaggerMapper = new SwaggerToMcpToolMapper(cacheService);
        objectMapper = new ObjectMapper();
    }

    @Test
    void convert_ShouldCreateTool_WhenOperationPresent() throws McpServerToolInitializeException {
        // Arrange
        ObjectNode swaggerJson = objectMapper.createObjectNode();
        swaggerJson.put("swagger", "2.0");

        ObjectNode paths = objectMapper.createObjectNode();
        ObjectNode getOp = objectMapper.createObjectNode();
        getOp.put("operationId", "testTool");
        paths.set("/test", objectMapper.createObjectNode().set("get", getOp));
        swaggerJson.set("paths", paths);

        ToolOverridesConfig overrides = new ToolOverridesConfig();

        // Act
        List<McpSchema.Tool> tools = swaggerMapper.convert(swaggerJson, overrides);

        // Assert
        assertEquals(1, tools.size(), "One tool should be created");
        assertEquals("testTool", tools.get(0).name());
        verify(cacheService).putTool("testTool", tools.get(0));
    }

    @Test
    void convert_ShouldSkipTool_WhenInExcludeList() throws McpServerToolInitializeException {
        // Arrange
        ObjectNode swaggerJson = objectMapper.createObjectNode();
        swaggerJson.put("swagger", "2.0");

        ObjectNode paths = objectMapper.createObjectNode();
        ObjectNode getOp = objectMapper.createObjectNode();
        getOp.put("operationId", "skipTool");
        paths.set("/skip", objectMapper.createObjectNode().set("get", getOp));
        swaggerJson.set("paths", paths);

        ToolOverridesConfig overrides = new ToolOverridesConfig();
        overrides.setExclude(Set.of("skipTool"));

        // Act
        List<McpSchema.Tool> tools = swaggerMapper.convert(swaggerJson, overrides);

        // Assert
        assertTrue(tools.isEmpty(), "Tool should be skipped due to exclude list");
        verify(cacheService, never()).putTool(anyString(), any(McpSchema.Tool.class));
    }

    @Test
    void convert_ShouldThrowException_WhenPathsMissing() {
        // Arrange
        ObjectNode swaggerJson = objectMapper.createObjectNode();
        swaggerJson.put("swagger", "2.0");

        ToolOverridesConfig overrides = new ToolOverridesConfig();

        // Act & Assert
        McpServerToolInitializeException ex = assertThrows(
                McpServerToolInitializeException.class,
                () -> swaggerMapper.convert(swaggerJson, overrides)
        );
        assertEquals(ErrorMessage.MISSING_PATH_IN_SPEC, ex.getMessage());
    }
}
