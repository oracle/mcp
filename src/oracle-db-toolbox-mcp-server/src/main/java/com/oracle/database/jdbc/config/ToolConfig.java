package com.oracle.database.jdbc.config;

import com.oracle.database.jdbc.EnvSubstitutor;

import java.util.List;

public class ToolConfig {
  public String name;           // The tool name (from YAML key)
  public String source;         // Reference key from sources
  public String description;
  public List<ToolParameterConfig> parameters;
  public String statement;      // The SQL statement to execute

  public void substituteEnvVars() {
    this.name        = EnvSubstitutor.substituteEnvVars(this.name);
    this.source      = EnvSubstitutor.substituteEnvVars(this.source);
    this.description = EnvSubstitutor.substituteEnvVars(this.description);
    this.statement   = EnvSubstitutor.substituteEnvVars(this.statement);
    if (this.parameters != null) {
      for (ToolParameterConfig param : this.parameters) {
        if (param != null) param.substituteEnvVars();
      }
    }
  }
}