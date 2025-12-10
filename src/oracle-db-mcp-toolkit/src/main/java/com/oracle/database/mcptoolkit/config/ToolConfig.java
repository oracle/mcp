package com.oracle.database.mcptoolkit.config;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.oracle.database.mcptoolkit.EnvSubstitutor;

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