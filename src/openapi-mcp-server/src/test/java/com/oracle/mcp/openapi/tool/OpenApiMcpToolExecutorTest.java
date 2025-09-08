/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.tool;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.constants.CommonConstant;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.rest.RestApiAuthHandler;
import com.oracle.mcp.openapi.rest.RestApiExecutionService;
import io.modelcontextprotocol.spec.McpSchema;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.IOException;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Unit tests for {@link OpenApiMcpToolExecutor}.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
@ExtendWith(MockitoExtension.class)
class OpenApiMcpToolExecutorTest {

    @Mock
    private McpServerCacheService mcpServerCacheService;

    @Mock
    private RestApiExecutionService restApiExecutionService;

    @Mock
    private RestApiAuthHandler restApiAuthHandler;

    @Spy
    private ObjectMapper jsonMapper = new ObjectMapper();

    @InjectMocks
    private OpenApiMcpToolExecutor openApiMcpToolExecutor;

    @Captor
    private ArgumentCaptor<String> urlCaptor;

    @Captor
    private ArgumentCaptor<String> methodCaptor;

    @Captor
    private ArgumentCaptor<String> bodyCaptor;

    @Captor
    private ArgumentCaptor<Map<String, String>> headersCaptor;

    private McpServerConfig serverConfig;

    @BeforeEach
    void setUp() {
        serverConfig = new McpServerConfig.Builder().apiBaseUrl("https://api.example.com").build();
    }

    /**
     * Tests a successful execution of a POST request with path and query parameters.
     */
    @Test
    void execute_PostRequest_Successful() throws IOException, InterruptedException {
        // Arrange
        Map<String, Object> arguments = new HashMap<>();
        arguments.put("userId", 123);
        arguments.put("filter", "active");
        arguments.put("requestData", Map.of("name", "test"));

        McpSchema.CallToolRequest callRequest = McpSchema.CallToolRequest.builder()
                .name("createUser")
                .arguments(arguments)
                .build();

        Map<String, Object> meta = new HashMap<>();
        meta.put("httpMethod", "POST");
        meta.put(CommonConstant.PATH, "/users/{userId}");
        meta.put("pathParams", Map.of("userId", "integer"));
        meta.put("queryParams", Map.of("filter", "string"));

        McpSchema.Tool tool = McpSchema.Tool.builder()
                .name("createUser")
                .meta(meta)
                .build();

        when(mcpServerCacheService.getTool("createUser")).thenReturn(tool);
        when(mcpServerCacheService.getServerConfig()).thenReturn(serverConfig);
        Map<String,String> headers = new HashMap<>();
        headers.put("Authorization", "Bearer token");
        when(restApiAuthHandler.extractAuthHeaders(serverConfig)).thenReturn(headers);
        when(restApiExecutionService.executeRequest(anyString(), anyString(), anyString(), any()))
                .thenReturn("{\"status\":\"success\"}");

        // Act
        McpSchema.CallToolResult result = openApiMcpToolExecutor.execute(callRequest);

        // Assert
        assertNotNull(result);
        assertTrue(result.structuredContent().containsKey("response"));
        assertEquals("{\"status\":\"success\"}", result.structuredContent().get("response"));

        verify(restApiExecutionService).executeRequest(urlCaptor.capture(), methodCaptor.capture(), bodyCaptor.capture(), headersCaptor.capture());
        assertEquals("https://api.example.com/users/123?filter=active", urlCaptor.getValue());
        assertEquals("POST", methodCaptor.getValue());
        assertEquals("{\"requestData\":{\"name\":\"test\"}}", bodyCaptor.getValue());
        assertEquals("Bearer token", headersCaptor.getValue().get("Authorization"));
        assertEquals("application/json", headersCaptor.getValue().get("Content-Type"));
    }

    /**
     * Tests a successful execution of a GET request, ensuring no request body is sent.
     */
    @Test
    void execute_GetRequest_Successful() throws IOException, InterruptedException {
        // Arrange
        McpSchema.CallToolRequest callRequest = McpSchema.CallToolRequest.builder()
                .name("getUser")
                .arguments(Collections.emptyMap())
                .build();

        Map<String, Object> meta = Map.of("httpMethod", "GET", CommonConstant.PATH, "/user");
        McpSchema.Tool tool = McpSchema.Tool.builder().name("getUser").meta(meta).build();

        when(mcpServerCacheService.getTool("getUser")).thenReturn(tool);
        when(mcpServerCacheService.getServerConfig()).thenReturn(serverConfig);
        when(restApiExecutionService.executeRequest(anyString(), anyString(), any(), any()))
                .thenReturn("{\"id\":1}");

        // Act
        openApiMcpToolExecutor.execute(callRequest);

        // Assert
        verify(restApiExecutionService).executeRequest(urlCaptor.capture(), methodCaptor.capture(), bodyCaptor.capture(), any());
        assertEquals("https://api.example.com/user", urlCaptor.getValue());
        assertEquals("GET", methodCaptor.getValue());
        assertNull(bodyCaptor.getValue()); // No body for GET requests
    }

    /**
     * Tests that an API key is correctly appended to the query parameters when configured.
     */
    @Test
    void execute_ApiKeyInQuery_Successful() throws IOException, InterruptedException {
        // Arrange
        serverConfig = new McpServerConfig.Builder().apiBaseUrl("https://api.example.com")
        .authType(OpenApiSchemaAuthType.API_KEY.name())
                .authApiKeyIn("query")
        .authApiKeyName("api_key")
        .authApiKey("test-secret-key".toCharArray()).build();

        McpSchema.CallToolRequest callRequest = McpSchema.CallToolRequest.builder()
                .name("getData")
                .arguments(Collections.emptyMap())
                .build();

        Map<String, Object> meta = Map.of("httpMethod", "GET", CommonConstant.PATH, "/data");
        McpSchema.Tool tool = McpSchema.Tool.builder().name("getData").meta(meta).build();

        when(mcpServerCacheService.getTool("getData")).thenReturn(tool);
        when(mcpServerCacheService.getServerConfig()).thenReturn(serverConfig);

        // Act
        openApiMcpToolExecutor.execute(callRequest);

        // Assert
        verify(restApiExecutionService).executeRequest(urlCaptor.capture(), anyString(), any(), any());
        assertEquals("https://api.example.com/data?api_key=test-secret-key", urlCaptor.getValue());
    }

    /**
     * Tests proper URL encoding of path and query parameters.
     */
    @Test
    void execute_UrlEncoding_Successful() throws IOException, InterruptedException {
        // Arrange
        Map<String, Object> arguments = new HashMap<>();
        arguments.put("folderName", "my documents/work");
        arguments.put("searchTerm", "a&b=c");

        McpSchema.CallToolRequest callRequest = McpSchema.CallToolRequest.builder()
                .name("searchFiles")
                .arguments(arguments)
                .build();

        Map<String, Object> meta = new HashMap<>();
        meta.put("httpMethod", "GET");
        meta.put(CommonConstant.PATH, "/files/{folderName}");
        meta.put("pathParams", Map.of("folderName", "string"));
        meta.put("queryParams", Map.of("searchTerm", "string"));
        McpSchema.Tool tool = McpSchema.Tool.builder().name("searchFiles").meta(meta).build();

        when(mcpServerCacheService.getTool("searchFiles")).thenReturn(tool);
        when(mcpServerCacheService.getServerConfig()).thenReturn(serverConfig);

        // Act
        openApiMcpToolExecutor.execute(callRequest);

        // Assert
        verify(restApiExecutionService).executeRequest(urlCaptor.capture(), anyString(), any(), any());
        String expectedUrl = "https://api.example.com/files/my%20documents%2Fwork?searchTerm=a%26b%3Dc";
        assertEquals(expectedUrl, urlCaptor.getValue());
    }
}