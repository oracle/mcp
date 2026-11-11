/*
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0.
 */

package com.oracle.database.mcptoolkit;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oracle.database.mcptoolkit.oauth.AuthenticatedPrincipal;
import com.oracle.database.mcptoolkit.oauth.DeepSecDatabaseTokenProvider;
import com.oracle.database.mcptoolkit.oauth.EndUserSecurityContextHolder;
import com.oracle.database.mcptoolkit.tools.OwnedTransactionTestHarness;
import oracle.jdbc.EndUserSecurityContext;
import oracle.ucp.jdbc.PoolDataSource;
import oracle.ucp.jdbc.PoolDataSourceFactory;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.time.Duration;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Database-backed verification of OJDBC DeepSec context propagation and pool reuse. */
@EnabledIfEnvironmentVariable(named = "DEEPSEC_IT_ENABLED", matches = "(?i)true")
class DeepSecIntegrationTest {
  private static final ObjectMapper MAPPER = new ObjectMapper();

  @Test
  void propagatesUserIdentityAndMappedRolesWithoutLeakingPooledContext() throws Exception {
    Utils.installExternalExtensionsFromDir();
    PoolDataSource dataSource = createDataSource();
    String databaseAccessToken = optionalEnvironment("DEEPSEC_IT_DATABASE_ACCESS_TOKEN");
    if (databaseAccessToken == null) {
      databaseAccessToken = DeepSecDatabaseTokenProvider.getToken();
    }

    InteractiveOAuthLogin.Configuration oauth = oauthConfiguration();
    UserFixture userA = fixture("A", InteractiveOAuthLogin.login(oauth, "user A"));

    UserSnapshot firstA = queryAs(dataSource, databaseAccessToken, userA);
    UserFixture userB = null;
    if (Boolean.parseBoolean(System.getenv().getOrDefault("DEEPSEC_IT_TWO_USERS", "false"))) {
      userB = fixture("B", InteractiveOAuthLogin.login(oauth, "user B"));
      UserSnapshot firstB = queryAs(dataSource, databaseAccessToken, userB);
      assertNotEquals(firstA.username(), firstB.username(),
              "The two integration-test logins must represent different users");
    }
    UserSnapshot secondA = queryAs(dataSource, databaseAccessToken, userA);
    assertEquals(firstA, secondA,
            "Returning to user A must not retain user B's context on the pooled connection");

    verifyTransactions(dataSource, databaseAccessToken, userA, userB);
  }

  private static void verifyTransactions(
          PoolDataSource dataSource,
          String databaseAccessToken,
          UserFixture userA,
          UserFixture userB) throws Exception {
    try (OwnedTransactionTestHarness transactions = new OwnedTransactionTestHarness()) {
      String ownerA = owner(userA);
      String transactionId = startTransaction(
              transactions, dataSource, databaseAccessToken, userA);

      String initialDatabaseTransactionId = inTransaction(
              transactions, transactionId, databaseAccessToken, userA,
              connection -> {
                try (Statement statement = connection.createStatement()) {
                  statement.execute("SAVEPOINT deepsec_integration_start");
                }
                assertDeepSecContext(connection, userA);
                return queryDatabaseTransactionId(connection);
              });
      assertTrue(initialDatabaseTransactionId != null && !initialDatabaseTransactionId.isBlank(),
              "Oracle did not create a local transaction after SAVEPOINT");

      String deniedOwner = userB == null ? ownerA + "-different-user" : owner(userB);
      AtomicBoolean connectionTouched = new AtomicBoolean();
      if (userB == null) {
        EndUserSecurityContextHolder.setPrincipal(new AuthenticatedPrincipal(
                deniedOwner, "integration-test", "different-user", List.of(), List.of()));
      } else {
        setRequestContext(databaseAccessToken, userB);
      }
      try {
        String requestOwner = EndUserSecurityContextHolder.getAuthenticatedPrincipal().ownerId();
        SQLException error = assertThrows(SQLException.class,
                () -> transactions.use(requestOwner, transactionId, connection -> {
                  connectionTouched.set(true);
                  return null;
                }));
        assertEquals("Unknown transaction", error.getMessage());
        assertFalse(connectionTouched.get(),
                "An unauthorized owner must be rejected before the JDBC connection is touched");
      } finally {
        EndUserSecurityContextHolder.clear();
      }

      String resumedDatabaseTransactionId = inTransaction(
              transactions, transactionId, databaseAccessToken, userA,
              connection -> {
                assertDeepSecContext(connection, userA);
                return queryDatabaseTransactionId(connection);
              });
      assertEquals(initialDatabaseTransactionId, resumedDatabaseTransactionId,
              "A resumed request must use the same Oracle transaction");

      setRequestContext(databaseAccessToken, userA);
      try {
        transactions.commit(ownerA, transactionId);
      } finally {
        EndUserSecurityContextHolder.clear();
      }
      assertThrows(SQLException.class,
              () -> transactions.use(ownerA, transactionId, connection -> null));

      String rollbackId = startTransaction(
              transactions, dataSource, databaseAccessToken, userA);
      inTransaction(transactions, rollbackId, databaseAccessToken, userA, connection -> {
        try (Statement statement = connection.createStatement()) {
          statement.execute("SAVEPOINT deepsec_integration_rollback");
        }
        assertTrue(queryDatabaseTransactionId(connection) != null);
        return null;
      });
      setRequestContext(databaseAccessToken, userA);
      try {
        transactions.rollback(ownerA, rollbackId);
      } finally {
        EndUserSecurityContextHolder.clear();
      }
      assertThrows(SQLException.class,
              () -> transactions.use(ownerA, rollbackId, connection -> null));
    }
  }

  private static String startTransaction(
          OwnedTransactionTestHarness transactions,
          PoolDataSource dataSource,
          String databaseAccessToken,
          UserFixture fixture) throws Exception {
    setRequestContext(databaseAccessToken, fixture);
    Connection connection = null;
    try {
      connection = dataSource.getConnection();
      String transactionId = transactions.start(owner(fixture), connection);
      connection = null;
      return transactionId;
    } finally {
      if (connection != null) {
        connection.close();
      }
      EndUserSecurityContextHolder.clear();
    }
  }

  private static <T> T inTransaction(
          OwnedTransactionTestHarness transactions,
          String transactionId,
          String databaseAccessToken,
          UserFixture fixture,
          OwnedTransactionTestHarness.SqlAction<T> action) throws Exception {
    setRequestContext(databaseAccessToken, fixture);
    try {
      return transactions.use(owner(fixture), transactionId, action);
    } finally {
      EndUserSecurityContextHolder.clear();
    }
  }

  private static void setRequestContext(String databaseAccessToken, UserFixture fixture) {
    EndUserSecurityContext context = EndUserSecurityContext.createWithToken(
            databaseAccessToken, fixture.accessToken());
    EndUserSecurityContextHolder.set(
            context, AuthenticatedPrincipal.fromValidatedDeepSecJwt(fixture.accessToken()));
  }

  private static String owner(UserFixture fixture) {
    return AuthenticatedPrincipal.fromValidatedDeepSecJwt(fixture.accessToken()).ownerId();
  }

  private static String queryDatabaseTransactionId(Connection connection) throws Exception {
    try (Statement statement = connection.createStatement();
         ResultSet resultSet = statement.executeQuery(
                 "SELECT DBMS_TRANSACTION.LOCAL_TRANSACTION_ID FROM dual")) {
      assertTrue(resultSet.next(), "DBMS_TRANSACTION.LOCAL_TRANSACTION_ID returned no row");
      return resultSet.getString(1);
    }
  }

  private static void assertDeepSecContext(Connection connection, UserFixture fixture) throws Exception {
    assertEquals(fixture.expectedUsername(), queryUsername(connection));
    Set<String> roles = queryDataRoles(connection);
    assertTrue(roles.containsAll(fixture.expectedRoles()),
            () -> "Expected mapped roles " + fixture.expectedRoles() + " but database activated " + roles);
  }

  private static PoolDataSource createDataSource() throws Exception {
    PoolDataSource dataSource = PoolDataSourceFactory.getPoolDataSource();
    dataSource.setConnectionPoolName("deepsec-integration-" + UUID.randomUUID());
    dataSource.setConnectionFactoryClassName("oracle.jdbc.pool.OracleDataSource");
    dataSource.setURL(requiredConfiguration("DEEPSEC_IT_DB_URL", "db.url"));
    dataSource.setUser(requiredConfiguration("DEEPSEC_IT_DB_USER", "db.user"));
    dataSource.setPassword(requiredConfiguration("DEEPSEC_IT_DB_PASSWORD", "db.password"));
    dataSource.setInitialPoolSize(0);
    dataSource.setMinPoolSize(0);
    dataSource.setMaxPoolSize(1);
    dataSource.setConnectionWaitTimeout(20);
    dataSource.setCreateConnectionInBorrowThread(true);
    dataSource.setValidateConnectionOnBorrow(true);
    dataSource.setConnectionProperty(
            "oracle.jdbc.provider.endUserSecurityContext",
            new EndUserSecurityContextHolder().getName());
    return dataSource;
  }

  private static UserSnapshot queryAs(
          PoolDataSource dataSource,
          String databaseAccessToken,
          UserFixture fixture) throws Exception {
    setRequestContext(databaseAccessToken, fixture);
    try (Connection connection = dataSource.getConnection()) {
      String username = queryUsername(connection);
      Set<String> roles = queryDataRoles(connection);
      assertEquals(fixture.expectedUsername(), username);
      assertTrue(roles.containsAll(fixture.expectedRoles()),
              () -> "Expected mapped roles " + fixture.expectedRoles() + " but database activated " + roles);
      return new UserSnapshot(username, roles);
    } finally {
      EndUserSecurityContextHolder.clear();
    }
  }

  private static String queryUsername(Connection connection) throws Exception {
    try (Statement statement = connection.createStatement();
         ResultSet resultSet = statement.executeQuery("SELECT ORA_END_USER_CONTEXT.username")) {
      assertTrue(resultSet.next(), "ORA_END_USER_CONTEXT.username returned no row");
      return normalizeJsonString(resultSet.getString(1));
    }
  }

  private static Set<String> queryDataRoles(Connection connection) throws Exception {
    Set<String> roles = new LinkedHashSet<>();
    try (Statement statement = connection.createStatement();
         ResultSet resultSet = statement.executeQuery("SELECT role_name FROM v$end_user_data_role")) {
      while (resultSet.next()) {
        roles.add(resultSet.getString(1));
      }
    }
    return Set.copyOf(roles);
  }

  private static String normalizeJsonString(String value) throws Exception {
    if (value != null && value.startsWith("\"")) {
      JsonNode json = MAPPER.readTree(value);
      if (json.isTextual()) {
        return json.asText();
      }
    }
    return value;
  }

  private static UserFixture fixture(String suffix, String accessToken) {
    AuthenticatedPrincipal principal = AuthenticatedPrincipal.fromValidatedDeepSecJwt(accessToken);
    String expectedUsername = optionalEnvironment("DEEPSEC_IT_USER_" + suffix + "_USERNAME");
    if (expectedUsername == null) {
      expectedUsername = principal.subject();
    }
    if (expectedUsername == null) {
      throw new IllegalStateException(
              "DEEPSEC_IT_USER_" + suffix + "_USERNAME is required when the user token has no subject");
    }
    return new UserFixture(
            accessToken,
            expectedUsername,
            csv(optionalEnvironment("DEEPSEC_IT_USER_" + suffix + "_ROLES")));
  }

  private static InteractiveOAuthLogin.Configuration oauthConfiguration() {
    String authorizationServer = stripTrailingSlash(requiredConfiguration(null, "auth.authorizationServer"));
    return new InteractiveOAuthLogin.Configuration(
            authorizationServer + "/oauth2/v1/authorize",
            authorizationServer + "/oauth2/v1/token",
            requiredConfiguration(null, "deepsec.it.userLogin.clientId"),
            requiredConfiguration(null, "deepsec.it.userLogin.clientSecret"),
            requiredConfiguration(null, "deepsec.it.userLogin.callbackUri"),
            configuration("deepsec.it.userLogin.scopes", "openid"),
            configuration("mcp.oauth.resourceUrl", null),
            Duration.ofSeconds(Long.parseLong(configuration("deepsec.it.loginTimeoutSeconds", "180"))));
  }

  private static Set<String> csv(String value) {
    Set<String> values = new LinkedHashSet<>();
    if (value == null) {
      return Set.of();
    }
    for (String item : value.split(",")) {
      if (!item.isBlank()) {
        values.add(item.trim());
      }
    }
    return Set.copyOf(values);
  }

  private static String optionalEnvironment(String name) {
    String value = System.getenv(name);
    return value == null || value.isBlank() ? null : value;
  }

  private static String requiredConfiguration(String environmentName, String propertyName) {
    String value = environmentName == null ? null : optionalEnvironment(environmentName);
    if (value == null && propertyName != null) {
      value = configuration(propertyName, null);
    }
    if (value == null) {
      throw new IllegalStateException(
              (environmentName == null ? "" : environmentName + " or ")
                      + "-D" + propertyName + " must be configured when DEEPSEC_IT_ENABLED=true");
    }
    return value;
  }

  private static String configuration(String name, String defaultValue) {
    String value = System.getProperty(name);
    return value == null || value.isBlank() ? defaultValue : value;
  }

  private static String stripTrailingSlash(String value) {
    return value.endsWith("/") ? value.substring(0, value.length() - 1) : value;
  }

  private record UserFixture(String accessToken, String expectedUsername, Set<String> expectedRoles) {}

  private record UserSnapshot(String username, Set<String> roles) {}
}
