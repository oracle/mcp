/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.web;

import com.oracle.database.mcptoolkit.oauth.OAuth2Configuration;
import com.oracle.database.mcptoolkit.oauth.OAuth2TokenValidator;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;

/**
 * The AuthorizationFilter class is a servlet filter that authenticates incoming requests
 * by verifying the presence and validity of an OAuth2 access token in the Authorization header.
 * <p>
 * If OAuth2 authentication is enabled (as determined by OAuth2Configuration), this filter
 * checks the Authorization header for a Bearer token and validates it using an instance of
 * OAuth2TokenValidator. If the token is invalid or missing, it returns a 401 Unauthorized response.
 * </p>
 * <p>
 * The filter delegates to the next filter in the chain if the token is valid or if OAuth2 authentication
 * is disabled.
 * </p>
 */
public class AuthorizationFilter implements Filter {
  /**
   * Validator instance used to verify the validity of OAuth2 access tokens.
   */
  private static final OAuth2TokenValidator VALIDATOR = new OAuth2TokenValidator();

  /**
   * Intercepts incoming requests to authenticate them based on the presence and validity of an OAuth2 access token.
   * <p>
   * If OAuth2 authentication is enabled, it checks the Authorization header for a Bearer token and validates it.
   * If the token is invalid or missing, it returns a 401 Unauthorized response. Otherwise, it delegates to the next filter in the chain.
   * </p>
   *
   * @param request  the servlet request
   * @param response the servlet response
   * @param chain    the filter chain
   * @throws IOException      if an I/O error occurs during the filtering process
   * @throws ServletException if the filter chain fails
   */
  @Override
  public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
    throws IOException, ServletException {
    if (OAuth2Configuration.getInstance().isAuthenticationEnabled()) {
      final HttpServletRequest httpRequest = (HttpServletRequest) request;
      final HttpServletResponse httpResponse = (HttpServletResponse) response;

      final String authHeader = httpRequest.getHeader("Authorization");
      if (authHeader == null || !authHeader.startsWith("Bearer ")) {
        handleError(httpResponse, httpRequest);
        return;
      }

      final String token = authHeader.substring("Bearer ".length()).trim();
      if (!VALIDATOR.isTokenValid(token)) {
        handleError(httpResponse, httpRequest);
        return;
      }
    }

    // token is valid
    chain.doFilter(request, response);
  }

  /**
   * Handles authentication errors by returning a 401 Unauthorized response with a WWW-Authenticate header
   * and a JSON payload containing error details.
   *
   * @param httpResponse the HTTP response
   * @param httpRequest  the HTTP request
   * @throws IOException if an I/O error occurs while writing the response
   */
  private void handleError(HttpServletResponse httpResponse, HttpServletRequest httpRequest) throws IOException {
    final String serverURL = WebUtils.buildURLFromRequest(httpRequest);
    final var resourceMetadataURL = serverURL + "/.well-known/oauth-protected-resource";

    httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
    httpResponse.setHeader("WWW-Authenticate",
      "Bearer error=\"invalid_request\", " +
        "error_description=\"Access token is invalid or not provided in the request\", " +
        "resource_metadata=\"" + resourceMetadataURL + "\"");
    final String json = """
            {
                "error": "invalid_request",
                "error_description": "Access token is invalid or not provided in the request",
                "resource_metadata": "%s"
            }
            """.formatted(resourceMetadataURL);
    httpResponse.getWriter()
      .write(json);
  }

}
