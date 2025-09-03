/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.fetcher.OpenApiSchemaFetcher;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.tool.OpenApiMcpToolExecutor;
import com.oracle.mcp.openapi.tool.OpenApiMcpToolInitializer;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;
import io.modelcontextprotocol.spec.McpServerTransportProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.support.DefaultListableBeanFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import io.modelcontextprotocol.server.McpServerFeatures.SyncToolSpecification;
import io.modelcontextprotocol.server.McpSyncServer;
import org.springframework.context.ConfigurableApplicationContext;

import java.util.*;

/**
 * Entry point for the OpenAPI MCP server.
 * <p>
 * This Spring Boot application:
 * <ul>
 *   <li>Parses command-line arguments into a {@link McpServerConfig}</li>
 *   <li>Fetches an OpenAPI/Swagger specification</li>
 *   <li>Converts the specification into {@link McpSchema.Tool} objects</li>
 *   <li>Registers the tools in an {@link McpSyncServer}</li>
 *   <li>Exposes the server via standard I/O transport</li>
 * </ul>
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
@SpringBootApplication
public class OpenApiMcpServer implements CommandLineRunner {

    @Autowired
    OpenApiSchemaFetcher openApiSchemaFetcher;

    @Autowired
    OpenApiMcpToolExecutor openApiMcpToolExecutor;

    @Autowired
    OpenApiMcpToolInitializer openApiMcpToolInitializer;

    @Autowired
    ConfigurableApplicationContext context;

    @Autowired
    McpServerCacheService mcpServerCacheService;

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiMcpServer.class);

    /**
     * Starts the Spring Boot application.
     *
     * @param args command-line arguments for configuring the server
     */
    public static void main(String[] args) {
        SpringApplication.run(OpenApiMcpServer.class, args);
    }

    /**
     * Callback method executed after the Spring Boot application starts.
     * <p>
     * Delegates to {@link #initialize(String[])} to set up the MCP server.
     *
     * @param args application command-line arguments
     * @throws Exception if initialization fails
     */
    @Override
    public void run(String... args) throws Exception {
        initialize(args);
    }

    /**
     * Initializes the MCP server.
     * <p>
     * The initialization process:
     * <ol>
     *   <li>Parses arguments into {@link McpServerConfig}</li>
     *   <li>Caches the server configuration</li>
     *   <li>Fetches and parses the OpenAPI/Swagger schema</li>
     *   <li>Converts the schema into MCP tools via {@link OpenApiMcpToolInitializer}</li>
     *   <li>Builds and configures an {@link McpSyncServer}</li>
     *   <li>Registers each tool with a {@link SyncToolSpecification}</li>
     *   <li>Registers the MCP server bean in the Spring context</li>
     * </ol>
     *
     * @param args command-line arguments
     * @throws Exception if initialization fails
     */
    private void initialize(String[] args) throws Exception {
        McpServerConfig argument;
        try {
            argument = McpServerConfig.fromArgs(args);
            mcpServerCacheService.putServerConfig(argument);

            // Fetch and convert OpenAPI to tools
            JsonNode openApiJson = openApiSchemaFetcher.fetch(argument);
            List<McpSchema.Tool> mcpTools = openApiMcpToolInitializer.extractTools(openApiJson);

            // Build MCP server capabilities
            McpSchema.ServerCapabilities serverCapabilities = McpSchema.ServerCapabilities.builder()
                    .tools(false)
                    .resources(false, false)
                    .prompts(false)
                    .logging()
                    .completions()
                    .build();

            // Use stdin/stdout for communication
            McpServerTransportProvider stdInOutTransport =
                    new StdioServerTransportProvider(new ObjectMapper(), System.in, System.out);

            McpSyncServer mcpSyncServer = McpServer.sync(stdInOutTransport)
                    .serverInfo("openapi-mcp-server", "1.0.0")
                    .capabilities(serverCapabilities)
                    .build();

            // Register each tool in the server
            for (McpSchema.Tool tool : mcpTools) {
                SyncToolSpecification syncTool = SyncToolSpecification.builder()
                        .tool(tool)
                        .callHandler(openApiMcpToolExecutor::execute)
                        .build();
                mcpSyncServer.addTool(syncTool);
            }

            // Expose MCP server as a Spring bean
            DefaultListableBeanFactory beanFactory = (DefaultListableBeanFactory) context.getBeanFactory();
            beanFactory.registerSingleton("mcpSyncServer", mcpSyncServer);

        } catch (McpServerToolInitializeException exception) {
            LOGGER.error(exception.getMessage());
            System.err.println(exception.getMessage());
            System.exit(1);
        }
    }
}
