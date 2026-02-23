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

  /**
   * Query to list all vector stores (tables that have at least one VECTOR column).
   */
  public static final String LIST_VECTOR_STORES_QUERY = """
    SELECT tc.table_name, tc.column_name, t.num_rows
    FROM user_tab_columns tc
    JOIN user_tables t ON tc.table_name = t.table_name
    WHERE tc.data_type = 'VECTOR'
    ORDER BY tc.table_name, tc.column_name
  """;

  /**
   * Query to list all vector embedding models available in the schema.
   */
  public static final String LIST_VECTOR_MODELS_QUERY = """
    SELECT model_name, mining_function, algorithm, creation_date, model_size
    FROM user_mining_models
    WHERE mining_function = 'EMBEDDING'
    ORDER BY creation_date DESC
  """;

  /**
   * Drops an ONNX vector embedding model from the database.
   */
  public static final String DROP_VECTOR_MODEL_QUERY = """
    BEGIN
      DBMS_VECTOR.DROP_ONNX_MODEL(MODEL_NAME => ?);
    END;
  """;

  /**
   * Query to check whether a table has a METADATA column.
   * <p>
   * Returns : COUNT(*) — 1 if column exists, 0 if not
   */
  public static final String CHECK_METADATA_COLUMN_QUERY = """
    SELECT COUNT(*)
    FROM user_tab_columns
    WHERE table_name = ? AND column_name = 'METADATA'
  """;

  /**
   * Atomic INSERT: BLOB → extract → chunk → embed → metadata, with NOT EXISTS deduplication on source_file.
  */
   public static final String INSERT_FILE_WITH_EMBEDDING_QUERY = """
    INSERT INTO %s (ID, CREATED_AT, METADATA, %s, %s)
    SELECT
      SYS_GUID(),
      SYSTIMESTAMP,
      JSON_OBJECT(
        'document_id' VALUE ?,
        'source_file' VALUE ?,
        'chunk_index' VALUE (ROW_NUMBER() OVER (ORDER BY ROWNUM) - 1),
        'total_chunks' VALUE COUNT(*) OVER ()
      ),
      jt.EMBED_DATA,
      TO_VECTOR(jt.EMBED_VECTOR)
    FROM TABLE(
      DBMS_VECTOR.UTL_TO_EMBEDDINGS(
        DBMS_VECTOR.UTL_TO_CHUNKS(
          DBMS_VECTOR_CHAIN.UTL_TO_TEXT(
            ?,
            JSON('{"plaintext": true, "charset": "UTF8", "format": "BINARY"}')
          ),
          JSON(?)
        ),
        JSON(?)
      )
    ) t,
    JSON_TABLE(t.COLUMN_VALUE, '$'
      COLUMNS (
        EMBED_DATA   CLOB PATH '$.embed_data',
        EMBED_VECTOR CLOB PATH '$.embed_vector'
      )
    ) jt
    WHERE NOT EXISTS (
      SELECT 1 FROM %s
      WHERE JSON_VALUE(METADATA, '$.source_file') = ?
    )
  """;

  /**
   * Same pipeline as {@link #INSERT_FILE_WITH_EMBEDDING_QUERY} but without METADATA or deduplication.
   */
  public static final String INSERT_FILE_WITHOUT_METADATA_QUERY = """
    INSERT INTO %s (ID, CREATED_AT, %s, %s)
    SELECT
      SYS_GUID(),
      SYSTIMESTAMP,
      jt.EMBED_DATA,
      TO_VECTOR(jt.EMBED_VECTOR)
    FROM TABLE(
      DBMS_VECTOR.UTL_TO_EMBEDDINGS(
        DBMS_VECTOR.UTL_TO_CHUNKS(
          DBMS_VECTOR_CHAIN.UTL_TO_TEXT(
            ?,
            JSON('{"plaintext": true, "charset": "UTF8", "format": "BINARY"}')
          ),
          JSON(?)
        ),
        JSON(?)
      )
    ) t,
    JSON_TABLE(t.COLUMN_VALUE, '$'
      COLUMNS (
        EMBED_DATA   CLOB PATH '$.embed_data',
        EMBED_VECTOR CLOB PATH '$.embed_vector'
      )
    ) jt
  """;

  /**
   * Embeds text from an existing source table into a vector store with metadata and deduplication.
   */
  public static final String INSERT_EMBEDDINGS_FROM_TABLE = """
    INSERT INTO %s (id, created_at, %s, %s, %s)
    SELECT
        SYS_GUID(),
        SYSTIMESTAMP,
        JSON_VALUE(t.COLUMN_VALUE, '$.embed_data' RETURNING CLOB),
        TO_VECTOR(JSON_VALUE(t.COLUMN_VALUE, '$.embed_vector' RETURNING CLOB)),
        JSON_OBJECT(
            KEY 'source_table'  VALUE ?,
            KEY 'source_id'     VALUE src.%s,
            KEY 'chunk_index'   VALUE (ROW_NUMBER() OVER (PARTITION BY src.%s ORDER BY ROWNUM) - 1),
            KEY 'embedded_at'   VALUE TO_CHAR(SYSTIMESTAMP, 'YYYY-MM-DD HH24:MI:SS')
        )
    FROM %s src,
    TABLE(
        DBMS_VECTOR.UTL_TO_EMBEDDINGS(
            data   => DBMS_VECTOR.UTL_TO_CHUNKS(data => src.%s, params => json(?)),
            params => json(?)
        )
    ) t
  """;

  /**
   * Embeds text from an existing source table into a vector store WITHOUT metadata column.
   */
  public static final String INSERT_EMBEDDINGS_FROM_TABLE_NO_METADATA = """
    INSERT INTO %s (id, created_at, %s, %s)
    SELECT
        SYS_GUID(),
        SYSTIMESTAMP,
        JSON_VALUE(t.COLUMN_VALUE, '$.embed_data' RETURNING CLOB),
        TO_VECTOR(JSON_VALUE(t.COLUMN_VALUE, '$.embed_vector' RETURNING CLOB))
    FROM %s src,
    TABLE(
        DBMS_VECTOR.UTL_TO_EMBEDDINGS(
            data   => DBMS_VECTOR.UTL_TO_CHUNKS(data => src.%s, params => json(?)),
            params => json(?)
        )
    ) t
  """;

  private SqlQueries() {
    // Utility class
  }
}