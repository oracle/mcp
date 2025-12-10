/*
 ** Oracle JDBC Log Analyzer MCP Server version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.jdbc.tools;

import com.oracle.database.jdbc.Utils;
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
public final class OracleJDBCLogAnalyzer {

  private static final String FILE_PATH = "filePath";
  private static final String SECOND_FILE_PATH = "secondFilePath";
  private static final String CONNECTION_ID = "connectionId";

  public static List<McpServerFeatures.SyncToolSpecification> getLogAnalyzerTools() {
    return List.of(
        getStatsTool(),
        getQueriesTool(),
        getErrorsTool(),
        getListLogsDirectoryTool(),
        getConnectionEventsTool(),
        logComparisonTool(),
        getRdbmsErrorsTool(),
        getPacketDumpsTool());
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification}
   *   for the {@code get-jdbc-stats} tool, which retrieves high-level statistics from an Oracle JDBC thin log file.
   *   The tool gathers information such as error count, the number of sent and
   *   received packets, and byte counts from the specified log file.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-jdbc-stats} tool.
   */
  private static SyncToolSpecification getStatsTool() {
    return SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
        .name("get-jdbc-stats")
        .title("Get JDBC Stats")
        .description("Return aggregated stats (error count, packets, bytes) from an Oracle JDBC thin log.")
        .inputSchema(ToolSchemas.FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall( () -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var stats = new JDBCLog(filePath).getStats();
        return McpSchema.CallToolResult.builder()
            .addTextContent(stats.toJSONString())
            .isError(false)
            .build();
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code get-jdbc-queries} tool.
   *   This tool extracts all executed SQL queries from an Oracle JDBC thin log file.
   *   For each query, it provides the corresponding timestamp, execution time, connection id and tenant.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-jdbc-queries} tool.
   */
  private static SyncToolSpecification getQueriesTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-jdbc-queries")
        .title("Get JDBC Queries")
        .description("Get all executed queries from an Oracle JDBC thin log file, including the timestamp and execution time.")
        .inputSchema(ToolSchemas.FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var queries = new JDBCLog(filePath).getQueries();
        String results = queries.stream()
          .map(JDBCExecutedQuery::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
        return McpSchema.CallToolResult.builder()
            .addTextContent(results)
            .isError(false)
            .build();
      }))
      .build();
  }


  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the <code>get-jdbc-errors</code> tool.
   *   This tool processes a specified Oracle JDBC thin log file and extracts all reported errors.
   *   Each error record includes details such as the stack trace and additional log context.
   * </p>
   * `
   * @return a {@link SyncToolSpecification SyncToolSpecification} representing the <code>get-jdbc-errors</code> tool.
   */
  private static SyncToolSpecification getErrorsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-jdbc-errors")
        .title("Get JDBC Errors")
        .description("Get all reported errors from an Oracle JDBC thin log file, including stacktrace and log context.")
        .inputSchema(ToolSchemas.FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var errors = new JDBCLog(filePath).getLogErrors();
        String results = errors.stream()
          .map(LogError::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
        return McpSchema.CallToolResult.builder()
            .addTextContent(results)
            .isError(false)
            .build();
      }))
      .build();
  }


  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code list-log-files-from-directory} tool.
   *   This tool lists all Oracle JDBC log files present in the specified directory path.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} for the {@code list-log-files-from-directory} tool.
   */
  private static SyncToolSpecification getListLogsDirectoryTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("list-log-files-from-directory")
        .title("List Log Files From Directory")
        .description("List all visible files from a specified directory, which helps the user analyze multiple files with one prompt.")
        .inputSchema(ToolSchemas.FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var directoryPath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var directory = new File(directoryPath);
        final var files = directory.listFiles();
        if (files == null || files.length == 0) {
          throw new IOException("No files found in the specified directory.");
        }
        String results =Arrays.stream(files)
            .filter(file -> !file.isHidden() && file.isFile())
            .map(File::getName)
            .collect(Collectors.joining(",", "[", "]"));

        return McpSchema.CallToolResult.builder()
            .addTextContent(results)
            .isError(false)
            .build();
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code jdbc-log-comparison} tool.
   *   This tool enables comparison of two Oracle JDBC log files. It analyzes the specified log files and provides a JSON report
   *   highlighting differences and similarities in performance metrics, encountered errors, and network-related information.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance that defines the {@code jdbc-log-comparison} tool.
   */
  private static SyncToolSpecification logComparisonTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("jdbc-log-comparison")
        .title("JDBC Log Comparison")
        .description("Compare two JDBC log files for performance metrics, errors, and network information.")
        .inputSchema(ToolSchemas.FILE_COMPARISON_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var secondFilePath = String.valueOf(callReq.arguments().get(SECOND_FILE_PATH));
        final var comparison = new JDBCLog(filePath).compareTo(secondFilePath);
        return McpSchema.CallToolResult.builder()
            .addTextContent(comparison.toJSONString())
            .isError(false)
            .build();
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code get-jdbc-connection-events} tool.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-jdbc-connection-events} tool.
   */
  private static SyncToolSpecification getConnectionEventsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-jdbc-connection-events")
        .title("Get JDBC Connection Events")
        .description("Retrieve opened and closed JDBC connection events from the log file with timestamp and connection details.")
        .inputSchema(ToolSchemas.FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var events = new JDBCLog(filePath).getConnectionEvents();
        String results = events.stream()
          .map(JDBCConnectionEvent::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
        return McpSchema.CallToolResult.builder()
            .addTextContent(results)
            .isError(false)
            .build();
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the <code>get-rdbms-errors</code> tool.
   *   This tool processes a specified Oracle RDBMS/SQLNet trace file to extract all reported errors.
   *   Each extracted error record includes relevant details, such as error messages and context information,
   *   and is serialized in JSON format.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} representing the {@code get-rdbms-errors} tool.
   */
  private static SyncToolSpecification getRdbmsErrorsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-rdbms-errors")
        .title("Get RDBMS/SQLNet Errors")
        .description("Retrieve errors from an RDBMS/SQLNet trace file.")
        .inputSchema(ToolSchemas.RDBMS_TOOLS_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var logFile = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var errors = new RDBMSLog(logFile).getErrors();
        String results = errors.stream()
          .map(RDBMSError::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
        return McpSchema.CallToolResult.builder()
            .addTextContent(results)
            .isError(false)
            .build();
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the <code>get-rdbms-packet-dumps</code> tool.
   *   This tool extracts packet dump information from a specified RDBMS/SQLNet trace file that matches a given connection ID.
   *   Each packet dump record includes its associated details and is serialized in JSON format.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-rdbms-packet-dumps} tool.
   */
  private static SyncToolSpecification getPacketDumpsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-rdbms-packet-dumps")
        .title("Get RDBMS/SQLNet Packet Dumps")
        .description("Extract packet dumps from RDBMS/SQLNet trace file for given connection ID.")
        .inputSchema(ToolSchemas.RDBMS_TOOLS_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> Utils.tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var connId = String.valueOf(callReq.arguments().get(CONNECTION_ID));
        final var packetDumps = new RDBMSLog(filePath).getPacketDumps(connId);
        String results = packetDumps.stream()
          .map(RDBMSPacketDump::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
        return McpSchema.CallToolResult.builder()
            .addTextContent(results)
            .isError(false)
            .build();
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
