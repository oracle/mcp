/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.oauth;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.util.Base64;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * The OAuth2TokenValidator class is responsible for validating OAuth2 access tokens.
 * It checks if the provided access token is valid by either using a local TokenGenerator
 * if OAuth2 is not configured, or by performing token introspection against an OAuth2
 * authorization server if OAuth2 is properly configured.
 * <p>
 * This class relies on the OAuth2Configuration singleton to retrieve necessary settings
 * such as the introspection endpoint, client credentials, and configuration flags.
 * </p>
 */
public class OAuth2TokenValidator {
  private static final OAuth2Configuration OAUTH_CONFIG = OAuth2Configuration.getInstance();
  private static final Logger LOG = Logger.getLogger(OAuth2TokenValidator.class.getName());

  /**
   * Validates the given access token.
   * <p>
   * If OAuth2 is not configured (as determined by OAuth2Configuration), this method
   * delegates validation to the TokenGenerator instance for local verification.
   * Otherwise, it performs an HTTP POST request to the OAuth2 introspection endpoint
   * using the configured client credentials. The response is parsed as JSON, and the
   * "active" field is checked to determine token validity.
   * </p>
   *
   * @param accessToken the OAuth2 access token to validate; must not be null or blank
   * @return true if the token is valid, false otherwise
   * @throws RuntimeException if an error occurs during token validation (e.g., network issues),
   *         though exceptions are logged and handled internally by returning false
   */
  public boolean isTokenValid(final String accessToken) {
    return validateToken(accessToken).valid();
  }

  public ValidationResult validateToken(final String accessToken) {
    if (!OAUTH_CONFIG.isOAuth2Configured())
      return new ValidationResult(TokenGenerator.getInstance().verifyToken(accessToken), Set.of());

    boolean isTokenValid = false;
    Set<String> scopes = Set.of();
    if (accessToken == null || accessToken.isBlank())
      return new ValidationResult(false, scopes);

    final var clientCredentials = "%s:%s".formatted(OAUTH_CONFIG.getClientId(), OAUTH_CONFIG.getClientSecret());
    final var encodedClientCredentials = Base64.getEncoder()
      .encodeToString(clientCredentials.getBytes());
    final var requestBody = "token=" + accessToken;

    try {
      final HttpClient client = HttpClient.newHttpClient();
      final HttpRequest request = HttpRequest.newBuilder()
        .uri(URI.create(OAUTH_CONFIG.getIntrospectionEndpoint()))
        .header("Authorization", "Basic " + encodedClientCredentials)
        .header("Content-Type", "application/x-www-form-urlencoded")
        .POST(HttpRequest.BodyPublishers.ofString(requestBody))
        .build();

      final HttpResponse<String> response = client.send(request, BodyHandlers.ofString());

      final int statusCode = response.statusCode();
      if (statusCode == HttpServletResponse.SC_OK) {
        final var mapper = new ObjectMapper();
        final var jsonNode = mapper.readTree(response.body());

        JsonNode active = jsonNode.get("active");
        isTokenValid = active != null && active.asBoolean();
        if (isTokenValid) {
          scopes = extractScopes(jsonNode);
        }
      }
    } catch (IOException | InterruptedException e) {
      LOG.log(Level.SEVERE, e.getMessage(), e);

      if (e instanceof InterruptedException)
        Thread.currentThread()
          .interrupt();
    }

    return new ValidationResult(isTokenValid, scopes);
  }

  private Set<String> extractScopes(JsonNode introspectionResponse) {
    String claimPath = OAUTH_CONFIG.getScopeClaimPath();
    if (claimPath == null || claimPath.isBlank()) {
      claimPath = "scope";
    }

    JsonNode scopeNode = introspectionResponse;
    for (String segment : claimPath.split("\\.")) {
      if (segment == null || segment.isBlank()) {
        continue;
      }
      scopeNode = scopeNode == null ? null : scopeNode.get(segment);
    }

    if (scopeNode == null || scopeNode.isMissingNode() || scopeNode.isNull()) {
      LOG.warning("OAuth token introspection response does not contain a scope claim at '"
          + claimPath + "'. Configure -Doauth.scopeClaimPath=<claim.path> if your authorization server uses a different claim.");
      return Set.of();
    }

    Set<String> scopes = new LinkedHashSet<>();
    if (scopeNode.isTextual()) {
      for (String scope : scopeNode.asText().split("\\s+")) {
        if (!scope.isBlank()) {
          scopes.add(scope);
        }
      }
      return scopes;
    }

    if (scopeNode.isArray()) {
      for (JsonNode item : scopeNode) {
        if (item != null && item.isTextual() && !item.asText().isBlank()) {
          scopes.add(item.asText());
        }
      }
      return scopes;
    }

    LOG.warning("OAuth scope claim at '" + claimPath + "' must be a space-delimited string or an array. Configure -Doauth.scopeClaimPath=<claim.path> if needed.");
    return Set.of();
  }

  public record ValidationResult(boolean valid, Set<String> scopes) {}

}
