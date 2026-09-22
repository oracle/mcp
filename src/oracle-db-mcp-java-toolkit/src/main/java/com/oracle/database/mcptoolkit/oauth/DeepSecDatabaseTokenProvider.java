/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.oauth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.mcptoolkit.LoadedConstants;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.OffsetDateTime;
import java.util.Base64;
import java.util.logging.Level;
import java.util.logging.Logger;

import static java.nio.charset.StandardCharsets.UTF_8;

/**
 * Fetches and caches database-scoped OAuth access tokens used in OJDBC Deep Data Security.
 */
public final class DeepSecDatabaseTokenProvider {
  private static final Logger LOG = Logger.getLogger(DeepSecDatabaseTokenProvider.class.getName());
  private static final long EXPIRY_SKEW_SECONDS = 60L;
  private static volatile AccessToken cachedToken;

  private DeepSecDatabaseTokenProvider() {}

  /**
   * Returns a usable database-scoped access token, obtaining and caching one when necessary.
   *
   * @return the configured static token or a client-credentials token for the database application
   * @throws IllegalStateException if token configuration is invalid or the token request fails
   */
  public static String getToken() {
    if (LoadedConstants.DEEPSEC_DATABASE_TOKEN_STATIC_VALUE != null
            && !LoadedConstants.DEEPSEC_DATABASE_TOKEN_STATIC_VALUE.isBlank()) {
      return LoadedConstants.DEEPSEC_DATABASE_TOKEN_STATIC_VALUE;
    }

    AccessToken token = cachedToken;
    if (isUsable(token)) {
      return token.value();
    }

    synchronized (DeepSecDatabaseTokenProvider.class) {
      token = cachedToken;
      if (isUsable(token)) {
        return token.value();
      }
      cachedToken = requestToken();
      return cachedToken.value();
    }
  }

  private static boolean isUsable(AccessToken token) {
    return token != null && token.expiresAt().isAfter(OffsetDateTime.now().plusSeconds(EXPIRY_SKEW_SECONDS));
  }

  private static AccessToken requestToken() {
    validateConfig();

    String credentials = LoadedConstants.DEEPSEC_DATABASE_TOKEN_CLIENT_ID + ":"
            + LoadedConstants.DEEPSEC_DATABASE_TOKEN_CLIENT_SECRET;
    String encodedCredentials = Base64.getEncoder().encodeToString(credentials.getBytes(UTF_8));
    String requestBody = "grant_type=client_credentials&scope="
            + URLEncoder.encode(LoadedConstants.DEEPSEC_DATABASE_TOKEN_SCOPE, UTF_8);

    try {
      HttpRequest request = HttpRequest.newBuilder()
              .uri(URI.create(LoadedConstants.DEEPSEC_DATABASE_TOKEN_ENDPOINT))
              .header("Authorization", "Basic " + encodedCredentials)
              .header("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
              .header("Accept", "application/json")
              .POST(HttpRequest.BodyPublishers.ofString(requestBody))
              .build();

      HttpResponse<String> response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
      if (response.statusCode() != HttpServletResponse.SC_OK) {
        throw new IllegalStateException("Database access token request failed with HTTP "
                + response.statusCode() + ": " + response.body());
      }

      var jsonNode = new ObjectMapper().readTree(response.body());
      String accessToken = jsonNode.get("access_token").asText();
      int expiresIn = jsonNode.has("expires_in") ? jsonNode.get("expires_in").asInt() : 3600;
      LOG.log(Level.FINE, "Fetched database access token for Deep Data Security");
      return new AccessToken(accessToken, OffsetDateTime.now().plusSeconds(expiresIn));
    } catch (IOException | InterruptedException e) {
      if (e instanceof InterruptedException) {
        Thread.currentThread().interrupt();
      }
      throw new IllegalStateException("Failed to request database access token", e);
    }
  }

  private static void validateConfig() {
    if (isBlank(LoadedConstants.DEEPSEC_DATABASE_TOKEN_ENDPOINT)) {
      throw new IllegalStateException(
              "Deep Data Security is enabled but neither deepsec.databaseToken.staticValue nor "
                      + "deepsec.databaseToken.tokenEndpoint is configured");
    }
    if (isBlank(LoadedConstants.DEEPSEC_DATABASE_TOKEN_CLIENT_ID)) {
      throw new IllegalStateException(
              "Deep Data Security token endpoint is configured but deepsec.databaseToken.clientId is missing");
    }
    if (isBlank(LoadedConstants.DEEPSEC_DATABASE_TOKEN_CLIENT_SECRET)) {
      throw new IllegalStateException(
              "Deep Data Security token endpoint is configured but deepsec.databaseToken.clientSecret is missing");
    }
    if (isBlank(LoadedConstants.DEEPSEC_DATABASE_TOKEN_SCOPE)) {
      throw new IllegalStateException(
              "Deep Data Security token endpoint is configured but deepsec.databaseToken.scope is missing");
    }
  }

  private static boolean isBlank(String value) {
    return value == null || value.isBlank();
  }

  private record AccessToken(String value, OffsetDateTime expiresAt) {}
}
