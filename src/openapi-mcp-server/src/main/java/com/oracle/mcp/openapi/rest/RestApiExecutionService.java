package com.oracle.mcp.openapi.rest;

import com.oracle.mcp.openapi.cache.McpServerCacheService;
import com.oracle.mcp.openapi.model.McpServerConfig;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.stream.Stream;

public class RestApiExecutionService {

    private final HttpClient httpClient;

    // HTTP Method constants
    public static final String GET = "GET";
    public static final String POST = "POST";
    public static final String PUT = "PUT";
    public static final String DELETE = "DELETE";
    public static final String PATCH = "PATCH";


    public RestApiExecutionService(McpServerCacheService mcpServerCacheService) {
        McpServerConfig mcpServerConfig = mcpServerCacheService.getServerConfig();
        this.httpClient = new HttpClientFactory().getClient(mcpServerConfig);
    }

    /**
     * Executes an HTTP request.
     *
     * @param targetUrl the URL to call
     * @param method    HTTP method (GET, POST, etc.)
     * @param body      Request body (only for POST, PUT, PATCH)
     * @param headers   Optional headers
     * @return the response as String
     * @throws IOException if an I/O error occurs
     * @throws InterruptedException if the operation is interrupted
     */
    public String executeRequest(String targetUrl, String method, String body, Map<String, String> headers)
            throws IOException, InterruptedException {

        HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                .uri(URI.create(targetUrl))
                .timeout(Duration.ofSeconds(30));

        // Add headers
        if (headers != null && !headers.isEmpty()) {
            requestBuilder.headers(headers.entrySet().stream()
                    .flatMap(e -> Stream.of(e.getKey(), e.getValue()))
                    .toArray(String[]::new));
        }

        // Attach body only for methods that support it
        if (body != null && !body.isEmpty() &&
                (POST.equalsIgnoreCase(method) || PUT.equalsIgnoreCase(method) || PATCH.equalsIgnoreCase(method))) {
            requestBuilder.method(method, HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8));
        } else {
            requestBuilder.method(method, HttpRequest.BodyPublishers.noBody());
        }

        HttpRequest request = requestBuilder.build();
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

        return response.body();
    }

    public String get(String url, Map<String, String> headers) throws IOException, InterruptedException {
        return executeRequest(url, GET, null, headers);
    }

    public String post(String url, String body, Map<String, String> headers) throws IOException, InterruptedException {
        return executeRequest(url, POST, body, headers);
    }

    public String put(String url, String body, Map<String, String> headers) throws IOException, InterruptedException {
        return executeRequest(url, PUT, body, headers);
    }

    public String delete(String url, Map<String, String> headers) throws IOException, InterruptedException {
        return executeRequest(url, DELETE, null, headers);
    }

    public String patch(String url, String body, Map<String, String> headers) throws IOException, InterruptedException {
        return executeRequest(url, PATCH, body, headers);
    }
}
