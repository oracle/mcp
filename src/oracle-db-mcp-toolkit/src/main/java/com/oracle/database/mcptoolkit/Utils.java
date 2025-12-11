/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.mcptoolkit.config.ConfigRoot;
import com.oracle.database.mcptoolkit.config.DataSourceConfig;
import com.oracle.database.mcptoolkit.config.ToolConfig;
import com.oracle.database.mcptoolkit.config.ToolParameterConfig;
import com.oracle.database.mcptoolkit.tools.ExplainAndExecutePlanTool;
import com.oracle.database.mcptoolkit.tools.LogAnalyzerTools;
import com.oracle.database.mcptoolkit.tools.SimilaritySearchTool;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.spec.McpSchema;
import org.yaml.snakeyaml.Yaml;
import oracle.ucp.jdbc.PoolDataSource;
import oracle.ucp.jdbc.PoolDataSourceFactory;

import javax.sql.DataSource;
import java.io.IOException;
import java.io.Reader;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.Provider;
import java.security.Security;
import java.sql.Clob;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Stream;

/**
 * Utility class for managing Oracle database connections and
 * executing SQL operations.
 *
 * <p>Provides methods for connection pooling (using Oracle UCP),
 * executing queries, converting results to JSON, and safely handling
 * database identifiers.
 *
 * <p>The connection pool uses minimal settings (1 connection).
 */
public class Utils {
  private static final Logger LOG = Logger.getLogger(Utils.class.getName());

  private static final Map<String, DataSource> dataSources = new ConcurrentHashMap<>();
  private static volatile DataSource defaultDataSource;

  /**
   * <p>
   *   Returns the list of all available tools for this server.
   * </p>
   */
  static void addSyncToolSpecifications(McpSyncServer server, ServerConfig config) {
    List<McpServerFeatures.SyncToolSpecification> specs = LogAnalyzerTools.getTools();
    for (McpServerFeatures.SyncToolSpecification spec : specs) {
      String toolName = spec.tool().name(); // e.g. "get-stats", "get-queries"
      if (isToolEnabled(config, toolName)) {
        server.addTool(spec);
      }
    }

    // similarity_search
    if (isToolEnabled(config, "similarity_search")) {
      server.addTool(SimilaritySearchTool.getSymilaritySearchTool(config));
    }

    // explain_plan
    if (isToolEnabled(config, "explain_plan")) {
      server.addTool(ExplainAndExecutePlanTool.getExplainAndExecutePlanTool(config));
    }

    // ---------- Dynamically Added Tools ----------
    for (Map.Entry<String, ToolConfig> entry : config.tools.entrySet()) {
      ToolConfig tc = entry.getValue();
      server.addTool(
          McpServerFeatures.SyncToolSpecification.builder()
              .tool(McpSchema.Tool.builder()
                  .name(tc.getName())
                  .title(tc.getName())
                  .description(tc.getDescription())
                  .inputSchema(tc.buildInputSchemaJson())
                  .build()
              )
              .callHandler((exchange, callReq) ->
                  tryCall(() -> {
                    try (Connection c = openConnection(config, tc.getDataSource())) {
                      PreparedStatement ps = c.prepareStatement(tc.getStatement());
                      int paramIdx = 1;
                      if (tc.getParameters() != null) {
                        for (ToolParameterConfig param : tc.getParameters()) {
                          Object argVal = callReq.arguments().get(param.getName());
                          ps.setObject(paramIdx++, argVal);
                        }
                      }
                      if (tc.getStatement().trim().toLowerCase().startsWith("select")) {
                        ResultSet rs = ps.executeQuery();
                        List<Map<String,Object>> rows = rsToList(rs);
                        return McpSchema.CallToolResult.builder()
                            .structuredContent(Map.of("rows", rows, "rowCount", rows.size()))
                            .addTextContent(new ObjectMapper().writeValueAsString(rows))
                            .build();
                      } else {
                        int n = ps.executeUpdate();
                        return McpSchema.CallToolResult.builder()
                            .structuredContent(Map.of("updateCount", n))
                            .addTextContent("{\"updateCount\":" + n + "}")
                            .build();
                      }
                    }
                  })
              )
              .build()
      );
    }
  }

  public static String getOrDefault(Object v, String def) {
    if (v == null) return def;
    String s = v.toString().trim();
    return s.isEmpty() ? def : s;
  }

  /**
   * Loads the server configuration from a YAML file specified by the <code>configFile</code> system property.
   * If the file cannot be read or parsed, falls back to using only system properties.
   * Also initializes tool names for dynamic tool entries.
   *
   * @return the loaded and initialized {@link ServerConfig} instance.
   */
  static ServerConfig loadConfig() {
    ServerConfig config;
    String configFilePath = LoadedConstants.CONFIG_FILE;
    ConfigRoot yamlConfig = null;
    try {
      try (Reader reader = Files.newBufferedReader(Paths.get(configFilePath))) {
        Yaml yaml = new Yaml();
        yamlConfig = yaml.loadAs(reader, ConfigRoot.class);
      }
    } catch (NullPointerException ignored) {
      LOG.info("YAML config file is not specified. Using values from system properties.");
    } catch (Exception e) {
      LOG.log(Level.SEVERE, e.getMessage(), e);
    }
    if (yamlConfig == null) {
      config = ServerConfig.fromSystemProperties();
    } else {
      String defaultSourceKey = yamlConfig.getDataSources()!=null?yamlConfig.getDataSources().keySet().stream().findFirst().orElse(null):null;
      config = ServerConfig.fromSystemPropertiesAndYaml(yamlConfig, defaultSourceKey);
    }
    return config;
  }

  /**
   * Acquires a JDBC connection from the active data source.
   *
   * @param cfg server configuration
   * @param sourceName database source
   * @return open JDBC connection
   * @throws SQLException on acquisition failure
   */
  public static Connection openConnection(ServerConfig cfg, String sourceName) throws SQLException {
    return getOrCreateDataSource(cfg, sourceName).getConnection();
  }

  /**
   * Lazily initializes and returns a UCP {@link PoolDataSource} for the given source,
   * using values from {@link ServerConfig}. Each source gets its own minimal pool.
   *
   * @param cfg        the server configuration
   * @param sourceName the name of the source; if null, uses the default source
   * @return a {@link DataSource} for the specified source
   * @throws SQLException if creation or configuration fails
   */
  private static DataSource getOrCreateDataSource(ServerConfig cfg, String sourceName) throws SQLException {
    if (sourceName == null || sourceName.equals(ServerConfig.defaultSourceName)) {
      if (defaultDataSource != null) return defaultDataSource;
      synchronized (Utils.class) {
        if (defaultDataSource != null) return defaultDataSource;
        defaultDataSource = createDataSource(cfg.dbUrl, cfg.dbUser, cfg.dbPassword);
        return defaultDataSource;
      }
    } else {
      return dataSources.computeIfAbsent(sourceName, name -> {
        try {
          DataSourceConfig src = (cfg.sources != null) ? cfg.sources.get(name) : null;
          if (src == null) throw new IllegalArgumentException("Unknown source: " + name);
          return createDataSource(src.toJdbcUrl(), src.getUser(), src.getPassword());
        } catch (SQLException ex) {
          throw new RuntimeException(ex);
        }
      });
    }
  }

  private static DataSource createDataSource(String url, String user, String password) throws SQLException {
    PoolDataSource pds = PoolDataSourceFactory.getPoolDataSource();
    pds.setConnectionFactoryClassName("oracle.jdbc.pool.OracleDataSource");
    pds.setURL(url);
    if (user != null) pds.setUser(user);
    if (password != null) pds.setPassword(password);
    pds.setInitialPoolSize(1);
    pds.setMinPoolSize(1);
    pds.setConnectionWaitTimeout(10);
    pds.setConnectionProperty("remarksReporting", "true");
    pds.setConnectionProperty("oracle.jdbc.vectorDefaultGetObjectType", "double[]");
    pds.setConnectionProperty("oracle.jdbc.jsonDefaultGetObjectType", "java.lang.String");
    return pds;
  }

  /**
   * <p>
   *   Executes the provided {@link LogAnalyzerTools.ThrowingSupplier ThrowingSupplier} action,
   *   which may throw an {@link Exception}, and returns the resulting {@link McpSchema.CallToolResult}.
   *   <br>
   *   If the action executes successfully, its {@link McpSchema.CallToolResult} is returned as-is.
   *   If any exception is thrown, this method returns a {@link McpSchema.CallToolResult}
   *   with the exception message added as {@link McpSchema.TextContent} and {@code isError} set to {@code true}.
   * </p>
   *
   * <p>
   *   This utility method provides standardized error handling and result formatting for methods that may throw exceptions,
   *   ensuring that errors are consistently reported back to the MCP server.
   * </p>
   *
   * @param action The supplier action to execute, which may throw an {@link Exception} and returns a {@link McpSchema.CallToolResult}.
   * @return The result of the supplier if successful, or an error {@link McpSchema.CallToolResult} if an exception occurs.
   */
  public static McpSchema.CallToolResult tryCall(ThrowingSupplier<McpSchema.CallToolResult> action) {
    try {
      return action.get();
    } catch (Exception e) {
      return McpSchema.CallToolResult.builder()
          .addTextContent("Unexpected: " + e.getMessage())
          .isError(true)
          .build();
    }
  }

  @FunctionalInterface
  public interface ThrowingSupplier<T> {
    T get() throws Exception;
  }

  /**
   * Loads external JARs from the directory given by
   * the system property {@code ojdbc.ext.dir} and makes them available
   * to the application at runtime.
   *
   * <p>Behavior:</p>
   * <ul>
   *   <li>If the property is missing/blank, does nothing.</li>
   *   <li>Recursively scans the directory for {@code .jar} files.</li>
   *   <li>Adds all found JARs to a temporary class loader and activates it.</li>
   *   <li>Logs basic problems (invalid dir, scan failures, no JARs found).</li>
   * </ul>
   *
   */
  static void installExternalExtensionsFromDir() {
    final String dir = LoadedConstants.OJDBC_EXT_DIR;
    if (dir == null || dir.isBlank()) {
      return;
    }

    final Path root = Paths.get(dir);
    if (!Files.isDirectory(root)) {
      LOG.warning("[oracle-db-toolbox-mcp-server] ojdbc.ext.dir is not a directory: " + dir);
      return;
    }
    final List<URL> jarUrls = new ArrayList<>();
    try (Stream<Path> walk = Files.walk(root)) {
      walk.filter(p -> Files.isRegularFile(p) && p.toString().toLowerCase(Locale.ROOT).endsWith(".jar"))
          .forEach(p -> {
            try {
              jarUrls.add(p.toUri().toURL());
            } catch (Exception e) {
              LOG.log(Level.WARNING, "[oracle-db-toolbox-mcp-server] Failed to add jar: " + p, e);
            }
          });
    } catch (Exception e) {
      LOG.log(Level.WARNING, "[oracle-db-toolbox-mcp-server] Failed to scan " + dir, e);
      return;
    }

    if (jarUrls.isEmpty()) {
      LOG.warning("[oracle-db-toolbox-mcp-server] No jars found under " + dir);
      return;
    }

    final ClassLoader previousTccl = Thread.currentThread().getContextClassLoader();
    final URLClassLoader ucl = new URLClassLoader(jarUrls.toArray(new URL[0]), previousTccl);
    Thread.currentThread().setContextClassLoader(ucl);

    try {
      Class<?> providerClass = Class.forName("oracle.security.pki.OraclePKIProvider", true, ucl);
      Provider provider = (Provider) providerClass.getDeclaredConstructor().newInstance();
      Security.addProvider(provider);
    } catch (Throwable ignored) {}

    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      try { Thread.currentThread().setContextClassLoader(previousTccl); } catch (Throwable ignored) {}
      try { ucl.close(); } catch (Throwable ignored) {}
    }));
  }

  /**
   * Converts a ResultSet into a list of maps (rows).
   *
   * @param rs a valid ResultSet
   * @return list of rows with column:value mapping
   * @throws SQLException if reading from ResultSet fails
   */
  static List<Map<String, Object>> rsToList(ResultSet rs) throws SQLException {
    List<Map<String, Object>> out = new ArrayList<>();
    ResultSetMetaData md = rs.getMetaData();
    int cols = md.getColumnCount();
    while (rs.next()) {
      Map<String, Object> row = new LinkedHashMap<>();
      for (int i = 1; i <= cols; i++) {
        String colName = md.getColumnLabel(i);
        Object value = rs.getObject(i);

        if (value instanceof Clob clob) {
          value = clobToString(clob);
        }

        row.put(colName, value);
      }
      out.add(row);
    }
    return out;
  }

  /**
   * Safely converts a CLOB to String.
   */
  private static String clobToString(Clob clob) throws SQLException {
    if (clob == null)
      return null;
    StringBuilder sb = new StringBuilder();
    try (Reader reader = clob.getCharacterStream()) {
      char[] buf = new char[4096];
      int len;
      while ((len = reader.read(buf)) != -1) {
        sb.append(buf, 0, len);
      }
    } catch (IOException e) {
      throw new SQLException("Failed to read CLOB", e);
    }
    return sb.toString();
  }

  private static boolean isToolEnabled(ServerConfig config, String toolName) {
    if (config.toolsFilter == null) {
      return true;
    }
    String key = toolName.toLowerCase(Locale.ROOT);
    return config.toolsFilter.contains(key);
  }

}