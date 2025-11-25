package com.oracle.database.jdbc.config;

import com.oracle.database.jdbc.EnvSubstitutor;

public class SourceConfig {
  public String host;
  public String port;
  public String database;  // Oracle SID or service name
  public String url;
  public String user;
  public String password;

  public String toJdbcUrl() {
    if(url == null) {
      return String.format("jdbc:oracle:thin:@%s:%s/%s", host, port, database);
    } else {
      return url;
    }
  }

  public void substituteEnvVars() {
    this.host     = EnvSubstitutor.substituteEnvVars(this.host);
    this.port     = EnvSubstitutor.substituteEnvVars(this.port);
    this.database = EnvSubstitutor.substituteEnvVars(this.database);
    this.url      = EnvSubstitutor.substituteEnvVars(this.url);
    this.user     = EnvSubstitutor.substituteEnvVars(this.user);
    this.password = EnvSubstitutor.substituteEnvVars(this.password);
  }
}