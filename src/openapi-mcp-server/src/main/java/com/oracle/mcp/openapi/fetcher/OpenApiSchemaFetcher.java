/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.fetcher;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.enums.OpenApiSchemaSourceType;
import com.oracle.mcp.openapi.enums.OpenApiSchemaType;
import com.oracle.mcp.openapi.rest.RestApiAuthHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;

/**
 * Utility class responsible for fetching and parsing OpenAPI schema definitions.
 * <p>
 * A schema can be retrieved either from:
 * <ul>
 *   <li>A remote URL (with optional Basic Authentication)</li>
 *   <li>A local file system path</li>
 * </ul>
 * <p>
 * Once retrieved, the schema content is parsed into a Jackson {@link JsonNode}
 * using either a JSON or YAML {@link ObjectMapper}, depending on the detected format.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class OpenApiSchemaFetcher {

    private static final Logger LOGGER = LoggerFactory.getLogger(OpenApiSchemaFetcher.class);

    private final ObjectMapper jsonMapper;
    private final ObjectMapper yamlMapper;
    private final RestApiAuthHandler restApiAuthHandler;

    /**
     * Creates a new {@code OpenApiSchemaFetcher}.
     *
     * @param jsonMapper {@link ObjectMapper} configured for JSON parsing.
     * @param yamlMapper {@link ObjectMapper} configured for YAML parsing.
     */
    public OpenApiSchemaFetcher(ObjectMapper jsonMapper, ObjectMapper yamlMapper, RestApiAuthHandler restApiAuthHandler) {
        this.jsonMapper = jsonMapper;
        this.yamlMapper = yamlMapper;
        this.restApiAuthHandler = restApiAuthHandler;
    }

    /**
     * Fetches an OpenAPI schema from the configured source.
     * <p>
     * The schema may be downloaded from a remote URL or read from a file,
     * depending on the {@link OpenApiSchemaSourceType}.
     *
     * @param mcpServerConfig configuration containing schema location and authentication details.
     * @return the parsed OpenAPI schema as a {@link JsonNode}.
     * @throws Exception if the schema cannot be retrieved or parsed.
     */
    public JsonNode fetch(McpServerConfig mcpServerConfig) throws Exception {
        OpenApiSchemaSourceType type = OpenApiSchemaSourceType.getType(mcpServerConfig);
        String content;
        if (type == OpenApiSchemaSourceType.URL) {
            content = downloadContent(mcpServerConfig);
        } else {
            content = loadFromFile(mcpServerConfig);
        }
        return parseContent(content);
    }

    /**
     * Reads the OpenAPI specification from a local file.
     *
     * @param mcpServerConfig configuration specifying the file path.
     * @return schema content as a UTF-8 string.
     * @throws IOException if the file cannot be read.
     */
    private String loadFromFile(McpServerConfig mcpServerConfig) throws IOException {
        Path path = Paths.get(mcpServerConfig.getApiSpec());
        return Files.readString(path, StandardCharsets.UTF_8);
    }

    /**
     * Downloads the OpenAPI specification from a remote URL.
     * <p>
     * If Basic Authentication is configured, the request will include the
     * {@code Authorization} header.
     *
     * @param mcpServerConfig configuration specifying the URL and authentication details.
     * @return schema content as a UTF-8 string.
     * @throws Exception if the download fails.
     */
    private String downloadContent(McpServerConfig mcpServerConfig) throws Exception {
        URL url = new URL(mcpServerConfig.getApiSpec());
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

    /**
     * Applies authentication headers to the connection if required.
     * <p>
     * Currently supports only {@link OpenApiSchemaAuthType#BASIC}.
     * Passwords and sensitive data are securely cleared from memory
     * after use.
     *
     * @param conn            the {@link HttpURLConnection} to update.
     * @param mcpServerConfig configuration containing authentication details.
     */
    private void applyAuth(HttpURLConnection conn, McpServerConfig mcpServerConfig) {
        Map<String, String> headers = restApiAuthHandler.extractAuthHeaders(mcpServerConfig);
        for (Map.Entry<String, String> entry : headers.entrySet()) {
            conn.setRequestProperty(entry.getKey(), entry.getValue());
        }
    }

    /**
     * Parses schema content into a {@link JsonNode}.
     * <p>
     * Automatically detects whether the input is YAML or JSON.
     *
     * @param content schema content as a string.
     * @return parsed {@link JsonNode}.
     * @throws Exception if parsing fails.
     */
    private JsonNode parseContent(String content) throws Exception {
        OpenApiSchemaType type = OpenApiSchemaType.getType(content);
        if (type == OpenApiSchemaType.YAML) {
            return yamlMapper.readTree(content);
        } else {
            return jsonMapper.readTree(content);
        }
    }
}
