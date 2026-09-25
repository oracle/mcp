/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.oauth;

import oracle.jdbc.EndUserSecurityContext;
import oracle.jdbc.spi.EndUserSecurityContextProvider;

import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Request-scoped end-user security context provider used by Oracle JDBC Deep Data Security.
 */
public final class EndUserSecurityContextHolder implements EndUserSecurityContextProvider {
  private static final Logger LOG = Logger.getLogger(EndUserSecurityContextHolder.class.getName());
  private static final ThreadLocal<RequestContext> THREAD_CONTEXT = new ThreadLocal<>();
  private static final String NAME = "oracle-db-mcp-toolkit-end-user-security-context";

  /**
   * Associates a Deep Data Security context and principal with the current request thread.
   *
   * @param context OJDBC end-user security context
   * @param principal validated end-user identity
   */
  public static void set(EndUserSecurityContext context, AuthenticatedPrincipal principal) {
    THREAD_CONTEXT.set(new RequestContext(context, principal));
    LOG.log(Level.FINER, "End-user security context set for current thread");
  }

  /** Sets only the current request's authenticated principal when Deep Data Security is disabled. */
  public static void setPrincipal(AuthenticatedPrincipal principal) {
    THREAD_CONTEXT.set(new RequestContext(null, principal));
  }

  /** Returns the principal associated with the current request thread, or {@code null} when absent. */
  public static AuthenticatedPrincipal getAuthenticatedPrincipal() {
    RequestContext context = THREAD_CONTEXT.get();
    return context == null ? null : context.principal();
  }

  /** Clears the request-scoped identity and OJDBC security context from the current thread. */
  public static void clear() {
    THREAD_CONTEXT.remove();
    LOG.log(Level.FINER, "End-user security context cleared for current thread");
  }

  /** Returns the OJDBC context currently associated with this request thread. */
  @Override
  public EndUserSecurityContext getEndUserSecurityContext(Map<Parameter, CharSequence> parameterValues) {
    RequestContext context = THREAD_CONTEXT.get();
    return context == null ? null : context.endUserSecurityContext();
  }

  /** Returns this provider's stable OJDBC registration name. */
  @Override
  public String getName() {
    return NAME;
  }

  private record RequestContext(
          EndUserSecurityContext endUserSecurityContext,
          AuthenticatedPrincipal principal) {}
}
