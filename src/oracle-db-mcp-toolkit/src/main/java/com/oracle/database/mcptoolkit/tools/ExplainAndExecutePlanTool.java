/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.oracle.database.mcptoolkit.ServerConfig;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.spec.McpSchema;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static com.oracle.database.mcptoolkit.Utils.openConnection;
import static com.oracle.database.mcptoolkit.Utils.tryCall;

/**
 * Provides functionality for explaining and executing Oracle SQL plans.
 * This class contains methods to generate execution plans for SQL queries and
 * to explain these plans in a human-readable format.
 */
public class ExplainAndExecutePlanTool {
  /**
   * Returns a tool specification for the "explain_plan" tool.
   * This tool generates an Oracle execution plan for the provided SQL and
   * produces an accompanying LLM prompt to explain and tune the plan.
   *
   * @param config Server configuration
   * @return Tool specification for the "explain_plan" tool
   */
  public static McpServerFeatures.SyncToolSpecification getExplainAndExecutePlanTool(ServerConfig config) {
    return
        McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
                .name("explain_plan")
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

  /**
   * Checks if the provided SQL looks like a SELECT.
   *
   * @param sql the SQL string
   * @return true if it begins with "SELECT" (case-insensitive)
   */
  static boolean looksSelect(String sql) {
    return sql != null && sql.trim().regionMatches(true, 0, "SELECT", 0, 6);
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

  static final Pattern FIRST_WORD = Pattern.compile("^\\s*([A-Za-z0-9_]+)");

  /**
   * DDL detector (CREATE/ALTER/DROP/TRUNCATE/RENAME/COMMENT/GRANT/REVOKE).
   * Used to block DDL inside user-managed transactions.
   */
  static boolean isDdl(String sql) {
    if (sql == null) return false;
    String s = sql.trim().toUpperCase();
    return s.startsWith("CREATE ")
        || s.startsWith("ALTER ")
        || s.startsWith("DROP ")
        || s.startsWith("TRUNCATE ")
        || s.startsWith("RENAME ")
        || s.startsWith("COMMENT ")
        || s.startsWith("GRANT ")
        || s.startsWith("REVOKE ");
  }

  record ExplainResult(String planText) {}

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
}
