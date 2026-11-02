/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */
package com.oracle.database.mcptoolkit.web;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class WellKnownServletRedirectAuthorizationServerTest {
  private static final String RESOURCE = "https://mcp.example.test/public/mcp";
  private static final String IDP = "https://auth.example.test";
  private static final String REQUEST_BASE = "http://foreign.example.test:18080";

  @Test
  void configuredResourceUsesConfiguredAuthorizationServerWithForeignHost() throws Exception {
    assertMetadata(RESOURCE, true, RESOURCE, IDP);
  }

  @Test
  void configuredResourceWithQueryAndTrailingSlashUsesConfiguredAuthorizationServer() throws Exception {
    String configured = RESOURCE + "/?version=1";
    assertMetadata(configured, true, configured, IDP);
  }

  @Test
  void absentResourceRetainsRedirectFacadeAtRequestOrigin() throws Exception {
    assertMetadata(null, true, REQUEST_BASE + "/mcp", REQUEST_BASE);
  }

  @Test
  void blankResourceRetainsRedirectFacadeAtRequestOrigin() throws Exception {
    assertMetadata("   ", true, REQUEST_BASE + "/mcp", REQUEST_BASE);
  }

  @Test
  void redirectDisabledRetainsConfiguredAuthorizationServer() throws Exception {
    assertMetadata(RESOURCE, false, RESOURCE, IDP);
  }

  private void assertMetadata(String configuredResource, boolean redirect,
                              String expectedResource, String expectedAuthorizationServer) throws Exception {
    // Configuration is loaded statically, so each case has its own JVM.
    List<String> command = new ArrayList<>(List.of(
        Path.of(System.getProperty("java.home"), "bin", "java").toString(),
        "-Dauth.enabled=true", "-Dauth.userTokenValidation.mode=jwt",
        "-Dauth.userTokenValidation.jwt.issuer=" + IDP,
        "-Dauth.userTokenValidation.jwt.jwksUri=" + IDP + "/jwks",
        "-Dauth.userTokenValidation.jwt.audience=configured-as-test",
        "-Dauth.authorizationServer=" + IDP,
        "-Dauth.openIdDiscoveryRedirectEnabled=" + redirect));
    if (configuredResource != null) {
      command.add("-Dmcp.oauth.resourceUrl=" + configuredResource);
    }
    command.addAll(List.of("-cp", System.getProperty("surefire.test.class.path",
        System.getProperty("java.class.path")), getClass().getName()));
    Process process = new ProcessBuilder(command).redirectError(ProcessBuilder.Redirect.INHERIT).start();
    try {
      assertTrue(process.waitFor(20, TimeUnit.SECONDS), "Servlet probe did not exit");
      assertEquals(0, process.exitValue(), "Servlet probe failed");
      JsonNode metadata = new ObjectMapper().readTree(
          new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8));
      assertEquals(expectedResource, metadata.path("resource").asText());
      assertEquals(expectedAuthorizationServer, metadata.path("authorization_servers").get(0).asText());
    } finally {
      if (process.isAlive()) {
        process.destroyForcibly();
        assertTrue(process.waitFor(5, TimeUnit.SECONDS), "Servlet probe did not stop");
      }
    }
  }

  public static void main(String[] args) throws Exception {
    HttpServletRequest request = (HttpServletRequest) Proxy.newProxyInstance(
        WellKnownServletRedirectAuthorizationServerTest.class.getClassLoader(),
        new Class<?>[]{HttpServletRequest.class}, (proxy, method, arguments) -> switch (method.getName()) {
          case "getHeader" -> "Host".equals(arguments[0]) ? "foreign.example.test:18080" : null;
          case "getScheme" -> "http";
          case "getServerName" -> "foreign.example.test";
          case "getServerPort" -> 18080;
          default -> throw new UnsupportedOperationException(method.getName());
        });
    StringWriter body = new StringWriter();
    int[] status = {0};
    HttpServletResponse response = (HttpServletResponse) Proxy.newProxyInstance(
        WellKnownServletRedirectAuthorizationServerTest.class.getClassLoader(),
        new Class<?>[]{HttpServletResponse.class}, (proxy, method, arguments) -> switch (method.getName()) {
          case "setContentType", "addHeader" -> null;
          case "setStatus" -> { status[0] = (int) arguments[0]; yield null; }
          case "getWriter" -> new PrintWriter(body);
          default -> throw new UnsupportedOperationException(method.getName());
        });
    new WellKnownServlet().doGet(request, response);
    if (status[0] != HttpServletResponse.SC_OK) {
      throw new IllegalStateException("Expected metadata status 200, got " + status[0]);
    }
    System.out.print(body);
  }
}
