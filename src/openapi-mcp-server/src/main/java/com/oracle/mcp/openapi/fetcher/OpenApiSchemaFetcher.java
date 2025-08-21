package com.oracle.mcp.openapi.fetcher;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.enums.OpenApiSchemaSourceType;
import com.oracle.mcp.openapi.enums.OpenApiSchemaType;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

public class OpenApiSchemaFetcher {

    private final HttpClient httpClient ;
    private final ObjectMapper jsonMapper ;
    private final ObjectMapper yamlMapper;

    public OpenApiSchemaFetcher(HttpClient httpClient, ObjectMapper jsonMapper, ObjectMapper yamlMapper){
        this.httpClient = httpClient;
        this.jsonMapper = jsonMapper;
        this.yamlMapper = yamlMapper;
    }

    public JsonNode fetch(McpServerConfig mcpServerConfig) throws Exception {
        OpenApiSchemaSourceType type = OpenApiSchemaSourceType.getType(mcpServerConfig);
        String content = null;
        if(type == OpenApiSchemaSourceType.URL){
            content = downloadContent(mcpServerConfig);
        }else{
            //TODO File
        }

        return parseContent(content);
    }

    private String downloadContent(McpServerConfig mcpServerConfig) throws Exception {
        URL url = new URL(mcpServerConfig.getSpecUrl());
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setConnectTimeout(10_000);
        conn.setReadTimeout(10_000);
        conn.setRequestMethod("GET");

        applyAuth(conn, mcpServerConfig);

        try (InputStream in = conn.getInputStream()) {
            byte[] bytes = in.readAllBytes();
            return new String(bytes, StandardCharsets.UTF_8);
        }
    }

    private void applyAuth(HttpURLConnection conn, McpServerConfig mcpServerConfig) {
        OpenApiSchemaAuthType authType = mcpServerConfig.getAuthType();
        if (authType == OpenApiSchemaAuthType.BASIC) {
            String encoded = Base64.getEncoder().encodeToString(
                    (mcpServerConfig.getAuthUsername() + ":" + mcpServerConfig.getAuthPassword())
                            .getBytes(StandardCharsets.UTF_8)
            );
            conn.setRequestProperty("Authorization", "Basic " + encoded);
        }
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
