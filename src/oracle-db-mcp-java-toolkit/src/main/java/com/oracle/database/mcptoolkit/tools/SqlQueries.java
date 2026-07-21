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
   * Deletes all rows inserted by a specific embedding task, identified by task_id in METADATA.
   * Used as a compensating DELETE when a cancelled task needs metadata-based cleanup.
   * <p>
   * Format args: table
   * Bind params: taskId
   */
  public static final String DELETE_TASK_ROWS_QUERY = """
    DELETE FROM %s WHERE JSON_VALUE(METADATA, '$.task_id') = ?
  """;

  /**
   * Check whether a file's source_uri already exists in a vector store's METADATA column.
   * <p>
   * Bind params: table (via format), sourceUri
   * Returns : COUNT(*) — 1 if found, 0 if not
   */
  public static final String CHECK_FILE_EXISTS_IN_STORE_QUERY = """
    SELECT COUNT(*)
    FROM %s
    WHERE JSON_VALUE(METADATA, '$.source_uri') = ?
  """;

  /**
   * Query to check whether a table has a METADATA column.
   * <p>
   * Returns : COUNT(*) — 1 if column exists, 0 if not
   */
  public static final String CHECK_METADATA_COLUMN_QUERY = """
    SELECT COUNT(*)
    FROM user_tab_columns
    WHERE table_name = UPPER(?) AND column_name = 'METADATA'
  """;

  /**
   * Atomic INSERT: BLOB → extract → chunk → embed → metadata, with NOT EXISTS deduplication on source_uri.
   * Local file paths are passed as {@code file:///} URIs so the metadata key matches OCI objects.
   */
  public static final String INSERT_FILE_WITH_EMBEDDING_QUERY = """
    INSERT INTO %s (ID, CREATED_AT, METADATA, %s, %s)
    SELECT
      SYS_GUID(),
      SYSTIMESTAMP,
      JSON_OBJECT(
        'task_id'      VALUE ?,
        'document_id'  VALUE ?,
        'source_uri'   VALUE ?,
        'chunk_index'  VALUE (ROW_NUMBER() OVER (ORDER BY ROWNUM) - 1),
        'total_chunks' VALUE COUNT(*) OVER ()
      ),
      jt.EMBED_DATA,
      TO_VECTOR(jt.EMBED_VECTOR)
    FROM TABLE(
      DBMS_VECTOR.UTL_TO_EMBEDDINGS(
        DBMS_VECTOR.UTL_TO_CHUNKS(
          DBMS_VECTOR_CHAIN.UTL_TO_TEXT(
            ?,
            JSON('{"charset": "UTF8", "format": "BINARY"}')
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
      WHERE JSON_VALUE(METADATA, '$.source_uri') = ?
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
            JSON('{"charset": "UTF8", "format": "BINARY"}')
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
   * Atomic INSERT from OCI Object Storage: DBMS_CLOUD.GET_OBJECT → extract → chunk → embed → metadata,
   * with NOT EXISTS deduplication on source_uri.
   * <p>
   * Format args: table, textColumn, embeddingColumn, table (dedup check)
   * Bind params: taskId, documentId, sourceUri, credentialName, objectUri, chunkParams, embeddingParams, sourceUri (dedup)
   */
  public static final String INSERT_FROM_OCI_OBJECT_QUERY = """
    INSERT INTO %s (ID, CREATED_AT, METADATA, %s, %s)
    SELECT
      SYS_GUID(),
      SYSTIMESTAMP,
      JSON_OBJECT(
        'task_id'      VALUE ?,
        'document_id'  VALUE ?,
        'source_uri'   VALUE ?,
        'chunk_index'  VALUE (ROW_NUMBER() OVER (ORDER BY ROWNUM) - 1),
        'total_chunks' VALUE COUNT(*) OVER ()
      ),
      jt.EMBED_DATA,
      TO_VECTOR(jt.EMBED_VECTOR)
    FROM TABLE(
      DBMS_VECTOR.UTL_TO_EMBEDDINGS(
        DBMS_VECTOR.UTL_TO_CHUNKS(
          DBMS_VECTOR_CHAIN.UTL_TO_TEXT(
            DBMS_CLOUD.GET_OBJECT(?, ?)
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
      WHERE JSON_VALUE(METADATA, '$.source_uri') = ?
    )
  """;

  /**
   * Same OCI pipeline as {@link #INSERT_FROM_OCI_OBJECT_QUERY} but without METADATA column or deduplication.
   * <p>
   * Format args: table, textColumn, embeddingColumn
   * Bind params: credentialName, objectUri, chunkParams, embeddingParams
   */
  public static final String INSERT_FROM_OCI_OBJECT_NO_METADATA_QUERY = """
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
            DBMS_CLOUD.GET_OBJECT(?, ?)
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
   * Lists objects in an OCI Object Storage bucket via DBMS_CLOUD.
   * <p>
   * Bind params: credentialName (null = public), bucketUri
   */
  public static final String LIST_OCI_BUCKET_OBJECTS_QUERY = """
    SELECT object_name, bytes, last_modified
    FROM DBMS_CLOUD.LIST_OBJECTS(?, ?)
    WHERE object_name LIKE ? || '%'
    ORDER BY object_name
  """;

  /**
   * Embeds matching objects in an OCI bucket in a single statement.
   * DBMS_CLOUD.LIST_OBJECTS drives the outer loop; DBMS_CLOUD.GET_OBJECT fetches
   * each file directly inside the DB.
   * <p>
   * Format args : table, textColumn, embeddingColumn, extensionCondition, table (dedup)
   * Bind params : taskId, bucketUri, credentialName, bucketUri, prefix ('' = no prefix filter),
   *               maxFileBytes, extension patterns, maxObjects, credentialName, bucketUri,
   *               chunkParams, embeddingParams, bucketUri
   */
  public static final String INSERT_FROM_OCI_BUCKET_QUERY = """
    INSERT INTO %s (ID, CREATED_AT, METADATA, %s, %s)
    SELECT
      SYS_GUID(),
      SYSTIMESTAMP,
      JSON_OBJECT(
        'task_id'      VALUE ?,
        'document_id'  VALUE SYS_GUID(),
        'source_uri'   VALUE (? || lst.object_name),
        'chunk_index' VALUE (ROW_NUMBER() OVER (PARTITION BY lst.object_name ORDER BY ROWNUM) - 1),
        'total_chunks' VALUE COUNT(*) OVER (PARTITION BY lst.object_name)
      ),
      jt.EMBED_DATA,
      TO_VECTOR(jt.EMBED_VECTOR)
    FROM (
      SELECT object_name
      FROM DBMS_CLOUD.LIST_OBJECTS(?, ?)
      WHERE object_name LIKE ? || '%%'
      AND bytes <= ?
      %s
      ORDER BY object_name
      FETCH FIRST ? ROWS ONLY
    ) lst
    CROSS APPLY TABLE(
      DBMS_VECTOR.UTL_TO_EMBEDDINGS(
        DBMS_VECTOR.UTL_TO_CHUNKS(
          DBMS_VECTOR_CHAIN.UTL_TO_TEXT(
            DBMS_CLOUD.GET_OBJECT(?, ? || lst.object_name)
          ),
          JSON(?)
        ),
        JSON(?)
      )
    ) embeds
    CROSS APPLY JSON_TABLE(embeds.COLUMN_VALUE, '$'
      COLUMNS (
        EMBED_DATA   CLOB PATH '$.embed_data',
        EMBED_VECTOR CLOB PATH '$.embed_vector'
      )
    ) jt
    WHERE NOT EXISTS (
      SELECT 1 FROM %s
      WHERE JSON_VALUE(METADATA, '$.source_uri') = ? || lst.object_name
    )
  """;

  /**
   * Same bucket pipeline without METADATA column or deduplication.
   * <p>
   * Format args : table, textColumn, embeddingColumn, extensionCondition
   * Bind params : credentialName, bucketUri, prefix ('' = no prefix filter), maxFileBytes,
   *               extension patterns, maxObjects, credentialName, bucketUri, chunkParams,
   *               embeddingParams
   */
  public static final String INSERT_FROM_OCI_BUCKET_NO_METADATA_QUERY = """
    INSERT INTO %s (ID, CREATED_AT, %s, %s)
    SELECT
      SYS_GUID(),
      SYSTIMESTAMP,
      jt.EMBED_DATA,
      TO_VECTOR(jt.EMBED_VECTOR)
    FROM (
      SELECT object_name
      FROM DBMS_CLOUD.LIST_OBJECTS(?, ?)
      WHERE object_name LIKE ? || '%%'
      AND bytes <= ?
      %s
      ORDER BY object_name
      FETCH FIRST ? ROWS ONLY
    ) lst
    CROSS APPLY TABLE(
      DBMS_VECTOR.UTL_TO_EMBEDDINGS(
        DBMS_VECTOR.UTL_TO_CHUNKS(
          DBMS_VECTOR_CHAIN.UTL_TO_TEXT(
            DBMS_CLOUD.GET_OBJECT(?, ? || lst.object_name)
          ),
          JSON(?)
        ),
        JSON(?)
      )
    ) embeds
    CROSS APPLY JSON_TABLE(embeds.COLUMN_VALUE, '$'
      COLUMNS (
        EMBED_DATA   CLOB PATH '$.embed_data',
        EMBED_VECTOR CLOB PATH '$.embed_vector'
      )
    ) jt
  """;

  /**
   * Embeds text from an existing source table into a vector store with metadata and deduplication.
   * Skips source rows whose source_id already appears in the target (keyed on source_table + source_id).
   * <p>
   * Format args (12): targetTable, textCol, embeddingCol, metadataCol,
   *                   sourceIdCol, sourceIdCol, sourceTable, sourceTextCol,
   *                   targetTable, metadataCol, sourceIdCol, metadataCol
   * Bind params  (5): taskId, sourceTable, chunkParams, embedParams, sourceTable (dedup)
   */
  public static final String INSERT_EMBEDDINGS_FROM_TABLE = """
    INSERT INTO %s (id, created_at, %s, %s, %s)
    SELECT
        SYS_GUID(),
        SYSTIMESTAMP,
        JSON_VALUE(t.COLUMN_VALUE, '$.embed_data' RETURNING CLOB),
        TO_VECTOR(JSON_VALUE(t.COLUMN_VALUE, '$.embed_vector' RETURNING CLOB)),
        JSON_OBJECT(
            KEY 'task_id'       VALUE ?,
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
    WHERE NOT EXISTS (
        SELECT 1 FROM %s
        WHERE JSON_VALUE(%s, '$.source_id')    = TO_CHAR(src.%s)
        AND   JSON_VALUE(%s, '$.source_table') = ?
    )
  """;

  /**
   * Embeds text from an existing source table into a vector store WITHOUT metadata column.
   * No deduplication is performed — all source rows are inserted on every run.
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

  /**
   * Lists all DBMS_CLOUD credentials available in the current user's schema.
   */
  public static final String LIST_CREDENTIALS_QUERY = """
    SELECT credential_name, username, enabled
    FROM user_credentials
    ORDER BY credential_name
  """;

  private SqlQueries() {
    // Utility class
  }
}
