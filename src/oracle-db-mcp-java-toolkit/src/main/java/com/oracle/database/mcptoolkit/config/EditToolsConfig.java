/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.config;

import java.util.List;

/**
 * Optional policy for the edit-tools administrative tool.
 */
public class EditToolsConfig {
  public Boolean enabled;
  public List<String> allowedDataSources;
  public List<String> allowedStatementTypes;
}
