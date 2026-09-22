/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0.
 */

package com.oracle.database.mcptoolkit.tools;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.Duration;

/** Test-only access to the package-private production transaction registry. */
public final class OwnedTransactionTestHarness implements AutoCloseable {
  private final OwnedTransactionRegistry registry = new OwnedTransactionRegistry(
          Duration.ofMinutes(2), Duration.ofMinutes(5), 4);

  public String start(String ownerId, Connection connection) throws SQLException {
    return registry.start(ownerId, connection);
  }

  public <T> T use(String ownerId, String transactionId, SqlAction<T> action) throws Exception {
    try (OwnedTransactionRegistry.Lease lease = registry.acquire(ownerId, transactionId)) {
      return action.execute(lease.connection());
    }
  }

  public void commit(String ownerId, String transactionId) throws SQLException {
    registry.commit(ownerId, transactionId);
  }

  public void rollback(String ownerId, String transactionId) throws SQLException {
    registry.rollback(ownerId, transactionId);
  }

  @Override
  public void close() {
    registry.closeAll();
  }

  @FunctionalInterface
  public interface SqlAction<T> {
    T execute(Connection connection) throws Exception;
  }
}
