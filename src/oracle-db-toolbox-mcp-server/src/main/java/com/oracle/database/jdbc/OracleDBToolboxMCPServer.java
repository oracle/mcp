package com.oracle.database.jdbc;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;

import static com.oracle.database.jdbc.Utils.installExternalExtensionsFromDir;

public class OracleDBToolboxMCPServer {

  static ServerConfig config;

  static {
    config = Utils.loadConfig();
  }

  public static void main(String[] args) {
    installExternalExtensionsFromDir();

    McpSyncServer server = McpServer.sync(new StdioServerTransportProvider(new ObjectMapper()))
        .serverInfo("ojdbc-log-analyzer-mcp-server", "1.0.0")
        .capabilities(McpSchema.ServerCapabilities.builder()
            .tools(true)
            .logging()
            .build())
        .build();
    Utils.addSyncToolSpecifications(server, config);
  }

  private OracleDBToolboxMCPServer() {
    // Prevent instantiation
  }

}
