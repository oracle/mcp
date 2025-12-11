/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.config;

import com.oracle.database.mcptoolkit.EnvSubstitutor;

/**
 * Represents the configuration for a data source, specifically for an Oracle database.
 * <p>
 * This class encapsulates the necessary properties to establish a connection to the database.
 */
public class DataSourceConfig {
  /**
   * The hostname or IP address of the database server.
   */
  public String host;

  /**
   * The port number on which the database server is listening.
   */
  public String port;

  /**
   * The Oracle SID or service name of the database.
   */
  public String database;

  /**
   * The JDBC URL for the database connection. If not provided, it will be constructed
   * using the host, port, and database properties.
   */
  public String url;

  /**
   * The username to use for the database connection.
   */
  public String user;

  /**
   * The password to use for the database connection.
   */
  public char[] password;

  /**
   * Returns the JDBC URL for the database connection. If the {@link #url} property is not set,
   * it will be constructed using the {@link #host}, {@link #port}, and {@link #database} properties.
   *
   * @return the JDBC URL for the database connection
   */
  public String toJdbcUrl() {
    if(url == null) {
      return String.format("jdbc:oracle:thin:@%s:%s/%s", host, port, database);
    } else {
      return url;
    }
  }

  /**
   * Substitutes environment variables in the configuration properties.
   * <p>
   * This method replaces placeholders in the form of ${VARIABLE_NAME} with the actual environment variable values.
   */
  public void substituteEnvVars() {
    this.host     = EnvSubstitutor.substituteEnvVars(this.host);
    this.port     = EnvSubstitutor.substituteEnvVars(this.port);
    this.database = EnvSubstitutor.substituteEnvVars(this.database);
    this.url      = EnvSubstitutor.substituteEnvVars(this.url);
    this.user     = EnvSubstitutor.substituteEnvVars(this.user);
    this.password = EnvSubstitutor.substituteEnvVarsInCharArray(this.password);
  }
}