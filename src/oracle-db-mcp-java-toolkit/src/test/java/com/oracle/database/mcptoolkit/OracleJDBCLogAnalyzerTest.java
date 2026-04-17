package com.oracle.database.mcptoolkit;

import com.oracle.database.mcptoolkit.tools.LogAnalyzerTools;
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
    tools = LogAnalyzerTools.getTools()
      .stream()
      .map(SyncToolSpecification::tool)
      .collect(Collectors.toMap(McpSchema.Tool::name, identity()));
  }

  @ParameterizedTest
  @ValueSource(strings = {
    "jdbc-analyzer",
    "rdbms-analyzer"
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

}