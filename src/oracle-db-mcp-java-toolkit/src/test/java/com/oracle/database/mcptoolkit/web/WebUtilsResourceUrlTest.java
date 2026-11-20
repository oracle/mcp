package com.oracle.database.mcptoolkit.web;

import jakarta.servlet.http.HttpServletRequest;
import java.lang.reflect.Proxy;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class WebUtilsResourceUrlTest {
  private HttpServletRequest request() {
    return (HttpServletRequest) Proxy.newProxyInstance(
        getClass().getClassLoader(), new Class<?>[]{HttpServletRequest.class},
        (proxy, method, args) -> switch (method.getName()) {
          case "getHeader" -> null;
          case "getScheme" -> "http";
          case "getServerName" -> "127.0.0.1";
          case "getServerPort" -> 18080;
          default -> throw new UnsupportedOperationException(method.getName());
        });
  }

  @Test
  void honorsConfiguredResourceInsteadOfServletOrigin() {
    String configured = "https://127.0.0.1:45450/mcp";
    assertEquals(configured, WebUtils.resolveMcpResourceUrl(request(), configured));
  }

  @Test
  void preservesPublicPathPrefixExactly() {
    String configured = "https://127.0.0.1:45450/owned/mcp";
    assertEquals(configured, WebUtils.resolveMcpResourceUrl(request(), configured));
  }

  @Test
  void preservesQueryAndTrailingSlashExactly() {
    String configured = "https://127.0.0.1:45450/owned/mcp/?version=1";
    assertEquals(configured, WebUtils.resolveMcpResourceUrl(request(), configured));
  }

  @Test
  void doesNotReadRequestWhenConfigured() {
    String configured = "https://127.0.0.1:45450/mcp";
    assertEquals(configured, WebUtils.resolveMcpResourceUrl(null, configured));
  }

  @Test
  void retainsRequestDefaultWhenAbsent() {
    assertEquals("http://127.0.0.1:18080/mcp", WebUtils.resolveMcpResourceUrl(request(), null));
  }

  @Test
  void retainsRequestDefaultWhenBlank() {
    assertEquals("http://127.0.0.1:18080/mcp", WebUtils.resolveMcpResourceUrl(request(), "   "));
  }

  @Test
  void absentConfigurationStillRequiresRequest() {
    assertThrows(NullPointerException.class, () -> WebUtils.resolveMcpResourceUrl(null, null));
  }
}
