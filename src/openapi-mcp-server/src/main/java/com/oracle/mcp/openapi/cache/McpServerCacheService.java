package com.oracle.mcp.openapi.cache;

import com.oracle.mcp.openapi.model.McpServerConfig;
import io.modelcontextprotocol.spec.McpSchema;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

public class McpServerCacheService {


    private final ConcurrentMap<String, McpSchema.Tool> toolListCache = new ConcurrentHashMap<>();
    private McpServerConfig serverConfig;

    // ===== MCP TOOL LIST =====
    public void putTool(String key, McpSchema.Tool tool) {
        toolListCache.put(key, tool);
    }

    public McpSchema.Tool getTool(String key) {
        return toolListCache.get(key);
    }

    // ===== MCP SERVER CONFIG (single instance) =====
    public void putServerConfig(McpServerConfig config) {
        serverConfig = config;
    }

    public McpServerConfig getServerConfig() {
        return serverConfig;
    }
}
