package com.oracle.mcp.openapi.tool;

import com.fasterxml.jackson.databind.JsonNode;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.mapper.impl.OpenApiToMcpToolMapper;
import com.oracle.mcp.openapi.mapper.impl.SwaggerToMcpToolMapper;
import io.modelcontextprotocol.spec.McpSchema;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;

public class OpenApiToMcpToolConverter {

    private final McpServerCacheService mcpServerCacheService;
    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiToMcpToolConverter.class);

    public OpenApiToMcpToolConverter(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    public List<McpSchema.Tool> convertJsonToMcpTools(JsonNode openApiJson) {
        LOGGER.debug("Parsing OpenAPI JsonNode to OpenAPI object...");
        List<McpSchema.Tool> mcpTools = parseApi(openApiJson);

        LOGGER.debug("Conversion complete. Total tools created: {}", mcpTools.size());
        updateToolsToCache(mcpTools);
        return mcpTools;
    }


    private void updateToolsToCache(List<McpSchema.Tool> tools) {
        for (McpSchema.Tool tool : tools) {
            mcpServerCacheService.putTool(tool.name(), tool);
        }
    }

    private List<McpSchema.Tool> parseApi(JsonNode jsonNode) {
        if (jsonNode == null) {
            throw new IllegalArgumentException("jsonNode cannot be null");
        }
        // Detect version
        if (jsonNode.has("openapi")) {


            return new OpenApiToMcpToolMapper(mcpServerCacheService).convert(jsonNode);

        } else if (jsonNode.has("swagger")) {

            return new SwaggerToMcpToolMapper(mcpServerCacheService).convert(jsonNode);

        } else {
            throw new IllegalArgumentException("Unsupported API definition: missing 'openapi' or 'swagger' field");
        }
    }

}
