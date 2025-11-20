package com.oracle.database.jdbc.config;

public class SourceConfig {
  public String host;
  public int port;
  public String database;  // Oracle SID or service name
  public String url;
  public String user;
  public String password;

  public String toJdbcUrl() {
    if(url == null) {
      return String.format("jdbc:oracle:thin:@%s:%d/%s", host, port, database);
    } else {
      return url;
    }
  }
}