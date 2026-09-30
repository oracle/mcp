/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit;

/**
 * Provides a set of constants loaded from system properties and environment variables.
 * These constants are used to configure various aspects of the application, including
 * network settings, tool configurations, OAuth settings, and more.
 *
 * <p>This class is not intended to be instantiated and provides only static constants.
 */
public final class LoadedConstants {
  private LoadedConstants() {} // Prevent instantiation

  /** Network config */
  public static final String TRANSPORT_KIND = System.getProperty("transport", "stdio")
    .trim()
    .toLowerCase();
  public static final String HTTPS_PORT = System.getProperty("https.port");
  public static final String KEYSTORE_PATH = System.getProperty("certificatePath");
  public static final String KEYSTORE_PASSWORD = System.getProperty("certificatePassword");
  public static final String HTTP_ALLOWED_ORIGINAL_HOSTS = System.getProperty("http.allowedOriginalHosts");
  public static final boolean HTTP_ALLOW_UNAUTHENTICATED_FOR_DEVELOPMENT = Boolean.parseBoolean(
    System.getProperty("http.allowUnauthenticatedForDevelopment", "false"));

  /** Tools config */
  public static final String TOOLS = System.getProperty("tools");
  public static final String INGEST_ROOT_DIR = System.getProperty("ingestRootDir");
  public static final String INGEST_MAX_FILE_SIZE_MB = System.getProperty("ingestMaxFileSizeMb");
  public static final String DB_URL = System.getProperty("db.url");
  public static final String DB_USER = System.getProperty("db.user");
  public static final char[] DB_PASSWORD = System.getProperty("db.password") != null
    ? System.getProperty("db.password").toCharArray()
    : null;
  public static final int DB_TRANSACTION_IDLE_TIMEOUT_SECONDS =
    Integer.parseInt(System.getProperty("db.transactionIdleTimeoutSeconds", "120"));
  public static final int DB_TRANSACTION_MAX_LIFETIME_SECONDS =
    Integer.parseInt(System.getProperty("db.transactionMaxLifetimeSeconds", "300"));
  public static final int DB_MAX_TRANSACTIONS_PER_USER =
    Integer.parseInt(System.getProperty("db.maxTransactionsPerUser", "4"));

  /** OAuth config */
  public static final String ALLOWED_HOSTS= System.getProperty("allowedHosts","*");
  public static final String AUTH_OPENID_DISCOVERY_REDIRECT_ENABLED =
    System.getProperty("auth.openIdDiscoveryRedirectEnabled", "false");
  public static final boolean AUTH_ENABLED = Boolean.parseBoolean(System.getProperty("auth.enabled", "false"));
  public static final String ORACLE_DB_TOOLKIT_AUTH_TOKEN = System.getenv("ORACLE_DB_TOOLKIT_AUTH_TOKEN");
  public static final String AUTH_AUTHORIZATION_SERVER = System.getProperty("auth.authorizationServer");
  public static final String USER_TOKEN_INTROSPECTION_ENDPOINT =
    System.getProperty("auth.userTokenValidation.introspection.endpoint");
  public static final String USER_TOKEN_INTROSPECTION_CLIENT_ID =
    System.getProperty("auth.userTokenValidation.introspection.clientId");
  public static final String USER_TOKEN_INTROSPECTION_CLIENT_SECRET =
    System.getProperty("auth.userTokenValidation.introspection.clientSecret");
  public static final String OAUTH_SCOPE_CLAIM_PATH = System.getProperty("oauth.scopeClaimPath", "scope");
  public static final boolean EDIT_TOOLS_REQUIRE_SCOPE = Boolean.parseBoolean(
    System.getProperty("editTools.requireScope", "true"));
  public static final boolean LIST_CREDENTIALS_REQUIRE_SCOPE = Boolean.parseBoolean(
    System.getProperty("listCredentials.requireScope", "true"));
  public static final String USER_TOKEN_VALIDATION_MODE =
    System.getProperty("auth.userTokenValidation.mode", "introspection")
      .trim()
      .toLowerCase();
  public static final String USER_TOKEN_JWT_ISSUER =
    System.getProperty("auth.userTokenValidation.jwt.issuer");
  public static final String USER_TOKEN_JWT_JWKS_URI =
    System.getProperty("auth.userTokenValidation.jwt.jwksUri");
  public static final String USER_TOKEN_JWT_AUDIENCE =
    System.getProperty("auth.userTokenValidation.jwt.audience");
  public static final long USER_TOKEN_JWT_JWKS_CACHE_SECONDS = Long.parseLong(
    System.getProperty("auth.userTokenValidation.jwt.jwksCacheSeconds", "600"));

  /** MCP OAuth discovery config */
  public static final String MCP_OAUTH_SCOPES = System.getProperty("mcp.oauth.scopes", "openid");
  public static final String MCP_OAUTH_RESOURCE_URL = System.getProperty("mcp.oauth.resourceUrl");

  /** Deep Data Security config */
  public static final boolean DEEPSEC_ENABLED = Boolean.parseBoolean(System.getProperty("deepsec.enabled", "false"));
  public static final String DEEPSEC_DATABASE_TOKEN_STATIC_VALUE =
    System.getProperty("deepsec.databaseToken.staticValue");
  public static final String DEEPSEC_DATABASE_TOKEN_ENDPOINT =
    System.getProperty("deepsec.databaseToken.tokenEndpoint");
  public static final String DEEPSEC_DATABASE_TOKEN_CLIENT_ID =
    System.getProperty("deepsec.databaseToken.clientId");
  public static final String DEEPSEC_DATABASE_TOKEN_CLIENT_SECRET =
    System.getProperty("deepsec.databaseToken.clientSecret");
  public static final String DEEPSEC_DATABASE_TOKEN_SCOPE =
    System.getProperty("deepsec.databaseToken.scope");

  /** Yaml config */
  public static final String CONFIG_FILE = System.getProperty("configFile");

  /** External extensions */
  public static final String OJDBC_EXT_DIR = System.getProperty("ojdbc.ext.dir");

}
