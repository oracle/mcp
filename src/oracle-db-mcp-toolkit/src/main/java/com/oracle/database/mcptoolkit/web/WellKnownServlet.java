/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.web;

import com.oracle.database.mcptoolkit.oauth.OAuth2Configuration;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;

/**
 * The WellKnownServlet class handles HTTP GET requests to the well-known endpoint,
 * providing information about the OAuth2 configuration and MCP endpoint.
 *
 */
public class WellKnownServlet extends HttpServlet {
  /**
   * The OAuth2 configuration instance.
   */
  private static final OAuth2Configuration OAUTH2_CONFIG = OAuth2Configuration.getInstance();

  /**
   * Handles HTTP GET requests to the well-known endpoint.
   *
   * If OAuth2 is not configured or authentication is disabled, returns a 204 No Content response.
   * Otherwise, returns a JSON response with the MCP endpoint and authorization server URL.
   *
   * @param request  the HTTP request
   * @param response the HTTP response
   * @throws ServletException if a servlet-specific error occurs
   * @throws IOException      if an I/O error occurs
   */
  @Override
  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
    if (!OAUTH2_CONFIG.isOAuth2Configured() || !OAUTH2_CONFIG.isAuthenticationEnabled()) {
      response.setStatus(HttpServletResponse.SC_NO_CONTENT);
      return;
    }

    response.setContentType("application/json");
    response.addHeader("Access-Control-Allow-Origin", WebUtils.getAllowedHosts());
    response.setStatus(HttpServletResponse.SC_OK);

    final String serverURL = WebUtils.buildURLFromRequest(request);
    final String mcpEndpoint = serverURL + "/mcp";
    String authServer = WebUtils.isRedirectOpenIDToOAuthEnabled() ? serverURL : OAUTH2_CONFIG.getAuthServer();

    final String json = """
          {
            "resource":"%s",
            "authorization_servers":["%s"]
          }""".formatted(mcpEndpoint, authServer);
    response.getWriter()
      .write(json);
  }
}
