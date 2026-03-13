/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.oracle.database.mcptoolkit.ServerConfig;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static com.oracle.database.mcptoolkit.Utils.openConnection;

/**
 * Manages background embedding tasks for both OCI Object Storage and local files.
 * <p>
 * OCI pipelines run entirely inside Oracle.
 * Local file pipelines read bytes from disk and insert via the Oracle vector pipeline.
 * <p>
 * Auth for OCI operations is handled by the Oracle database through a
 * {@code DBMS_CLOUD} credential. Pass {@code null} as credential name for public buckets.
 */
public class EmbeddingTaskManager {

  private static final EmbeddingTaskManager INSTANCE = new EmbeddingTaskManager();

  private final ConcurrentHashMap<String, EmbeddingTask> tasks = new ConcurrentHashMap<>();
  private final ExecutorService executor = Executors.newCachedThreadPool();

  private EmbeddingTaskManager() {}

  public static EmbeddingTaskManager getInstance() {
    return INSTANCE;
  }

  /**
   * Mutable state for a single background embedding task.
   */
  public static class EmbeddingTask {
    public final String  taskId;
    public volatile String  status; // PENDING | RUNNING | COMPLETED | FAILED
    public final String  table;
    public final String  credentialName;
    public volatile int  totalChunksCreated  = 0;
    public final List<Map<String, Object>> results = Collections.synchronizedList(new ArrayList<>());
    public volatile String  errorMessage;
    public final Instant submittedAt = Instant.now();
    public volatile Instant completedAt;

    EmbeddingTask(String taskId, String table, String credentialName) {
      this.taskId         = taskId;
      this.table          = table;
      this.credentialName = credentialName;
      this.status         = "PENDING";
    }
  }

  /**
   * Submits a background job to embed a single OCI Object Storage object.
   *
   * @param config          server configuration (data source)
   * @param table           target vector store table
   * @param credentialName  DBMS_CLOUD credential name; {@code null} for public objects
   * @param objectUri       full OCI object URL or PAR URL
   * @param textColumn      text column in the target table
   * @param embeddingColumn embedding column in the target table
   * @param modelName       ONNX embedding model name
   * @param chunkParams     JSON chunking parameters
   * @return the task ID
   */
  public String submitSingleFile(
          ServerConfig config,
          String table, String credentialName, String objectUri,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    String taskId = UUID.randomUUID().toString();
    EmbeddingTask task = new EmbeddingTask(taskId, table, credentialName);
    tasks.put(taskId, task);
    executor.submit(() -> runSingleFile(task, config, table, credentialName, objectUri,
            textColumn, embeddingColumn, modelName, chunkParams));
    return taskId;
  }

  /**
   * Submits a background job to embed all objects in an OCI bucket.
   * <p>
   * The entire pipeline — listing, downloading, chunking, embedding, inserting — is
   * executed as a single SQL statement inside the database. Nothing is transferred to Java.
   *
   * @param config             server configuration (data source)
   * @param table              target vector store table
   * @param credentialName     DBMS_CLOUD credential name; {@code null} for public buckets
   * @param bucketUri          full OCI bucket URL or PAR URL
   * @param prefix             object-name prefix filter; blank = all objects
   * @param allowedExtensions  file extension filter (e.g. ["pdf","txt"]); empty = all files
   * @param textColumn         text column in the target table
   * @param embeddingColumn    embedding column in the target table
   * @param modelName          ONNX embedding model name
   * @param chunkParams        JSON chunking parameters
   * @return the task ID
   */
  public String submitBucket(
          ServerConfig config,
          String table, String credentialName, String bucketUri, String prefix,
          List<String> allowedExtensions,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    String taskId = UUID.randomUUID().toString();
    EmbeddingTask task = new EmbeddingTask(taskId, table, credentialName);
    tasks.put(taskId, task);
    executor.submit(() -> runBucket(task, config, table, credentialName, bucketUri,
            prefix, allowedExtensions, textColumn, embeddingColumn, modelName, chunkParams));
    return taskId;
  }

  /**
   * Submits a background job to embed a list of local files.
   * Each file is read from disk, chunked, and inserted into the vector store.
   *
   * @param config          server configuration (data source)
   * @param table           target vector store table
   * @param filePaths       list of absolute local file paths
   * @param textColumn      text column in the target table
   * @param embeddingColumn embedding column in the target table
   * @param modelName       ONNX embedding model name
   * @param chunkParams     JSON chunking parameters
   * @return the task ID
   */
  public String submitLocalFiles(
          ServerConfig config,
          String table, List<String> filePaths,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    String taskId = UUID.randomUUID().toString();
    EmbeddingTask task = new EmbeddingTask(taskId, table, null);
    tasks.put(taskId, task);
    executor.submit(() -> runLocalFiles(task, config, table, filePaths,
            textColumn, embeddingColumn, modelName, chunkParams));
    return taskId;
  }

  /**
   * Retrieve a task by ID, or {@code null} if unknown.
   */
  public EmbeddingTask getTask(String taskId) {
    return tasks.get(taskId);
  }

  /**
   * Submits a background job to embed text from an existing Oracle table into a vector store.
   *
   * @param config         server configuration (data source)
   * @param sourceTable    table containing the source text
   * @param sourceTextCol  column in the source table that holds the text to embed
   * @param sourceIdCol    column in the source table used as a unique row identifier
   * @param targetTable    target vector store table
   * @param textCol        text column in the target table
   * @param embeddingCol   embedding column in the target table
   * @param metadataCol    metadata column in the target table (used for deduplication)
   * @param modelName      ONNX embedding model name
   * @param chunkParams    JSON chunking parameters
   * @return the task ID
   */
  public String submitTableEmbedding(
          ServerConfig config,
          String sourceTable, String sourceTextCol, String sourceIdCol,
          String targetTable, String textCol, String embeddingCol, String metadataCol,
          String modelName, String chunkParams) {

    String taskId = UUID.randomUUID().toString();
    EmbeddingTask task = new EmbeddingTask(taskId, targetTable, null);
    tasks.put(taskId, task);
    executor.submit(() -> runTableEmbedding(task, config, sourceTable, sourceTextCol, sourceIdCol,
            targetTable, textCol, embeddingCol, metadataCol, modelName, chunkParams));
    return taskId;
  }

  /**
   * Returns all tasks known to this server process.
   */
  public Collection<EmbeddingTask> getAllTasks() {
    return tasks.values();
  }

  /**
   * Serialize a task to a plain map for JSON responses.
   */
  public static Map<String, Object> taskToMap(EmbeddingTask t) {
    Map<String, Object> m = new LinkedHashMap<>();
    m.put("taskId",             t.taskId);
    m.put("status",             t.status);
    m.put("table",              t.table);
    m.put("totalChunksCreated", t.totalChunksCreated);
    m.put("submittedAt",        t.submittedAt.toString());
    if (t.completedAt != null) {
      m.put("completedAt", t.completedAt.toString());
    }
    if (t.errorMessage != null) {
      m.put("errorMessage", t.errorMessage);
    }
    if (!t.results.isEmpty()) {
      m.put("results", new ArrayList<>(t.results));
    }
    return m;
  }

  /**
   * Embeds a single OCI object.
   * The pipeline (GET_OBJECT → UTL_TO_TEXT → UTL_TO_CHUNKS → UTL_TO_EMBEDDINGS → INSERT)
   * runs as one SQL statement entirely inside the database.
   */
  private void runSingleFile(
          EmbeddingTask task, ServerConfig config,
          String table, String credentialName, String objectUri,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    task.status = "RUNNING";

    try (Connection c = openConnection(config, null)) {

      String embeddingParams = RagTools.buildEmbeddingParams(modelName);
      boolean withMetadata   = RagTools.hasMetadataColumn(c, table);

      int chunks;
      if (withMetadata) {
        String sql = String.format(
                SqlQueries.INSERT_FROM_OCI_OBJECT_QUERY,
                quoteIdent(table),
                quoteIdent(textColumn),
                quoteIdent(embeddingColumn),
                quoteIdent(table)
        );
        try (PreparedStatement ps = c.prepareStatement(sql)) {
          ps.setString(1, UUID.randomUUID().toString()); // document_id
          ps.setString(2, objectUri);                    // source_uri in metadata
          ps.setString(3, credentialName);               // GET_OBJECT credential (null = public)
          ps.setString(4, objectUri);                    // GET_OBJECT object uri
          ps.setString(5, chunkParams);
          ps.setString(6, embeddingParams);
          ps.setString(7, objectUri);                    // NOT EXISTS dedup check
          chunks = ps.executeUpdate();
        }
      } else {
        String sql = String.format(
                SqlQueries.INSERT_FROM_OCI_OBJECT_NO_METADATA_QUERY,
                quoteIdent(table),
                quoteIdent(textColumn),
                quoteIdent(embeddingColumn)
        );
        try (PreparedStatement ps = c.prepareStatement(sql)) {
          ps.setString(1, credentialName);               // null = public bucket
          ps.setString(2, objectUri);
          ps.setString(3, chunkParams);
          ps.setString(4, embeddingParams);
          chunks = ps.executeUpdate();
        }
      }

      task.totalChunksCreated = chunks;
      if (chunks == 0) {
        task.results.add(Map.of(
                "objectUri", objectUri,
                "status",    "skipped",
                "reason",    "Object already exists in vector store"));
      } else {
        task.results.add(Map.of(
                "objectUri",     objectUri,
                "status",        "success",
                "chunksCreated", chunks));
      }
      task.status      = "COMPLETED";
      task.completedAt = Instant.now();

    } catch (Exception e) {
      task.errorMessage = errorMessage(e);
      task.status       = "FAILED";
      task.completedAt  = Instant.now();
    }
  }

  /**
   * Embeds all objects in an OCI bucket via a single SQL statement.
   * {@code DBMS_CLOUD.LIST_OBJECTS} drives the outer iteration;
   * {@code DBMS_CLOUD.GET_OBJECT} fetches each file directly inside the DB.
   */
  private void runBucket(
          EmbeddingTask task, ServerConfig config,
          String table, String credentialName, String bucketUri,
          String prefix, List<String> allowedExtensions,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    task.status = "RUNNING";

    String effectivePrefix   = (prefix == null) ? "" : prefix;
    String embeddingParams   = RagTools.buildEmbeddingParams(modelName);
    String extensionCondition = buildExtensionCondition(allowedExtensions);

    try (Connection c = openConnection(config, null)) {

      boolean withMetadata = RagTools.hasMetadataColumn(c, table);
      int inserted;

      if (withMetadata) {
        String sql = String.format(
                SqlQueries.INSERT_FROM_OCI_BUCKET_QUERY,
                quoteIdent(table),
                quoteIdent(textColumn),
                quoteIdent(embeddingColumn),
                extensionCondition,
                quoteIdent(table)
        );
        try (PreparedStatement ps = c.prepareStatement(sql)) {
          ps.setString(1, bucketUri);        // source_uri prefix in metadata
          ps.setString(2, credentialName);   // LIST_OBJECTS credential (null = public)
          ps.setString(3, bucketUri);        // LIST_OBJECTS bucket uri
          ps.setString(4, credentialName);   // GET_OBJECT credential (null = public)
          ps.setString(5, bucketUri);        // GET_OBJECT base uri
          ps.setString(6, chunkParams);
          ps.setString(7, embeddingParams);
          ps.setString(8, effectivePrefix);  // LIKE prefix filter
          ps.setString(9, bucketUri);        // NOT EXISTS dedup base uri
          inserted = ps.executeUpdate();
        }
      } else {
        String sql = String.format(
                SqlQueries.INSERT_FROM_OCI_BUCKET_NO_METADATA_QUERY,
                quoteIdent(table),
                quoteIdent(textColumn),
                quoteIdent(embeddingColumn),
                extensionCondition
        );
        try (PreparedStatement ps = c.prepareStatement(sql)) {
          ps.setString(1, credentialName);   // LIST_OBJECTS credential (null = public)
          ps.setString(2, bucketUri);        // LIST_OBJECTS bucket uri
          ps.setString(3, credentialName);   // GET_OBJECT credential (null = public)
          ps.setString(4, bucketUri);        // GET_OBJECT base uri
          ps.setString(5, chunkParams);
          ps.setString(6, embeddingParams);
          ps.setString(7, effectivePrefix);  // LIKE prefix filter
          inserted = ps.executeUpdate();
        }
      }

      task.totalChunksCreated = inserted;
      task.status             = "COMPLETED";
      task.completedAt        = Instant.now();

    } catch (Exception e) {
      task.errorMessage = errorMessage(e);
      task.status       = "FAILED";
      task.completedAt  = Instant.now();
    }
  }

  /**
   * Embeds a list of local files in the background.
   * Each file is read from disk and inserted via the Oracle vector pipeline.
   * One bad file does not abort the rest.
   */
  private void runLocalFiles(
          EmbeddingTask task, ServerConfig config,
          String table, List<String> filePaths,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    task.status = "RUNNING";

    try (Connection c = openConnection(config, null)) {
      boolean withMetadata = RagTools.hasMetadataColumn(c, table);
      int totalChunks = 0;
      for (String filePath : filePaths) {
        Path path = Paths.get(filePath);
        if (!Files.exists(path)) {
          task.results.add(Map.of(
                  "file",   filePath,
                  "status", "error",
                  "error",  "File not found: " + filePath));
          continue;
        }
        try {
          byte[] fileBytes = Files.readAllBytes(path);
          String fullPath  = path.toAbsolutePath().toString();
          String sourceUri = Paths.get(fullPath).toUri().toString();

          // Pre-check deduplication so we can distinguish "already exists" from "no text extracted"
          if (withMetadata && RagTools.fileExistsInVectorStore(c, table, sourceUri)) {
            task.results.add(Map.of(
                    "file",   fullPath,
                    "status", "skipped",
                    "reason", "File already exists in vector store"));
            continue;
          }

          int chunks = RagTools.insertFileWithNativeChunking(
                  c, table, textColumn, embeddingColumn, modelName, fileBytes, fullPath, chunkParams);
          if (chunks == 0) {
            task.results.add(Map.of(
                    "file",   fullPath,
                    "status", "skipped",
                    "reason", "No text could be extracted (image or unsupported file format)"));
          } else {
            totalChunks += chunks;
            task.results.add(Map.of(
                    "file",          fullPath,
                    "status",        "success",
                    "chunksCreated", chunks));
          }
        } catch (Exception e) {
          task.results.add(Map.of(
                  "file",   filePath,
                  "status", "error",
                  "error",  errorMessage(e)));
        }
      }
      task.totalChunksCreated = totalChunks;
      task.status             = "COMPLETED";
      task.completedAt        = Instant.now();

    } catch (Exception e) {
      task.errorMessage = errorMessage(e);
      task.status       = "FAILED";
      task.completedAt  = Instant.now();
    }
  }

  /**
   * Embeds text from an existing Oracle source table into a target vector store.
   * Runs as a single SQL INSERT entirely inside the database.
   */
  private void runTableEmbedding(
          EmbeddingTask task, ServerConfig config,
          String sourceTable, String sourceTextCol, String sourceIdCol,
          String targetTable, String textCol, String embeddingCol, String metadataCol,
          String modelName, String chunkParams) {

    task.status = "RUNNING";
    String embedParams = RagTools.buildEmbeddingParams(modelName);

    try (Connection conn = openConnection(config, null)) {
      boolean withMetadata = RagTools.hasMetadataColumn(conn, targetTable);

      String sql;
      if (withMetadata) {
        sql = String.format(SqlQueries.INSERT_EMBEDDINGS_FROM_TABLE,
                quoteIdent(targetTable), quoteIdent(textCol), quoteIdent(embeddingCol), quoteIdent(metadataCol),
                quoteIdent(sourceIdCol), quoteIdent(sourceIdCol), quoteIdent(sourceTable), quoteIdent(sourceTextCol),
                quoteIdent(targetTable), quoteIdent(metadataCol), quoteIdent(sourceIdCol), quoteIdent(metadataCol));
      } else {
        sql = String.format(SqlQueries.INSERT_EMBEDDINGS_FROM_TABLE_NO_METADATA,
                quoteIdent(targetTable), quoteIdent(textCol), quoteIdent(embeddingCol),
                quoteIdent(sourceTable), quoteIdent(sourceTextCol));
      }

      try (PreparedStatement stmt = conn.prepareStatement(sql)) {
        if (withMetadata) {
          stmt.setString(1, sourceTable);   // JSON_OBJECT KEY 'source_table'
          stmt.setString(2, chunkParams);
          stmt.setString(3, embedParams);
          stmt.setString(4, sourceTable);   // NOT EXISTS dedup check
        } else {
          stmt.setString(1, chunkParams);
          stmt.setString(2, embedParams);
        }
        int inserted = stmt.executeUpdate();
        task.totalChunksCreated = inserted;
        task.results.add(Map.of(
                "sourceTable",   sourceTable,
                "targetTable",   targetTable,
                "status",        "success",
                "chunksCreated", inserted));
      }
      task.status      = "COMPLETED";
      task.completedAt = Instant.now();

    } catch (Exception e) {
      task.errorMessage = errorMessage(e);
      task.status       = "FAILED";
      task.completedAt  = Instant.now();
    }
  }

  /**
   * Builds an optional SQL AND clause that filters bucket objects by file extension.
   * Returns an empty string when the list is empty (all files are processed).
   */
  private static String buildExtensionCondition(List<String> extensions) {
    if (extensions == null || extensions.isEmpty()) return "";
    String conditions = extensions.stream()
            .map(ext -> {
              String e = ext.startsWith(".") ? ext : "." + ext;
              return "lst.object_name LIKE '%" + e + "'";
            })
            .collect(java.util.stream.Collectors.joining(" OR "));
    return "AND (" + conditions + ")";
  }

  private static String errorMessage(Exception e) {
    return e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
  }

  private static String quoteIdent(String name) {
    return "\"" + name.replace("\"", "\"\"") + "\"";
  }
}