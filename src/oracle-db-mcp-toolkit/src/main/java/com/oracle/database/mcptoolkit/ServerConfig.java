/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit;

import com.oracle.database.mcptoolkit.config.ConfigRoot;
import com.oracle.database.mcptoolkit.config.DataSourceConfig;
import com.oracle.database.mcptoolkit.config.ToolConfig;

import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Immutable server configuration loaded from system properties.
 *
 * <p>Conditionally required property:</p>
 * <ul>
 *   <li>{@code db.url} — required only when any database tool is enabled.</li>
 * </ul>
 *
 * <p>Optional properties:</p>
 * <ul>
 *   <li>{@code db.user}</li>
 *   <li>{@code db.password}</li>
 *   <li>{@code tools} — comma-separated allow-list of tool names; {@code *} or {@code all} enables all.</li>
 * </ul>
 *
 * <p>Use {@link #fromSystemProperties()} to create an instance with validation and defaults.</p>
 */
public final class ServerConfig {
  public final String dbUrl;
  public final String dbUser;
  public final String dbPassword;
  public final Set<String> toolsFilter;
  public final Map<String, DataSourceConfig> sources;
  public final Map<String, ToolConfig> tools;
  public static String defaultSourceName; // Only if the default db info are from yaml config to avoid redundancy

  private ServerConfig(
      String dbUrl,
      String dbUser,
      String dbPassword,
      Set<String> toolsFilter,
      Map<String, DataSourceConfig> sources,
      Map<String, ToolConfig> tools
  ) {
    this.dbUrl = dbUrl;
    this.dbUser = dbUser;
    this.dbPassword = dbPassword;
    this.toolsFilter = toolsFilter;
    this.sources = sources;
    this.tools = tools;
  }

  private static final Set<String> DB_TOOLS = Set.of(
    "similarity_search", "explain_plan"
  );


  /**
   * Builds a {@link ServerConfig} from JVM system properties (i.e., {@code -Dkey=value}),
   * with fallback to values from a parsed YAML configuration.
   * <p>
   * Resolution order for each property:
   * <ol>
   *   <li>JVM system property (highest priority, e.g., {@code -Ddb.url}, {@code -Ddb.user}, {@code -Ddb.password})</li>
   *   <li>YAML config ({@link ConfigRoot} and specified source), if system property is absent or blank</li>
   * </ol>
   * <p>
   * Validates that all required values are present if any database tool is enabled.
   *
   * @param configRoot the parsed YAML configuration root (nullable if not used)
   * @param defaultSourceKey the source key in YAML to use for Oracle connection details fallback
   * @return a validated configuration
   * @throws IllegalStateException if required properties are missing from both system properties and YAML config
   */
  public static ServerConfig fromSystemPropertiesAndYaml(ConfigRoot configRoot, String defaultSourceKey) {
    Set<String> tools = parseToolsProp(LoadedConstants.TOOLS);
    boolean needDb = wantsAnyDbTools(tools);

    String dbUrl = LoadedConstants.DB_URL;
    String dbUser = LoadedConstants.DB_USER;
    String dbPass = LoadedConstants.DB_PASSWORD;

    Map<String, DataSourceConfig> sources = configRoot != null ? configRoot.getDataSources() : Collections.emptyMap();
    Map<String, ToolConfig> toolsMap = configRoot != null ? configRoot.getTools() : Collections.emptyMap();

    if (toolsMap != null) {
      for (Map.Entry<String, ToolConfig> entry : toolsMap.entrySet()) {
        entry.getValue().setName(entry.getKey());
      }
    }
    configRoot.substituteEnvVars();
    boolean allLoadedConstantsPresent =
        dbUrl != null && !dbUrl.isBlank()
        && dbUser != null && !dbUser.isBlank()
        && dbPass != null && !dbPass.isBlank();

    if (!allLoadedConstantsPresent && sources!=null && sources.containsKey(defaultSourceKey)) {
      DataSourceConfig src = sources.get(defaultSourceKey);
      dbUrl = src.toJdbcUrl();
      dbUser = src.getUser();
      dbPass = src.getPassword();
      defaultSourceName = defaultSourceKey;
    }

    if (needDb && (dbUrl == null || dbUrl.isBlank())) {
      throw new IllegalStateException("Missing required db.url in both system properties and YAML config");
    }
    if (needDb && (dbUser == null || dbUser.isBlank())) {
      throw new IllegalStateException("Missing required db.user in both system properties and YAML config");
    }
    if (needDb && (dbPass == null || dbPass.isBlank())) {
      throw new IllegalStateException("Missing required db.password in both system properties and YAML config");
    }
    return new ServerConfig(dbUrl, dbUser, dbPass, tools, sources, toolsMap);
  }

  /**
   * Builds a {@link ServerConfig} from JVM system properties(i.e., {@code -Dkey=value}).
   * Validates required properties and applies sensible defaults for optional ones.
   *
   * @return a validated configuration
   * @throws IllegalStateException if {@code db.url} is missing or blank
   */
  static ServerConfig fromSystemProperties() {
    Set<String> tools = parseToolsProp(LoadedConstants.TOOLS);
    boolean needDb = wantsAnyDbTools(tools);

    String dbUrl = LoadedConstants.DB_URL;
    if (needDb && (dbUrl == null || dbUrl.isBlank())) {
      throw new IllegalStateException("Missing required system property: db.url");
    }

    return new ServerConfig(
            dbUrl,
            LoadedConstants.DB_USER,
            LoadedConstants.DB_PASSWORD,
            tools,
            new HashMap<>(),
            new HashMap<>()
    );
  }

  /**
   * Reads a comma-separated list of tool names and returns which tools
   * should be enabled.
   * If the input is empty, missing, "*" or "all", it means
   * “enable every tool” and returns {@code null}.
   *
   * Examples:
   *   "similarity_search,explain_plan"  -> ["similarity_search","explain_plan"]
   *   "*" or "all" or ""        -> null (treat as all tools enabled)
   *
   * @param prop comma-separated tool names
   * @return a set of enabled tool names, or {@code null} to mean “all tools”
   */
  private static Set<String> parseToolsProp(String prop) {
    if (prop == null || prop.isBlank()) return null; // null = allow all
    Set<String> s = new LinkedHashSet<>();
    for (String t : prop.split(",")) {
      String k = t.trim().toLowerCase(Locale.ROOT);
      if (!k.isEmpty()) s.add(k);
    }
    if (s.contains("*") || s.contains("all")) return null; // treat as allow all
    return s;
  }

  private static boolean wantsAnyDbTools(Set<String> toolsFilter) {
    if (toolsFilter == null) return true; // null == all tools enabled
    for (String t : toolsFilter) {
      if (DB_TOOLS.contains(t)) return true;
    }
    return false;
  }

}
