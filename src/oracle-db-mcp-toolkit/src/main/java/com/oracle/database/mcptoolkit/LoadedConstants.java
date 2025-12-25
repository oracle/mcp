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

  /** Tools config */
  public static final String TOOLS = System.getProperty("tools");
  public static final String DB_URL = System.getProperty("db.url");
  public static final String DB_USER = System.getProperty("db.user");
  public static final char[] DB_PASSWORD = System.getProperty("db.password") != null
      ? System.getProperty("db.password").toCharArray()
      : null;

  /** OAuth config */
  public static final String ALLOWED_HOSTS= System.getProperty("allowedHosts","*");
  public static final String REDIRECT_OPENID_TO_OAUTH= System.getProperty("redirectOpenIDToOAuth","false");
  public static final boolean ENABLE_AUTH = Boolean.parseBoolean(System.getProperty("enableAuthentication","false"));
  public static final String ORACLE_DB_TOOLKIT_AUTH_TOKEN = System.getenv("ORACLE_DB_TOOLKIT_AUTH_TOKEN");
  public static final String AUTH_SERVER = System.getProperty("authServer");
  public static final String INTROSPECTION_ENDPOINT = System.getProperty("introspectionEndpoint");
  public static final String CLIENT_ID = System.getProperty("clientId");
  public static final String CLIENT_SECRET = System.getProperty("clientSecret");

  /** Yaml config */
  public static final String CONFIG_FILE = System.getProperty("configFile");

  /** External extensions */
  public static final String OJDBC_EXT_DIR = System.getProperty("ojdbc.ext.dir");

}
