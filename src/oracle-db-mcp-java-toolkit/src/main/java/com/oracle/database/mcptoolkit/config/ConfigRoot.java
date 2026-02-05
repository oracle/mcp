/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.config;

import java.util.List;
import java.util.Map;

/**
 * Represents the root configuration for the application, containing a map of source configurations and tool configurations.
 */
public class ConfigRoot {
  public Map<String, DataSourceConfig> dataSources;
  public Map<String, ToolConfig> tools;
  /**
   * Optional named toolsets allowing users to group custom tools and enable them with -Dtools.
   * Example YAML:
   * toolsets:
   *   reporting: [top_customers, sales_by_region]
   */
  public Map<String, List<String>> toolsets;

  /**
   * Substitutes environment variables in the source and tool configurations.
   * <p>
   * This method iterates over the source and tool configurations, substituting environment variables
   * in each configuration's fields.
   */
  public void substituteEnvVars() {
    if (dataSources != null) {
      for (DataSourceConfig sc : dataSources.values()) {
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
