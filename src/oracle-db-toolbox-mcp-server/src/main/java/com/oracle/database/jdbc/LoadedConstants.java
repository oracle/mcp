package com.oracle.database.jdbc;

public final class LoadedConstants {
  private LoadedConstants() {} // Prevent instantiation

  /** Network config */
  public static final String TRANSPORT_KIND = System.getProperty("transport", "stdio")
      .trim()
      .toLowerCase();
  public static final int HTTP_PORT = Integer.parseInt(System.getProperty("http.port", "45450"));
  public static final int HTTPS_PORT = Integer.parseInt(System.getProperty("https.port", "45451"));
  public static final String KEYSTORE_PATH = System.getProperty("certificatePath");
  public static final String KEYSTORE_PASSWORD = System.getProperty("certificatePassword");

  /** Tools config */
  public static final String TOOLS = System.getProperty("tools");
  public static final String DB_URL = System.getProperty("db.url");
  public static final String DB_USER = System.getProperty("db.user");
  public static final String DB_PASSWORD = System.getProperty("db.password");

  /** OAuth config */
  public static final String ALLOWED_HOSTS= System.getProperty("allowedHosts","*");
  public static final String REDIRECT_OPENID_TO_OAUTH= System.getProperty("redirectOpenIDToOAuth","false");
  public static final boolean ENABLE_AUTH = Boolean.parseBoolean(System.getProperty("enableAuthentication","false"));
  public static final String ORACLE_DB_TOOLBOX_AUTH_TOKEN = System.getenv("ORACLE_DB_TOOLBOX_AUTH_TOKEN");
  public static final String AUTH_SERVER = System.getProperty("authServer");
  public static final String INTROSPECTION_ENDPOINT = System.getProperty("introspectionEndpoint");
  public static final String CLIENT_ID = System.getProperty("clientId");
  public static final String CLIENT_SECRET = System.getProperty("clientSecret");

  /** Yaml config */
  public static final String CONFIG_FILE = System.getProperty("configFile");

  /** External extensions */
  public static final String OJDBC_EXT_DIR = System.getProperty("ojdbc.ext.dir");

}
