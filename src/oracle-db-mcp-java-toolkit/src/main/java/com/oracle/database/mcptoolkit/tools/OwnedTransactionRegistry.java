/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0.
 */

package com.oracle.database.mcptoolkit.tools;

import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;

/** Owns JDBC transactions that span requests and binds each one to one authenticated principal. */
final class OwnedTransactionRegistry {
  private static final String UNKNOWN_TRANSACTION = "Unknown transaction";

  private final Map<String, Entry> entries = new ConcurrentHashMap<>();
  private final Duration idleTimeout;
  private final Duration maximumLifetime;
  private final int maximumPerOwner;
  private final Clock clock;

  OwnedTransactionRegistry(Duration idleTimeout, Duration maximumLifetime, int maximumPerOwner) {
    this(idleTimeout, maximumLifetime, maximumPerOwner, Clock.systemUTC());
  }

  OwnedTransactionRegistry(
          Duration idleTimeout,
          Duration maximumLifetime,
          int maximumPerOwner,
          Clock clock) {
    if (idleTimeout == null || idleTimeout.isZero() || idleTimeout.isNegative()) {
      throw new IllegalArgumentException("Transaction idle timeout must be positive");
    }
    if (maximumLifetime == null || maximumLifetime.isZero() || maximumLifetime.isNegative()) {
      throw new IllegalArgumentException("Transaction maximum lifetime must be positive");
    }
    if (maximumPerOwner <= 0) {
      throw new IllegalArgumentException("Maximum transactions per owner must be positive");
    }
    this.idleTimeout = idleTimeout;
    this.maximumLifetime = maximumLifetime;
    this.maximumPerOwner = maximumPerOwner;
    this.clock = clock;
  }

  String start(String ownerId, Connection connection) throws SQLException {
    requireOwner(ownerId);
    if (connection == null) {
      throw new IllegalArgumentException("Connection is required");
    }
    cleanupExpired();
    Instant now = clock.instant();
    synchronized (entries) {
      long ownerCount = entries.values().stream()
              .filter(entry -> ownerId.equals(entry.ownerId))
              .count();
      if (ownerCount >= maximumPerOwner) {
        throw new SQLException("Maximum open transactions reached for the authenticated user");
      }
      connection.setAutoCommit(false);
      String transactionId = UUID.randomUUID().toString();
      entries.put(transactionId, new Entry(connection, ownerId, now));
      return transactionId;
    }
  }

  Lease acquire(String ownerId, String transactionId) throws SQLException {
    requireOwner(ownerId);
    cleanupExpired();
    Entry entry = entries.get(transactionId);
    if (entry == null || !ownerId.equals(entry.ownerId)) {
      throw unknownTransaction();
    }

    entry.lock.lock();
    boolean leased = false;
    try {
      Instant now = clock.instant();
      if (entries.get(transactionId) != entry
              || !ownerId.equals(entry.ownerId)
              || isExpired(entry, now)) {
        expireLocked(transactionId, entry);
        throw unknownTransaction();
      }
      entry.lastAccess = now;
      entry.activeLeases.incrementAndGet();
      leased = true;
      return new Lease(entry.connection, entry.lock, () -> {
        entry.lastAccess = clock.instant();
        entry.activeLeases.decrementAndGet();
      });
    } finally {
      if (!leased) {
        entry.lock.unlock();
      }
    }
  }

  boolean isActive(String ownerId, String transactionId) throws SQLException {
    try (Lease ignored = acquire(ownerId, transactionId)) {
      return true;
    }
  }

  void commit(String ownerId, String transactionId) throws SQLException {
    finish(ownerId, transactionId, true);
  }

  void rollback(String ownerId, String transactionId) throws SQLException {
    finish(ownerId, transactionId, false);
  }

  void cleanupExpired() {
    Instant now = clock.instant();
    entries.forEach((transactionId, entry) -> {
      if (isExpired(entry, now) && entry.activeLeases.get() == 0 && entry.lock.tryLock()) {
        try {
          if (isExpired(entry, clock.instant()) && entries.remove(transactionId, entry)) {
            rollbackAndClose(entry.connection);
          }
        } finally {
          entry.lock.unlock();
        }
      }
    });
  }

  void closeAll() {
    entries.forEach((transactionId, entry) -> {
      if (entries.remove(transactionId, entry)) {
        entry.lock.lock();
        try {
          rollbackAndClose(entry.connection);
        } finally {
          entry.lock.unlock();
        }
      }
    });
  }

  int size() {
    return entries.size();
  }

  private void finish(String ownerId, String transactionId, boolean commit) throws SQLException {
    requireOwner(ownerId);
    cleanupExpired();
    Entry entry = entries.get(transactionId);
    if (entry == null || !ownerId.equals(entry.ownerId)) {
      throw unknownTransaction();
    }

    entry.lock.lock();
    try {
      if (entries.get(transactionId) != entry
              || !ownerId.equals(entry.ownerId)
              || isExpired(entry, clock.instant())) {
        expireLocked(transactionId, entry);
        throw unknownTransaction();
      }
      if (!entries.remove(transactionId, entry)) {
        throw unknownTransaction();
      }
      try {
        if (commit) {
          entry.connection.commit();
        } else {
          entry.connection.rollback();
        }
      } finally {
        entry.connection.close();
      }
    } finally {
      entry.lock.unlock();
    }
  }

  private void expireLocked(String transactionId, Entry entry) {
    if (entries.remove(transactionId, entry)) {
      rollbackAndClose(entry.connection);
    }
  }

  private boolean isExpired(Entry entry, Instant now) {
    return !entry.createdAt.plus(maximumLifetime).isAfter(now)
            || !entry.lastAccess.plus(idleTimeout).isAfter(now);
  }

  private void rollbackAndClose(Connection connection) {
    try {
      connection.rollback();
    } catch (SQLException ignored) {
      // Closing the connection remains mandatory after a rollback failure.
    }
    try {
      connection.close();
    } catch (SQLException ignored) {
      // Cleanup is best-effort; the pool will discard an invalid physical connection.
    }
  }

  private void requireOwner(String ownerId) throws SQLException {
    if (ownerId == null || ownerId.isBlank()) {
      throw new SQLException("Authenticated transaction owner is unavailable");
    }
  }

  private SQLException unknownTransaction() {
    return new SQLException(UNKNOWN_TRANSACTION);
  }

  private static final class Entry {
    private final Connection connection;
    private final String ownerId;
    private final Instant createdAt;
    private final ReentrantLock lock = new ReentrantLock();
    private final AtomicInteger activeLeases = new AtomicInteger();
    private volatile Instant lastAccess;

    private Entry(Connection connection, String ownerId, Instant now) {
      this.connection = connection;
      this.ownerId = ownerId;
      this.createdAt = now;
      this.lastAccess = now;
    }
  }

  static final class Lease implements AutoCloseable {
    private final Connection connection;
    private final ReentrantLock lock;
    private final Runnable onClose;
    private final AtomicBoolean closed = new AtomicBoolean();

    private Lease(Connection connection, ReentrantLock lock, Runnable onClose) {
      this.connection = connection;
      this.lock = lock;
      this.onClose = onClose;
    }

    Connection connection() {
      return connection;
    }

    @Override
    public void close() {
      if (closed.compareAndSet(false, true)) {
        try {
          onClose.run();
        } finally {
          lock.unlock();
        }
      }
    }
  }
}
