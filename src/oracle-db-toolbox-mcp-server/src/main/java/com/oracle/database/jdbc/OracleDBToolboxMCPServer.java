package com.oracle.database.jdbc;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.jdbc.config.ConfigRoot;
import com.oracle.database.jdbc.config.SourceConfig;
import com.oracle.database.jdbc.config.ToolConfig;
import com.oracle.database.jdbc.config.ToolParameterConfig;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;
import org.yaml.snakeyaml.Yaml;

import java.io.Reader;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.List;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

import static com.oracle.database.jdbc.Utils.errorResult;
import static com.oracle.database.jdbc.Utils.installExternalExtensionsFromDir;
import static com.oracle.database.jdbc.Utils.rsToList;

public class OracleDBToolboxMCPServer {

  static ServerConfig config;
  private static final ObjectMapper JSON = new ObjectMapper();

  static {
    String configFilePath = System.getProperty("configFile");
    ConfigRoot yamlConfig = null;
    try {
      try (Reader reader = Files.newBufferedReader(Paths.get(configFilePath))) {
        Yaml yaml = new Yaml();
        yamlConfig = yaml.loadAs(reader, ConfigRoot.class);
      }
    } catch (Exception e) {
      Logger logger = Logger.getLogger(OracleDBToolboxMCPServer.class.getName());
      logger.log(Level.SEVERE, e.getMessage());
    }
    if (yamlConfig == null) {
      config = ServerConfig.fromSystemProperties();
    } else {
      String defaultSourceKey = yamlConfig.sources.keySet().stream().findFirst().orElseThrow();
      config = ServerConfig.fromSystemPropertiesAndYaml(yamlConfig, defaultSourceKey);
      if (config.tools != null) {
        for (Map.Entry<String, ToolConfig> entry : config.tools.entrySet()) {
          entry.getValue().name = entry.getKey();
        }
      }
    }
  }

  private static final String SQL_ONLY = """
      {
        "type":"object",
        "properties": {
          "sql": {
            "type": "string"
            },
          "txId": {
            "type": "string",
            "description": "Optional active transaction id"
            }
          },
          "required":["sql"]
      }""";

  public static void main(String[] args) {
    installExternalExtensionsFromDir();

    McpSyncServer server = McpServer.sync(new StdioServerTransportProvider(new ObjectMapper()))
        .serverInfo("ojdbc-log-analyzer-mcp-server", "1.0.0")
        .capabilities(McpSchema.ServerCapabilities.builder()
            .tools(true)
            .logging()
            .build())
        .build();
    addSyncToolSpecifications(server);
  }

  private OracleDBToolboxMCPServer() {
    // Prevent instantiation
  }

  /**
   * <p>
   *   Returns the list of all available SyncToolSpecification instances for this server.
   * </p>
   */
  public static void addSyncToolSpecifications(McpSyncServer server) {
    // ---------- Dynamically Added Tools ----------
    for (Map.Entry<String, ToolConfig> entry : config.tools.entrySet()) {
      ToolConfig tc = entry.getValue();
      server.addTool(
          McpServerFeatures.SyncToolSpecification.builder()
              .tool(McpSchema.Tool.builder()
                  .name(tc.name)
                  .title(tc.name)
                  .description(tc.description)
                  .inputSchema(SQL_ONLY)
                  .build()
              )
              .callHandler((exchange, callReq) -> {
                // Resolve source
                SourceConfig src = config.sources.get(tc.source);
                String jdbcUrl = (src != null) ? src.toJdbcUrl() : config.dbUrl;
                String dbUser = (src != null) ? src.user : config.dbUser;
                String dbPassword = (src != null) ? src.password : config.dbPassword;

                // Obtain a connection for this invocation
                try (Connection c = DriverManager.getConnection(jdbcUrl, dbUser, dbPassword)) {
                  // Prepare statement and parameters
                  PreparedStatement ps = c.prepareStatement(tc.statement);
                  // map callReq.arguments() to tc.parameters
                  int paramIdx = 1;
                  if (tc.parameters != null) {
                    for (ToolParameterConfig param : tc.parameters) {
                      Object argVal = callReq.arguments().get(param.name);
                      ps.setObject(paramIdx++, argVal);
                    }
                  }

                  if (tc.statement.trim().toLowerCase().startsWith("select")) {
                    ResultSet rs = ps.executeQuery();
                    List<Map<String,Object>> rows = rsToList(rs);
                    return McpSchema.CallToolResult.builder()
                        .structuredContent(Map.of("rows", rows, "rowCount", rows.size()))
                        .addTextContent(JSON.writeValueAsString(rows))
                        .build();
                  } else {
                    int n = ps.executeUpdate();
                    return McpSchema.CallToolResult.builder()
                        .structuredContent(Map.of("updateCount", n))
                        .addTextContent("{\"updateCount\":" + n + "}")
                        .build();
                  }
                } catch (Exception ex) {
                  return errorResult(tc.name, ex);
                }
              })
              .build()
      );
    }
    List<McpServerFeatures.SyncToolSpecification> specs = OracleJDBCLogAnalyzerMCPServer.getLogAnalyzerTools();
    for (McpServerFeatures.SyncToolSpecification spec : specs) {
      server.addTool(spec);
    }
  }

}
