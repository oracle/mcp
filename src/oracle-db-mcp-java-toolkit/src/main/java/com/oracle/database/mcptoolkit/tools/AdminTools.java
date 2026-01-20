/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.mcptoolkit.LoadedConstants;
import com.oracle.database.mcptoolkit.ServerConfig;
import com.oracle.database.mcptoolkit.Utils;
import com.oracle.database.mcptoolkit.OracleDatabaseMCPToolkit;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.spec.McpSchema;
import org.yaml.snakeyaml.Yaml;

import java.io.Reader;
import java.io.Writer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

import static com.oracle.database.mcptoolkit.Utils.*;

/**
 * Admin/maintenance tools:
 * - list-tools: list all available tools with descriptions
 * - edit-tools: upsert a YAML-defined tool in the config file and rely on runtime reload
 * - read-query: execute SELECT queries and return JSON results
 * - write-query: execute DML/DDL statements
 * - create-table: create table.
 * - delete-table: drop table by name
 * - list-tables: list all tables and synonyms in the current schema
 * - describe-table: get column details for a specific table
 * - start-transaction: begin a new JDBC transaction
 * - resume-transaction: verify a transaction ID is active
 * - commit-transaction: commit and close a transaction
 * - rollback-transaction: rollback and close a transaction
 * - db-ping: check database connectivity and latency
 * - db-metrics-range: retrieve Oracle performance metrics from V$SYSSTAT
 */
public final class AdminTools {

  // Transaction store (txId -> Connection)
  private static final Map<String, Connection> TX = new ConcurrentHashMap<>();


  private AdminTools() {}

  /**
   * Returns all admin tool specifications.
   */
  public static List<McpServerFeatures.SyncToolSpecification> getTools(ServerConfig config) {
    List<McpServerFeatures.SyncToolSpecification> tools = new ArrayList<>();

    tools.add(getListToolsTool(config));
    tools.add(getEditToolsTool(config));
    tools.add(getReadQueryTool(config));
    tools.add(getWriteQueryTool(config));
    tools.add(getCreateTableTool(config));
    tools.add(getDeleteTableTool(config));
    tools.add(getListTablesTool(config));
    tools.add(getDescribeTableTool(config));
    tools.add(getStartTransactionTool(config));
    tools.add(getResumeTransactionTool());
    tools.add(getCommitTransactionTool());
    tools.add(getRollbackTransactionTool());
    tools.add(getDbPingTool(config));
    tools.add(getDbMetricsTool(config));

    // Add shutdown hook to clean up transactions
    Runtime.getRuntime().addShutdownHook(new Thread(() -> {
      TX.values().forEach(conn -> {
        try { if (!conn.getAutoCommit()) conn.rollback(); } catch (Exception ignored) {}
        try { conn.close(); } catch (Exception ignored) {}
      });
      TX.clear();
    }));

    return tools;
  }

  public static McpServerFeatures.SyncToolSpecification getListToolsTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
        .tool(McpSchema.Tool.builder()
            .name("list-tools")
            .title("List Tools")
            .description("List all available tools with their descriptions.")
            .inputSchema(ToolSchemas.NO_INPUT_SCHEMA)
            .build())
        .callHandler((exchange, callReq) -> {
          try {
            // Always use the latest runtime config to avoid requiring a rebuild
            ServerConfig current = OracleDatabaseMCPToolkit.getConfig() != null ? OracleDatabaseMCPToolkit.getConfig() : config;

            List<Map<String, Object>> tools = new ArrayList<>();

            // 1) Built-in log analyzer tools (respect toolsFilter)
            for (McpServerFeatures.SyncToolSpecification spec : LogAnalyzerTools.getTools()) {
              String name = spec.tool().name();
              if (isEnabled(current, name)) {
                tools.add(Map.of(
                    "name", name,
                    "title", spec.tool().title(),
                    "description", spec.tool().description()
                ));
              }
            }

            // 2) Built-in database tools (respect toolsFilter)
            if (isEnabled(current, "similarity_search")) {
              var t = SimilaritySearchTool.getSymilaritySearchTool(current).tool();
              tools.add(Map.of(
                  "name", t.name(),
                  "title", t.title(),
                  "description", t.description()
              ));
            }
            if (isEnabled(current, "explain_plan")) {
              var t = ExplainAndExecutePlanTool.getExplainAndExecutePlanTool(current).tool();
              tools.add(Map.of(
                  "name", t.name(),
                  "title", t.title(),
                  "description", t.description()
              ));
            }

            // 3) Custom YAML tools (always listed if present in config)
            if (current.tools != null) {
              for (Map.Entry<String, com.oracle.database.mcptoolkit.config.ToolConfig> e : current.tools.entrySet()) {
                var tc = e.getValue();
                tools.add(Map.of(
                    "name", tc.name,
                    "title", tc.name,
                    "description", tc.description
                ));
              }
            }

            // 4) Admin tools themselves if enabled
            if (isEnabled(current, "list-tools")) {
              tools.add(Map.of(
                  "name", "list-tools",
                  "title", "List Tools",
                  "description", "List all available tools with their descriptions."
              ));
            }
            if (isEnabled(current, "edit-tools")) {
              tools.add(Map.of(
                  "name", "edit-tools",
                  "title", "Edit/Add Tools",
                  "description", "Create or update YAML-defined tools and trigger live reload."
              ));
            }

            return McpSchema.CallToolResult.builder()
                .structuredContent(Map.of("tools", tools))
                .addTextContent(new ObjectMapper().writeValueAsString(tools))
                .build();
          } catch (Exception e) {
            return McpSchema.CallToolResult.builder()
                .addTextContent("Unexpected: " + e.getMessage())
                .isError(true)
                .build();
          }
        })
        .build();
  }

  public static McpServerFeatures.SyncToolSpecification getEditToolsTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
        .tool(McpSchema.Tool.builder()
            .name("edit-tools")
            .title("Edit/Add Tools")
            .description("Create or update YAML-defined tools in the config file. Changes are auto-reloaded.")
            .inputSchema(ToolSchemas.EDIT_TOOL_SCHEMA)
            .build())
        .callHandler((exchange, callReq) -> {
          try {
            final var cfgPath = LoadedConstants.CONFIG_FILE;
            if (cfgPath == null || cfgPath.isBlank()) {
              return McpSchema.CallToolResult.builder()
                  .addTextContent("Config file path (configFile) is not set. Cannot edit tools.")
                  .isError(true)
                  .build();
            }

            String name = asString(callReq.arguments().get("name"));
            if (name == null || name.isBlank()) {
              return McpSchema.CallToolResult.builder()
                  .addTextContent("'name' is required")
                  .isError(true)
                  .build();
            }

            Path path = Paths.get(cfgPath);
            Yaml yaml = new Yaml();

            // Load existing YAML into a mutable map
            Map<String, Object> root;
            if (Files.exists(path)) {
              try (Reader r = Files.newBufferedReader(path)) {
                Object loaded = yaml.load(r);
                if (loaded instanceof Map) {
                  //noinspection unchecked
                  root = new LinkedHashMap<>((Map<String, Object>) loaded);
                } else {
                  root = new LinkedHashMap<>();
                }
              }
            } else {
              root = new LinkedHashMap<>();
            }

            // Ensure 'tools' map exists
            Map<String, Object> tools = getOrCreateMap(root, "tools");

            // Remove if requested
            Object removeFlag = callReq.arguments().get("remove");
            boolean remove = (removeFlag instanceof Boolean b && b) ||
                (removeFlag != null && "true".equalsIgnoreCase(String.valueOf(removeFlag)));
            if (remove) {
              if (tools.remove(name) != null) {
                root.put("tools", tools);
                try (Writer w = Files.newBufferedWriter(path)) {
                  yaml.dump(root, w);
                }
                // Try to remove the tool from the running server as well
                try {
                  OracleDatabaseMCPToolkit.getServer().removeTool(name);
                  Utils.unregisterCustomToolLocally(name);
                } catch (Exception ignored) {}

                return McpSchema.CallToolResult.builder()
                    .structuredContent(Map.of(
                        "status", "ok",
                        "message", "Tool '" + name + "' removed from YAML. Reload will occur shortly.",
                        "configFile", cfgPath
                    ))
                    .addTextContent("{\"status\":\"ok\",\"removed\":\"" + name + "\"}")
                    .build();
              } else {
                return McpSchema.CallToolResult.builder()
                    .structuredContent(Map.of(
                        "status", "noop",
                        "message", "Tool '" + name + "' not found; nothing to remove.",
                        "configFile", cfgPath
                    ))
                    .addTextContent("{\"status\":\"noop\",\"missing\":\"" + name + "\"}")
                    .build();
              }
            }

            // Upsert tool entry
            Map<String, Object> t = getOrCreateMap(tools, name);

            // Optional fields
            putIfPresent(t, callReq.arguments(), "description");
            putIfPresent(t, callReq.arguments(), "dataSource");
            putIfPresent(t, callReq.arguments(), "statement");

            // parameters: array of objects
            Object paramsObj = callReq.arguments().get("parameters");
            if (paramsObj instanceof List<?> list) {
              List<Map<String, Object>> params = new ArrayList<>();
              for (Object o : list) {
                if (o instanceof Map<?, ?> m) {
                  Map<String, Object> p = new LinkedHashMap<>();
                  copyIfPresent(m, p, "name");
                  copyIfPresent(m, p, "type");
                  copyIfPresent(m, p, "description");
                  copyIfPresent(m, p, "required");
                  params.add(p);
                }
              }
              t.put("parameters", params);
            }

            tools.put(name, t);
            root.put("tools", tools);

            // Write back YAML
            try (Writer w = Files.newBufferedWriter(path)) {
              yaml.dump(root, w);
            }

            // Try to remove stale instance at runtime (best-effort hot update); server will re-add on reload
            try {
              var srv = OracleDatabaseMCPToolkit.getServer();
              if (srv != null) srv.removeTool(name);
            } catch (Exception ignored) {}


            // The config poller will pick up the change and hot-reload within ~2 seconds.
            return McpSchema.CallToolResult.builder()
                .structuredContent(Map.of(
                    "status", "ok",
                    "message", "Tool '" + name + "' upserted into YAML. Reload will occur shortly.",
                    "configFile", cfgPath
                ))
                .addTextContent("{\"status\":\"ok\",\"name\":\"" + name + "\"}")
                .build();
          } catch (Exception e) {

            return McpSchema.CallToolResult.builder()
                .addTextContent("Unexpected: " + e.getMessage())
                .isError(true)
                .build();
          }
        })
        .build();
  }

  private static McpServerFeatures.SyncToolSpecification getReadQueryTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("read-query")
               .title("Read Query")
               .description("Run a SELECT and return rows as JSON. (Optionally accepts txId to run inside an open transaction.)")
               .inputSchema(ToolSchemas.SQL_ONLY)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              try (ConnLease lease = acquireConnection(config, callReq.arguments().get("txId"))) {
                Connection c = lease.c;
                String sql = String.valueOf(callReq.arguments().get("sql"));
                if (!looksSelect(sql)) {
                  return new McpSchema.CallToolResult("Only SELECT is allowed", true);
                }
                var rows = rsToList(c.createStatement().executeQuery(sql));
                return McpSchema.CallToolResult.builder()
                        .structuredContent(Map.of("rows", rows, "rowCount", rows.size()))
                        .addTextContent(new ObjectMapper().writeValueAsString(rows))
                        .build();
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getWriteQueryTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("write-query")
               .title("Write Query")
               .description("Execute DML (inside a transaction if txId is provided) or DML/DDL in autocommit mode.")
               .inputSchema(ToolSchemas.SQL_ONLY)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              try (ConnLease lease = acquireConnection(config, callReq.arguments().get("txId"))) {
                Connection c = lease.c;
                String sql = String.valueOf(callReq.arguments().get("sql"));
                boolean inTx = !lease.closeOnExit;
                if (inTx && isDdl(sql)) {
                  return new McpSchema.CallToolResult(
                          "DDL is not allowed inside a transaction. Run this statement without txId.", true);
                }
                int n = execUpdate(c, sql);
                return McpSchema.CallToolResult.builder()
                        .structuredContent(Map.of("updateCount", n))
                        .addTextContent("{\"updateCount\":" + n + "}")
                        .build();
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getCreateTableTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("create-table")
               .title("Create Table")
               .description("Create a table from a full CREATE TABLE statement.")
               .inputSchema(ToolSchemas.SQL_ONLY)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              try (Connection c = openConnection(config, null)) {
                String sql = String.valueOf(callReq.arguments().get("sql"));
                execUpdate(c, sql);
                return new McpSchema.CallToolResult("OK", false);
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getDeleteTableTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("delete-table")
               .title("Drop Table")
               .description("Drop a table by name.")
               .inputSchema(ToolSchemas.DROP_OR_DESCRIBE_TABLE)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              try (Connection c = openConnection(config, null)) {
                String table = String.valueOf(callReq.arguments().get("table"));
                int updateCount = execUpdate(c, "DROP TABLE " + quoteIdent(table));
                return McpSchema.CallToolResult.builder()
                        .structuredContent(Map.of("updateCount", updateCount, "table", table))
                        .addTextContent("OK")
                        .build();
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getListTablesTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("list-tables")
               .title("List Tables & Synonyms")
               .description("List TABLE and SYNONYM in the current schema via DatabaseMetaData (includes comments).")
               .inputSchema(ToolSchemas.NO_INPUT_SCHEMA)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              try (Connection c = openConnection(config, null)) {
                DatabaseMetaData md = c.getMetaData();
                String schema = Optional.ofNullable(c.getSchema())
                        .orElseGet(() -> {
                          try {
                            return md.getUserName();
                          } catch (SQLException e) {
                            return null;
                          }
                        });
                if (schema != null)
                  schema = schema.toUpperCase(Locale.ROOT);
                List<Map<String,Object>> tables = new ArrayList<>();
                List<Map<String,Object>> synonyms = new ArrayList<>();
                try (ResultSet rs = md.getTables(null, schema, "%", new String[]{"TABLE", "SYNONYM"})) {
                  while (rs.next()) {
                    Map<String,Object> row = new LinkedHashMap<>();
                    row.put("owner", rs.getString("TABLE_SCHEM"));
                    row.put("name", rs.getString("TABLE_NAME"));
                    row.put("kind", rs.getString("TABLE_TYPE"));
                    row.put("comment", rs.getString("REMARKS"));
                    String kind = String.valueOf(row.get("kind"));
                    if ("SYNONYM".equalsIgnoreCase(kind)) {
                      synonyms.add(row);
                    } else {
                      tables.add(row);
                    }
                  }
                }
                Map<String,Object> payload = Map.of(
                        "schema", schema,
                        "counts", Map.of("tables", tables.size(), "synonyms", synonyms.size()),
                        "tables", tables,
                        "synonyms", synonyms
                );
                return McpSchema.CallToolResult.builder()
                        .structuredContent(payload)
                        .addTextContent(new ObjectMapper().writeValueAsString(payload))
                        .build();
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getDescribeTableTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("describe-table")
               .title("Describe Table")
               .description("Describe columns via DatabaseMetaData. Returns COLUMN_ID, COLUMN_NAME, DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE, NULLABLE, COMMENTS.")
               .inputSchema(ToolSchemas.DROP_OR_DESCRIBE_TABLE)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              try (Connection c = openConnection(config, null)) {
                String table = String.valueOf(callReq.arguments().get("table"));
                if (table == null || table.isBlank()) {
                  return new McpSchema.CallToolResult("Parameter 'table' is required", true);
                }
                DatabaseMetaData md = c.getMetaData();
                String schema = Optional.ofNullable(c.getSchema())
                        .orElseGet(() -> {
                          try {
                            return md.getUserName();
                          } catch (SQLException e) {
                            return null;
                          }
                        });
                if (schema != null)
                  schema = schema.toUpperCase(Locale.ROOT);
                String tableName = table.toUpperCase(Locale.ROOT);
                List<Map<String,Object>> rows = new ArrayList<>();
                try (ResultSet rs = md.getColumns(null, schema, tableName, "%")) {
                  while (rs.next()) {
                    int ordinal = rs.getInt("ORDINAL_POSITION");
                    String colName = rs.getString("COLUMN_NAME");
                    String typeName = rs.getString("TYPE_NAME");
                    int colSize = rs.getInt("COLUMN_SIZE");
                    int precision = rs.getInt("COLUMN_SIZE");
                    int scale = rs.getInt("DECIMAL_DIGITS");
                    int nullableFlag = rs.getInt("NULLABLE");
                    String remarks = rs.getString("REMARKS");
                    String nullableYN = (nullableFlag == DatabaseMetaData.columnNullable) ? "Y" : "N";
                    if (remarks == null)
                      remarks = "";
                    Map<String,Object> row = new LinkedHashMap<>();
                    row.put("COLUMN_ID", ordinal);
                    row.put("COLUMN_NAME", colName);
                    row.put("DATA_TYPE", typeName);
                    row.put("DATA_LENGTH", colSize);
                    row.put("DATA_PRECISION", (scale >= 0 && precision > 0) ? precision : null);
                    row.put("DATA_SCALE", (scale >= 0) ? scale : null);
                    row.put("NULLABLE", nullableYN);
                    row.put("COMMENTS", remarks);
                    rows.add(row);
                  }
                }
                rows.sort(Comparator.comparingInt(m -> ((Number)m.get("COLUMN_ID")).intValue()));
                return McpSchema.CallToolResult.builder()
                        .structuredContent(Map.of("columns", rows))
                        .addTextContent(new ObjectMapper().writeValueAsString(rows))
                        .build();
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getStartTransactionTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("start-transaction")
               .title("Start Transaction")
               .description("Start a JDBC transaction (autoCommit=false). Returns txId.")
               .inputSchema(ToolSchemas.NO_INPUT_SCHEMA)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              Connection c = openConnection(config, null);
              c.setAutoCommit(false);
              String txId = UUID.randomUUID().toString();
              TX.put(txId, c);
              return McpSchema.CallToolResult.builder()
                      .structuredContent(Map.of("txId", txId))
                      .addTextContent("{\"txId\":\"" + txId + "\"}")
                      .build();
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getResumeTransactionTool() {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("resume-transaction")
               .title("Resume Transaction")
               .description("Verify a txId is active (no-op). Returns ok.")
               .inputSchema(ToolSchemas.TX_ID)
               .build())
            .callHandler((exchange, callReq) -> {
              String txId = String.valueOf(callReq.arguments().get("txId"));
              if (TX.containsKey(txId)) {
                return new McpSchema.CallToolResult("{\"ok\":true}", false);
              }
              return new McpSchema.CallToolResult("Unknown txId", true);
            })
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getCommitTransactionTool() {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("commit-transaction")
               .title("Commit Transaction")
               .description("Commit and close a txId.")
               .inputSchema(ToolSchemas.TX_ID)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              String txId = String.valueOf(callReq.arguments().get("txId"));
              Connection c = TX.remove(txId);
              if (c == null)
                return new McpSchema.CallToolResult("Unknown txId", true);
              try (c) {
                c.commit();
                return new McpSchema.CallToolResult("{\"ok\":true}", false);
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getRollbackTransactionTool() {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("rollback-transaction")
               .title("Rollback Transaction")
               .description("Rollback and close a txId.")
               .inputSchema(ToolSchemas.TX_ID)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              String txId = String.valueOf(callReq.arguments().get("txId"));
              Connection c = TX.remove(txId);
              if (c == null)
                return new McpSchema.CallToolResult("Unknown txId", true);
              try (c) {
                c.rollback();
                return new McpSchema.CallToolResult("{\"ok\":true}", false);
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getDbPingTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("db-ping")
               .title("DB Ping")
               .description("Checks connectivity and round-trip latency; returns user, schema, DB name, and version.")
               .inputSchema(ToolSchemas.NO_INPUT_SCHEMA)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              long connStart = System.nanoTime();
              try (Connection c = openConnection(config, null)) {
                long connectMs = (System.nanoTime() - connStart) / 1_000_000L;
                long rtStart = System.nanoTime();
                String user = null, schema = null, dbName = null, dbTime = null;
                try (PreparedStatement ps = c.prepareStatement(SqlQueries.DB_PING_QUERY);
                     ResultSet rs = ps.executeQuery()) {
                  if (rs.next()) {
                    user = rs.getString(1);
                    schema = rs.getString(2);
                    dbName = rs.getString(3);
                    dbTime = rs.getString(4);
                  }
                }
                long roundTripMs = (System.nanoTime() - rtStart) / 1_000_000L;
                DatabaseMetaData md = c.getMetaData();
                Map<String, Object> sc = new LinkedHashMap<>();
                sc.put("ok", true);
                sc.put("connectLatencyMs", connectMs);
                sc.put("roundTripMs", roundTripMs);
                sc.put("dbProduct", md.getDatabaseProductName());
                sc.put("dbVersion", md.getDatabaseProductVersion());
                sc.put("user", user);
                sc.put("schema", schema);
                sc.put("dbName", dbName);
                sc.put("dbTime", dbTime);
                String text = String.format("""
                     OK — connection verified
                     connectLatencyMs: %d
                     roundTripMs: %d
                     dbProduct: %s
                     dbVersion: %s
                     user: %s
                     schema: %s
                     dbName: %s
                     dbTime: %s
                """, connectMs, roundTripMs, md.getDatabaseProductName(),
                        md.getDatabaseProductVersion(), user, schema, dbName, dbTime
                );
                return McpSchema.CallToolResult.builder()
                        .structuredContent(sc)
                        .addTextContent(text)
                        .build();
              }
            }))
            .build();
  }

  private static McpServerFeatures.SyncToolSpecification getDbMetricsTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
               .name("db-metrics-range")
               .title("DB Metrics")
               .description("Returns Oracle DB metrics from V$SYSSTAT (cumulative counters only).")
               .inputSchema(ToolSchemas.NO_INPUT_SCHEMA)
               .build())
            .callHandler((exchange, callReq) -> tryCall(() -> {
              try (Connection c = openConnection(config, null);
                   Statement st = c.createStatement();
                   ResultSet rs = st.executeQuery(SqlQueries.DB_METRICS_RANGE)) {
                var rows = rsToList(rs);
                Map<String, Object> metrics = new LinkedHashMap<>();
                StringBuilder text = new StringBuilder(
                        "Live metrics — V$SYSSTAT (cumulative counters; rates not available):\n"
                );
                for (Map<String, Object> r : rows) {
                  String name = String.valueOf(r.get("NAME"));
                  Object value = r.get("VALUE");
                  metrics.put(name, Map.of("value", value, "unit", ""));
                  text.append("- ").append(name).append(": ").append(value).append("\n");
                }
                return McpSchema.CallToolResult.builder()
                        .structuredContent(Map.of(
                                "source", "V$SYSSTAT",
                                "note", "Cumulative since instance startup; these are totals, not per-second rates.",
                                "metrics", metrics))
                        .addTextContent(text.toString().trim())
                        .build();
              }
            }))
            .build();
  }

  private static boolean isEnabled(ServerConfig config, String toolName) {
    if (config.toolsFilter == null) return true;
    String key = toolName.toLowerCase(Locale.ROOT);
    return config.toolsFilter.contains(key);
  }

  private static String asString(Object v) {
    return v == null ? null : String.valueOf(v);
  }

  @SuppressWarnings("unchecked")
  private static Map<String, Object> getOrCreateMap(Map<String, Object> parent, String key) {
    Object o = parent.get(key);
    if (o instanceof Map<?, ?> m) {
      return new LinkedHashMap<>((Map<String, Object>) m);
    }
    Map<String, Object> created = new LinkedHashMap<>();
    parent.put(key, created);
    return created;
  }

  private static void putIfPresent(Map<String, Object> target, Map<String, Object> source, String key) {
    Object v = source.get(key);
    if (v != null) target.put(key, v);
  }

  private static void copyIfPresent(Map<?, ?> src, Map<String, Object> dst, String key) {
    Object v = src.get(key);
    if (v != null) dst.put(key, v);
  }

  private static int execUpdate(Connection c, String sql) throws SQLException {
    try (Statement st = c.createStatement()) {
      return st.executeUpdate(sql);
    }
  }

  private static class ConnLease implements AutoCloseable {
    final Connection c;
    final boolean closeOnExit;

    ConnLease(Connection c, boolean closeOnExit) {
      this.c = c;
      this.closeOnExit = closeOnExit;
    }

    @Override
    public void close() {
      if (closeOnExit) {
        try { c.close(); } catch (Exception ignored) {}
      }
    }
  }

  private static ConnLease acquireConnection(ServerConfig config, Object txIdArg) throws SQLException {
    String txId = (txIdArg == null) ? null : String.valueOf(txIdArg);
    if (txId == null || txId.isBlank()) {
      Connection c = openConnection(config, null);
      try {
        c.setAutoCommit(true);
      } catch (Exception ignored) {}
      return new ConnLease(c, true);
    }
    Connection c = TX.get(txId);
    if (c == null) throw new SQLException("Unknown txId");
    return new ConnLease(c, false);
  }
}
