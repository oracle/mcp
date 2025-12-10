package com.oracle.database.mcptoolkit.config;

import com.oracle.database.mcptoolkit.EnvSubstitutor;

public class ToolParameterConfig {
  public String name;
  public String type;
  public String description;
  public boolean required;

  public void substituteEnvVars() {
    this.name        = EnvSubstitutor.substituteEnvVars(this.name);
    this.type        = EnvSubstitutor.substituteEnvVars(this.type);
    this.description = EnvSubstitutor.substituteEnvVars(this.description);
  }
}