package com.oracle.mcp.openapi.mapper;

import com.fasterxml.jackson.databind.JsonNode;
import io.modelcontextprotocol.spec.McpSchema;

import java.util.List;

public interface McpToolMapper {

    List<McpSchema.Tool> convert(JsonNode apiSpec);
}
