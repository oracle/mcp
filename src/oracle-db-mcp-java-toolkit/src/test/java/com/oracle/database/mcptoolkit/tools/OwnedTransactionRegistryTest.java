/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0.
 */

package com.oracle.database.mcptoolkit.tools;

import org.junit.jupiter.api.Test;

import java.lang.reflect.Proxy;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertSame;

class OwnedTransactionRegistryTest {
  @Test
  void rejectsAnotherOwnerWithoutDestroyingTransaction() throws Exception {
    OwnedTransactionRegistry registry = registry(Clock.systemUTC(), 4);
    ConnectionState state = new ConnectionState();
    String transactionId = registry.start("alice", connection(state));

    SQLException error = assertThrows(SQLException.class,
            () -> registry.acquire("bob", transactionId));
    assertEquals("Unknown transaction", error.getMessage());

    try (OwnedTransactionRegistry.Lease lease = registry.acquire("alice", transactionId)) {
      assertFalse(state.closed.get());
      assertSame(lease.connection(), state.connection);
    }
    registry.rollback("alice", transactionId);
    assertEquals(1, state.rollbacks.get());
    assertTrue(state.closed.get());
  }

  @Test
  void commitsOnlyForOwnerAndReturnsConnection() throws Exception {
    OwnedTransactionRegistry registry = registry(Clock.systemUTC(), 4);
    ConnectionState state = new ConnectionState();
    String transactionId = registry.start("alice", connection(state));

    assertThrows(SQLException.class, () -> registry.commit("bob", transactionId));
    registry.commit("alice", transactionId);

    assertEquals(1, state.commits.get());
    assertTrue(state.closed.get());
    assertEquals(0, registry.size());
  }

  @Test
  void expiresAndRollsBackAbandonedTransactions() throws Exception {
    MutableClock clock = new MutableClock(Instant.parse("2026-07-14T12:00:00Z"));
    OwnedTransactionRegistry registry = new OwnedTransactionRegistry(
            Duration.ofSeconds(10), Duration.ofMinutes(5), 4, clock);
    ConnectionState state = new ConnectionState();
    String transactionId = registry.start("alice", connection(state));

    clock.advance(Duration.ofSeconds(11));
    registry.cleanupExpired();

    assertEquals(1, state.rollbacks.get());
    assertTrue(state.closed.get());
    assertThrows(SQLException.class, () -> registry.acquire("alice", transactionId));
  }

  @Test
  void doesNotExpireAConnectionWhileItIsInUse() throws Exception {
    MutableClock clock = new MutableClock(Instant.parse("2026-07-14T12:00:00Z"));
    OwnedTransactionRegistry registry = new OwnedTransactionRegistry(
            Duration.ofSeconds(10), Duration.ofMinutes(5), 4, clock);
    ConnectionState state = new ConnectionState();
    String transactionId = registry.start("alice", connection(state));
    OwnedTransactionRegistry.Lease lease = registry.acquire("alice", transactionId);

    clock.advance(Duration.ofSeconds(11));
    registry.cleanupExpired();
    assertEquals(1, registry.size());
    assertFalse(state.closed.get());

    lease.close();
    clock.advance(Duration.ofSeconds(11));
    registry.cleanupExpired();
    assertTrue(state.closed.get());
  }

  @Test
  void enforcesPerOwnerLimit() throws Exception {
    OwnedTransactionRegistry registry = registry(Clock.systemUTC(), 1);
    ConnectionState first = new ConnectionState();
    ConnectionState second = new ConnectionState();
    registry.start("alice", connection(first));

    assertThrows(SQLException.class, () -> registry.start("alice", connection(second)));
    registry.start("bob", connection(new ConnectionState()));
    registry.closeAll();
  }

  @Test
  void serializesConcurrentUseOfOneConnection() throws Exception {
    OwnedTransactionRegistry registry = registry(Clock.systemUTC(), 4);
    String transactionId = registry.start("alice", connection(new ConnectionState()));
    OwnedTransactionRegistry.Lease first = registry.acquire("alice", transactionId);
    CountDownLatch attempting = new CountDownLatch(1);
    var executor = Executors.newSingleThreadExecutor();
    try {
      var second = executor.submit(() -> {
        attempting.countDown();
        try (OwnedTransactionRegistry.Lease ignored = registry.acquire("alice", transactionId)) {
          return true;
        }
      });
      assertTrue(attempting.await(1, TimeUnit.SECONDS));
      Thread.sleep(50);
      assertFalse(second.isDone());

      first.close();
      assertTrue(second.get(1, TimeUnit.SECONDS));
    } finally {
      first.close();
      registry.closeAll();
      executor.shutdownNow();
    }
  }

  private OwnedTransactionRegistry registry(Clock clock, int maximumPerOwner) {
    return new OwnedTransactionRegistry(
            Duration.ofMinutes(2), Duration.ofMinutes(5), maximumPerOwner, clock);
  }

  private Connection connection(ConnectionState state) {
    Connection connection = (Connection) Proxy.newProxyInstance(
            getClass().getClassLoader(),
            new Class<?>[]{Connection.class},
            (proxy, method, args) -> switch (method.getName()) {
              case "setAutoCommit" -> {
                state.autoCommit.set((Boolean) args[0]);
                yield null;
              }
              case "getAutoCommit" -> state.autoCommit.get();
              case "commit" -> {
                state.commits.incrementAndGet();
                yield null;
              }
              case "rollback" -> {
                state.rollbacks.incrementAndGet();
                yield null;
              }
              case "close" -> {
                state.closed.set(true);
                yield null;
              }
              case "isClosed" -> state.closed.get();
              case "toString" -> "test-connection";
              default -> defaultValue(method.getReturnType());
            });
    state.connection = connection;
    return connection;
  }

  private Object defaultValue(Class<?> type) {
    if (!type.isPrimitive()) {
      return null;
    }
    if (type == boolean.class) {
      return false;
    }
    if (type == char.class) {
      return '\0';
    }
    return 0;
  }

  private static final class ConnectionState {
    private Connection connection;
    private final AtomicBoolean autoCommit = new AtomicBoolean(true);
    private final AtomicBoolean closed = new AtomicBoolean();
    private final AtomicInteger commits = new AtomicInteger();
    private final AtomicInteger rollbacks = new AtomicInteger();
  }

  private static final class MutableClock extends Clock {
    private Instant instant;

    private MutableClock(Instant instant) {
      this.instant = instant;
    }

    void advance(Duration duration) {
      instant = instant.plus(duration);
    }

    @Override
    public ZoneId getZone() {
      return ZoneOffset.UTC;
    }

    @Override
    public Clock withZone(ZoneId zone) {
      return this;
    }

    @Override
    public Instant instant() {
      return instant;
    }
  }
}
