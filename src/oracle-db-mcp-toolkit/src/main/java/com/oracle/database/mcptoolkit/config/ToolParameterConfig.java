/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.config;

import com.oracle.database.mcptoolkit.EnvSubstitutor;

/**
 * Represents a configuration for a tool parameter.
 * <p>
 * This class encapsulates the properties of a tool parameter, including its name, type, description, and whether it is required.
 */
public class ToolParameterConfig {
  /**
   * The name of the tool parameter.
   */
  public String name;

  /**
   * The data type of the tool parameter.
   */
  public String type;

  /**
   * A human-readable description of the tool parameter.
   */
  public String description;

  /**
   * Indicates whether the tool parameter is required.
   */
  public boolean required;

  /**
   * Substitutes environment variables in the tool parameter's properties.
   * <p>
   * This method replaces any environment variable references in the {@link #name}, {@link #type}, and {@link #description} fields with their corresponding values.
   */
  public void substituteEnvVars() {
    this.name        = EnvSubstitutor.substituteEnvVars(this.name);
    this.type        = EnvSubstitutor.substituteEnvVars(this.type);
    this.description = EnvSubstitutor.substituteEnvVars(this.description);
  }

}