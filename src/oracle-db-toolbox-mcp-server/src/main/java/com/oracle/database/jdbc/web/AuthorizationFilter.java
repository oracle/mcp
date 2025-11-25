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
        errorHeader(httpResponse);
        return;
      }

      final String token = authHeader.substring("Bearer ".length()).trim();
      if (!VALIDATOR.isTokenValid(token)) {
        errorHeader(httpResponse);
        return;
      }
    }

    // token is valid
    chain.doFilter(request, response);
  }

  private void errorHeader(HttpServletResponse httpResponse) throws IOException {
    final var serverURL = System.getProperty("serverURL", "http://localhost:45450");
    final var resourceMetadataURL = serverURL + "/.well-known/oauth-protected-resource";

    httpResponse.setHeader("WWW-Authenticate",
      "Bearer error=\"invalid_request\", " +
        "error_description=\"No access token was provided in this request\", " +
        "resource_metadata=\"" + resourceMetadataURL + "\"");
    httpResponse.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
    final String json = """
            {
                "error": "invalid_request",
                "error_description": "Access token is invalid or not present in this request",
                "resource_metadata": "%s"
            }
            """.formatted(resourceMetadataURL);
    httpResponse.getWriter()
      .write(json);
  }

}
