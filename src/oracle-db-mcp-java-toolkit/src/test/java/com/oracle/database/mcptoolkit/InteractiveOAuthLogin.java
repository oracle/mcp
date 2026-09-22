/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0.
 */

package com.oracle.database.mcptoolkit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.awt.Desktop;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Duration;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

import static java.nio.charset.StandardCharsets.UTF_8;

/** Interactive authorization-code login used only by the opt-in DeepSec integration test. */
public final class InteractiveOAuthLogin {
  private static final ObjectMapper MAPPER = new ObjectMapper();
  private static final SecureRandom RANDOM = new SecureRandom();

  private InteractiveOAuthLogin() {}

  public static String login(Configuration configuration, String userLabel) throws Exception {
    URI redirectUri = URI.create(configuration.redirectUri());
    validateLoopbackRedirect(redirectUri);

    String state = randomValue();
    String verifier = randomValue();
    String challenge = Base64.getUrlEncoder().withoutPadding().encodeToString(
            MessageDigest.getInstance("SHA-256").digest(verifier.getBytes(UTF_8)));
    CompletableFuture<String> authorizationCode = new CompletableFuture<>();

    HttpServer callbackServer = HttpServer.create(
            new InetSocketAddress(redirectUri.getHost(), redirectPort(redirectUri)), 0);
    callbackServer.createContext(redirectUri.getPath(), exchange ->
            handleCallback(exchange, state, authorizationCode));
    callbackServer.start();
    try {
      URI authorizationUri = authorizationUri(configuration, state, challenge);
      System.out.println("Complete OCI login for " + userLabel + " in the browser:");
      System.out.println(authorizationUri);
      openBrowser(authorizationUri);

      String code = authorizationCode.get(configuration.loginTimeout().toSeconds(), TimeUnit.SECONDS);
      return exchangeCode(configuration, code, verifier);
    } finally {
      callbackServer.stop(0);
    }
  }

  private static URI authorizationUri(
          Configuration configuration, String state, String challenge) {
    Map<String, String> parameters = new LinkedHashMap<>();
    parameters.put("response_type", "code");
    parameters.put("client_id", configuration.clientId());
    parameters.put("redirect_uri", configuration.redirectUri());
    parameters.put("scope", configuration.scopes());
    parameters.put("state", state);
    parameters.put("code_challenge", challenge);
    parameters.put("code_challenge_method", "S256");
    parameters.put("prompt", "login");
    if (!isBlank(configuration.resource())) {
      parameters.put("resource", configuration.resource());
    }
    return URI.create(configuration.authorizationEndpoint() + "?" + formEncode(parameters));
  }

  private static String exchangeCode(
          Configuration configuration, String code, String verifier) throws Exception {
    Map<String, String> parameters = new LinkedHashMap<>();
    parameters.put("grant_type", "authorization_code");
    parameters.put("code", code);
    parameters.put("redirect_uri", configuration.redirectUri());
    parameters.put("client_id", configuration.clientId());
    parameters.put("code_verifier", verifier);
    if (!isBlank(configuration.resource())) {
      parameters.put("resource", configuration.resource());
    }

    String credentials = configuration.clientId() + ":" + configuration.clientSecret();
    HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(configuration.tokenEndpoint()))
            .timeout(Duration.ofSeconds(30))
            .header("Authorization", "Basic " + Base64.getEncoder().encodeToString(credentials.getBytes(UTF_8)))
            .header("Content-Type", "application/x-www-form-urlencoded;charset=UTF-8")
            .header("Accept", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(formEncode(parameters)))
            .build();
    HttpResponse<String> response = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build()
            .send(request, HttpResponse.BodyHandlers.ofString());
    if (response.statusCode() < 200 || response.statusCode() >= 300) {
      throw new IOException("OAuth token exchange failed with HTTP " + response.statusCode());
    }
    JsonNode body = MAPPER.readTree(response.body());
    String accessToken = body.path("access_token").asText(null);
    if (isBlank(accessToken)) {
      throw new IOException("OAuth token exchange did not return an access token");
    }
    return accessToken;
  }

  private static void handleCallback(
          HttpExchange exchange,
          String expectedState,
          CompletableFuture<String> authorizationCode) throws IOException {
    Map<String, String> parameters = parseQuery(exchange.getRequestURI().getRawQuery());
    String error = parameters.get("error");
    String code = parameters.get("code");
    String state = parameters.get("state");
    boolean valid = error == null && code != null && MessageDigest.isEqual(
            expectedState.getBytes(UTF_8), state == null ? new byte[0] : state.getBytes(UTF_8));

    String message = valid
            ? "Authorization received. Return to the integration test."
            : "Authorization failed. Return to the integration test for details.";
    byte[] response = message.getBytes(UTF_8);
    exchange.getResponseHeaders().set("Content-Type", "text/plain;charset=UTF-8");
    exchange.sendResponseHeaders(valid ? 200 : 400, response.length);
    exchange.getResponseBody().write(response);
    exchange.close();

    if (valid) {
      authorizationCode.complete(code);
    } else {
      authorizationCode.completeExceptionally(new IOException(
              error == null ? "OAuth callback state or code was invalid" : "Upstream authorization failed: " + error));
    }
  }

  private static Map<String, String> parseQuery(String query) {
    Map<String, String> values = new LinkedHashMap<>();
    if (query == null || query.isBlank()) {
      return values;
    }
    for (String pair : query.split("&")) {
      String[] parts = pair.split("=", 2);
      values.put(
              URLDecoder.decode(parts[0], UTF_8),
              parts.length == 2 ? URLDecoder.decode(parts[1], UTF_8) : "");
    }
    return values;
  }

  private static String formEncode(Map<String, String> parameters) {
    return parameters.entrySet().stream()
            .map(entry -> URLEncoder.encode(entry.getKey(), UTF_8)
                    + "=" + URLEncoder.encode(entry.getValue(), UTF_8))
            .reduce((left, right) -> left + "&" + right)
            .orElse("");
  }

  private static void openBrowser(URI uri) {
    try {
      if (Desktop.isDesktopSupported() && Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
        Desktop.getDesktop().browse(uri);
        return;
      }
      String os = System.getProperty("os.name", "").toLowerCase();
      String command = os.contains("mac") ? "open" : "xdg-open";
      new ProcessBuilder(command, uri.toString()).start();
    } catch (Exception e) {
      System.out.println("The browser could not be opened automatically; visit the URL above manually.");
    }
  }

  private static void validateLoopbackRedirect(URI redirectUri) {
    String host = redirectUri.getHost();
    if (!"http".equalsIgnoreCase(redirectUri.getScheme())
            || !("localhost".equalsIgnoreCase(host) || "127.0.0.1".equals(host))
            || isBlank(redirectUri.getPath())) {
      throw new IllegalArgumentException(
              "DeepSec integration redirect URI must be an HTTP localhost callback path");
    }
  }

  private static int redirectPort(URI redirectUri) {
    return redirectUri.getPort() == -1 ? 80 : redirectUri.getPort();
  }

  private static String randomValue() {
    byte[] bytes = new byte[32];
    RANDOM.nextBytes(bytes);
    return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
  }

  private static boolean isBlank(String value) {
    return value == null || value.isBlank();
  }

  public record Configuration(
          String authorizationEndpoint,
          String tokenEndpoint,
          String clientId,
          String clientSecret,
          String redirectUri,
          String scopes,
          String resource,
          Duration loginTimeout) {}
}
