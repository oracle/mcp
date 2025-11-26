package com.oracle.database.jdbc.web;

import com.oracle.database.jdbc.oauth.OAuth2Configuration;
import com.oracle.database.jdbc.oauth.OAuth2TokenValidator;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;

public class AuthorizationFilter implements Filter {
  private static final OAuth2TokenValidator VALIDATOR = new OAuth2TokenValidator();

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
