package com.oracle.database.mcptoolkit;

import com.oracle.database.mcptoolkit.tools.OracleJDBCLogAnalyzer;
import io.modelcontextprotocol.server.McpServerFeatures.SyncToolSpecification;
import io.modelcontextprotocol.spec.McpSchema;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.Map;
import java.util.stream.Collectors;

import static java.util.function.Function.identity;
import static org.junit.jupiter.api.Assertions.*;

@SuppressWarnings("unchecked")
class OracleJDBCLogAnalyzerTest {

  private static Map<String, McpSchema.Tool> tools;

  @BeforeAll
  static void initializeTools(){
    tools = OracleJDBCLogAnalyzer.getLogAnalyzerTools()
      .stream()
      .map(SyncToolSpecification::tool)
      .collect(Collectors.toMap(McpSchema.Tool::name, identity()));
  }

  @ParameterizedTest
  @ValueSource(strings = {
    "get-jdbc-stats",
    "get-jdbc-queries",
    "get-jdbc-errors",
    "list-log-files-from-directory",
    "get-jdbc-connection-events",
    "jdbc-log-comparison",
    "get-rdbms-errors",
    "get-rdbms-packet-dumps"
  })
  void testToolPresence(final String toolName) {
    final var isToolPresent = tools.containsKey(toolName);
    assertTrue(isToolPresent, toolName + " tool should be present.");
  }

  @Test
  void testFilePathParameterInAllTools() {
    for (var tool : tools.values()) {
      final var properties = tool.inputSchema().properties();
      assertTrue(properties.containsKey("filePath"), "Every tool " +
        "should have filePath parameter");

      final var filePathProperty = (Map<String, String>) properties.get("filePath");
      assertEquals("string", filePathProperty.get("type"));
    }
  }

  @Test
  void testSecondFilePathParameterInLogComparisonTool() {
    final var toolProperties = tools.get("jdbc-log-comparison")
      .inputSchema()
      .properties();

    final var isSecondFileParameterPresent = toolProperties.containsKey("filePath");
    assertTrue(isSecondFileParameterPresent, "log-comparison tool " +
      "should have 'secondFilePath' parameter.");

    final var secondFilePathProperty = (Map<String, String>) toolProperties.get("secondFilePath");

    assertEquals("string", secondFilePathProperty.get("type"),
      "The type of 'filePath' and 'secondFilePath' parameters should be 'string'");
  }

  @Test
  void testConnectionIdParameterInGetPacketDumpsTool() {
    final var toolProperties = tools.get("get-rdbms-packet-dumps")
      .inputSchema()
      .properties();

    final var isConnectionIdPresent = toolProperties.containsKey("connectionId");
    assertTrue(isConnectionIdPresent, "log-comparison tool " +
      "should have 'connectionId' parameter.");

    var connectionIdProperty = (Map<String, String>) toolProperties.get("connectionId");

    assertEquals("string", connectionIdProperty.get("type"),
      "The type of 'filePath' and 'secondFilePath' parameters should be 'string'");
  }
}