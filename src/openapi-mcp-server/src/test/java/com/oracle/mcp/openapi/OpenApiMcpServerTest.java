package com.oracle.mcp.openapi;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.WireMockServer;
import com.github.tomakehurst.wiremock.core.WireMockConfiguration;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.rest.RestApiAuthHandler;
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

    @Autowired private McpSyncServer mcpSyncServer;
    @Autowired private RestApiExecutionService restApiExecutionService;
    @Autowired private McpServerCacheService mcpServerCacheService;
    @Autowired private RestApiAuthHandler restApiAuthHandler;
    @Autowired private ApplicationContext context;

    private static final ObjectMapper objectMapper = new ObjectMapper();

    private static String expectedTools;
    private static String companiesResponse;
    private static String companyResponse;

    @BeforeAll
    static void setup() throws Exception {
        // Start WireMock once for all tests
        WireMockServer wireMockServer = new WireMockServer(
                WireMockConfiguration.options()
                        .port(8080)
                        .usingFilesUnderDirectory("src/test/resources")
        );
        wireMockServer.start();

        // Load test resources
        expectedTools = readFile("src/test/resources/tools/listTool.json");
        companiesResponse = readFile("src/test/resources/__files/companies-response.json");
        companyResponse = readFile("src/test/resources/__files/company-1-response.json");
    }

    private static String readFile(String path) throws Exception {
        return Files.readString(Paths.get(path));
    }

    private OpenApiMcpToolExecutor newExecutor(McpServerCacheService cache) {
        return new OpenApiMcpToolExecutor(cache, restApiExecutionService, objectMapper, restApiAuthHandler);
    }

    private String executeTool(McpServerCacheService cache, String toolName, String input) throws Exception {
        OpenApiMcpToolExecutor executor = newExecutor(cache);
        McpSchema.CallToolRequest request = new McpSchema.CallToolRequest(toolName, input);
        McpSchema.CallToolResult result = executor.execute(request);
        Object resultObj = result.structuredContent().get("response");
        JsonNode jsonNode = objectMapper.readTree((String)resultObj);
        return objectMapper.writeValueAsString(jsonNode);
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

        String response = executeTool(cacheService, "getCompanies", "{}");
        assertEquals(companiesResponse, response);
    }

    @Test
    void testExecuteGetOneCompany_BearerAuth() throws Exception {
        McpServerCacheService cacheService = mockConfig(
                McpServerConfig.builder()
                        .apiBaseUrl("http://localhost:8080")
                        .authType("BEARER")
                        .authToken("test-token".toCharArray())
                        .build(),
                "getCompanyById"
        );

        String response = executeTool(cacheService, "getCompanyById", "{\"companyId\":1}");
        assertEquals(companyResponse, response);
    }

    @Test
    void testExecuteCreateCompany_ApiKeyAuth() throws Exception {
        McpServerCacheService cacheService = mockConfig(
                McpServerConfig.builder()
                        .apiBaseUrl("http://localhost:8080")
                        .authType("API_KEY")
                        .authApiKeyIn("HEADER")
                        .authApiKeyName("X-API-KEY")
                        .authApiKey("test-api-key".toCharArray())
                        .build(),
                "createCompany"
        );

        String response = executeTool(cacheService, "createCompany",
                "{ \"name\": \"Test Company\", \"address\": \"123 Main St\" }");
        assertEquals(companyResponse, response);
    }

    @Test
    void testExecuteUpdateCompany_CustomAuth() throws Exception {
        McpServerCacheService cacheService = mockConfig(
                McpServerConfig.builder()
                        .apiBaseUrl("http://localhost:8080")
                        .authType("CUSTOM")
                        .authCustomHeaders(Map.of("CUSTOM-HEADER", "test-custom-key"))
                        .build(),
                "updateCompany"
        );

        String response = executeTool(cacheService, "updateCompany",
                "{ \"companyId\": 1, \"name\": \"Acme Corp - Updated\", \"industry\": \"Technology\" }");
        assertEquals(companyResponse, response);
    }

    private McpServerCacheService mockConfig(McpServerConfig config, String toolName) {
        McpServerCacheService mockCache = Mockito.mock(McpServerCacheService.class);
        Mockito.when(mockCache.getServerConfig()).thenReturn(config);
        Mockito.when(mockCache.getTool(toolName)).thenReturn(this.mcpServerCacheService.getTool(toolName));
        return mockCache;
    }
}
