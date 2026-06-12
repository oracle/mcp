package com.oracle.database.mcptoolkit.oauth;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;

class OAuth2TokenValidatorTest {
  private static final ObjectMapper MAPPER = new ObjectMapper();

  @Test
  void extractScopesReadsDefaultScopeClaim() throws Exception {
    var json = MAPPER.readTree("""
        {
          "active": true,
          "scope": "mcp:admin mcp:tools:write"
        }
        """);

    assertEquals(
        Set.of("mcp:admin", "mcp:tools:write"),
        OAuth2TokenValidator.extractScopes(json, "scope")
    );
  }

  @Test
  void extractScopesReadsCustomNestedScopeClaim() throws Exception {
    var json = MAPPER.readTree("""
        {
          "active": true,
          "permissions": {
            "scopes": ["mcp:credentials:read", "mcp:admin"]
          }
        }
        """);

    assertEquals(
        Set.of("mcp:credentials:read", "mcp:admin"),
        OAuth2TokenValidator.extractScopes(json, "permissions.scopes")
    );
  }
}
