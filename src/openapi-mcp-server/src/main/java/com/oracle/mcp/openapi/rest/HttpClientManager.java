/*
 * --------------------------------------------------------------------------
 * Copyright (c) 2025, Oracle and/or its affiliates.
 * Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
 * --------------------------------------------------------------------------
 */
package com.oracle.mcp.openapi.rest;

import com.oracle.mcp.openapi.model.McpServerConfig;

import java.net.InetSocketAddress;
import java.net.ProxySelector;
import java.net.http.HttpClient;
import java.time.Duration;

/**
 * Utility class responsible for creating and configuring {@link HttpClient} instances
 * based on the properties defined in a {@link McpServerConfig}.
 * <p>
 * This class centralizes client configuration such as connection timeout, HTTP version,
 * redirect handling, and proxy settings, ensuring consistent HTTP client creation
 * across the application.
 *
 * @author Joby Wilson Mathews (joby.mathews@oracle.com)
 */
public class HttpClientManager {

    /**
     * Creates a new instance of {@code HttpClientManager}.
     * <p>
     * The constructor is empty since this class only provides factory-style behavior.
     */
    public HttpClientManager() {
    }

    /**
     * Builds and returns a configured {@link HttpClient} using the values provided
     * in the given {@link McpServerConfig}.
     * <p>
     * The configuration can include:
     * <ul>
     *   <li>Connection timeout (in milliseconds)</li>
     *   <li>HTTP version (HTTP/1.1 or HTTP/2)</li>
     *   <li>Redirect policy (NEVER, NORMAL, ALWAYS)</li>
     *   <li>Proxy host and port</li>
     * </ul>
     *
     * @param config the server configuration containing HTTP client settings
     * @return a configured {@link HttpClient} instance
     * @throws IllegalArgumentException if an unsupported redirect policy is provided
     */
    public HttpClient getClient(McpServerConfig config) {
        HttpClient.Builder builder = HttpClient.newBuilder();

        // Connection timeout
        if (config.getConnectTimeout() != null) {
            builder.connectTimeout(Duration.ofMillis(config.getConnectTimeoutMs()));
        }

        // HTTP version
        if (config.getHttpVersion() != null) {
            if (config.getHttpVersion().equalsIgnoreCase("HTTP_2")) {
                builder.version(HttpClient.Version.HTTP_2);
            } else {
                builder.version(HttpClient.Version.HTTP_1_1);
            }
        }

        // Redirect policy
        if (config.getRedirectPolicy() != null) {
            switch (config.getRedirectPolicy().toUpperCase()) {
                case "NEVER":
                    builder.followRedirects(HttpClient.Redirect.NEVER);
                    break;
                case "NORMAL":
                    builder.followRedirects(HttpClient.Redirect.NORMAL);
                    break;
                case "ALWAYS":
                    builder.followRedirects(HttpClient.Redirect.ALWAYS);
                    break;
                default:
                    throw new IllegalArgumentException("Unsupported redirect policy: " + config.getRedirectPolicy());
            }
        }

        if (config.getProxyHost() != null && config.getProxyPort() != null) {
            builder.proxy(ProxySelector.of(new InetSocketAddress(
                    config.getProxyHost(),
                    config.getProxyPort()
            )));
        }

        return builder.build();
    }
}
