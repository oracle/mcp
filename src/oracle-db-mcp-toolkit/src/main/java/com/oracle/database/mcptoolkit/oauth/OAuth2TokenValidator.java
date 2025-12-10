package com.oracle.database.mcptoolkit.oauth;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.util.Base64;
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
    if (!OAUTH_CONFIG.isOAuth2Configured())
      return TokenGenerator.getInstance().verifyToken(accessToken);

    boolean isTokenValid = false;
    if (accessToken == null || accessToken.isBlank())
      return false;

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

        isTokenValid = jsonNode.get("active").asBoolean();
      }
    } catch (IOException | InterruptedException e) {
      LOG.log(Level.SEVERE, e.getMessage(), e);

      if (e instanceof InterruptedException)
        Thread.currentThread()
          .interrupt();
    }

    return isTokenValid;
  }

}
