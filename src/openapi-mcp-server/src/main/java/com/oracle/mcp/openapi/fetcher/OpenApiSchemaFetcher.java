package com.oracle.mcp.openapi.fetcher;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.mcp.openapi.enums.OpenApiSchemaAuthType;
import com.oracle.mcp.openapi.model.McpServerConfig;
import com.oracle.mcp.openapi.enums.OpenApiSchemaSourceType;
import com.oracle.mcp.openapi.enums.OpenApiSchemaType;
import com.oracle.mcp.openapi.rest.RestApiExecutionService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Base64;

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

    private void applyAuth(HttpURLConnection conn, McpServerConfig mcpServerConfig) {
        OpenApiSchemaAuthType authType = mcpServerConfig.getAuthType();
        if (authType != OpenApiSchemaAuthType.BASIC) {
            return;
        }

        String username = mcpServerConfig.getAuthUsername();
        char[] passwordChars = mcpServerConfig.getAuthPassword();

        if (username == null || passwordChars == null) {
            System.err.println("Username or password is not configured for Basic Auth.");
            return;
        }

        // This will hold the "username:password" bytes
        byte[] credentialsBytes = null;
        // This will hold a temporary copy of the password as bytes
        byte[] passwordBytes = null;

        try {
            // 2. Convert username to bytes.
            byte[] usernameBytes = username.getBytes(StandardCharsets.UTF_8);
            byte[] separator = {':'};

            // Convert password char[] to byte[] for encoding.
            ByteBuffer passwordByteBuffer = StandardCharsets.UTF_8.encode(CharBuffer.wrap(passwordChars));
            passwordBytes = new byte[passwordByteBuffer.remaining()];
            passwordByteBuffer.get(passwordBytes);

            // 3. Combine them all in a byte array, avoiding intermediate Strings.
            credentialsBytes = new byte[usernameBytes.length + separator.length + passwordBytes.length];
            System.arraycopy(usernameBytes, 0, credentialsBytes, 0, usernameBytes.length);
            System.arraycopy(separator, 0, credentialsBytes, usernameBytes.length, separator.length);
            System.arraycopy(passwordBytes, 0, credentialsBytes, usernameBytes.length + separator.length, passwordBytes.length);

            // 4. Base64 encode the combined bytes and set the header.
            String encoded = Base64.getEncoder().encodeToString(credentialsBytes);
            conn.setRequestProperty("Authorization", "Basic " + encoded);

        } finally {
            // 5. IMPORTANT: Clear all sensitive arrays from memory.
            Arrays.fill(passwordChars, '0');
            if (passwordBytes != null) {
                Arrays.fill(passwordBytes, (byte) 0);
            }
            if (credentialsBytes != null) {
                Arrays.fill(credentialsBytes, (byte) 0);
            }
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
