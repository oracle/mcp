package com.oracle.mcp.openapi;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.WireMockConfiguration;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.rest.RestApiExecutionService;
import com.oracle.mcp.openapi.tool.OpenApiMcpToolExecutor;
import io.modelcontextprotocol.server.McpAsyncServer;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.spec.McpSchema;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;

import java.lang.reflect.Field;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(
        args = {
                "--api-spec", "http://localhost:8080/rest/v1/metadata-catalog/companies",
                "--api-base-url", "http://localhost:8080"
        }
)
class OpenApiMcpServerTest {

    @Autowired
    private McpSyncServer mcpSyncServer;

    @Autowired
    private RestApiExecutionService restApiExecutionService;

    @Autowired
    private McpServerCacheService mcpServerCacheService;

    @Autowired
    private ApplicationContext context;

    private static final ObjectMapper objectMapper = new ObjectMapper();

    private static String expectedTools;
    private static String getAllCompaniesToolResponse;
    private static String getOneCompanyToolResponse;
    private static String getUpdateCompanyToolResponse;

    @BeforeAll
    static void setup() throws Exception {
        // Start WireMock once
        WireMockServer wireMockServer = new WireMockServer(WireMockConfiguration.options()
                .port(8080)
                .usingFilesUnderDirectory("src/test/resources"));
        wireMockServer.start();

        // Load test resources once
        expectedTools = readFile("src/test/resources/tools/listTool.json");
        getAllCompaniesToolResponse = readFile("src/test/resources/__files/companies-response.json");
        getOneCompanyToolResponse = readFile("src/test/resources/__files/company-1-response.json");
        getUpdateCompanyToolResponse = getOneCompanyToolResponse;
        System.out.println("WireMock server started on port 8080");
    }

    private static String readFile(String path) throws Exception {
        String content = Files.readString(Paths.get(path));
        assertNotNull(content, "File not found: " + path);
        return content;
    }

    @Test
    void testListTools() throws Exception {
        McpAsyncServer asyncServer = mcpSyncServer.getAsyncServer();

        Field toolsField = asyncServer.getClass().getDeclaredField("tools");
        toolsField.setAccessible(true);
        CopyOnWriteArrayList<?> tools = (CopyOnWriteArrayList<?>) toolsField.get(asyncServer);

        assertEquals(4, tools.size());
        assertEquals(expectedTools, objectMapper.writeValueAsString(tools));
    }

    @Test
    void testExecuteGetAllTools_BasicAuth() throws Exception {
        McpServerCacheService cacheService = mockConfig(
                McpServerConfig.builder()
                        .apiBaseUrl("http://localhost:8080")
                        .authType("BASIC")
                        .authUsername("test-user")
                        .authPassword("test-password".toCharArray())
                        .build(),
                "getCompanies"
        );

        OpenApiMcpToolExecutor executor = new OpenApiMcpToolExecutor(cacheService, restApiExecutionService, objectMapper);
        McpSchema.CallToolRequest request = new McpSchema.CallToolRequest("getCompanies", "{}");
        McpSchema.CallToolResult result = executor.execute(request);

        String response = objectMapper.writeValueAsString(result.structuredContent().get("response"));
        assertEquals(getAllCompaniesToolResponse, response);
    }

    @Test
    void testExecuteGetAllTools_BearerAuth() throws Exception {
        McpServerCacheService cacheService = mockConfig(
                McpServerConfig.builder()
                        .apiBaseUrl("http://localhost:8080")
                        .authType("BEARER")
                        .authToken("test-token".toCharArray())
                        .build(),
                "getCompanyById"
        );

        OpenApiMcpToolExecutor executor = new OpenApiMcpToolExecutor(cacheService, restApiExecutionService, objectMapper);
        McpSchema.CallToolRequest request = new McpSchema.CallToolRequest("getCompanyById", "{\"companyId\":1}");
        McpSchema.CallToolResult result = executor.execute(request);

        String response = objectMapper.writeValueAsString(result.structuredContent().get("response"));
        assertEquals(getOneCompanyToolResponse, response);
    }

    @Test
    void testExecuteCreateCompany_ApiKeyAuth() throws Exception {
        McpServerCacheService cacheService = mockConfig(
                McpServerConfig.builder()
                        .apiBaseUrl("http://localhost:8080")
                        .authType("API_KEY")
                        .authApiKeyIn("HEADER")
                        .authApiKeyName("X-API-KEY")
                        .authApiKey("test-api-key".toCharArray()) // <- new field in your config
                        .build(),
                "createCompany"
        );

        OpenApiMcpToolExecutor executor = new OpenApiMcpToolExecutor(cacheService, restApiExecutionService, objectMapper);
        McpSchema.CallToolRequest request = new McpSchema.CallToolRequest(
                "createCompany",
                "{ \"name\": \"Test Company\", \"address\": \"123 Main St\" }"
        );
        McpSchema.CallToolResult result = executor.execute(request);

        String response = objectMapper.writeValueAsString(result.structuredContent().get("response"));
        assertEquals(getOneCompanyToolResponse, response); // should match __files/company-1-response.json
    }

    @Test
    void testExecuteUpdateCompany_CustomAuth() throws Exception {
        McpServerCacheService cacheService = mockConfig(
                McpServerConfig.builder()
                        .apiBaseUrl("http://localhost:8080")
                        .authType("CUSTOM")
                        .authCustomHeaders(Map.of("CUSTOM-HEADER","test-custom-key"))
                        .build(),
                "updateCompany"
        );

        OpenApiMcpToolExecutor executor = new OpenApiMcpToolExecutor(cacheService, restApiExecutionService, objectMapper);

        McpSchema.CallToolRequest request = new McpSchema.CallToolRequest(
                "updateCompany",
                "{ \"companyId\": 1, \"name\": \"Acme Corp - Updated\", \"industry\": \"Technology\" }"
        );

        McpSchema.CallToolResult result = executor.execute(request);

        String response = objectMapper.writeValueAsString(result.structuredContent().get("response"));
        assertEquals(getUpdateCompanyToolResponse, response);
    }




    private McpServerCacheService mockConfig(McpServerConfig config, String toolName) {
        McpServerCacheService mockCache = Mockito.mock(McpServerCacheService.class);
        Mockito.when(mockCache.getServerConfig()).thenReturn(config);
        Mockito.when(mockCache.getTool(toolName)).thenReturn(this.mcpServerCacheService.getTool(toolName));
        return mockCache;
    }
}
