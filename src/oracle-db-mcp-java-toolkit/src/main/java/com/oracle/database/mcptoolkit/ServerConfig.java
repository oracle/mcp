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

import java.util.*;
import java.util.logging.Logger;
import java.util.logging.Level;

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
 *   <li>{@code tools} — comma-separated allow-list of tool names or toolset
 *   names; (e.g., {@code log_analyzer}, {@code admin}, {@code explain},
 *   {@code rag}); {@code *} or {@code all} enables all.</li>
 * </ul>
 *
 * <p>Use {@link #fromSystemProperties()} to create an instance with validation and defaults.</p>
 */
public final class ServerConfig {
  private static final Logger LOG = Logger.getLogger(ServerConfig.class.getName());
  public final String dbUrl;
  public final String dbUser;
  public final char[] dbPassword;
  public final Set<String> toolsFilter;
  public final Set<String> disabledToolsetMembers;
  public final Map<String, DataSourceConfig> sources;
  public final Map<String, ToolConfig> tools;
  public static String defaultSourceName; // Only if the default db info are from yaml config to avoid redundancy

  private ServerConfig(
      String dbUrl,
      String dbUser,
      char[] dbPassword,
      Set<String> toolsFilter,
      Set<String> disabledToolsetMembers,
      Map<String, DataSourceConfig> sources,
      Map<String, ToolConfig> tools
  ) {
    this.dbUrl = dbUrl;
    this.dbUser = dbUser;
    this.dbPassword = dbPassword;
    this.toolsFilter = toolsFilter;
    this.disabledToolsetMembers = disabledToolsetMembers;
    this.sources = sources;
    this.tools = tools;
  }

  private static final Set<String> DB_TOOLS = Set.of(
    "similarity-search", "explain-plan", "read-query", "write-query",
    "transaction", "table", "db-ping", "db-metrics-range", "vector-store",
    "vector-model", "embed", "task", "oci-storage"
  );

  /** Built-in toolsets covering predefined tools. Lowercase keys and members. */
  private static final Map<String, Set<String>> BUILTIN_TOOLSETS = Map.of(
      "log-analyzer", Set.of("jdbc-analyzer", "rdbms-analyzer"),
      "rag", Set.of(
                  "similarity-search", "vector-store", "vector-model",
                  "embed", "task", "oci-storage"
          ),
      "database-operator", Set.of(
              "read-query", "write-query", "transaction", "table", "db-ping", "db-metrics-range",
              "explain-plan"
      ),
      "mcp-admin", Set.of("list-tools", "edit-tools")
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
    Set<String> disabledToolsetMembers = collectDisabledToolsetMembers(configRoot);

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
    return new ServerConfig(dbUrl, dbUser, dbPass, expandedTools, disabledToolsetMembers, sources, toolsMap);
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
            Collections.emptySet(),
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
   *   "similarity-search,explain-plan"  -> ["similarity-search","explain-plan"]
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
    Map<String, Object> yamlSets = (configRoot != null) ? configRoot.toolsets : null;

    // -Dtools omitted or * / all => all built-ins + all custom tools, then prune disabled custom tools.
    if (raw == null) {
      return null;
    }

    Set<String> out = new LinkedHashSet<>();

    // Custom tools are enabled by default even when absent from -Dtools
    if (configRoot != null && configRoot.tools != null) {
      for (Map.Entry<String, ToolConfig> e : configRoot.tools.entrySet()) {
        String tn = e.getKey();
        ToolConfig tc = e.getValue();
        if (tn == null) continue;
        if (tc != null && Boolean.FALSE.equals(tc.enabled)) continue;
        if (tc != null && tc.enabled == null && isMemberOfDisabledToolset(configRoot, tn)) continue;
        String k = tn.trim().toLowerCase(Locale.ROOT);
        if (!k.isEmpty()) out.add(k);
      }
    }

    // Custom toolsets are enabled by default even when absent from -Dtools
    if (yamlSets != null) {
      for (Map.Entry<String, Object> e : yamlSets.entrySet()) {
        String setName = e.getKey();
        if (setName == null) continue;
        ToolsetDef def = parseToolsetDef(e.getValue());
        if (!def.enabled) continue;
        out.addAll(def.members);
      }
    }

    for (String name : raw) {
      String k = name == null ? null : name.trim().toLowerCase(Locale.ROOT);
      if (k == null || k.isEmpty()) continue;

      // Built-in toolset match first. If a YAML toolset has the same name, prefer built-in and log an error.
      Set<String> builtin = BUILTIN_TOOLSETS.get(k);
      if (builtin != null) {
        if (yamlSets != null && yamlSets.containsKey(k)) {
          LOG.log(Level.SEVERE, () -> "Custom toolset '" + k + "' conflicts with built-in toolset; ignoring custom definition and using built-in.");
        }
        out.addAll(builtin);
        continue;
      }

      // YAML toolset match (only if not a built-in name)
      if (yamlSets != null && yamlSets.containsKey(k)) {
        ToolsetDef def = parseToolsetDef(yamlSets.get(k));
        if (def.enabled) {
          out.addAll(def.members);
        }
        continue;
      }

      // Fallback to explicit tool name
      out.add(k);
    }

    // Ensure tool-level enabled:false always wins
    if (configRoot != null && configRoot.tools != null) {
      for (Map.Entry<String, ToolConfig> e : configRoot.tools.entrySet()) {
        String tn = e.getKey();
        ToolConfig tc = e.getValue();
        if (tn == null || tc == null) continue;
        if (Boolean.FALSE.equals(tc.enabled)) {
          out.remove(tn.trim().toLowerCase(Locale.ROOT));
        }
      }
    }

    return out;
  }

  private static final class ToolsetDef {
    final boolean enabled;
    final Set<String> members;

    ToolsetDef(boolean enabled, Set<String> members) {
      this.enabled = enabled;
      this.members = members;
    }
  }

  @SuppressWarnings("unchecked")
  private static ToolsetDef parseToolsetDef(Object raw) {
    boolean enabled = true;
    Set<String> members = new LinkedHashSet<>();

    if (raw instanceof List<?> list) {
      for (Object m : list) {
        if (m == null) continue;
        String mm = String.valueOf(m).trim().toLowerCase(Locale.ROOT);
        if (!mm.isEmpty()) members.add(mm);
      }
      return new ToolsetDef(enabled, members);
    }

    if (raw instanceof Map<?, ?> map) {
      Object enabledObj = map.get("enabled");
      if (enabledObj instanceof Boolean b) {
        enabled = b;
      } else if (enabledObj != null) {
        enabled = Boolean.parseBoolean(String.valueOf(enabledObj));
      }

      Object toolsObj = map.get("tools");
      if (toolsObj instanceof List<?> list) {
        for (Object m : list) {
          if (m == null) continue;
          String mm = String.valueOf(m).trim().toLowerCase(Locale.ROOT);
          if (!mm.isEmpty()) members.add(mm);
        }
      }
      return new ToolsetDef(enabled, members);
    }

    return new ToolsetDef(true, members);
  }

  public static boolean isToolEnabled(ServerConfig config, String toolName) {
    if (toolName == null) return false;
    String key = toolName.trim().toLowerCase(Locale.ROOT);
    if (key.isEmpty()) return false;

    ToolConfig tc = config != null && config.tools != null ? config.tools.get(key) : null;
    if (tc == null && config != null && config.tools != null) {
      tc = config.tools.get(toolName);
    }

    if (tc != null && Boolean.FALSE.equals(tc.enabled)) {
      return false;
    }

    if (tc != null && tc.enabled == null && config != null && config.disabledToolsetMembers != null
        && config.disabledToolsetMembers.contains(key)) {
      return false;
    }

    if (config == null || config.toolsFilter == null) {
      return true;
    }

    // Custom tools are enabled by default even when absent from -Dtools
    if (tc != null) {
      return true;
    }

    return config.toolsFilter.contains(key);
  }

  private static boolean isMemberOfDisabledToolset(ConfigRoot configRoot, String toolName) {
    if (configRoot == null || configRoot.toolsets == null || toolName == null) return false;
    String key = toolName.trim().toLowerCase(Locale.ROOT);
    if (key.isEmpty()) return false;
    for (Map.Entry<String, Object> e : configRoot.toolsets.entrySet()) {
      ToolsetDef def = parseToolsetDef(e.getValue());
      if (!def.enabled && def.members.contains(key)) {
        return true;
      }
    }
    return false;
  }

  private static Set<String> collectDisabledToolsetMembers(ConfigRoot configRoot) {
    Set<String> out = new LinkedHashSet<>();
    if (configRoot == null || configRoot.toolsets == null) return out;
    for (Map.Entry<String, Object> e : configRoot.toolsets.entrySet()) {
      ToolsetDef def = parseToolsetDef(e.getValue());
      if (!def.enabled) out.addAll(def.members);
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
