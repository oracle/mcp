/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0.
 */

package com.oracle.database.mcptoolkit.oauth;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.util.Base64;
import java.util.List;

import static java.nio.charset.StandardCharsets.UTF_8;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AuthenticatedPrincipalTest {
  @AfterEach
  void clearContext() {
    EndUserSecurityContextHolder.clear();
  }

  @Test
  void derivesStableOwnerFromIssuerAndSubjectAcrossTokens() {
    AuthenticatedPrincipal first = AuthenticatedPrincipal.fromValidatedToken(jwt(
            "{\"iss\":\"https://identity.example\",\"sub\":\"alice\","
                    + "\"group\":[\"CustomerReaders\"]}"));
    AuthenticatedPrincipal refreshed = AuthenticatedPrincipal.fromValidatedToken(jwt(
            "{\"iss\":\"https://identity.example\",\"sub\":\"alice\",\"exp\":9999999999}"));
    AuthenticatedPrincipal bob = AuthenticatedPrincipal.fromValidatedToken(jwt(
            "{\"iss\":\"https://identity.example\",\"sub\":\"bob\"}"));

    assertEquals(first.ownerId(), refreshed.ownerId());
    assertNotEquals(first.ownerId(), bob.ownerId());
    assertEquals("alice", first.subject());
    assertEquals("CustomerReaders", first.groups().get(0));
  }

  @Test
  void usesOnlyStandardSubjectClaimForJwtPrincipals() {
    AuthenticatedPrincipal principal = AuthenticatedPrincipal.fromValidatedToken(jwt(
            "{\"iss\":\"https://identity.example\",\"user_id\":\"alice\",\"username\":\"alice\"}"));

    assertNull(principal.issuer());
    assertNull(principal.subject());
  }

  @Test
  void keepsOnlyPrincipalInRequestHolderWhenDeepSecIsDisabled() {
    AuthenticatedPrincipal principal = AuthenticatedPrincipal.fromValidatedToken("opaque-token");
    EndUserSecurityContextHolder.setPrincipal(principal);

    assertEquals(principal, EndUserSecurityContextHolder.getAuthenticatedPrincipal());
    assertNull(new EndUserSecurityContextHolder().getEndUserSecurityContext(null));
  }

  @Test
  void requiresJwtIssuerAndSubjectForDeepSec() {
    assertThrows(IllegalArgumentException.class,
            () -> AuthenticatedPrincipal.fromValidatedDeepSecJwt("opaque-token"));
    assertThrows(IllegalArgumentException.class,
            () -> AuthenticatedPrincipal.fromValidatedDeepSecJwt(jwt("{\"iss\":\"https://identity.example\"}")));

    AuthenticatedPrincipal principal = AuthenticatedPrincipal.fromValidatedDeepSecJwt(jwt(
            "{\"iss\":\"https://identity.example\",\"sub\":\"alice\","
                    + "\"groups\":[\"CustomerReaders\"]}"));
    assertEquals("alice", principal.subject());
    assertEquals(List.of("CustomerReaders"), principal.groups());
  }

  @Test
  void readsAzureRolesAndIdentifiesAzureAndOciIssuers() {
    AuthenticatedPrincipal azure = AuthenticatedPrincipal.fromValidatedToken(jwt(
            "{\"iss\":\"https://login.microsoftonline.com/tenant/v2.0\","
                    + "\"sub\":\"alice\",\"roles\":[\"DatabaseReader\"]}"));
    AuthenticatedPrincipal oci = AuthenticatedPrincipal.fromValidatedToken(jwt(
            "{\"iss\":\"https://idcs-example.identity.oraclecloud.com/\","
                    + "\"sub\":\"bob\",\"groups\":[\"CustomerReaders\"]}"));

    assertEquals(List.of("DatabaseReader"), azure.roles());
    assertTrue(azure.isAzureIssuer());
    assertTrue(oci.isOciIssuer());
    assertEquals(List.of("CustomerReaders"), oci.groups());
  }

  private String jwt(String payload) {
    Base64.Encoder encoder = Base64.getUrlEncoder().withoutPadding();
    return encoder.encodeToString("{\"alg\":\"RS256\"}".getBytes(UTF_8))
            + "." + encoder.encodeToString(payload.getBytes(UTF_8))
            + ".signature";
  }
}
