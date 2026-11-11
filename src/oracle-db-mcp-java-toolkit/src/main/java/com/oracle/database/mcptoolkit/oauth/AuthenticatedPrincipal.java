/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0.
 */

package com.oracle.database.mcptoolkit.oauth;

import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;

import static java.nio.charset.StandardCharsets.UTF_8;

/** Stable request identity derived from an already validated OAuth access token. */
public record AuthenticatedPrincipal(
        String ownerId,
        String issuer,
        String subject,
        List<String> groups,
        List<String> roles) {
  /**
   * Derives a stable principal from a token that has already passed authentication.
   *
   * <p>Readable JWTs use their issuer and subject claims; opaque tokens use a token-bound fallback.
   *
   * @param token validated access token
   * @return the authenticated principal
   */
  public static AuthenticatedPrincipal fromValidatedToken(String token) {
    if (token == null || token.isBlank()) {
      throw new IllegalArgumentException("Validated access token is required");
    }

    try {
      JWTClaimsSet claims = parseSignedJwtClaims(token);
      if (claims != null) {
        String issuer = text(claims, "iss");
        String subject = text(claims, "sub");
        if (subject != null) {
          return new AuthenticatedPrincipal(
                  fingerprint((issuer == null ? "" : issuer) + "\0" + subject),
                  issuer,
                  subject,
                  groups(claims),
                  roles(claims));
        }
      }
    } catch (Exception ignored) {
      // Opaque tokens and non-standard JWT payloads use a token-bound fallback identity.
    }

    return new AuthenticatedPrincipal(
            fingerprint("token\0" + token), null, null, List.of(), List.of());
  }

  /**
   * Derives an identity for Deep Data Security from a validated JWT access token.
   *
   * <p>Deep Data Security relies on the token's issuer and subject claims for end-user identity.
   * Opaque tokens are deliberately not accepted here: they have no locally readable, stable identity
   * that can be propagated consistently to the database.</p>
   *
   * @param token a validated JWT access token
   * @return the principal represented by the JWT
   * @throws IllegalArgumentException if the token is not a JWT or lacks {@code iss} or {@code sub}
   */
  public static AuthenticatedPrincipal fromValidatedDeepSecJwt(String token) {
    if (token == null || token.isBlank()) {
      throw new IllegalArgumentException("Validated JWT access token is required for Deep Data Security");
    }

    try {
      JWTClaimsSet claims = parseSignedJwtClaims(token);
      String issuer = text(claims, "iss");
      String subject = text(claims, "sub");
      if (issuer == null || subject == null) {
        throw new IllegalArgumentException(
                "Deep Data Security JWT end-user access token must contain iss and sub claims");
      }
      return new AuthenticatedPrincipal(
              fingerprint(issuer + "\0" + subject), issuer, subject, groups(claims), roles(claims));
    } catch (IllegalArgumentException e) {
      throw e;
    } catch (Exception e) {
      throw new IllegalArgumentException("Deep Data Security requires a readable JWT end-user access token", e);
    }
  }

  /** Returns whether this principal was issued by a recognized Microsoft Entra ID issuer. */
  public boolean isAzureIssuer() {
    String host = issuerHost();
    return "login.microsoftonline.com".equals(host) || "sts.windows.net".equals(host);
  }

  /** Returns whether this principal was issued by a recognized OCI IAM issuer. */
  public boolean isOciIssuer() {
    String host = issuerHost();
    return "identity.oraclecloud.com".equals(host) || host.endsWith(".identity.oraclecloud.com");
  }

  private static JWTClaimsSet parseSignedJwtClaims(String token) throws Exception {
    return SignedJWT.parse(token).getJWTClaimsSet();
  }

  private static String text(JWTClaimsSet claims, String name) {
    Object value = claims.getClaim(name);
    return value instanceof String text && !text.isBlank() ? text : null;
  }

  private static List<String> groups(JWTClaimsSet claims) {
    return stringClaim(claims, "group", "groups");
  }

  private static List<String> roles(JWTClaimsSet claims) {
    return stringClaim(claims, "roles");
  }

  private static List<String> stringClaim(JWTClaimsSet claims, String... names) {
    Object value = null;
    for (String name : names) {
      value = claims.getClaim(name);
      if (value != null) {
        break;
      }
    }
    if (value == null) {
      return List.of();
    }
    List<String> groups = new ArrayList<>();
    if (value instanceof List<?> values) {
      values.forEach(group -> {
        if (group instanceof String text && !text.isBlank()) {
          groups.add(text);
        }
      });
    } else if (value instanceof String text && !text.isBlank()) {
      groups.add(text);
    }
    return List.copyOf(groups);
  }

  private String issuerHost() {
    if (issuer == null) {
      return "";
    }
    try {
      java.net.URI uri = java.net.URI.create(issuer);
      return uri.getHost() == null ? "" : uri.getHost().toLowerCase(java.util.Locale.ROOT);
    } catch (IllegalArgumentException ignored) {
      return "";
    }
  }

  private static String fingerprint(String value) {
    try {
      return HexFormat.of().formatHex(
              MessageDigest.getInstance("SHA-256").digest(value.getBytes(UTF_8)));
    } catch (NoSuchAlgorithmException e) {
      throw new IllegalStateException("SHA-256 is unavailable", e);
    }
  }
}
