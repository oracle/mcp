/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.oauth;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.jwk.source.DefaultJWKSetCache;
import com.nimbusds.jose.jwk.source.RemoteJWKSet;
import com.nimbusds.jose.proc.BadJOSEException;
import com.nimbusds.jose.proc.JWSVerificationKeySelector;
import com.nimbusds.jose.proc.SecurityContext;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.proc.DefaultJWTClaimsVerifier;
import com.nimbusds.jwt.proc.DefaultJWTProcessor;
import com.oracle.database.mcptoolkit.LoadedConstants;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.net.URI;
import java.net.URL;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.text.ParseException;
import java.util.Base64;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

import static java.nio.charset.StandardCharsets.UTF_8;

/**
 * The OAuth2TokenValidator class is responsible for validating OAuth2 access tokens.
 * It checks if the provided access token is valid by either using a local TokenGenerator
 * if OAuth2 is not configured, validating a JWT against the authorization server's JWKS,
 * or performing token introspection against an OAuth2 authorization server.
 * <p>
 * This class relies on the OAuth2Configuration singleton to retrieve necessary settings
 * such as the introspection endpoint, client credentials, and configuration flags.
 * </p>
 */
public class OAuth2TokenValidator {
  private static final OAuth2Configuration OAUTH_CONFIG = OAuth2Configuration.getInstance();
  private static final Logger LOG = Logger.getLogger(OAuth2TokenValidator.class.getName());
  private static final ObjectMapper MAPPER = new ObjectMapper();
  private static volatile JwtProcessorCache jwtProcessorCache;

  /**
   * Validates the given access token.
   * <p>
   * JWT validation uses only the configured issuer, JWKS URI, and audience. Introspection
   * requires the OAuth2 client configuration; when that configuration is absent, this method
   * delegates to the local TokenGenerator for backward compatibility.
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

  /** Validates a token and returns its introspected scopes when available. */
  public ValidationResult validateToken(final String accessToken) {
    if (accessToken == null || accessToken.isBlank())
      return new ValidationResult(false, Set.of());

    if ("jwt".equals(LoadedConstants.USER_TOKEN_VALIDATION_MODE))
      return new ValidationResult(isJwtTokenValid(accessToken), Set.of());

    if (!"introspection".equals(LoadedConstants.USER_TOKEN_VALIDATION_MODE)) {
      LOG.log(Level.WARNING, () -> "Unsupported auth.userTokenValidation.mode: "
        + LoadedConstants.USER_TOKEN_VALIDATION_MODE);
      return new ValidationResult(false, Set.of());
    }

    if (!OAUTH_CONFIG.isOAuth2Configured())
      return new ValidationResult(TokenGenerator.getInstance().verifyToken(accessToken), Set.of());

    return isTokenValidByIntrospection(accessToken);
  }

  private ValidationResult isTokenValidByIntrospection(final String accessToken) {
    boolean isTokenValid = false;
    Set<String> scopes = Set.of();
    final var clientCredentials = "%s:%s".formatted(OAUTH_CONFIG.getClientId(), OAUTH_CONFIG.getClientSecret());
    final var encodedClientCredentials = Base64.getEncoder()
      .encodeToString(clientCredentials.getBytes());
    final var requestBody = "token=" + URLEncoder.encode(accessToken, UTF_8);

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
        final var jsonNode = MAPPER.readTree(response.body());

        JsonNode active = jsonNode.get("active");
        isTokenValid = active != null && active.asBoolean();
        if (isTokenValid) {
          scopes = extractScopes(jsonNode, LoadedConstants.OAUTH_SCOPE_CLAIM_PATH);
        }
        if (!isTokenValid) {
          LOG.log(Level.WARNING, () -> "OAuth2 token introspection returned inactive token: " + response.body());
        }
      } else {
        LOG.log(Level.WARNING, () -> "OAuth2 token introspection failed with HTTP "
          + statusCode + ": " + response.body());
      }
    } catch (IOException | InterruptedException e) {
      LOG.log(Level.SEVERE, e.getMessage(), e);

      if (e instanceof InterruptedException)
        Thread.currentThread()
          .interrupt();
    }

    return new ValidationResult(isTokenValid, scopes);
  }

  private boolean isJwtTokenValid(final String accessToken) {
    try {
      requireJwtConfig();
      jwtProcessor().process(accessToken, null);
      return true;
    } catch (IOException | ParseException | BadJOSEException | com.nimbusds.jose.JOSEException
             | IllegalArgumentException e) {
      LOG.log(Level.WARNING, "JWT validation failed: " + e.getMessage(), e);
      return false;
    }
  }

  static Set<String> extractScopes(JsonNode introspectionResponse, String claimPath) {
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
        + claimPath + "'. Configure -Doauth.scopeClaimPath=<claim.path> if your authorization "
        + "server uses a different claim.");
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
    LOG.warning("OAuth scope claim at '" + claimPath + "' must be a space-delimited string or an "
      + "array. Configure -Doauth.scopeClaimPath=<claim.path> if needed.");
    return Set.of();
  }

  /** Result of token validation and any OAuth scopes obtained from introspection. */
  public record ValidationResult(boolean valid, Set<String> scopes) {}

  private void requireJwtConfig() {
    if (isBlank(LoadedConstants.USER_TOKEN_JWT_ISSUER))
      throw new IllegalArgumentException("auth.userTokenValidation.jwt.issuer is required for JWT validation");
    if (isBlank(LoadedConstants.USER_TOKEN_JWT_JWKS_URI))
      throw new IllegalArgumentException("auth.userTokenValidation.jwt.jwksUri is required for JWT validation");
    if (isBlank(LoadedConstants.USER_TOKEN_JWT_AUDIENCE))
      throw new IllegalArgumentException("auth.userTokenValidation.jwt.audience is required for JWT validation");
  }

  private DefaultJWTProcessor<SecurityContext> jwtProcessor() throws IOException {
    JwtProcessorCache cache = jwtProcessorCache;
    if (cache != null && cache.matchesCurrentConfiguration()) {
      return cache.processor();
    }

    synchronized (OAuth2TokenValidator.class) {
      cache = jwtProcessorCache;
      if (cache != null && cache.matchesCurrentConfiguration()) {
        return cache.processor();
      }

      long cacheSeconds = Math.max(LoadedConstants.USER_TOKEN_JWT_JWKS_CACHE_SECONDS, 1);
      RemoteJWKSet<SecurityContext> jwkSource = new RemoteJWKSet<>(
        new URL(LoadedConstants.USER_TOKEN_JWT_JWKS_URI),
        null,
        new DefaultJWKSetCache(cacheSeconds, cacheSeconds, TimeUnit.SECONDS));
      DefaultJWTProcessor<SecurityContext> processor = new DefaultJWTProcessor<>();
      processor.setJWSKeySelector(new JWSVerificationKeySelector<>(JWSAlgorithm.RS256, jwkSource));

      DefaultJWTClaimsVerifier<SecurityContext> claimsVerifier = new DefaultJWTClaimsVerifier<>(
        Set.of(LoadedConstants.USER_TOKEN_JWT_AUDIENCE),
        new JWTClaimsSet.Builder().issuer(LoadedConstants.USER_TOKEN_JWT_ISSUER).build(),
        Set.of("iss", "aud", "exp"),
        Set.of());
      claimsVerifier.setMaxClockSkew(0);
      processor.setJWTClaimsSetVerifier(claimsVerifier);
      jwtProcessorCache = new JwtProcessorCache(
        processor,
        LoadedConstants.USER_TOKEN_JWT_ISSUER,
        LoadedConstants.USER_TOKEN_JWT_JWKS_URI,
        LoadedConstants.USER_TOKEN_JWT_AUDIENCE,
        cacheSeconds);
      return processor;
    }
  }

  private boolean isBlank(String value) {
    return value == null || value.isBlank();
  }

  private record JwtProcessorCache(
    DefaultJWTProcessor<SecurityContext> processor,
    String issuer,
    String jwksUri,
    String audience,
    long cacheSeconds) {
    private boolean matchesCurrentConfiguration() {
      return issuer.equals(LoadedConstants.USER_TOKEN_JWT_ISSUER)
        && jwksUri.equals(LoadedConstants.USER_TOKEN_JWT_JWKS_URI)
        && audience.equals(LoadedConstants.USER_TOKEN_JWT_AUDIENCE)
        && cacheSeconds == Math.max(LoadedConstants.USER_TOKEN_JWT_JWKS_CACHE_SECONDS, 1);
    }
  }
}
