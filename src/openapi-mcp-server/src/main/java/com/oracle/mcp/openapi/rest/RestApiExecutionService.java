/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
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

/**
 * Service for executing REST API requests using Java's {@link HttpClient}.
 * <p>
 * This class provides a generic request execution method
 * ({@link #executeRequest(String, String, String, Map)})
 * and convenience methods for common HTTP verbs (e.g., {@link #get(String, Map)}).
 * <p>
 * The HTTP client is lazily initialized using configuration stored in
 * {@link McpServerCacheService} via {@link McpServerConfig}.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class RestApiExecutionService {

    /**
     * Lazily initialized {@link HttpClient} instance.
     */
    private HttpClient httpClient;

    /**
     * Service providing cached server configuration details used to
     * initialize the {@link HttpClient}.
     */
    private final McpServerCacheService mcpServerCacheService;

    /** Constant for HTTP GET method. */
    public static final String GET = "GET";
    /** Constant for HTTP POST method. */
    public static final String POST = "POST";
    /** Constant for HTTP PUT method. */
    public static final String PUT = "PUT";
    /** Constant for HTTP PATCH method. */
    public static final String PATCH = "PATCH";

    /**
     * Constructs a new {@code RestApiExecutionService}.
     *
     * @param mcpServerCacheService cache service providing server configuration
     */
    public RestApiExecutionService(McpServerCacheService mcpServerCacheService) {
        this.mcpServerCacheService = mcpServerCacheService;
    }

    /**
     * Returns a configured {@link HttpClient} instance.
     * <p>
     * If the client has already been initialized, it is returned directly.
     * Otherwise, a new client is created using the cached {@link McpServerConfig}.
     *
     * @return an {@link HttpClient} ready for use
     */
    private HttpClient getHttpClient() {
        if (this.httpClient != null) {
            return this.httpClient;
        }
        McpServerConfig mcpServerConfig = mcpServerCacheService.getServerConfig();
        return new HttpClientManager().getClient(mcpServerConfig);
    }

    /**
     * Executes an HTTP request using the given URL, method, optional request body, and headers.
     * <p>
     * This method supports all standard HTTP methods. For {@code GET} and {@code DELETE},
     * the request body is ignored. For {@code POST}, {@code PUT}, and {@code PATCH}, the
     * body is included in the request if provided.
     * </p>
     *
     * @param targetUrl the absolute URL to send the request to (must be a valid URI)
     * @param method    the HTTP method (e.g., GET, POST, PUT, PATCH, DELETE)
     * @param body      the request body content; only used for POST, PUT, or PATCH requests;
     *                  ignored for other methods; may be {@code null} or empty
     * @param headers   optional request headers; may be {@code null} or empty; headers with
     *                  {@code null} values are skipped
     * @return the HTTP response containing status, headers, and body as a {@link String}
     * @throws IOException          if an I/O error occurs while sending or receiving the request
     * @throws InterruptedException if the operation is interrupted while waiting for a response
     */
    public HttpResponse<String> executeRequest(String targetUrl, String method, String body, Map<String, String> headers)
            throws IOException, InterruptedException {

        HttpRequest.Builder requestBuilder = HttpRequest.newBuilder()
                .uri(URI.create(targetUrl))
                .version(HttpClient.Version.HTTP_1_1) // force HTTP/1.1
                .timeout(Duration.ofSeconds(30));

        // Add headers
        if (headers != null && !headers.isEmpty()) {
            for (Map.Entry<String, String> entry : headers.entrySet()) {
                if (entry.getValue() != null) {
                    requestBuilder.header(entry.getKey(), entry.getValue());
                }
            }
        }

        // Attach body only for methods that support it
        if (body != null && !body.isEmpty() &&
                (POST.equalsIgnoreCase(method) || PUT.equalsIgnoreCase(method) || PATCH.equalsIgnoreCase(method))) {
            requestBuilder.method(method, HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8));
        } else {
            requestBuilder.method(method, HttpRequest.BodyPublishers.noBody());
        }

        HttpRequest request = requestBuilder.build();
        HttpResponse<String> response =
                getHttpClient().send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));

        return response;
    }

    /**
     * Executes a simple HTTP GET request.
     *
     * @param url     the target URL
     * @param headers optional request headers; may be {@code null} or empty
     * @return the response body as a {@link String}
     * @throws IOException          if an I/O error occurs while sending or receiving
     * @throws InterruptedException if the operation is interrupted while waiting
     */
    public String get(String url, Map<String, String> headers) throws IOException, InterruptedException {
        return executeRequest(url, GET, null, headers).body();
    }
}
