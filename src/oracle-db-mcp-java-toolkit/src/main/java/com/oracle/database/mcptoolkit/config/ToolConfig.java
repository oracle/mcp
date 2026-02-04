/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.config;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.oracle.database.mcptoolkit.EnvSubstitutor;

import java.util.List;

/**
 * Represents a tool configuration, encapsulating its properties and behavior.
 */
public class ToolConfig {
  /**
   * The tool name, derived from the YAML key.
   */
  public String name;

  /**
   * Reference key from data sources.
   */
  public String dataSource;

  /**
   * A brief description of the tool.
   */
  public String description;

  /**
   * A list of parameter configurations for the tool.
   */
  public List<ToolParameterConfig> parameters;

  /**
   * The SQL statement to be executed by the tool.
   */
  public String statement;

  /**
   * Substitutes environment variables in the tool configuration.
   * <p>
   * Replaces placeholders in the tool's name, source, description, and statement with their corresponding environment variable values.
   * Also substitutes environment variables in the tool's parameters, if any.
   */
  public void substituteEnvVars() {
    this.name        = EnvSubstitutor.substituteEnvVars(this.name);
    this.dataSource      = EnvSubstitutor.substituteEnvVars(this.dataSource);
    this.description = EnvSubstitutor.substituteEnvVars(this.description);
    this.statement   = EnvSubstitutor.substituteEnvVars(this.statement);
    if (this.parameters != null) {
      for (ToolParameterConfig param : this.parameters) {
        if (param != null) param.substituteEnvVars();
      }
    }
  }

  public String buildInputSchemaJson() {
    ObjectNode schema = JsonNodeFactory.instance.objectNode();
    schema.put("type", "object");
    ObjectNode properties = schema.putObject("properties");
    ArrayNode required = JsonNodeFactory.instance.arrayNode();

      for (ToolParameterConfig param : this.parameters) {
        if (param == null) {
          continue;
        }
        ObjectNode prop = properties.putObject(param.name);
        prop.put("type", param.type);
        prop.put("description", param.description);
        if (param.required) {
          required.add(param.name);
        }
      }
    if (!required.isEmpty()) {
      schema.set("required", required);
    }
    return schema.toString();
  }
}