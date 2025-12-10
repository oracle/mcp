package com.oracle.database.mcptoolkit.config;

import java.util.Map;

public class ConfigRoot {
  public Map<String, SourceConfig> sources;
  public Map<String, ToolConfig> tools;

  public void substituteEnvVars() {
    if (sources != null) {
      for (SourceConfig sc : sources.values()) {
        if (sc != null) sc.substituteEnvVars();
      }
    }
    if (tools != null) {
      for (ToolConfig tc : tools.values()) {
        if (tc != null) tc.substituteEnvVars();
      }
    }
  }
}
