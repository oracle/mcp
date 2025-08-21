package com.oracle.mcp.openapi.fetcher;

import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Map;

public class RestApiExecutionService {

    // HTTP Method constants (Java doesn't provide these by default)
    public static final String GET = "GET";
    public static final String POST = "POST";
    public static final String PUT = "PUT";
    public static final String DELETE = "DELETE";
    public static final String PATCH = "PATCH";

    /**
     * Executes an HTTP request.
     *
     * @param targetUrl the URL to call
     * @param method    HTTP method (GET, POST, etc.)
     * @param body      Request body (only for POST, PUT, PATCH)
     * @param headers   Optional headers
     * @return the response as String
     * @throws IOException if an I/O error occurs
     */
    public String executeRequest(String targetUrl, String method, String body, Map<String, String> headers) throws IOException {
        HttpURLConnection connection = null;
        try {
            // Create connection
            URL url = java.net.URI.create(targetUrl).toURL();
            connection = (HttpURLConnection) url.openConnection();
            connection.setRequestMethod(method);

            // Add headers
            if (headers != null) {
                for (Map.Entry<String, String> entry : headers.entrySet()) {
                    connection.setRequestProperty(entry.getKey(), entry.getValue());
                }
            }

            // If method supports a body, set Content-Type to application/json
            if (body != null && !body.isEmpty() &&
                    (POST.equalsIgnoreCase(method) || PUT.equalsIgnoreCase(method) || PATCH.equalsIgnoreCase(method))) {
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setDoOutput(true);
                try (DataOutputStream wr = new DataOutputStream(connection.getOutputStream())) {
                    wr.write(body.getBytes(StandardCharsets.UTF_8));
                }
            }

            // Read response (success or error)
            int responseCode = connection.getResponseCode();
            try (BufferedReader in = new BufferedReader(
                    new InputStreamReader(
                            responseCode >= 200 && responseCode < 300
                                    ? connection.getInputStream()
                                    : connection.getErrorStream()
                    ))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = in.readLine()) != null) {
                    response.append(line);
                }
                return response.toString();
            }
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    // --- Convenience methods ---
    public String get(String url, Map<String, String> headers) throws IOException {
        return executeRequest(url, GET, null, headers);
    }

    public String post(String url, String body, Map<String, String> headers) throws IOException {
        return executeRequest(url, POST, body, headers);
    }

    public String put(String url, String body, Map<String, String> headers) throws IOException {
        return executeRequest(url, PUT, body, headers);
    }

    public String delete(String url, Map<String, String> headers) throws IOException {
        return executeRequest(url, DELETE, null, headers);
    }

    public String patch(String url, String body, Map<String, String> headers) throws IOException {
        return executeRequest(url, PATCH, body, headers);
    }
}
