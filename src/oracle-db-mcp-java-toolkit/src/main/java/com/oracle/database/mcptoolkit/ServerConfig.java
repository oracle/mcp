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
  public final char[] dbPassword;
  public final Set<String> toolsFilter;
  public final Map<String, DataSourceConfig> sources;
  public final Map<String, ToolConfig> tools;
  public static String defaultSourceName; // Only if the default db info are from yaml config to avoid redundancy

  private ServerConfig(
      String dbUrl,
      String dbUser,
      char[] dbPassword,
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

  /** Built-in toolsets covering predefined tools. Lowercase keys and members. */
  private static final Map<String, Set<String>> BUILTIN_TOOLSETS = Map.of(
      "log_analyzer", Set.of(
          "get-jdbc-stats",
          "get-jdbc-queries",
          "get-jdbc-errors",
          "list-log-files-from-directory",
          "jdbc-log-comparison",
          "get-jdbc-connection-events",
          "get-rdbms-errors",
          "get-rdbms-packet-dumps"
      ),
      "explain", Set.of("explain_plan"),
      "similarity", Set.of("similarity_search"),
      "admin", Set.of("list-tools", "edit-tools")
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
    Set<String> rawTools = parseToolsProp(LoadedConstants.TOOLS);

    String dbUrl = LoadedConstants.DB_URL;
    String dbUser = LoadedConstants.DB_USER;
    char[] dbPass = LoadedConstants.DB_PASSWORD;

    Map<String, DataSourceConfig> sources = configRoot != null ? configRoot.dataSources : Collections.emptyMap();
    Map<String, ToolConfig> toolsMap = configRoot != null ? configRoot.tools : Collections.emptyMap();

    if (toolsMap != null) {
      for (Map.Entry<String, ToolConfig> entry : toolsMap.entrySet()) {
        entry.getValue().name = entry.getKey();
      }
    }
    if (configRoot != null) configRoot.substituteEnvVars();

    Set<String> expandedTools = expandToolsFilter(rawTools, configRoot);

    boolean allLoadedConstantsPresent =
        dbUrl != null && !dbUrl.isBlank()
        && dbUser != null && !dbUser.isBlank()
        && dbPass != null && dbPass.length > 0;

    if (!allLoadedConstantsPresent && sources!=null && sources.containsKey(defaultSourceKey)) {
      DataSourceConfig src = sources.get(defaultSourceKey);
      dbUrl = src.toJdbcUrl();
      dbUser = src.user;
      dbPass = src.getPasswordChars();
      defaultSourceName = defaultSourceKey;
    }

    boolean needDb = wantsAnyDbToolsExpanded(expandedTools);

    if (needDb && (dbUrl == null || dbUrl.isBlank())) {
      throw new IllegalStateException("Missing required db.url in both system properties and YAML config");
    }
    if (needDb && (dbUser == null || dbUser.isBlank())) {
      throw new IllegalStateException("Missing required db.user in both system properties and YAML config");
    }
    if (needDb && (dbPass == null || dbPass.length == 0)) {
      throw new IllegalStateException("Missing required db.password in both system properties and YAML config");
    }
    return new ServerConfig(dbUrl, dbUser, dbPass, expandedTools, sources, toolsMap);
  }

  /**
   * Builds a {@link ServerConfig} from JVM system properties(i.e., {@code -Dkey=value}).
   * Validates required properties and applies sensible defaults for optional ones.
   *
   * @return a validated configuration
   * @throws IllegalStateException if {@code db.url} is missing or blank
   */
  static ServerConfig fromSystemProperties() {
    Set<String> raw = parseToolsProp(LoadedConstants.TOOLS);
    Set<String> expanded = expandToolsFilter(raw, null);
    boolean needDb = wantsAnyDbToolsExpanded(expanded);

    String dbUrl = LoadedConstants.DB_URL;
    if (needDb && (dbUrl == null || dbUrl.isBlank())) {
      throw new IllegalStateException("Missing required system property: db.url");
    }

    return new ServerConfig(
            dbUrl,
            LoadedConstants.DB_USER,
            LoadedConstants.DB_PASSWORD,
            expanded,
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

  /**
   * Expands the raw -Dtools filter to concrete tool names by resolving YAML and built-in toolsets.
   * Returns null to mean "all tools" if the input is null.
   */
  private static Set<String> expandToolsFilter(Set<String> raw, ConfigRoot configRoot) {
    if (raw == null) return null; // all tools enabled
    Map<String, List<String>> yamlSets = (configRoot != null) ? configRoot.toolsets : null;

    Set<String> out = new LinkedHashSet<>();
    for (String name : raw) {
      String k = name == null ? null : name.trim().toLowerCase(Locale.ROOT);
      if (k == null || k.isEmpty()) continue;

      // YAML toolset match
      if (yamlSets != null && yamlSets.containsKey(k)) {
        List<String> members = yamlSets.get(k);
        if (members != null) {
          for (String m : members) {
            if (m != null) {
              String mm = m.trim().toLowerCase(Locale.ROOT);
              if (!mm.isEmpty()) out.add(mm);
            }
          }
        }
        continue;
      }

      // Built-in toolset match
      Set<String> builtin = BUILTIN_TOOLSETS.get(k);
      if (builtin != null) {
        out.addAll(builtin);
        continue;
      }

      // Fallback to explicit tool name
      out.add(k);
    }
    return out;
  }

  private static boolean wantsAnyDbToolsExpanded(Set<String> expandedFilter) {
    if (expandedFilter == null) return true; // all enabled
    for (String t : expandedFilter) {
      if (DB_TOOLS.contains(t)) return true;
    }
    return false;
  }

}
