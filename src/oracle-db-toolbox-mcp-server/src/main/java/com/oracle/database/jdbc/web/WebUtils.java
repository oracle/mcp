package com.oracle.database.jdbc.web;

import jakarta.servlet.http.HttpServletRequest;

import java.util.Objects;

/**
 * Utility class for web-related operations, such as URL construction from HTTP requests.
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
}
