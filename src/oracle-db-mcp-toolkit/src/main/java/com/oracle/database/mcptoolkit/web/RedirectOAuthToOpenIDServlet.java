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
 * Servlet responsible for redirecting OAuth requests to the OpenID configuration endpoint.
 * <p>
 * This servlet handles HTTP GET requests and redirects the client to the OpenID configuration endpoint
 * specified in the OAuth2 configuration.
 */
public class RedirectOAuthToOpenIDServlet extends HttpServlet {

  /**
   * Handles HTTP GET requests by redirecting the client to the OpenID configuration endpoint.
   * <p>
   * The redirect URL is constructed using the authentication server URL from the OAuth2 configuration.
   * <p>
   * The response includes an "Access-Control-Allow-Origin" header with the allowed hosts.
   *
   * @param request  the HTTP request
   * @param response the HTTP response
   * @throws ServletException if a servlet-specific error occurs
   * @throws IOException      if an I/O error occurs
   */
  @Override
  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
    final String redirectLink = OAuth2Configuration.getInstance().getAuthServer() +
      "/.well-known/openid-configuration";

    response.addHeader("Access-Control-Allow-Origin", WebUtils.getAllowedHosts());
    response.sendRedirect(redirectLink);
  }
}
