/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit;

import com.oracle.database.mcptoolkit.config.RuntimeConfigRoot;
import com.oracle.database.mcptoolkit.config.RuntimePropertyNames;
import java.util.LinkedHashMap;
import java.util.Map;

/** Provides runtime settings loaded from system properties and an optional YAML file. */
public final class LoadedConstants {
  private LoadedConstants() {}

  /** Identifies the existing YAML file for datasources and custom tools. */
  public static final String CONFIG_FILE = System.getProperty("configFile");
  /** Identifies the optional YAML file containing runtime settings. */
  public static final String RUNTIME_CONFIG_FILE = System.getProperty("runtimeConfigFile");

  /** Network config. */
  public static String TRANSPORT_KIND;
  public static String HTTPS_PORT;
  public static String KEYSTORE_PATH;
  public static String KEYSTORE_PASSWORD;
  public static String HTTP_ALLOWED_ORIGINAL_HOSTS;
  public static boolean HTTP_ALLOW_UNAUTHENTICATED_FOR_DEVELOPMENT;

  /** Tools and database config. */
  public static String TOOLS;
  public static String INGEST_ROOT_DIR;
  public static String INGEST_MAX_FILE_SIZE_MB;
  public static String DB_URL;
  public static String DB_USER;
  public static char[] DB_PASSWORD;
  public static int DB_TRANSACTION_IDLE_TIMEOUT_SECONDS;
  public static int DB_TRANSACTION_MAX_LIFETIME_SECONDS;
  public static int DB_MAX_TRANSACTIONS_PER_USER;

  /** User authentication and OAuth discovery config. */
  public static String CORS_ALLOWED_ORIGIN;
  public static String AUTH_OPENID_DISCOVERY_REDIRECT_ENABLED;
  public static boolean AUTH_ENABLED;
  public static final String ORACLE_DB_TOOLKIT_AUTH_TOKEN = System.getenv("ORACLE_DB_TOOLKIT_AUTH_TOKEN");
  public static String AUTH_AUTHORIZATION_SERVER;
  public static String USER_TOKEN_INTROSPECTION_ENDPOINT;
  public static String USER_TOKEN_INTROSPECTION_CLIENT_ID;
  public static String USER_TOKEN_INTROSPECTION_CLIENT_SECRET;
  public static String OAUTH_SCOPE_CLAIM_PATH;
  public static boolean EDIT_TOOLS_REQUIRE_SCOPE;
  public static boolean LIST_CREDENTIALS_REQUIRE_SCOPE;
  public static String USER_TOKEN_VALIDATION_MODE;
  public static String USER_TOKEN_JWT_ISSUER;
  public static String USER_TOKEN_JWT_JWKS_URI;
  public static String USER_TOKEN_JWT_AUDIENCE;
  public static long USER_TOKEN_JWT_JWKS_CACHE_SECONDS;

  /** MCP OAuth discovery config. */
  public static String MCP_OAUTH_SCOPES;
  public static String MCP_OAUTH_RESOURCE_URL;

  /** Deep Data Security config. */
  public static boolean DEEPSEC_ENABLED;
  public static String DEEPSEC_DATABASE_TOKEN_STATIC_VALUE;
  public static String DEEPSEC_DATABASE_TOKEN_ENDPOINT;
  public static String DEEPSEC_DATABASE_TOKEN_CLIENT_ID;
  public static String DEEPSEC_DATABASE_TOKEN_CLIENT_SECRET;
  public static String DEEPSEC_DATABASE_TOKEN_SCOPE;

  /** External extensions. */
  public static String OJDBC_EXT_DIR;

  static {
    initialize(null);
  }

  /**
   * Applies canonical runtime settings. A non-blank JVM system property always takes precedence.
   *
   * @param configRoot parsed runtime YAML root, or {@code null} when no YAML file was supplied
   */
  public static void initialize(RuntimeConfigRoot configRoot) {
    Map<String, String> yamlProperties = configRoot == null ? null : configRoot.properties();
    Map<String, String> systemProperties = canonicalSystemProperties();
    TRANSPORT_KIND = value("network.transport", yamlProperties, systemProperties, "stdio").trim().toLowerCase();
    HTTPS_PORT = value("network.https.port", yamlProperties, systemProperties, null);
    KEYSTORE_PATH = value("network.https.certificatePath", yamlProperties, systemProperties, null);
    KEYSTORE_PASSWORD = value("network.https.certificatePassword", yamlProperties, systemProperties, null);
    HTTP_ALLOWED_ORIGINAL_HOSTS = value("network.http.allowedOriginalHosts", yamlProperties, systemProperties, null);
    HTTP_ALLOW_UNAUTHENTICATED_FOR_DEVELOPMENT = bool(
        "network.http.allowUnauthenticatedForDevelopment", yamlProperties, systemProperties, false);
    TOOLS = value("toolSelection.enabled", yamlProperties, systemProperties, null);
    INGEST_ROOT_DIR = value("dataIngestion.rootDirectory", yamlProperties, systemProperties, null);
    INGEST_MAX_FILE_SIZE_MB = value("dataIngestion.maxFileSizeMb", yamlProperties, systemProperties, null);
    DB_URL = value("database.url", yamlProperties, systemProperties, null);
    DB_USER = value("database.user", yamlProperties, systemProperties, null);
    String dbPassword = value("database.password", yamlProperties, systemProperties, null);
    DB_PASSWORD = dbPassword == null ? null : dbPassword.toCharArray();
    DB_TRANSACTION_IDLE_TIMEOUT_SECONDS = integer("database.transactions.idleTimeoutSeconds", yamlProperties, systemProperties, 120);
    DB_TRANSACTION_MAX_LIFETIME_SECONDS = integer("database.transactions.maxLifetimeSeconds", yamlProperties, systemProperties, 300);
    DB_MAX_TRANSACTIONS_PER_USER = integer("database.transactions.maxPerUser", yamlProperties, systemProperties, 4);
    CORS_ALLOWED_ORIGIN = value("network.cors.allowedOrigin", yamlProperties, systemProperties, "*");
    AUTH_OPENID_DISCOVERY_REDIRECT_ENABLED = value("userAuth.openIdDiscoveryRedirectEnabled", yamlProperties, systemProperties, "false");
    AUTH_ENABLED = bool("userAuth.enabled", yamlProperties, systemProperties, false);
    AUTH_AUTHORIZATION_SERVER = value("userAuth.authorizationServer", yamlProperties, systemProperties, null);
    USER_TOKEN_INTROSPECTION_ENDPOINT = value("userAuth.tokenValidation.introspection.endpoint", yamlProperties, systemProperties, null);
    USER_TOKEN_INTROSPECTION_CLIENT_ID = value("userAuth.tokenValidation.introspection.clientId", yamlProperties, systemProperties, null);
    USER_TOKEN_INTROSPECTION_CLIENT_SECRET = value("userAuth.tokenValidation.introspection.clientSecret", yamlProperties, systemProperties, null);
    OAUTH_SCOPE_CLAIM_PATH = value("userAuth.tokenValidation.introspection.scopeClaimPath", yamlProperties, systemProperties, "scope");
    EDIT_TOOLS_REQUIRE_SCOPE = bool("toolAuthorization.editTools.requireScope", yamlProperties, systemProperties, true);
    LIST_CREDENTIALS_REQUIRE_SCOPE = bool("toolAuthorization.listCredentials.requireScope", yamlProperties, systemProperties, true);
    USER_TOKEN_VALIDATION_MODE = value("userAuth.tokenValidation.mode", yamlProperties, systemProperties, "introspection").trim().toLowerCase();
    USER_TOKEN_JWT_ISSUER = value("userAuth.tokenValidation.jwt.issuer", yamlProperties, systemProperties, null);
    USER_TOKEN_JWT_JWKS_URI = value("userAuth.tokenValidation.jwt.jwksUri", yamlProperties, systemProperties, null);
    USER_TOKEN_JWT_AUDIENCE = value("userAuth.tokenValidation.jwt.audience", yamlProperties, systemProperties, null);
    USER_TOKEN_JWT_JWKS_CACHE_SECONDS = longValue("userAuth.tokenValidation.jwt.jwksCacheSeconds", yamlProperties, systemProperties, 600);
    MCP_OAUTH_SCOPES = value("mcp.oauth.scopes", yamlProperties, systemProperties, "openid");
    MCP_OAUTH_RESOURCE_URL = value("mcp.oauth.resourceUrl", yamlProperties, systemProperties, null);
    DEEPSEC_ENABLED = bool("deepDataSecurity.enabled", yamlProperties, systemProperties, false);
    DEEPSEC_DATABASE_TOKEN_STATIC_VALUE = value("deepDataSecurity.databaseToken.staticValue", yamlProperties, systemProperties, null);
    DEEPSEC_DATABASE_TOKEN_ENDPOINT = value("deepDataSecurity.databaseToken.tokenEndpoint", yamlProperties, systemProperties, null);
    DEEPSEC_DATABASE_TOKEN_CLIENT_ID = value("deepDataSecurity.databaseToken.clientId", yamlProperties, systemProperties, null);
    DEEPSEC_DATABASE_TOKEN_CLIENT_SECRET = value("deepDataSecurity.databaseToken.clientSecret", yamlProperties, systemProperties, null);
    DEEPSEC_DATABASE_TOKEN_SCOPE = value("deepDataSecurity.databaseToken.scope", yamlProperties, systemProperties, null);
    OJDBC_EXT_DIR = value("database.jdbc.extensionsDirectory", yamlProperties, systemProperties, null);
  }

  private static Map<String, String> canonicalSystemProperties() {
    Map<String, String> canonical = new LinkedHashMap<>();
    Map<String, String> legacy = new LinkedHashMap<>();
    System.getProperties().forEach((key, value) -> {
      String name = key.toString();
      String canonicalName = RuntimePropertyNames.canonicalName(name);
      if (canonicalName.equals(name)) {
        canonical.put(name, value.toString());
      } else {
        legacy.putIfAbsent(canonicalName, value.toString());
      }
    });
    legacy.forEach(canonical::putIfAbsent);
    return canonical;
  }

  private static String value(String name, Map<String, String> yamlProperties,
      Map<String, String> systemProperties, String defaultValue) {
    String systemValue = systemProperties.get(name);
    if (systemValue != null && !systemValue.isBlank()) return systemValue;
    if (yamlProperties != null) {
      String yamlValue = yamlProperties.get(name);
      if (yamlValue != null && !yamlValue.isBlank()) return yamlValue;
    }
    return defaultValue;
  }

  private static boolean bool(String name, Map<String, String> yamlProperties,
      Map<String, String> systemProperties, boolean defaultValue) {
    return Boolean.parseBoolean(value(name, yamlProperties, systemProperties, Boolean.toString(defaultValue)));
  }

  private static int integer(String name, Map<String, String> yamlProperties,
      Map<String, String> systemProperties, int defaultValue) {
    return Integer.parseInt(value(name, yamlProperties, systemProperties, Integer.toString(defaultValue)));
  }

  private static long longValue(String name, Map<String, String> yamlProperties,
      Map<String, String> systemProperties, long defaultValue) {
    return Long.parseLong(value(name, yamlProperties, systemProperties, Long.toString(defaultValue)));
  }
}
