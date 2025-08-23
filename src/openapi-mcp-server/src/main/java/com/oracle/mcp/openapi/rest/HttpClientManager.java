package com.oracle.mcp.openapi.rest;

import com.oracle.mcp.openapi.model.McpServerConfig;

import java.net.InetSocketAddress;
import java.net.ProxySelector;
import java.net.http.HttpClient;
import java.time.Duration;

public class HttpClientManager {


    public HttpClientManager() {

    }

    public HttpClient getClient(McpServerConfig config) {
        HttpClient.Builder builder = HttpClient.newBuilder();

        if (config.getConnectTimeout() != null) {
            builder.connectTimeout(Duration.ofMillis(config.getConnectTimeoutMs()));
        }


        if (config.getHttpVersion() != null) {
            if (config.getHttpVersion().equalsIgnoreCase("HTTP_2")) {
                builder.version(HttpClient.Version.HTTP_2);
            } else {
                builder.version(HttpClient.Version.HTTP_1_1);
            }
        }

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
