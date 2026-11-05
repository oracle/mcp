/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.config;

import java.util.Map;

/** Resolves legacy runtime property names to the canonical public names. */
public final class RuntimePropertyNames {
  private static final Map<String, String> CANONICAL_NAMES = Map.ofEntries(
      Map.entry("transport", "network.transport"),
      Map.entry("http.port", "network.http.port"),
      Map.entry("http.allowedOriginalHosts", "network.http.allowedOriginalHosts"),
      Map.entry("http.allowUnauthenticatedForDevelopment", "network.http.allowUnauthenticatedForDevelopment"),
      Map.entry("https.port", "network.https.port"),
      Map.entry("certificatePath", "network.https.certificatePath"),
      Map.entry("certificatePassword", "network.https.certificatePassword"),
      Map.entry("tools", "toolSelection.enabled"),
      Map.entry("ingestRootDir", "dataIngestion.rootDirectory"),
      Map.entry("ingestMaxFileSizeMb", "dataIngestion.maxFileSizeMb"),
      Map.entry("db.url", "database.url"), Map.entry("db.user", "database.user"),
      Map.entry("db.password", "database.password"),
      Map.entry("db.transactionIdleTimeoutSeconds", "database.transactions.idleTimeoutSeconds"),
      Map.entry("db.transactionMaxLifetimeSeconds", "database.transactions.maxLifetimeSeconds"),
      Map.entry("db.maxTransactionsPerUser", "database.transactions.maxPerUser"),
      Map.entry("ojdbc.ext.dir", "database.jdbc.extensionsDirectory"),
      Map.entry("auth.enabled", "userAuth.enabled"), Map.entry("allowedHosts", "network.cors.allowedOrigin"),
      Map.entry("auth.authorizationServer", "userAuth.authorizationServer"),
      Map.entry("auth.openIdDiscoveryRedirectEnabled", "userAuth.openIdDiscoveryRedirectEnabled"),
      Map.entry("oauth.scopeClaimPath", "userAuth.tokenValidation.introspection.scopeClaimPath"),
      Map.entry("editTools.requireScope", "toolAuthorization.editTools.requireScope"),
      Map.entry("listCredentials.requireScope", "toolAuthorization.listCredentials.requireScope"),
      Map.entry("deepsec.enabled", "deepDataSecurity.enabled"),
      Map.entry("deepsec.databaseToken.staticValue", "deepDataSecurity.databaseToken.staticValue"),
      Map.entry("deepsec.databaseToken.tokenEndpoint", "deepDataSecurity.databaseToken.tokenEndpoint"),
      Map.entry("deepsec.databaseToken.clientId", "deepDataSecurity.databaseToken.clientId"),
      Map.entry("deepsec.databaseToken.clientSecret", "deepDataSecurity.databaseToken.clientSecret"),
      Map.entry("deepsec.databaseToken.scope", "deepDataSecurity.databaseToken.scope"));

  private RuntimePropertyNames() {}

  public static String canonicalName(String name) {
    String mapped = CANONICAL_NAMES.get(name);
    if (mapped != null) return mapped;
    if (name.startsWith("auth.userTokenValidation.")) {
      return "userAuth.tokenValidation." + name.substring("auth.userTokenValidation.".length());
    }
    return name;
  }
}
