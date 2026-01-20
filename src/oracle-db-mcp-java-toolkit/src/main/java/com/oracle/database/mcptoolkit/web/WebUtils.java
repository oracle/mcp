/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.web;

import com.oracle.database.mcptoolkit.LoadedConstants;
import jakarta.servlet.http.HttpServletRequest;

import java.util.Objects;

/**
 * Utility class for web-related operations, such as reading web-related system properties.
 * This class is not intended to be instantiated and provides only static methods.
 */
public class WebUtils {

  private WebUtils() {}

  /**
   * Builds a URL string from the given {@link HttpServletRequest}, considering
   * forwarded protocol headers and default port handling.
   * <p>
   * The method first checks for the {@code X-Forwarded-Proto} header to determine
   * the schema ({@code http} or {@code https}).
   * If the header is missing, empty, or invalid, it falls back to the request's scheme.
   * It then appends the server name and, if necessary, the port number
   * (omitting defaults: 80 for http, 443 for https).
   * </p>
   *
   * @param request the {@link HttpServletRequest} from which to build the URL; must not be null
   * @return a string representing the constructed URL in the format {@code scheme://serverName[:port]}
   * @throws NullPointerException if the request parameter is null
   */
  static String buildURLFromRequest(final HttpServletRequest request) {
    Objects.requireNonNull(request, "request cannot be null");

    final StringBuilder url = new StringBuilder();

    String schema = request.getHeader("X-Forwarded-Proto");
    if (schema == null || schema.isEmpty() ||
      !("http".equalsIgnoreCase(schema) || "https".equalsIgnoreCase(schema)))
      schema = request.getScheme();

    url.append(schema)
      .append("://")
      .append(request.getServerName());

    final int port = request.getServerPort();

    if (!("http".equals(request.getScheme()) && port == 80) &&
      !("https".equals(request.getScheme()) && port == 443))
      url.append(":").append(port);

    return url.toString();
  }

  /**
   * Retrieves the value of the system property {@code allowedHosts}.
   * If the property is not set, it defaults to {@code "*"}.
   *
   * @return the value of the {@code allowedHosts} system property, or {@code "*"} if not set
   */
  static String getAllowedHosts() {
    return LoadedConstants.ALLOWED_HOSTS;
  }

  /**
   * Checks if redirection from OpenID to OAuth is enabled by examining the
   * system property {@code redirectOpenIDToOAuth}. If the property is set to
   * "true" (case-insensitive), the method returns {@code true}; otherwise,
   * it returns {@code false}. If the property is not set, it defaults to {@code false}.
   *
   * @return {@code true} if redirection from OpenID to OAuth is enabled, {@code false} otherwise
   */
  public static boolean isRedirectOpenIDToOAuthEnabled() {
    return Boolean.parseBoolean(LoadedConstants.REDIRECT_OPENID_TO_OAUTH);
  }

}
