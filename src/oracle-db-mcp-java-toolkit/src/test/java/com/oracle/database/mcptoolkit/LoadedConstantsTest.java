/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;

import com.oracle.database.mcptoolkit.config.RuntimeConfigRoot;
import java.io.StringReader;
import java.util.Map;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.yaml.snakeyaml.Yaml;

class LoadedConstantsTest {
  @AfterEach
  void resetConstants() {
    for (String property : new String[] {
        "transport", "network.transport", "https.port", "network.https.port", "db.user", "database.user",
        "db.password", "database.password", "http.allowedOriginalHosts", "network.http.allowedOriginalHosts",
        "http.allowUnauthenticatedForDevelopment", "network.http.allowUnauthenticatedForDevelopment",
        "auth.enabled", "userAuth.enabled", "allowedHosts", "network.cors.allowedOrigin",
        "editTools.requireScope", "toolAuthorization.editTools.requireScope",
        "deepsec.enabled", "deepDataSecurity.enabled", "deepsec.databaseToken.tokenEndpoint",
        "deepDataSecurity.databaseToken.tokenEndpoint"
    }) {
      System.clearProperty(property);
    }
    LoadedConstants.initialize(null);
  }

  @Test
  void loadsRuntimeSettingsFromYamlProperties() {
    RuntimeConfigRoot root = RuntimeConfigRoot.fromProperties(Map.of(
        "network.transport", "HTTP", "database.user", "yaml-user", "database.password", "yaml-password",
        "toolAuthorization.editTools.requireScope", "false"));

    LoadedConstants.initialize(root);

    assertEquals("http", LoadedConstants.TRANSPORT_KIND);
    assertEquals("yaml-user", LoadedConstants.DB_USER);
    assertArrayEquals("yaml-password".toCharArray(), LoadedConstants.DB_PASSWORD);
    assertEquals(false, LoadedConstants.EDIT_TOOLS_REQUIRE_SCOPE);
  }

  @Test
  void systemPropertiesOverrideYamlProperties() {
    RuntimeConfigRoot root = RuntimeConfigRoot.fromProperties(Map.of(
        "network.transport", "stdio", "database.user", "yaml-user"));
    System.setProperty("transport", "http");
    System.setProperty("database.user", "system-user");

    LoadedConstants.initialize(root);

    assertEquals("http", LoadedConstants.TRANSPORT_KIND);
    assertEquals("system-user", LoadedConstants.DB_USER);
  }

  @Test
  void parsesNestedRuntimeSettingsFromYaml() {
    RuntimeConfigRoot root = RuntimeConfigRoot.fromYaml(new Yaml().load(new StringReader("""
        network:
          transport: http
          http:
            allowedOriginalHosts: mcp.example.com
          https:
            port: \"45451\"
          cors:
            allowedOrigin: mcp.example.com
        database:
          user: ${DB_USER}
        toolSelection:
          enabled: read-query
        userAuth:
          enabled: true
        deepDataSecurity:
          enabled: true
        """)));

    root.properties().put("database.user", "yaml-user");
    LoadedConstants.initialize(root);

    assertEquals("http", LoadedConstants.TRANSPORT_KIND);
    assertEquals("mcp.example.com", LoadedConstants.HTTP_ALLOWED_ORIGINAL_HOSTS);
    assertEquals("45451", LoadedConstants.HTTPS_PORT);
    assertEquals("yaml-user", LoadedConstants.DB_USER);
    assertEquals("read-query", LoadedConstants.TOOLS);
    assertEquals(true, LoadedConstants.AUTH_ENABLED);
    assertEquals("mcp.example.com", LoadedConstants.CORS_ALLOWED_ORIGIN);
    assertEquals(true, LoadedConstants.DEEPSEC_ENABLED);
  }

  @Test
  void loadsHttpSecurityAndDeepSecSettingsFromYamlProperties() {
    RuntimeConfigRoot root = RuntimeConfigRoot.fromProperties(Map.of(
        "network.http.allowedOriginalHosts", "mcp.example.com",
        "network.http.allowUnauthenticatedForDevelopment", "true", "userAuth.enabled", "true",
        "deepDataSecurity.enabled", "true",
        "deepDataSecurity.databaseToken.tokenEndpoint", "https://identity.example.com/token"));

    LoadedConstants.initialize(root);

    assertEquals("mcp.example.com", LoadedConstants.HTTP_ALLOWED_ORIGINAL_HOSTS);
    assertEquals(true, LoadedConstants.HTTP_ALLOW_UNAUTHENTICATED_FOR_DEVELOPMENT);
    assertEquals(true, LoadedConstants.AUTH_ENABLED);
    assertEquals(true, LoadedConstants.DEEPSEC_ENABLED);
    assertEquals("https://identity.example.com/token", LoadedConstants.DEEPSEC_DATABASE_TOKEN_ENDPOINT);
  }

  @Test
  void canonicalSystemPropertiesOverrideLegacyAliasesWithoutMutation() {
    RuntimeConfigRoot root = RuntimeConfigRoot.fromProperties(Map.of("database.user", "yaml-user"));
    System.setProperty("db.user", "legacy-user");
    System.setProperty("database.user", "canonical-user");

    LoadedConstants.initialize(root);

    assertEquals("canonical-user", LoadedConstants.DB_USER);
    assertEquals("canonical-user", System.getProperty("database.user"));
    assertEquals("legacy-user", System.getProperty("db.user"));
  }

}
