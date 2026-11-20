/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.web;

import com.oracle.database.mcptoolkit.LoadedConstants;
import jakarta.servlet.http.HttpServletRequest;

import java.net.URI;
import java.net.URISyntaxException;
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
   * Resolves the protected resource identifier without changing a configured value.
   * A configured identifier may include a public path prefix or query component.
   *
   * @param request the servlet request used only when the configured value is absent or blank
   * @param configuredResourceUrl the optional externally visible MCP resource identifier
   * @return the configured identifier, or the existing request-derived default
   */
  static String resolveMcpResourceUrl(
      final HttpServletRequest request, final String configuredResourceUrl) {
    if (configuredResourceUrl != null && !configuredResourceUrl.isBlank()) {
      return configuredResourceUrl;
    }
    return buildURLFromRequest(request) + "/mcp";
  }

  /**
   * Validates an optional public metadata URL before it is advertised in a challenge.
   * No network lookup or URL normalization is performed.
   *
   * @param configuredUrl an ASCII HTTPS URI, or an absent/blank value
   * @return the unchanged configured URL, or null to retain the request-derived default
   * @throws IllegalArgumentException if a nonblank value is not a valid public metadata URL
   */
  static String validateMcpResourceMetadataUrl(final String configuredUrl) {
    if (configuredUrl == null || configuredUrl.isBlank()) {
      return null;
    }
    if (configuredUrl.chars().anyMatch(c -> c <= 0x20 || c >= 0x7f)) {
      throw invalidMcpResourceMetadataUrl();
    }
    try {
      final URI uri = new URI(configuredUrl);
      final int port = uri.getPort();
      if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null
          || uri.getRawUserInfo() != null || uri.getRawFragment() != null
          || (port != -1 && (port < 1 || port > 65535))) {
        throw invalidMcpResourceMetadataUrl();
      }
    } catch (URISyntaxException e) {
      throw invalidMcpResourceMetadataUrl();
    }
    return configuredUrl;
  }

  private static IllegalArgumentException invalidMcpResourceMetadataUrl() {
    return new IllegalArgumentException(
      "mcp.oauth.resourceMetadataUrl must be an absolute ASCII HTTPS URL "
        + "without user-info or a fragment, and with a valid port");
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
   * system property {@code auth.openIdDiscoveryRedirectEnabled}. If the property is set to
   * "true" (case-insensitive), the method returns {@code true}; otherwise,
   * it returns {@code false}. If the property is not set, it defaults to {@code false}.
   *
   * @return {@code true} if redirection from OpenID to OAuth is enabled, {@code false} otherwise
   */
  public static boolean isRedirectOpenIDToOAuthEnabled() {
    return Boolean.parseBoolean(LoadedConstants.AUTH_OPENID_DISCOVERY_REDIRECT_ENABLED);
  }

}
