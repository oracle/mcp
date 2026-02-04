/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

/**
 * Centralized SQL queries used by JDBC admin and other database tools.
 */
final class SqlQueries {

  /** Query template for vector similarity search. **/
  public static final String SIMILARITY_SEARCH_QUERY = """
    SELECT dbms_lob.substr(%s, %s, 1) AS text
    FROM %s
    ORDER BY VECTOR_DISTANCE(%s,
             TO_VECTOR(VECTOR_EMBEDDING(%s USING ? AS data)))
    FETCH FIRST ? ROWS ONLY
  """;

  /** Query for fetching session user, schema, DB name, and time. */
  public static final String DB_PING_QUERY = """
    SELECT SYS_CONTEXT('USERENV','SESSION_USER') AS u,
           SYS_CONTEXT('USERENV','CURRENT_SCHEMA') AS s,
           SYS_CONTEXT('USERENV','DB_NAME') AS d,
           TO_CHAR(SYSDATE,'YYYY-MM-DD HH24:MI:SS') AS t
    FROM dual
  """;

  /** Query for fetching selected metrics. */
  public static final String DB_METRICS_RANGE = """
    SELECT name, value
    FROM v$sysstat
    WHERE name IN (
      'session logical reads',
      'db block gets',
      'consistent gets',
      'physical reads',
      'physical writes',
      'redo size'
    )
  """;

  private SqlQueries() {
    // Utility class
  }
}