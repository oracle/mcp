package com.oracle.database.mcptoolkit.web;

import java.util.stream.Stream;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class WebUtilsResourceMetadataUrlTest {
  @Test
  void absentAndBlankValuesRetainTheDefault() {
    assertNull(WebUtils.validateMcpResourceMetadataUrl(null));
    assertNull(WebUtils.validateMcpResourceMetadataUrl(""));
    assertNull(WebUtils.validateMcpResourceMetadataUrl(" \t\r\n"));
  }

  @ParameterizedTest
  @ValueSource(strings = {
    "https://127.0.0.1:45450/owned/.well-known/oauth-protected-resource",
    "HTTPS://metadata.example.test:8443/discovery?tenant=demo",
    "https://[::1]:443/discovery",
    "https://metadata.example.test:65535/a/../metadata",
    "https://metadata.example.test/m%C3%A9tadata?value=%22safe%22"
  })
  void preservesValidConfiguredUrlsExactly(String configured) {
    assertEquals(configured, WebUtils.validateMcpResourceMetadataUrl(configured));
  }

  @ParameterizedTest
  @MethodSource("invalidUrls")
  void rejectsInvalidConfigurationWithoutEchoingItsValue(String configured) {
    IllegalArgumentException error = assertThrows(
        IllegalArgumentException.class, () -> WebUtils.validateMcpResourceMetadataUrl(configured));
    assertTrue(error.getMessage().contains("mcp.oauth.resourceMetadataUrl"));
    assertFalse(error.getMessage().contains(configured));
  }

  static Stream<String> invalidUrls() {
    return Stream.of(
        "http://127.0.0.1/discovery",
        "/discovery",
        "https:///discovery",
        "https://127.0.0.1/discovery#section",
        "https://fixture:fixture@127.0.0.1/discovery",
        " https://127.0.0.1/discovery",
        "https://127.0.0.1/discovery ",
        "https://127.0.0.1:0/discovery",
        "https://127.0.0.1:65536/discovery",
        "https://127.0.0.1/discovery\n",
        "https://127.0.0.1/dis\rcovery",
        "https://127.0.0.1/discovery\u007f",
        "https://127.0.0.1/m\u00e9tadata",
        "https://127.0.0.1/discovery?value=\"raw\"",
        "https://127.0.0.1/dis\\covery",
        "https://127.0.0.1/discovery?value=\u0080");
  }
}
