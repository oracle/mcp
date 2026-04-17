/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.oracle.database.mcptoolkit.Utils;
import com.oracle.database.jdbc.logs.model.JDBCConnectionEvent;
import com.oracle.database.jdbc.logs.model.JDBCExecutedQuery;
import com.oracle.database.jdbc.logs.model.LogError;
import com.oracle.database.jdbc.logs.model.RDBMSError;
import com.oracle.database.jdbc.logs.model.RDBMSPacketDump;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.server.McpServerFeatures.SyncToolSpecification;
import io.modelcontextprotocol.spec.McpSchema;
import io.modelcontextprotocol.spec.McpSchema.Tool;

import com.oracle.database.jdbc.logs.analyzer.JDBCLog;
import com.oracle.database.jdbc.logs.analyzer.RDBMSLog;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/**
 * <p>
 *   This class provides an MCP Server for Oracle JDBC Log Analyzer with tools
 *   to analyze and process Oracle JDBC and RDBMS/SQLNet log files.
 * </p>
 */
public final class LogAnalyzerTools {

  private static final String FILE_PATH = "filePath";
  private static final String SECOND_FILE_PATH = "secondFilePath";
  private static final String CONNECTION_ID = "connectionId";
  private static final String JDBC_ANALYZER_DESCRIPTION = """
          Analyzes Oracle JDBC thin log files and directories.
          Supports the following JDBC actions:
            - stats (aggregated statistics such as errors, packets, bytes).
            - queries (executed SQL queries with timestamp/execution info)
            - errors (reported errors with stack trace/context)
            - connection-events (opened/closed connection events)
            - list-files (list visible files in a directory)
            - compare (compare two JDBC logs and return a JSON report highlighting differences and similarities in performance metrics, encountered errors, and network-related information).
          Returns results serialized in JSON format.
          """;
  private static final String RDBMS_ANALYZER_DESCRIPTION = """
          Analyzes Oracle RDBMS/SQLNet trace files.
          Supports the following RDBMS actions:
            - rdbms-errors (extract all reported errors from an RDBMS/SQLNet trace)
            - packet-dumps (extract packet dump records that match a specified connectionId).
          Each extracted record includes relevant details/context and is returned serialized in JSON format.
          """;

  /**
   * Returns the set of MCP tools exposed by the Oracle JDBC Log Analyzer server.
   *
   * <p>The returned {@link McpServerFeatures.SyncToolSpecification SyncToolSpecification}
   * instances describe the following logical analyzers:</p>
   *
   * <ul>
   *   <li><strong>JDBC analyzer</strong> ({@code jdbc-analyzer}):
   *     <ul>
   *       <li>{@code stats} – retrieves aggregated statistics (for example, errors, packets, bytes)
   *           from an Oracle JDBC thin log file.</li>
   *       <li>{@code queries} – extracts executed SQL statements together with timing/execution
   *           information.</li>
   *       <li>{@code errors} – extracts reported errors, including stack traces and contextual
   *           information.</li>
   *       <li>{@code connection-events} – returns opened and closed JDBC connection events
   *           from the log file.</li>
   *       <li>{@code list-files} – lists the visible log files in a given directory.</li>
   *       <li>{@code compare} – compares two JDBC log files and returns a JSON report that
   *           highlights differences and similarities in performance metrics, encountered errors,
   *           and network‑related information.</li>
   *     </ul>
   *   </li>
   *   <li><strong>RDBMS/SQLNet analyzer</strong> ({@code rdbms-analyzer}):
   *     <ul>
   *       <li>{@code errors} – extracts all reported errors from an RDBMS/SQLNet trace file.</li>
   *       <li>{@code packet-dumps} – extracts packet dump records matching a specified
   *           {@code connectionId}.</li>
   *     </ul>
   *   </li>
   * </ul>
   *
   * <p>All tool results are serialized in JSON format as defined by the individual tool
   * implementations.</p>
   *
   * @return an immutable list containing the JDBC and RDBMS/SQLNet analyzer tool specifications
   *         to be registered with an MCP server
   */
  public static List<McpServerFeatures.SyncToolSpecification> getTools() {
    return List.of(getJDBCAnalyzerTool(), getRDBMSAnalyzerTool());
  }

  private static SyncToolSpecification getJDBCAnalyzerTool() {
    return SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
        .name("jdbc-analyzer")
        .title("Oracle JDBC Log Analyzer")
        .description(JDBC_ANALYZER_DESCRIPTION)
        .inputSchema(ToolSchemas.JDBC_ANALYZER_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall( () -> {
        final var args = callReq.arguments();
        final var action = String.valueOf(args.get("action"));

        return switch (action) {
          case "stats" -> {
            final String filePath = String.valueOf(args.get(FILE_PATH));
            final var stats = new JDBCLog(filePath).getStats();
            yield McpSchema.CallToolResult.builder()
              .addTextContent(stats.toJSONString())
              .isError(false)
              .build();
          }
          case "queries" -> {
            final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
            final var queries = new JDBCLog(filePath).getQueries();
            final var json = queries.stream()
              .map(JDBCExecutedQuery::toJSONString)
              .collect(Collectors.joining(",", "[", "]"));
            yield McpSchema.CallToolResult.builder()
              .addTextContent(json)
              .isError(false)
              .build();
          }
          case "errors" -> {
            final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
            final var errors = new JDBCLog(filePath).getLogErrors();
            final var json = errors.stream()
              .map(LogError::toJSONString)
              .collect(Collectors.joining(",", "[", "]"));
            yield  McpSchema.CallToolResult.builder()
              .addTextContent(json)
              .isError(false)
              .build();
          }
          case "connection-events" -> {
            final var filePath = String.valueOf(args.get(FILE_PATH));
            final var events = new JDBCLog(filePath).getConnectionEvents();
            final var json = events.stream()
              .map(JDBCConnectionEvent::toJSONString)
              .collect(Collectors.joining(",", "[", "]"));

            yield McpSchema.CallToolResult.builder()
              .addTextContent(json)
              .isError(false)
              .build();
          }
          case "compare" -> {
            final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
            final var secondFilePath = String.valueOf(callReq.arguments().get(SECOND_FILE_PATH));
            final var comparison = new JDBCLog(filePath).compareTo(secondFilePath);
            yield McpSchema.CallToolResult.builder()
              .addTextContent(comparison.toJSONString())
              .isError(false)
              .build();
          }
          case "list-files" -> {
            final var directoryPath = String.valueOf(args.get(FILE_PATH));
            final var directory = new File(directoryPath);
            final var files = directory.listFiles();
            if (files == null || files.length == 0)
              throw new IOException("No files found in the specified directory.");

            final var json =Arrays.stream(files)
              .filter(file -> !file.isHidden() && file.isFile())
              .map(File::getName)
              .collect(Collectors.joining(",", "[", "]"));

            yield McpSchema.CallToolResult.builder()
              .addTextContent(json)
              .isError(false)
              .build();
          }
          default -> McpSchema.CallToolResult.builder()
            .addTextContent("Unsupported action: " + action)
            .isError(true)
            .build();
        };
      }))
      .build();
  }



  private static SyncToolSpecification getRDBMSAnalyzerTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("rdbms-analyzer")
        .title("RDBMS/SQLNet Trace Analyzer")
        .description(RDBMS_ANALYZER_DESCRIPTION)
        .inputSchema(ToolSchemas.RDBMS_ANALYZER_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var args = callReq.arguments();
        final var filePath = String.valueOf(args.get(FILE_PATH));
        final var action = String.valueOf(args.get("action"));

        return switch (action) {
          case "errors" -> {
            final var errors = new RDBMSLog(filePath).getErrors();
            final var json = errors.stream()
              .map(RDBMSError::toJSONString)
              .collect(java.util.stream.Collectors.joining(",", "[", "]"));
            yield McpSchema.CallToolResult.builder()
              .addTextContent(json)
              .isError(false)
              .build();
          }
          case "packet-dumps" -> {
            final var connId = String.valueOf(args.get(CONNECTION_ID));
            final var dumps = new RDBMSLog(filePath).getPacketDumps(connId);
            final var json = dumps.stream()
              .map(RDBMSPacketDump::toJSONString)
              .collect(java.util.stream.Collectors.joining(",", "[", "]"));
            yield McpSchema.CallToolResult.builder()
              .addTextContent(json)
              .isError(false)
              .build();
          }
          default -> McpSchema.CallToolResult.builder()
            .addTextContent("Unsupported action: " + action)
            .isError(true)
            .build();
        };
      }))
      .build();
  }

  /**
   * <p>
   *   A functional interface similar to {@link java.util.function.Supplier Supplier}, but allows for throwing an {@link IOException}.
   * </p>
   *
   * @param <T> the type of results supplied by this supplier
   */
  @FunctionalInterface
  public interface ThrowingSupplier<T> {
    /**
     * Gets a result, potentially throwing an {@link IOException}.
     *
     * @return a result
     * @throws IOException if an I/O error occurs
     */
    T get() throws IOException;
  }


}
