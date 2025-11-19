/*
 ** Oracle JDBC Log Analyzer MCP Server version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.jdbc;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpServerFeatures.SyncToolSpecification;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;
import io.modelcontextprotocol.spec.McpSchema.Tool;
import io.modelcontextprotocol.spec.McpSchema.CallToolResult;
import io.modelcontextprotocol.spec.McpSchema.TextContent;
import oracle.jdbc.logs.analyzer.JDBCLog;
import oracle.jdbc.logs.analyzer.RDBMSLog;
import oracle.jdbc.logs.model.JDBCConnectionEvent;
import oracle.jdbc.logs.model.JDBCExecutedQuery;
import oracle.jdbc.logs.model.LogError;
import oracle.jdbc.logs.model.RDBMSError;
import oracle.jdbc.logs.model.RDBMSPacketDump;

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
public final class OracleJDBCLogAnalyzerMCPServer {

  public static void main(String[] args) {
    McpServer.sync(new StdioServerTransportProvider(new ObjectMapper()))
      .serverInfo("ojdbc-log-analyzer-mcp-server", "1.0.0")
      .capabilities(McpSchema.ServerCapabilities.builder()
        .tools(true)
        .logging()
        .build())
      .tools(getSyncToolSpecifications())
      .build();
  }

  private static final String FILE_PATH = "filePath";
  private static final String SECOND_FILE_PATH = "secondFilePath";
  private static final String CONNECTION_ID = "connectionId";
  private static final String FILE_PATH_SCHEMA = """
            {
              "type": "object",
              "properties": {
                "filePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the Oracle JDBC log file."
                }
              },
              "required": ["filePath"]
            }
            """;
  private static final String FILE_COMPARISON_SCHEMA = """
            {
              "type": "object",
              "properties": {
                "filePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the 1st Oracle JDBC log file"
                },
                "secondFilePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the 2nd Oracle JDBC log file"
                }
              },
              "required": ["filePath", "secondFilePath"]
            }
            """;
  private static final String RDBMS_TOOLS_SCHEMA = """
            {
              "type": "object",
              "properties": {
                "filePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the RDBMS/SQLNet trace file"
                },
                "connectionId": {
                  "type": "string",
                  "description": "Connection ID string"
                }
              },
              "required": ["filePath", "connectionId"]
            }
            """;

  private OracleJDBCLogAnalyzerMCPServer() {
    // Prevent instantiation
  }

  /**
   * <p>
   *   Returns the list of all available SyncToolSpecification instances for this server.
   * </p>
   */
  public static List<SyncToolSpecification> getSyncToolSpecifications() {
    return List.of(
      buildGetStatsTool(),
      buildGetQueriesTool(),
      buildGetErrorsTool(),
      buildListLogsDirectoryTool(),
      buildGetConnectionEventsTool(),
      buildLogComparisonTool(),
      buildGetRdbmsErrorsTool(),
      buildGetPacketDumpsTool());
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification}
   *   for the {@code get-stats} tool, which retrieves high-level statistics from an Oracle JDBC thin log file.
   *   The tool gathers information such as error count, the number of sent and
   *   received packets, and byte counts from the specified log file.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-stats} tool.
   */
  private static SyncToolSpecification buildGetStatsTool() {
    return SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
        .name("get-stats")
        .title("Get JDBC Log Stats")
        .description("Return aggregated stats (error count, packets, bytes) from an Oracle JDBC thin log.")
        .inputSchema(FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> tryCall( () -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var stats = new JDBCLog(filePath).getStats();
        return stats.toJSONString();
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code get-queries} tool.
   *   This tool extracts all executed SQL queries from an Oracle JDBC thin log file.
   *   For each query, it provides the corresponding timestamp, execution time, connection id and tenant.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-queries} tool.
   */
  private static SyncToolSpecification buildGetQueriesTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
          .name("get-queries")
          .description("Get all executed queries from an Oracle JDBC thin log file, including the timestamp and execution time.")
          .inputSchema(FILE_PATH_SCHEMA)
          .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var queries = new JDBCLog(filePath).getQueries();
        return queries.stream()
          .map(JDBCExecutedQuery::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
      }))
      .build();
  }


  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the <code>get-errors</code> tool.
   *   This tool processes a specified Oracle JDBC thin log file and extracts all reported errors.
   *   Each error record includes details such as the stack trace and additional log context.
   * </p>
   * `
   * @return a {@link SyncToolSpecification SyncToolSpecification} representing the <code>get-errors</code> tool.
   */
  private static SyncToolSpecification buildGetErrorsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-errors")
        .description("Get all reported errors from an Oracle JDBC thin log file, including stacktrace and log context.")
        .inputSchema(FILE_PATH_SCHEMA)
        .build())
    .callHandler((exchange, callReq) -> tryCall(() -> {
      final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var errors = new JDBCLog(filePath).getLogErrors();
        return errors.stream()
          .map(LogError::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
      }))
      .build();
  }


  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code get-log-files-from-directory} tool.
   *   This tool lists all Oracle JDBC log files present in the specified directory path.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} for the {@code get-log-files-from-directory} tool.
   */
  private static SyncToolSpecification buildListLogsDirectoryTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-log-files-from-directory")
        .description("List all Oracle JDBC log files from the specified directory.")
        .inputSchema(FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        final var directoryPath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var directory = new File(directoryPath);
        final var files = directory.listFiles();
        if (files == null || files.length == 0) {
          throw new IOException("No files found in the specified directory.");
        }
        return Arrays.stream(files)
          .filter(file -> !file.isHidden() && file.isFile())
          .map(File::getName)
          .collect(Collectors.joining(",", "[", "]"));
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code log-comparison} tool.
   *   This tool enables comparison of two Oracle JDBC log files. It analyzes the specified log files and provides a JSON report
   *   highlighting differences and similarities in performance metrics, encountered errors, and network-related information.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance that defines the {@code log-comparison} tool.
   */
  private static SyncToolSpecification buildLogComparisonTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("log-comparison")
        .description("Compare two JDBC log files for performance metrics, errors, and network information.")
        .inputSchema(FILE_COMPARISON_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var secondFilePath = String.valueOf(callReq.arguments().get(SECOND_FILE_PATH));
        final var comparison = new JDBCLog(filePath).compareTo(secondFilePath);
        return comparison.toJSONString();
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the {@code get-connection-events} tool.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-connection-events} tool.
   */
  private static SyncToolSpecification buildGetConnectionEventsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-connection-events")
        .description("Retrieve opened and closed JDBC connection events from the log file with timestamp and connection details.")
        .inputSchema(FILE_PATH_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var events = new JDBCLog(filePath).getConnectionEvents();
        return events.stream()
          .map(JDBCConnectionEvent::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
      })).build();
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
  private static SyncToolSpecification buildGetRdbmsErrorsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-rdbms-errors")
        .description("Retrieve errors from an RDBMS/SQLNet trace file.")
        .inputSchema(RDBMS_TOOLS_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        final var logFile = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var errors = new RDBMSLog(logFile).getErrors();
        return errors.stream()
          .map(RDBMSError::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
      }))
      .build();
  }

  /**
   * <p>
   *   Builds and returns a {@link SyncToolSpecification SyncToolSpecification} for the <code>get-packet-dumps</code> tool.
   *   This tool extracts packet dump information from a specified RDBMS/SQLNet trace file that matches a given connection ID.
   *   Each packet dump record includes its associated details and is serialized in JSON format.
   * </p>
   *
   * @return a {@link SyncToolSpecification SyncToolSpecification} instance for the {@code get-packet-dumps} tool.
   */
  private static SyncToolSpecification buildGetPacketDumpsTool() {
    return SyncToolSpecification.builder()
      .tool(Tool.builder()
        .name("get-packet-dumps")
        .description("Extract packet dumps from RDBMS/SQLNet trace file for given connection ID.")
        .inputSchema(RDBMS_TOOLS_SCHEMA)
        .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        final var filePath = String.valueOf(callReq.arguments().get(FILE_PATH));
        final var connId = String.valueOf(callReq.arguments().get(CONNECTION_ID));
        final var packetDumps = new RDBMSLog(filePath).getPacketDumps(connId);
        return packetDumps.stream()
          .map(RDBMSPacketDump::toJSONString)
          .collect(Collectors.joining(",", "[", "]"));
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
  private interface ThrowingSupplier<T> {
    /**
     * Gets a result, potentially throwing an {@link IOException}.
     *
     * @return a result
     * @throws IOException if an I/O error occurs
     */
    T get() throws IOException;
  }


  /**
   * <p>
   *   Executes the given {@link ThrowingSupplier ThrowingSupplier} action that may throw an {@link IOException}
   *   and wraps the result in a {@link CallToolResult CallToolResult}. If the action completes successfully,
   *   the result is returned in a {@link CallToolResult CallToolResult} with {@code isError} set to {@code false}.
   *   If an {@link IOException} is thrown, the exception message is returned as {@link TextContent TextContent}
   *   and {@code isError} is set to {@code true}.
   * </p>
   *
   * <p>
   *   This utility method is used to standardize error handling and result formatting for
   *   methods that perform I/O operations and return responses to the MCP server.
   * </p>
   *
   * @param action The supplier action to execute, which may throw an {@link IOException}.
   * @return a {@link CallToolResult} containing the response and error flag indicating success or failure.
   */
  private static CallToolResult tryCall(ThrowingSupplier<String> action) {
    boolean isError = false;
    String response;
    try {
      response = action.get();
    } catch (IOException e) {
      response = e.getMessage();
      isError = true;
    }

    return CallToolResult.builder()
      .addTextContent(response)
      .isError(isError)
      .build();
  }
}
