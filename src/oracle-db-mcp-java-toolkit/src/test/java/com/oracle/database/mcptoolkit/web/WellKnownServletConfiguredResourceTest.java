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
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class WellKnownServletConfiguredResourceTest {
  private static final String RESOURCE = "https://mcp.example.test/public/mcp";
  private static final String AUTHORIZATION_SERVER = "https://auth.example.test";

  @Test
  void advertisesConfiguredResourceAndAuthorizationServer() throws Exception {
    // Configuration is static, so use a fresh JVM independent of other tests.
    Process process = new ProcessBuilder(
        Path.of(System.getProperty("java.home"), "bin", "java").toString(),
        "-Dauth.enabled=true",
        "-Dauth.userTokenValidation.mode=jwt",
        "-Dauth.userTokenValidation.jwt.issuer=" + AUTHORIZATION_SERVER,
        "-Dauth.userTokenValidation.jwt.jwksUri=" + AUTHORIZATION_SERVER + "/jwks",
        "-Dauth.userTokenValidation.jwt.audience=configured-resource-test",
        "-Dauth.authorizationServer=" + AUTHORIZATION_SERVER,
        "-Dauth.openIdDiscoveryRedirectEnabled=false",
        "-Dmcp.oauth.resourceUrl=" + RESOURCE,
        "-cp", System.getProperty("surefire.test.class.path",
                                  System.getProperty("java.class.path")),
        WellKnownServletConfiguredResourceTest.class.getName())
        .redirectError(ProcessBuilder.Redirect.INHERIT)
        .start();
    try {
      assertTrue(process.waitFor(20, TimeUnit.SECONDS), "Servlet probe did not exit");
      assertEquals(0, process.exitValue(), "Servlet probe failed");
      String output = new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
      JsonNode metadata = new ObjectMapper().readTree(output);
      assertEquals(RESOURCE, metadata.path("resource").asText());
      assertEquals(AUTHORIZATION_SERVER, metadata.path("authorization_servers").get(0).asText());
    } finally {
      if (process.isAlive()) {
        process.destroyForcibly();
        assertTrue(process.waitFor(5, TimeUnit.SECONDS), "Servlet probe did not stop");
      }
    }
  }

  public static void main(String[] args) throws Exception {
    HttpServletRequest request = (HttpServletRequest) Proxy.newProxyInstance(
        WellKnownServletConfiguredResourceTest.class.getClassLoader(),
        new Class<?>[]{HttpServletRequest.class},
        (proxy, method, arguments) -> switch (method.getName()) {
          case "getHeader" -> null;
          case "getScheme" -> "http";
          case "getServerName" -> "127.0.0.1";
          case "getServerPort" -> 18080;
          default -> throw new UnsupportedOperationException(method.getName());
        });
    StringWriter body = new StringWriter();
    int[] status = {0};
    HttpServletResponse response = (HttpServletResponse) Proxy.newProxyInstance(
        WellKnownServletConfiguredResourceTest.class.getClassLoader(),
        new Class<?>[]{HttpServletResponse.class},
        (proxy, method, arguments) -> switch (method.getName()) {
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
