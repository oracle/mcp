/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.web;

import com.oracle.database.mcptoolkit.oauth.AuthContext;
import com.oracle.database.mcptoolkit.LoadedConstants;
import com.oracle.database.mcptoolkit.oauth.DeepSecDatabaseTokenProvider;
import com.oracle.database.mcptoolkit.oauth.AuthenticatedPrincipal;
import com.oracle.database.mcptoolkit.oauth.EndUserSecurityContextHolder;
import com.oracle.database.mcptoolkit.oauth.OAuth2Configuration;
import com.oracle.database.mcptoolkit.oauth.OAuth2TokenValidator;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import oracle.jdbc.EndUserSecurityContext;

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
  private static final RequestTargetValidator REQUEST_TARGET_VALIDATOR =
    new RequestTargetValidator(LoadedConstants.HTTP_ALLOWED_ORIGINAL_HOSTS);

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
    final HttpServletRequest httpRequest = (HttpServletRequest) request;
    final HttpServletResponse httpResponse = (HttpServletResponse) response;
    if (!REQUEST_TARGET_VALIDATOR.allows(httpRequest.getHeader("Origin"))) {
      httpResponse.sendError(HttpServletResponse.SC_FORBIDDEN, "Untrusted request origin");
      return;
    }
    if (OAuth2Configuration.getInstance().isAuthenticationEnabled()) {
      final String authHeader = httpRequest.getHeader("Authorization");
      if (authHeader == null || !authHeader.startsWith("Bearer ")) {
        handleError(httpResponse, httpRequest);
        return;
      }

      final String token = authHeader.substring("Bearer ".length()).trim();
      OAuth2TokenValidator.ValidationResult validationResult = VALIDATOR.validateToken(token);
      if (!validationResult.valid()) {
        handleError(httpResponse, httpRequest);
        return;
      }

      AuthContext.set(new AuthContext.AuthenticationInfo(validationResult.scopes()));
      final AuthenticatedPrincipal principal;
      try {
        principal = LoadedConstants.DEEPSEC_ENABLED
          ? AuthenticatedPrincipal.fromValidatedDeepSecJwt(token)
          : AuthenticatedPrincipal.fromValidatedToken(token);
      } catch (IllegalArgumentException e) {
        handleError(httpResponse, httpRequest);
        return;
      }
      if (LoadedConstants.DEEPSEC_ENABLED) {
        try {
          EndUserSecurityContextHolder.set(createEndUserSecurityContext(token), principal);
        } catch (IllegalStateException e) {
          httpResponse.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, e.getMessage());
          return;
        }
      } else {
        EndUserSecurityContextHolder.setPrincipal(principal);
      }
    }

    try {
      // token is valid
      chain.doFilter(request, response);
    } finally {
      AuthContext.clear();
      EndUserSecurityContextHolder.clear();
    }
  }

  private EndUserSecurityContext createEndUserSecurityContext(String endUserToken) {
    return EndUserSecurityContext.createWithToken(
      DeepSecDatabaseTokenProvider.getToken(),
      endUserToken);
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
    final String resourceMetadataURL = serverURL + "/.well-known/oauth-protected-resource";
    final String scopes = LoadedConstants.MCP_OAUTH_SCOPES == null || LoadedConstants.MCP_OAUTH_SCOPES.isBlank()
      ? "openid"
      : LoadedConstants.MCP_OAUTH_SCOPES;

    httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
    httpResponse.setHeader("WWW-Authenticate",
      "Bearer error=\"invalid_request\", " +
        "error_description=\"Access token is invalid or not provided in the request\", " +
        "resource_metadata=\"" + resourceMetadataURL + "\", " +
        "scope=\"" + scopes + "\"");
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
