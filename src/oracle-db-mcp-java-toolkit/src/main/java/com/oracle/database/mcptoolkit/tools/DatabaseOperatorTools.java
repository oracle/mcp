/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.mcptoolkit.ServerConfig;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.spec.McpSchema;

import java.sql.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static com.oracle.database.mcptoolkit.Utils.*;

/**
 * Provides a set of database operator tools for various database operations.
 *
 * <p>The available tools are:</p>
 * <ul>
 *   <li><strong>read-query</strong>: Execute SELECT queries and return JSON results.</li>
 *   <li><strong>write-query</strong>: Execute DML/DDL statements.</li>
 *   <li><strong>create-table</strong>: Create table.</li>
 *   <li><strong>delete-table</strong>: Drop table by name.</li>
 *   <li><strong>list-tables</strong>: List all tables and synonyms in the current schema.</li>
 *   <li><strong>describe-table</strong>: Get column details for a specific table.</li>
 *   <li><strong>start-transaction</strong>: Begin a new JDBC transaction.</li>
 *   <li><strong>resume-transaction</strong>: Verify a transaction ID is active.</li>
 *   <li><strong>commit-transaction</strong>: Commit and close a transaction.</li>
 *   <li><strong>rollback-transaction</strong>: Rollback and close a transaction.</li>
 *   <li><strong>db-ping</strong>: Check database connectivity and latency.</li>
 *   <li><strong>db-metrics-range</strong>: Retrieve Oracle performance metrics from V$SYSSTAT.</li>
 *   <li><strong>explain-plan</strong>: Generate and explain Oracle SQL execution plans (static or dynamic).</li>
 * </ul>
 */
public final class DatabaseOperatorTools {

  // Transaction store (txId -> Connection)
  private static final Map<String, Connection> TX = new ConcurrentHashMap<>();

  private DatabaseOperatorTools() {}

  /**
   * Returns a list of database operator tool specifications based on the provided server configuration.
   * The returned tools are used for various database operations such as executing queries, managing transactions,
   * and retrieving database metrics.
   *
   * <p>The tools returned include:</p>
   * <ul>
   *   <li><strong>read-query</strong>: Execute SELECT queries and return JSON results.</li>
   *   <li><strong>write-query</strong>: Execute DML/DDL statements.</li>
   *   <li><strong>create-table</strong>: Create table.</li>
   *   <li><strong>delete-table</strong>: Drop table by name.</li>
   *   <li><strong>list-tables</strong>: List all tables and synonyms in the current schema.</li>
   *   <li><strong>describe-table</strong>: Get column details for a specific table.</li>
   *   <li><strong>start-transaction</strong>: Begin a new JDBC transaction.</li>
   *   <li><strong>resume-transaction</strong>: Verify a transaction ID is active.</li>
   *   <li><strong>commit-transaction</strong>: Commit and close a transaction.</li>
   *   <li><strong>rollback-transaction</strong>: Rollback and close a transaction.</li>
   *   <li><strong>db-ping</strong>: Check database connectivity and latency.</li>
   *   <li><strong>db-metrics-range</strong>: Retrieve Oracle performance metrics from V$SYSSTAT.</li>
   *   <li><strong>explain-plan</strong>: Generate and explain Oracle SQL execution plans (static or dynamic).</li>
   * </ul>
   *
   * <p>A shutdown hook is added to clean up any active transactions when the JVM shuts down.</p>
   *
   * @param config the server configuration to use for database connections
   * @return a list of tool specifications for database operations
   */
  public static List<McpServerFeatures.SyncToolSpecification> getTools(ServerConfig config) {
    List<McpServerFeatures.SyncToolSpecification> tools = new ArrayList<>();

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
    tools.add(getExplainAndExecutePlanTool(config));

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

  private static McpServerFeatures.SyncToolSpecification getReadQueryTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("read-query")
         .title("Read Query")
         .description("Run a SELECT and return rows as JSON. (Optionally accepts txId to run inside an open transaction.)")
         .inputSchema(ToolSchemas.SQL_ONLY)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (DatabaseOperatorTools.ConnLease lease = acquireConnection(config, callReq.arguments().get("txId"))) {
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
        try (DatabaseOperatorTools.ConnLease lease = acquireConnection(config, callReq.arguments().get("txId"))) {
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

  public static McpServerFeatures.SyncToolSpecification getExplainAndExecutePlanTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("explain-plan")
         .title("Explain Plan (static or dynamic)")
         .description("""
            Returns an Oracle execution plan for the provided SQL.
            mode: "static" (EXPLAIN PLAN) or "dynamic" (DISPLAY_CURSOR of the last execution in this session).
            Response includes: planText (DBMS_XPLAN output) and llmPrompt (ready-to-use for the LLM).
            
            You are an Oracle SQL performance expert. Explain the execution plan to the user in clear language and then provide prioritized, practical tuning advice.
            
            Instructions:
            1) Summarize how the query executes (major steps, joins, access paths).
            2) Point out potential bottlenecks (scans, sorts, joins, TEMP/PGA, cardinality mismatches if present).
            3) Give the top 3–5 tuning ideas with rationale (indexes, predicates, rewrites, stats/histograms, hints if appropriate).
            4) Mention any trade-offs or risks.
            
            Note to model:
            If the sql is a dml operation and it was actually executed No permanent data changes were committed. When explaining the plan, mention this statement will be rolled back
          """)
         .inputSchema(ToolSchemas.EXPLAIN_PLAN)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection c = openConnection(config, null)) {
          final String sql = String.valueOf(callReq.arguments().get("sql"));
          if (sql == null || sql.isBlank()) {
            return new McpSchema.CallToolResult("Parameter 'sql' is required", true);
          }
          final String mode = String.valueOf(callReq.arguments().getOrDefault("mode", "static"))
                  .toLowerCase(Locale.ROOT);
          Boolean executeArg = null;
          Object exObj = callReq.arguments().get("execute");
          if (exObj != null) executeArg = Boolean.parseBoolean(String.valueOf(exObj));

          Integer maxRows = null;
          try {
            Object mr = callReq.arguments().get("maxRows");
            if (mr != null) maxRows = Integer.parseInt(String.valueOf(mr));
          } catch (Exception ignored) {}
           final String xplanOptions = Optional.ofNullable(callReq.arguments().get("xplanOptions"))
                   .map(Object::toString).orElse(null);
           var res = getExplainPlan(
                   c,
                   sql,
                   "dynamic".equals(mode),
                   maxRows,
                   executeArg,
                   xplanOptions
           );
           Map<String, Object> payload = new LinkedHashMap<>();
           payload.put("mode", mode);
           payload.put("sql", sql);
           payload.put("planText", res.planText());

           return McpSchema.CallToolResult.builder()
                   .structuredContent(payload)
                   .addTextContent(res.planText())
                   .build();
        }
      }))
    .build();
  }

  /**
   * Returns an execution plan (static or dynamic) for the given SQL and also produces
   * an accompanying LLM prompt to explain and tune the plan.
   * - static  → EXPLAIN PLAN (no execution, estimated plan only)
   * - dynamic → DISPLAY_CURSOR (requires a real cursor; may lightly execute the SQL)
   *
   * @param c            JDBC connection
   * @param sql          SQL to analyze
   * @param dynamic      true = dynamic plan, false = static plan
   * @param maxRows      limit when lightly executing SELECT (default = 1)
   * @param execute      whether to execute or just parse (null = auto per SQL type)
   * @param xplanOptions DBMS_XPLAN formatting options
   */
  static ExplainResult getExplainPlan(
          Connection c,
          String sql,
          boolean dynamic,
          Integer maxRows,
          Boolean execute,
          String xplanOptions
  ) throws Exception {

    if (!dynamic) {
      try (Statement st = c.createStatement()) {
        st.executeUpdate("EXPLAIN PLAN FOR " + sql);
      }
      String planText = readXplan(c, false, xplanOptions);
      return new ExplainResult(planText);
    }

    // dynamic mode → prepare or execute depending on flags
    runQueryLightweight(c, sql, maxRows, execute);

    String planText = readXplan(c, true, xplanOptions);
    return new ExplainResult(planText);
  }

  /**
   * Prepare or execute a statement lightly so a cursor exists for DISPLAY_CURSOR.
   * Handles SELECT, DML, and DDL safely.
   *
   * @param c open connection
   * @param sql SQL text
   * @param maxRows optional limit (applies to SELECT only)
   * @param execute whether to actually execute (null = smart default)
   */
  private static void runQueryLightweight(Connection c, String sql, Integer maxRows, Boolean execute)
          throws SQLException {

    boolean isSelect = looksSelect(sql);
    boolean doExecute = (execute != null) ? execute : isSelect; // smart default

    if (!doExecute) {
      // just parse (safe)
      try (PreparedStatement ps = c.prepareStatement(sql)) { /* parse only */ }
      return;
    }

    if (isSelect) {
      try (PreparedStatement ps = c.prepareStatement(sql)) {
        ps.setMaxRows((maxRows != null && maxRows > 0) ? maxRows : 1);
        ps.setFetchSize(1);
        try (ResultSet rs = ps.executeQuery()) {
          if (rs.next()) { /* first row only */ }
        }
      }
      return;
    }

    // DML/DDL: execute inside rollback-safe transaction (to minimise side effects)
    boolean prevAutoCommit = c.getAutoCommit();
    try {
      c.setAutoCommit(false);

      String execSql = injectGatherStatsHintAfterVerb(sql);
      try (PreparedStatement ps = c.prepareStatement(execSql)) {
        ps.execute();
      }

      c.rollback();
    } finally {
      c.setAutoCommit(prevAutoCommit);
    }

  }

  /** Read DBMS_XPLAN for either EXPLAIN PLAN or last cursor. */
  private static String readXplan(Connection c, boolean dynamic, String xplanOptions) throws SQLException {
    final String opts = (xplanOptions == null || xplanOptions.isBlank())
            ? (dynamic ? "ALLSTATS LAST +PEEKED_BINDS +OUTLINE +PROJECTION"
            : "BASIC +OUTLINE +PROJECTION +ALIAS")
            : xplanOptions;
    final String q = dynamic
            ? ("SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, '" + opts + "'))")
            : ("SELECT PLAN_TABLE_OUTPUT FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, NULL, '" + opts + "'))");

    StringBuilder sb = new StringBuilder();
    try (Statement st = c.createStatement(); ResultSet rs = st.executeQuery(q)) {
      while (rs.next()) sb.append(Objects.toString(rs.getString(1), "")).append('\n');
    }
    return sb.toString().trim();
  }

  private static final Pattern DML_VERB =
          Pattern.compile("^\\s*(?:--.*?$|/\\*.*?\\*/\\s*)*(UPDATE|DELETE|INSERT|MERGE)\\b",
                  Pattern.CASE_INSENSITIVE | Pattern.DOTALL | Pattern.MULTILINE);

  /** Injects "/*+ gather_plan_statistics +*\/" immediately after the first DML verb.
   * - Preserves leading whitespace and comments
   * - No-op if the SQL already contains the hint (case-insensitive)
   * - Skips if not a DML statement (e.g., SELECT/BEGIN/DECLARE/ALTER/CREATE)
   */
  static String injectGatherStatsHintAfterVerb(String sql) {
    if (sql == null) return null;
    String s = sql.trim();
    if (s.toLowerCase(Locale.ROOT).contains("gather_plan_statistics")) return sql;
    String head = s.length() >= 16 ? s.substring(0, 16).toLowerCase(Locale.ROOT) : s.toLowerCase(Locale.ROOT);
    if (head.startsWith("begin") || head.startsWith("declare") || isDdl(head)) {
      return sql;
    }
    return injectAfterMatch(sql, DML_VERB, "/*+ gather_plan_statistics */", "gather_plan_statistics");
  }

  /**
   * Injects a given string after the first match group found by the pattern,
   * unless the SQL already contains the skip string (case-insensitive).
   *
   * @param sql SQL statement to operate on
   * @param pattern Regex pattern with a capturing group for insertion point
   * @param injection Text to inject
   * @param skipIfContains Injection is skipped if this substring (case-insensitive) is present
   * @return Modified SQL with the injection, or original if no changes made
   */
  private static String injectAfterMatch(
          String sql, Pattern pattern, String injection, String skipIfContains
  ) {
    if (sql == null) return null;
    String s = sql.trim();
    if (s.toLowerCase(Locale.ROOT).contains(skipIfContains.toLowerCase(Locale.ROOT)))
      return sql;
    Matcher m = pattern.matcher(sql);
    if (!m.find()) return sql;
    int start = m.start(1), end = m.end(1);
    String word = sql.substring(start, end);
    StringBuilder out = new StringBuilder(sql.length() + injection.length() + 4);
    out.append(sql, 0, start)
            .append(word)
            .append(" ").append(injection)
            .append(sql.substring(end));
    return out.toString();
  }

  private record ExplainResult(String planText) {}

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

  private static DatabaseOperatorTools.ConnLease acquireConnection(ServerConfig config,
                                               Object txIdArg) throws SQLException {
    String txId = (txIdArg == null) ? null : String.valueOf(txIdArg);
    if (txId == null || txId.isBlank()) {
      Connection c = openConnection(config, null);
      try {
        c.setAutoCommit(true);
      } catch (Exception ignored) {}
      return new DatabaseOperatorTools.ConnLease(c, true);
    }
    Connection c = TX.get(txId);
    if (c == null) throw new SQLException("Unknown txId");
    return new DatabaseOperatorTools.ConnLease(c, false);
  }

}
