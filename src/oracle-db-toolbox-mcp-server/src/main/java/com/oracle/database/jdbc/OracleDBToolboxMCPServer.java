package com.oracle.database.jdbc;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.jdbc.oauth.OAuth2Configuration;
import com.oracle.database.jdbc.web.AuthorizationFilter;
import com.oracle.database.jdbc.web.RedirectOAuthToOpenIDServlet;
import com.oracle.database.jdbc.web.WebUtils;
import com.oracle.database.jdbc.web.WellKnownServlet;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.server.transport.HttpServletStreamableServerTransportProvider;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;

import org.apache.catalina.Context;
import org.apache.catalina.startup.Tomcat;
import org.apache.tomcat.util.descriptor.web.FilterDef;
import org.apache.tomcat.util.descriptor.web.FilterMap;

import javax.sql.DataSource;

import java.io.File;
import java.util.logging.Logger;

import static com.oracle.database.jdbc.Utils.installExternalExtensionsFromDir;

public class OracleDBToolboxMCPServer {
  private static final Logger LOG = Logger.getLogger(OracleDBToolboxMCPServer.class.getName());

  static ServerConfig config;

  static {
    config = Utils.loadConfig();
  }

  /**
   * Injects a custom {@link javax.sql.DataSource} used by all tools
   * to obtain connections.
   * <p>Call this before {@link #main(String[])} to override the default
   * configuration-based data source.</p>
   *
   * @param ds the data source to use for all DB operations
   */
  public static void useDataSource(DataSource ds) {
    Utils.useDataSource(ds);
  }

  public static void main(String[] args) {
    installExternalExtensionsFromDir();

    final String transportKind = System.getProperty("transport", "stdio")
      .trim()
      .toLowerCase();

    McpSyncServer server;

    switch (transportKind) {
      case "http" -> {
        server = startHttpServer();
      }
      case "stdio" -> {
        server = McpServer
          .sync(new StdioServerTransportProvider(new ObjectMapper()))
          .serverInfo("oracle-db-toolbox-mcp-server", "1.0.0")
          .capabilities(McpSchema.ServerCapabilities.builder()
             .tools(true)
             .logging()
             .build())
          .immediateExecution(true)
          .build();
      }
      default -> throw new IllegalArgumentException(
              "Unsupported transport: " + transportKind + " (expected 'stdio' or 'http')");
    }
    Utils.addSyncToolSpecifications(server, config);
  }

  private OracleDBToolboxMCPServer() {
    // Prevent instantiation
  }

  /**
   * Start HTTP Streamable MCP transport on /mcp using Tomcat.
   */
  private static McpSyncServer startHttpServer() {
    try {
      int port = Integer.parseInt(System.getProperty("http.port", "45450"));

      HttpServletStreamableServerTransportProvider transport =
              HttpServletStreamableServerTransportProvider.builder()
                      .objectMapper(new ObjectMapper())
                      .mcpEndpoint("/mcp")
                      .build();

      McpSyncServer server = McpServer
        .sync(transport)
        .serverInfo("oracle-db-toolbox-mcp-server", "1.0.0")
        .capabilities(McpSchema.ServerCapabilities.builder()
           .tools(true)
           .logging()
           .build())
        .immediateExecution(true)
        .build();

      Tomcat tomcat = new Tomcat();
      tomcat.setPort(port);
      tomcat.getConnector();

      String ctxPath = "";
      String docBase = new File(".").getAbsolutePath();
      Context ctx = tomcat.addContext(ctxPath, docBase);

      Tomcat.addServlet(ctx, "mcpServlet", transport);
      ctx.addServletMappingDecoded("/mcp/*", "mcpServlet");

      Tomcat.addServlet(ctx, "wellKnownServlet", new WellKnownServlet());
      ctx.addServletMappingDecoded(
              "/.well-known/oauth-protected-resource", "wellKnownServlet");

      if (OAuth2Configuration.getInstance().isOAuth2Configured() && WebUtils.isRedirectOpenIDToOAuthEnabled()) {
        Tomcat.addServlet(ctx, "redirectOAuthToOpenIDServlet", new RedirectOAuthToOpenIDServlet());
        ctx.addServletMappingDecoded("/.well-known/oauth-authorization-server", "redirectOAuthToOpenIDServlet");
      }

      FilterDef filterDef = new FilterDef();
      filterDef.setFilterName("authFilter");
      filterDef.setFilter(new AuthorizationFilter());
      filterDef.setFilterClass(AuthorizationFilter.class.getName());
      ctx.addFilterDef(filterDef);

      FilterMap filterMap = new FilterMap();
      filterMap.setFilterName("authFilter");
      filterMap.addURLPattern("/mcp/*");
      ctx.addFilterMap(filterMap);

      tomcat.start();

      LOG.info(() -> "[oracle-db-toolbox-mcp-server] HTTP transport started on " + port + " (endpoint: /mcp)");

      return server;
    } catch (Exception e) {
      throw new RuntimeException("Failed to start HTTP/streamable server", e);
    }
  }

}
