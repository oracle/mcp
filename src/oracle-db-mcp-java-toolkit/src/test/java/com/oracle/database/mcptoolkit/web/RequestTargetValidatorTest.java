package com.oracle.database.mcptoolkit.web;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RequestTargetValidatorTest {
  private final RequestTargetValidator validator =
          new RequestTargetValidator("localhost,127.0.0.1,[::1],mcp.example.com");

  @Test
  void allowsRequestsWhenOriginValidationIsNotConfigured() {
    assertTrue(new RequestTargetValidator(null).allows(null));
  }

  @Test
  void rejectsRequestWithoutOrigin() {
    assertFalse(validator.allows(null));
  }

  @Test
  void rejectsUntrustedBrowserOrigin() {
    assertFalse(validator.allows("https://attacker.example"));
  }

  @Test
  void rejectsMalformedOrigin() {
    assertFalse(validator.allows("not an origin"));
  }

  @Test
  void acceptsConfiguredBrowserOrigin() {
    assertTrue(validator.allows("https://mcp.example.com"));
  }
}
