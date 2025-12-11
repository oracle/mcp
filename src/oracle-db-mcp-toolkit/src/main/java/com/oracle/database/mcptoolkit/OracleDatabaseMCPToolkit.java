package com.oracle.database.mcptoolkit;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.mcptoolkit.oauth.OAuth2Configuration;
import com.oracle.database.mcptoolkit.web.AuthorizationFilter;
import com.oracle.database.mcptoolkit.web.RedirectOAuthToOpenIDServlet;
import com.oracle.database.mcptoolkit.web.WebUtils;
import com.oracle.database.mcptoolkit.web.WellKnownServlet;
import io.modelcontextprotocol.server.McpServer;
import io.modelcontextprotocol.server.McpSyncServer;
import io.modelcontextprotocol.server.transport.HttpServletStreamableServerTransportProvider;
import io.modelcontextprotocol.server.transport.StdioServerTransportProvider;
import io.modelcontextprotocol.spec.McpSchema;

import org.apache.catalina.Context;
import org.apache.catalina.startup.Tomcat;
import org.apache.tomcat.util.descriptor.web.FilterDef;
import org.apache.tomcat.util.descriptor.web.FilterMap;
import org.apache.catalina.connector.Connector;
import org.apache.tomcat.util.net.SSLHostConfig;
import org.apache.tomcat.util.net.SSLHostConfigCertificate;

import java.io.File;
import java.util.logging.Logger;

import static com.oracle.database.mcptoolkit.Utils.installExternalExtensionsFromDir;

/**
 * The OracleDatabaseMCPToolkit class provides the main entry point for the MCP server.
 * It initializes the configuration, sets up the transport layer, and starts the MCP server.
 */
public class OracleDatabaseMCPToolkit {
  private static final Logger LOG = Logger.getLogger(OracleDatabaseMCPToolkit.class.getName());

  static ServerConfig config;

  static {
    config = Utils.loadConfig();
  }

  public static void main(String[] args) {
    installExternalExtensionsFromDir();

    McpSyncServer server;

    switch (LoadedConstants.TRANSPORT_KIND) {
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
              "Unsupported transport: " + LoadedConstants.TRANSPORT_KIND + " (expected 'stdio' or 'http')");
    }
    Utils.addSyncToolSpecifications(server, config);
  }

  private OracleDatabaseMCPToolkit() {
    // Prevent instantiation
  }

  /**
   * Start HTTP Streamable MCP transport on /mcp using Tomcat.
   */
  private static McpSyncServer startHttpServer() {
    try {
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
      if(LoadedConstants.HTTP_PORT!=null){
        tomcat.setPort(Integer.parseInt(LoadedConstants.HTTP_PORT));
        tomcat.getConnector();
      } else {
        tomcat.setPort(-1);
        LOG.warning("Http setup is skipped: http port is not specified");
      }


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

      if(LoadedConstants.HTTPS_PORT!=null && LoadedConstants.KEYSTORE_PATH!=null && LoadedConstants.KEYSTORE_PASSWORD != null) {
        enableHttps(tomcat, LoadedConstants.KEYSTORE_PATH, LoadedConstants.KEYSTORE_PASSWORD);
      }
      else LOG.warning("SSL setup is skipped: Https port or Keystore path or password not specified");

      tomcat.start();

      LOG.info(() -> "[oracle-db-toolbox-mcp-server] HTTP transport started on " + LoadedConstants.HTTP_PORT + " (endpoint: /mcp)");

      return server;
    } catch (Exception e) {
      throw new RuntimeException("Failed to start HTTP/streamable server", e);
    }
  }

  /**
   * Configures and enables HTTPS on the provided Tomcat server using the specified keystore.
   *
   * @param tomcat          the Tomcat server instance to configure
   * @param keystorePath    the file path to the PKCS12 keystore containing the SSL certificate
   * @param keystorePassword the password for the keystore
   * @throws RuntimeException if the HTTPS connector or SSL configuration fails
   */
  private static void enableHttps(Tomcat tomcat, String keystorePath, String keystorePassword) {
    try {
      // Create HTTPS connector
      Connector https = new Connector("org.apache.coyote.http11.Http11NioProtocol");
      https.setPort(Integer.parseInt(LoadedConstants.HTTPS_PORT));
      https.setSecure(true);
      https.setScheme("https");
      https.setProperty("SSLEnabled", "true");

      // Create SSL config
      SSLHostConfig sslHostConfig = new SSLHostConfig();
      sslHostConfig.setHostName("_default_");

      SSLHostConfigCertificate cert = new SSLHostConfigCertificate(
          sslHostConfig,
          SSLHostConfigCertificate.Type.RSA
      );

      cert.setCertificateKeystoreFile(keystorePath);
      cert.setCertificateKeystorePassword(keystorePassword);
      cert.setCertificateKeystoreType("PKCS12");

      // Attach certificate to SSL config
      sslHostConfig.addCertificate(cert);

      // Enable SSL
      https.addSslHostConfig(sslHostConfig);

      // Register connector
      tomcat.getService().addConnector(https);

    } catch (Exception e) {
      throw new RuntimeException("Failed to enable HTTPS on Tomcat", e);
    }
  }


}
