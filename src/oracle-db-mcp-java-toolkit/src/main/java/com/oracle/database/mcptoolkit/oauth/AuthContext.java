/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.oauth;

import java.util.Collections;
import java.util.Set;

/**
 * Request-scoped authentication metadata populated by the HTTP authorization filter.
 */
public final class AuthContext {
  private static final ThreadLocal<AuthenticationInfo> CURRENT = new ThreadLocal<>();

  private AuthContext() {}

  public static void set(AuthenticationInfo authenticationInfo) {
    CURRENT.set(authenticationInfo);
  }

  public static AuthenticationInfo get() {
    return CURRENT.get();
  }

  public static boolean hasScope(String requiredScope) {
    AuthenticationInfo info = get();
    return info != null && info.scopes().contains(requiredScope);
  }

  public static void clear() {
    CURRENT.remove();
  }

  public record AuthenticationInfo(Set<String> scopes) {
    public AuthenticationInfo {
      scopes = scopes == null ? Set.of() : Collections.unmodifiableSet(scopes);
    }
  }
}
