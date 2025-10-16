/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.cache;

import com.oracle.mcp.openapi.model.McpServerConfig;
import io.modelcontextprotocol.spec.McpSchema;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/**
 * A thread-safe, in-memory cache to store the server configuration and parsed OpenAPI tools.
 * <p>
 * This service acts as a simple singleton-like container for shared resources that are
 * required throughout the server's lifecycle, preventing the need to re-parse or
 * re-initialize these objects for each request.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class McpServerCacheService {


    private final ConcurrentMap<String, McpSchema.Tool> toolListCache = new ConcurrentHashMap<>();
    private McpServerConfig serverConfig;

    /**
     * Caches a tool definition, associating it with a unique key (e.g., the operation ID).
     * If a tool with the same key already exists, it will be overwritten.
     *
     * @param key  The unique identifier for the tool.
     * @param tool The {@link McpSchema.Tool} object to cache.
     */
    public void putTool(String key, McpSchema.Tool tool) {
        toolListCache.put(key, tool);
    }

    /**
     * Retrieves a tool from the cache by its key.
     *
     * @param key The unique identifier of the tool to retrieve.
     * @return The cached {@link McpSchema.Tool} object, or {@code null} if no tool is found for the given key.
     */
    public McpSchema.Tool getTool(String key) {
        return toolListCache.get(key);
    }

    /**
     * Caches the server's global configuration object.
     * This will overwrite any previously stored configuration.
     *
     * @param config The {@link McpServerConfig} object to cache.
     */
    public void putServerConfig(McpServerConfig config) {
        serverConfig = config;
    }

    /**
     * Retrieves the cached server configuration object.
     *
     * @return The cached {@link McpServerConfig} object.
     */
    public McpServerConfig getServerConfig() {
        return serverConfig;
    }
}
