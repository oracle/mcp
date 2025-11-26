package com.oracle.database.jdbc.web;

import com.oracle.database.jdbc.oauth.OAuth2Configuration;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;

public class WellKnownServlet extends HttpServlet {
  private static final String ALLOWED_HOSTS = System.getProperty("allowedHosts","*");

  private static final OAuth2Configuration OAUTH2_CONFIG = OAuth2Configuration.getInstance();

  @Override
  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
    if (!OAUTH2_CONFIG.isOAuth2Configured() || !OAUTH2_CONFIG.isAuthenticationEnabled()) {
      response.setStatus(HttpServletResponse.SC_NO_CONTENT);
      return;
    }

    response.setContentType("application/json");
    response.addHeader("Access-Control-Allow-Origin", ALLOWED_HOSTS);
    response.setStatus(HttpServletResponse.SC_OK);
    final String mcpEndpoint = WebUtils.buildURLFromRequest(request) + "/mcp";

    final String json = """
          {
            "resource":"%s",
            "authorization_servers":["%s"]
          }""".formatted(mcpEndpoint, OAUTH2_CONFIG.getAuthServer());
    response.getWriter()
      .write(json);
  }
}
