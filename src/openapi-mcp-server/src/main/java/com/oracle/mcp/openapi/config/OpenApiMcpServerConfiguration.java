/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.fetcher.OpenApiSchemaFetcher;
import com.oracle.mcp.openapi.rest.RestApiAuthHandler;
import com.oracle.mcp.openapi.rest.RestApiExecutionService;
import com.oracle.mcp.openapi.tool.OpenApiMcpToolExecutor;
import com.oracle.mcp.openapi.tool.OpenApiMcpToolInitializer;

import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Spring configuration class responsible for defining and wiring all the necessary beans
 * for the OpenAPI MCP server application.
 * <p>
 * This class centralizes the creation of services, mappers, and other components,
 * managing their dependencies through Spring's dependency injection framework.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
@Configuration
public class OpenApiMcpServerConfiguration {

    /**
     * Creates a singleton {@link ObjectMapper} bean for handling JSON serialization and deserialization.
     *
     * @return A new {@code ObjectMapper} instance.
     */
    @Bean("jsonMapper")
    public ObjectMapper jsonMapper() {
        return new ObjectMapper();
    }

    /**
     * Creates a singleton {@link ObjectMapper} bean specifically configured for handling YAML.
     *
     * @return A new {@code ObjectMapper} instance configured with a {@link YAMLFactory}.
     */
    @Bean("yamlMapper")
    public ObjectMapper yamlMapper() {
        return new ObjectMapper(new YAMLFactory());
    }

    /**
     * Creates a singleton {@link McpServerCacheService} bean to act as an in-memory
     * cache for the server configuration and parsed tools.
     *
     * @return A new {@code McpServerCacheService} instance.
     */
    @Bean
    public McpServerCacheService mcpServerCacheService() {
        return new McpServerCacheService();
    }

    /**
     * Creates a singleton {@link RestApiExecutionService} bean responsible for executing
     * HTTP requests against the target OpenAPI.
     *
     * @param mcpServerCacheService The cache service, used to retrieve server and auth configurations.
     * @return A new {@code RestApiExecutionService} instance.
     */
    @Bean
    public RestApiExecutionService restApiExecutionService(McpServerCacheService mcpServerCacheService) {
        return new RestApiExecutionService(mcpServerCacheService);
    }

    /**
     * Creates a singleton {@link OpenApiMcpToolInitializer} bean that parses an OpenAPI
     * specification and converts its operations into MCP tools.
     *
     * @param mcpServerCacheService The cache service where the converted tools will be stored.
     * @return A new {@code OpenApiMcpToolInitializer} instance.
     */
    @Bean
    public OpenApiMcpToolInitializer openApiToMcpToolConverter(McpServerCacheService mcpServerCacheService) {
        return new OpenApiMcpToolInitializer(mcpServerCacheService);
    }

    /**
     * Creates a singleton {@link OpenApiSchemaFetcher} bean for retrieving the
     * OpenAPI specification from a URL or local path.
     *
     * @param jsonMapper              The mapper for parsing JSON-formatted specifications.
     * @param yamlMapper              The mapper for parsing YAML-formatted specifications.
     * @return A new {@code OpenApiSchemaFetcher} instance.
     */
    @Bean
    public OpenApiSchemaFetcher openApiDefinitionFetcher(@Qualifier("jsonMapper") ObjectMapper jsonMapper,
                                                         @Qualifier("yamlMapper") ObjectMapper yamlMapper,
                                                         RestApiAuthHandler restApiAuthHandler) {
        return new OpenApiSchemaFetcher(jsonMapper, yamlMapper, restApiAuthHandler);
    }

    @Bean
    public RestApiAuthHandler restApiAuthHandler(){
        return new RestApiAuthHandler();
    }

    /**
     * Creates a singleton {@link OpenApiMcpToolExecutor} bean that handles the
     * execution of a specific MCP tool call by translating it into an HTTP request.
     *
     * @param mcpServerCacheService   The cache service to look up tool definitions and server config.
     * @param restApiExecutionService The service to execute the final HTTP request.
     * @param jsonMapper              The mapper to serialize the request body arguments to JSON.
     * @return A new {@code OpenApiMcpToolExecutor} instance.
     */
    @Bean
    public OpenApiMcpToolExecutor openApiMcpToolExecutor(McpServerCacheService mcpServerCacheService, RestApiExecutionService restApiExecutionService, @Qualifier("jsonMapper") ObjectMapper jsonMapper,RestApiAuthHandler restApiAuthHandler) {
        return new OpenApiMcpToolExecutor(mcpServerCacheService, restApiExecutionService, jsonMapper,restApiAuthHandler);
    }
}