package com.oracle.mcp.openapi;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.exception.McpServerToolInitializeException;
import com.oracle.mcp.openapi.fetcher.OpenApiSchemaFetcher;
import com.oracle.mcp.openapi.rest.RestApiExecutionService;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.tool.OpenApiToMcpToolConverter;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpSyncServerExchange;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;
import io.modelcontextprotocol.spec.McpServerTransportProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.support.BeanDefinitionBuilder;
import org.springframework.beans.factory.support.DefaultListableBeanFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import io.modelcontextprotocol.server.McpServerFeatures.SyncToolSpecification;
import io.modelcontextprotocol.server.McpSyncServer;

import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.Bean;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;

@SpringBootApplication
public class OpenApiMcpServer implements CommandLineRunner {

    @Autowired
    OpenApiSchemaFetcher openApiSchemaFetcher;

    @Autowired
    OpenApiToMcpToolConverter openApiToMcpToolConverter;

    @Autowired
    ConfigurableApplicationContext context;

    @Autowired
    McpServerCacheService mcpServerCacheService;

    @Autowired
    RestApiExecutionService restApiExecutionService;

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiMcpServer.class);



    public static void main(String[] args) {
        SpringApplication.run(OpenApiMcpServer.class, args);
    }

    @Override
    public void run(String... args) throws Exception {
        initialize(args);
    }


    private void initialize(String[] args) throws Exception {
        // No latch, register immediately
        McpServerConfig argument = null;
        try {
            argument = McpServerConfig.fromArgs(args);
            mcpServerCacheService.putServerConfig(argument);
            // Fetch and convert OpenAPI to tools
            JsonNode openApiJson = openApiSchemaFetcher.fetch(argument);
            List<McpSchema.Tool> mcpTools = openApiToMcpToolConverter.convertJsonToMcpTools(openApiJson);

            // Build MCP server
            McpSchema.ServerCapabilities serverCapabilities = McpSchema.ServerCapabilities.builder()
                    .tools(false)
                    .resources(false, false)
                    .prompts(false)
                    .logging()
                    .completions()
                    .build();

            McpServerTransportProvider stdInOutTransport =
                    new StdioServerTransportProvider(new ObjectMapper(), System.in, System.out);

            McpSyncServer mcpSyncServer = McpServer.sync(stdInOutTransport)
                    .serverInfo("openapi-mcp-server", "1.0.0")
                    .capabilities(serverCapabilities)
                    .build();
            // Register tools
            for (McpSchema.Tool tool : mcpTools) {
                SyncToolSpecification syncTool = SyncToolSpecification.builder()
                        .tool(tool)
                        .callHandler(this::executeTool)
                        .build();
                mcpSyncServer.addTool(syncTool);
            }
            DefaultListableBeanFactory beanFactory = (DefaultListableBeanFactory) context.getBeanFactory();

            beanFactory.registerSingleton("mcpSyncServer", mcpSyncServer);
        } catch (McpServerToolInitializeException exception) {
            LOGGER.error(exception.getMessage());
            System.err.println(exception.getMessage());
            System.exit(1);
        }

    }

    private McpSchema.CallToolResult executeTool(McpSyncServerExchange exchange, McpSchema.CallToolRequest callRequest){
        String response="";
        try {
            McpSchema.Tool toolToExecute =  mcpServerCacheService.getTool(callRequest.name());
            String httpMethod = toolToExecute.meta().get("httpMethod").toString();
            String path = toolToExecute.meta().get("path").toString();

            McpServerConfig config = mcpServerCacheService.getServerConfig();
            String url = config.getApiBaseUrl() + path;
            Map<String, Object> arguments =callRequest.arguments();
            Map<String, Map<String, Object>>  pathParams = (Map<String, Map<String, Object>>) Optional.ofNullable(toolToExecute.meta().get("pathParams"))
                    .orElse(Collections.emptyMap());
            Map<String, Map<String, Object>> queryParams = (Map<String, Map<String, Object>>) Optional.ofNullable(toolToExecute.meta().get("queryParams"))
                    .orElse(Collections.emptyMap());
            String formattedUrl = url;
            Iterator<Map.Entry<String, Object>> iterator = arguments.entrySet().iterator();
            LOGGER.debug("Path params {}", pathParams);
            while (iterator.hasNext()) {
                Map.Entry<String, Object> entry = iterator.next();
                if (pathParams.containsKey(entry.getKey())) {
                    LOGGER.info("Entry {}", new ObjectMapper().writeValueAsString(entry));

                    String placeholder = "{" + entry.getKey() + "}";
                    String value = entry.getValue() != null ? entry.getValue().toString() : "";
                    formattedUrl = formattedUrl.replace(placeholder, value);
                    iterator.remove();
                }
            }
            LOGGER.info("Formated URL {}", formattedUrl);

            OpenApiSchemaAuthType authType = config.getAuthType();
            Map<String,String> headers = new java.util.HashMap<>();
            if (authType == OpenApiSchemaAuthType.BASIC) {
                String encoded = Base64.getEncoder().encodeToString(
                        (config.getAuthUsername() + ":" + config.getAuthPassword())
                                .getBytes(StandardCharsets.UTF_8)
                );
                headers.put("Authorization", "Basic " + encoded);
            }
            String body = new ObjectMapper().writeValueAsString(arguments);
            response = restApiExecutionService.executeRequest(formattedUrl,httpMethod,body,headers);
            LOGGER.info("Server exchange {}", new ObjectMapper().writeValueAsString(toolToExecute));
            LOGGER.info("Server callRequest {}", new ObjectMapper().writeValueAsString(callRequest));

        } catch (JsonProcessingException | InterruptedException e) {
            throw new RuntimeException(e);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return McpSchema.CallToolResult.builder()
                .structuredContent(response)
                .build();
    }
}
