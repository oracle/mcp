package com.oracle.mcp.openapi.fetcher;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.exception.OpenApiException;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.enums.OpenApiSchemaSourceType;
import com.oracle.mcp.openapi.enums.OpenApiSchemaType;
import com.oracle.mcp.openapi.rest.RestApiExecutionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

public class OpenApiSchemaFetcher {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiSchemaFetcher.class);


    private final ObjectMapper jsonMapper ;
    private final ObjectMapper yamlMapper;
    private final RestApiExecutionService restApiExecutionService;

    public OpenApiSchemaFetcher(RestApiExecutionService restApiExecutionService, ObjectMapper jsonMapper, ObjectMapper yamlMapper){
        this.restApiExecutionService = restApiExecutionService;
        this.jsonMapper = jsonMapper;
        this.yamlMapper = yamlMapper;
    }

    public JsonNode fetch(McpServerConfig mcpServerConfig) throws Exception {
        OpenApiSchemaSourceType type = OpenApiSchemaSourceType.getType(mcpServerConfig);
        String content = null;
        if(type == OpenApiSchemaSourceType.URL){
            content = downloadContent(mcpServerConfig);
        }else{
            content = loadFromFile(mcpServerConfig);
        }

        return parseContent(content);
    }

    private String loadFromFile(McpServerConfig mcpServerConfig) throws IOException {
        Path path = Paths.get(mcpServerConfig.getApiSpec());
        return Files.readString(path, StandardCharsets.UTF_8);
    }

    private String downloadContent(McpServerConfig mcpServerConfig) throws OpenApiException {
        try {
            String url = mcpServerConfig.getSpecUrl();

            // You can also build headers here via applyAuth if you prefer
            Map<String, String> headers = applyAuth(mcpServerConfig);

            return restApiExecutionService.get(url, headers);

        } catch (IOException | InterruptedException e) {
            String errorMessage = "Failed to download OpenAPI schema.";
            LOGGER.error(errorMessage, e);
            throw new OpenApiException(errorMessage, e);
        }
    }


    private Map<String, String> applyAuth(McpServerConfig mcpServerConfig) {
        Map<String, String> headers = new HashMap<>();
        OpenApiSchemaAuthType authType = mcpServerConfig.getAuthType();
        if (authType == null || authType == OpenApiSchemaAuthType.NONE) {
            return headers;
        }

        switch (authType) {
            case BASIC -> {
                String encoded = Base64.getEncoder().encodeToString(
                        (mcpServerConfig.getAuthUsername() + ":" + mcpServerConfig.getAuthPassword())
                                .getBytes(StandardCharsets.UTF_8)
                );
                headers.put("Authorization", "Basic " + encoded);
            }

            case BEARER -> {
                headers.put("Authorization", "Bearer " + mcpServerConfig.getAuthToken());
            }
            default -> {
                // NONE or unrecognized
            }
        }
        return headers;
    }


    private JsonNode parseContent(String content) throws Exception {
        OpenApiSchemaType type = OpenApiSchemaType.getType(content);
        if (type == OpenApiSchemaType.YAML) {
            return yamlMapper.readTree(content);
        } else {
            return jsonMapper.readTree(content);
        }
    }

}
