/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.oauth;

import com.oracle.database.mcptoolkit.LoadedConstants;

import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

/**
 * The OAuth2Configuration class is a singleton that manages OAuth2 authentication configuration settings.
 * It reads configuration values from system properties and provides access to them via getter methods.
 * <p>
 * This class also handles logging based on whether authentication, JWT validation, or OAuth2
 * introspection are configured. If neither remote validation mode is configured, it initializes
 * a TokenGenerator for local token generation.
 */
public class OAuth2Configuration {
  private static final Logger LOG = Logger.getLogger(OAuth2Configuration.class.getName());
  private static final OAuth2Configuration INSTANCE = new OAuth2Configuration();

  /** The OAuth2 authorization server URL. */
  private final String authServer;
  /** The OAuth2 token introspection endpoint URL. */
  private final String introspectionEndpoint;
  /** The OAuth2 client ID. */
  private final String clientId;
  /** The OAuth2 client secret. */
  private final String clientSecret;

  /** Flag indicating whether authentication is enabled. */
  private final boolean isAuthenticationEnabled;
  /** Flag indicating whether OAuth2 is fully configured. */
  private final boolean isOAuth2Configured;
  /** Flag indicating whether local JWT validation is fully configured. */
  private final boolean isJwtValidationConfigured;

  /**
   * Private constructor to initialize the singleton instance.
   * Reads system properties for authentication settings and OAuth2 configuration.
   * Logs warnings or info messages based on the configuration status. If neither JWT validation
   * nor OAuth2 introspection is configured, initializes a TokenGenerator for local token generation.
   */
  private OAuth2Configuration() {
    isAuthenticationEnabled = LoadedConstants.AUTH_ENABLED;
    authServer = LoadedConstants.AUTH_AUTHORIZATION_SERVER;
    introspectionEndpoint = LoadedConstants.USER_TOKEN_INTROSPECTION_ENDPOINT;
    clientId = LoadedConstants.USER_TOKEN_INTROSPECTION_CLIENT_ID;
    clientSecret = LoadedConstants.USER_TOKEN_INTROSPECTION_CLIENT_SECRET;
    isOAuth2Configured = authServer != null && introspectionEndpoint != null && clientId != null && clientSecret != null;
    isJwtValidationConfigured = "jwt".equals(LoadedConstants.USER_TOKEN_VALIDATION_MODE)
      && !isBlank(LoadedConstants.USER_TOKEN_JWT_ISSUER)
      && !isBlank(LoadedConstants.USER_TOKEN_JWT_JWKS_URI)
      && !isBlank(LoadedConstants.USER_TOKEN_JWT_AUDIENCE);

    if (!isAuthenticationEnabled)
      LOG.warning("Authentication is disabled");
    else {
      LOG.info("Authentication is enabled");

      if (isJwtValidationConfigured) {
        LOG.info("JWT validation is configured");
      } else if (isOAuth2Configured) {
        LOG.info("OAuth2 is configured");
      } else {
        LOG.warning("OAuth2 is not configured");
        if (authServer != null || introspectionEndpoint != null || clientId != null || clientSecret != null) {
          final var warningMessage = getMissingConfigurationWarningMessage();

          LOG.warning(warningMessage);
        }
        // Generate a local UUID string token or load it from ORACLE_DB_TOOLBOX_AUTH_TOKEN env var.
        TokenGenerator.getInstance();
      }
    }
  }

  private String getMissingConfigurationWarningMessage() {
    final List<String> warningMessages = new ArrayList<>();
    final var mainMessage = "The following OAuth system properties are not configured correctly: ";

    if (authServer == null)
      warningMessages.add("Authentication server URL (-Dauth.authorizationServer)");

    if (introspectionEndpoint == null)
      warningMessages.add("Introspection endpoint (-Dauth.userTokenValidation.introspection.endpoint)");

    if (clientId == null)
      warningMessages.add("Client ID (-Dauth.userTokenValidation.introspection.clientId)");

    if (clientSecret == null)
      warningMessages.add("Client secret (-Dauth.userTokenValidation.introspection.clientSecret)");

    return mainMessage + String.join(", ", warningMessages);
  }

  private static boolean isBlank(String value) {
    return value == null || value.isBlank();
  }

  /**
   * Returns the singleton instance of OAuth2Configuration.
   *
   * @return the singleton instance
   */
  public static OAuth2Configuration getInstance() {
    return INSTANCE;
  }

  /**
   * Returns the OAuth2 authorization server URL.
   *
   * @return the auth server URL
   */
  public String getAuthServer() {
    return authServer;
  }

  /**
   * Returns the OAuth2 client ID.
   *
   * @return the client ID
   */
  public String getClientId() {
    return clientId;
  }

  /**
   * Returns the OAuth2 client secret.
   *
   * @return the client secret
   */
  public String getClientSecret() {
    return clientSecret;
  }

  /**
   * Returns the OAuth2 token introspection endpoint URL.
   *
   * @return the introspection endpoint URL
   */
  public String getIntrospectionEndpoint() {
    return introspectionEndpoint;
  }

  /**
   * Checks if authentication is enabled.
   *
   * @return true if authentication is enabled, false otherwise
   */
  public boolean isAuthenticationEnabled() {
    return isAuthenticationEnabled;
  }

  /**
   * Checks if OAuth2 is fully configured.
   *
   * @return true if OAuth2 is configured, false otherwise
   */
  public boolean isOAuth2Configured() {
    return isOAuth2Configured;
  }

  /**
   * Checks whether an authorization server is configured for MCP discovery.
   *
   * @return true if an authorization server URL is configured
   */
  public boolean isAuthorizationServerConfigured() {
    return !isBlank(authServer);
  }
}
