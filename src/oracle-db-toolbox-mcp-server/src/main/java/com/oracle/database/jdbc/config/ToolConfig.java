package com.oracle.database.jdbc.config;

import java.util.List;

public class ToolConfig {
  public String name;           // The tool name (from YAML key)
  public String source;         // Reference key from sources
  public String description;
  public List<ToolParameterConfig> parameters;
  public String statement;      // The SQL statement to execute
}