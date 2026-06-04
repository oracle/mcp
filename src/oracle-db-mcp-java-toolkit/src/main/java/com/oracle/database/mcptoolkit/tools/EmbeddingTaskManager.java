/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2026 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.oracle.database.mcptoolkit.LoadedConstants;
import com.oracle.database.mcptoolkit.ServerConfig;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

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

  private static final int MAX_EMBEDDING_THREADS = 5;
  private static final int MAX_EMBEDDING_QUEUE_SIZE = 100;
  private static final int MAX_STORED_TASKS = 1000;
  private static final int MAX_LOCAL_INGEST_FILES = 100;
  private static final Duration COMPLETED_TASK_TTL = Duration.ofHours(72);
  private static final String SIMPLE_FILE_EXTENSION = "[a-z0-9]{1,16}";
  private static final long DEFAULT_INGEST_MAX_FILE_SIZE_MB = 50L;
  private static final Set<String> LOCAL_INGEST_ALLOWED_EXTENSIONS = Set.of(
          "txt", "md", "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
          "html", "htm", "json", "csv", "xml");
  private static final EmbeddingTaskManager INSTANCE = new EmbeddingTaskManager();

  private final ConcurrentHashMap<String, EmbeddingTask> tasks = new ConcurrentHashMap<>();
  private final ExecutorService executor = new ThreadPoolExecutor(
          MAX_EMBEDDING_THREADS,
          MAX_EMBEDDING_THREADS,
          0L,
          TimeUnit.MILLISECONDS,
          new ArrayBlockingQueue<>(MAX_EMBEDDING_QUEUE_SIZE),
          new ThreadPoolExecutor.AbortPolicy());

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
    submitTask(task, () -> runSingleFile(task, config, table, credentialName, objectUri,
            textColumn, embeddingColumn, modelName, chunkParams));
    return taskId;
  }

  /**
   * Submits a background job to embed matching objects in an OCI bucket.
   * <p>
   * The entire pipeline — listing, downloading, chunking, embedding, inserting — is
   * executed as a single SQL statement inside the database. Nothing is transferred to Java.
   *
   * @param config             server configuration (data source)
   * @param table              target vector store table
   * @param credentialName     DBMS_CLOUD credential name; {@code null} for public buckets
   * @param bucketUri          full OCI bucket URL or PAR URL
   * @param prefix             object-name prefix filter; blank means no prefix filter
   * @param allowedExtensions  file extension filter (e.g. ["pdf","txt"]); empty means no extension filter
   * @param maxObjects         maximum number of bucket objects to process
   * @param textColumn         text column in the target table
   * @param embeddingColumn    embedding column in the target table
   * @param modelName          ONNX embedding model name
   * @param chunkParams        JSON chunking parameters
   * @return the task ID
   */
  public String submitBucket(
          ServerConfig config,
          String table, String credentialName, String bucketUri, String prefix,
          List<String> allowedExtensions, int maxObjects,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    String taskId = UUID.randomUUID().toString();
    EmbeddingTask task = new EmbeddingTask(taskId, table, credentialName);
    submitTask(task, () -> runBucket(task, config, table, credentialName, bucketUri,
            prefix, allowedExtensions, maxObjects, textColumn, embeddingColumn, modelName, chunkParams));
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

    validateLocalIngestFileCount(filePaths);
    String taskId = UUID.randomUUID().toString();
    EmbeddingTask task = new EmbeddingTask(taskId, table, null);
    submitTask(task, () -> runLocalFiles(task, config, table, filePaths,
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
    submitTask(task, () -> runTableEmbedding(task, config, sourceTable, sourceTextCol, sourceIdCol,
            targetTable, textCol, embeddingCol, metadataCol, modelName, chunkParams));
    return taskId;
  }

  /**
   * Stores and submits a background embedding task, rejecting it if task storage or queue limits are full.
   */
  private void submitTask(EmbeddingTask task, Runnable work) {
    cleanupTasks();
    if (tasks.size() >= MAX_STORED_TASKS) {
      throw new IllegalStateException("Embedding task storage is full; try again later");
    }

    tasks.put(task.taskId, task);
    try {
      executor.submit(work);
    } catch (RejectedExecutionException e) {
      tasks.remove(task.taskId);
      throw new IllegalStateException("Embedding task queue is full; try again later", e);
    }
  }

  /**
   * Removes completed or failed task records that are older than the retention window.
   */
  private void cleanupTasks() {
    Instant expiresBefore = Instant.now().minus(COMPLETED_TASK_TTL);
    tasks.entrySet().removeIf(entry -> {
      EmbeddingTask task = entry.getValue();
      return task.completedAt != null
              && task.completedAt.isBefore(expiresBefore)
              && ("COMPLETED".equals(task.status) || "FAILED".equals(task.status));
    });
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
   * Embeds matching objects in an OCI bucket via a single SQL statement.
   * {@code DBMS_CLOUD.LIST_OBJECTS} drives the outer iteration;
   * {@code DBMS_CLOUD.GET_OBJECT} fetches each file directly inside the DB.
   */
  private void runBucket(
          EmbeddingTask task, ServerConfig config,
          String table, String credentialName, String bucketUri,
          String prefix, List<String> allowedExtensions, int maxObjects,
          String textColumn, String embeddingColumn,
          String modelName, String chunkParams) {

    task.status = "RUNNING";

    String effectivePrefix   = (prefix == null) ? "" : prefix;
    String embeddingParams   = RagTools.buildEmbeddingParams(modelName);
    ExtensionFilter extensionFilter = buildExtensionFilter(allowedExtensions);
    long maxFileBytes = ingestMaxFileBytes();

    try (Connection c = openConnection(config, null)) {

      boolean withMetadata = RagTools.hasMetadataColumn(c, table);
      int inserted;

      if (withMetadata) {
        String sql = String.format(
                SqlQueries.INSERT_FROM_OCI_BUCKET_QUERY,
                quoteIdent(table),
                quoteIdent(textColumn),
                quoteIdent(embeddingColumn),
                extensionFilter.condition(),
                quoteIdent(table)
        );
        try (PreparedStatement ps = c.prepareStatement(sql)) {
          ps.setString(1, bucketUri);        // source_uri prefix in metadata
          ps.setString(2, credentialName);   // LIST_OBJECTS credential (null = public)
          ps.setString(3, bucketUri);        // LIST_OBJECTS bucket uri
          ps.setString(4, effectivePrefix);  // LIKE prefix filter
          ps.setLong(5, maxFileBytes);       // LIST_OBJECTS bytes filter
          int nextIndex = bindExtensionPatterns(ps, 6, extensionFilter.patterns());
          ps.setInt(nextIndex++, maxObjects);
          ps.setString(nextIndex++, credentialName); // GET_OBJECT credential (null = public)
          ps.setString(nextIndex++, bucketUri);      // GET_OBJECT base uri
          ps.setString(nextIndex++, chunkParams);
          ps.setString(nextIndex++, embeddingParams);
          ps.setString(nextIndex, bucketUri);        // NOT EXISTS dedup base uri
          inserted = ps.executeUpdate();
        }
      } else {
        String sql = String.format(
                SqlQueries.INSERT_FROM_OCI_BUCKET_NO_METADATA_QUERY,
                quoteIdent(table),
                quoteIdent(textColumn),
                quoteIdent(embeddingColumn),
                extensionFilter.condition()
        );
        try (PreparedStatement ps = c.prepareStatement(sql)) {
          ps.setString(1, credentialName);   // LIST_OBJECTS credential (null = public)
          ps.setString(2, bucketUri);        // LIST_OBJECTS bucket uri
          ps.setString(3, effectivePrefix);  // LIKE prefix filter
          ps.setLong(4, maxFileBytes);       // LIST_OBJECTS bytes filter
          int nextIndex = bindExtensionPatterns(ps, 5, extensionFilter.patterns());
          ps.setInt(nextIndex++, maxObjects);
          ps.setString(nextIndex++, credentialName); // GET_OBJECT credential (null = public)
          ps.setString(nextIndex++, bucketUri);      // GET_OBJECT base uri
          ps.setString(nextIndex++, chunkParams);
          ps.setString(nextIndex, embeddingParams);
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

    try {
      Path ingestRoot = resolveIngestRootDir();
      long maxFileBytes = ingestMaxFileBytes();

      try (Connection c = openConnection(config, null)) {
        boolean withMetadata = RagTools.hasMetadataColumn(c, table);
        int totalChunks = 0;
        for (String filePath : filePaths) {
          try {
            Path path = validateLocalIngestFile(filePath, ingestRoot, maxFileBytes);
            byte[] fileBytes = Files.readAllBytes(path);
            String fullPath  = path.toString();
            String displayName  = path.getFileName().toString();
            String sourceUri = path.toUri().toString();

            // Pre-check deduplication so we can distinguish "already exists" from "no text extracted"
            if (withMetadata && RagTools.fileExistsInVectorStore(c, table, sourceUri)) {
              task.results.add(Map.of(
                      "file",   displayName,
                      "status", "skipped",
                      "reason", "File already exists in vector store"));
              continue;
            }

            int chunks = RagTools.insertFileWithNativeChunking(
                    c, table, textColumn, embeddingColumn, modelName, fileBytes, fullPath, chunkParams);
            if (chunks == 0) {
              task.results.add(Map.of(
                      "file",   displayName,
                      "status", "skipped",
                      "reason", "No text could be extracted (image or unsupported file format)"));
            } else {
              totalChunks += chunks;
              task.results.add(Map.of(
                      "file",          displayName,
                      "status",        "success",
                      "chunksCreated", chunks));
            }
          } catch (Exception e) {
            task.results.add(Map.of(
                    "file",   displayFileName(filePath),
                    "status", "error",
                    "error",  errorMessage(e)));
          }
        }
        task.totalChunksCreated = totalChunks;
        task.status             = "COMPLETED";
        task.completedAt        = Instant.now();
      }

    } catch (Exception e) {
      task.errorMessage = errorMessage(e);
      task.status       = "FAILED";
      task.completedAt  = Instant.now();
    }
  }

  /**
   * Validates the number of local files accepted in one embedding task.
   */
  static void validateLocalIngestFileCount(List<String> filePaths) {
    if (filePaths == null || filePaths.isEmpty()) {
      throw new IllegalArgumentException("filePaths must not be empty");
    }
    if (filePaths.size() > MAX_LOCAL_INGEST_FILES) {
      throw new IllegalArgumentException(
              "Too many local ingest files; maximum is " + MAX_LOCAL_INGEST_FILES);
    }
  }

  /**
   * Resolves the configured ingest root directory to its real filesystem path.
   *
   * @return canonical ingest root directory
   */
  private static Path resolveIngestRootDir() throws IOException {
    String root = LoadedConstants.INGEST_ROOT_DIR;
    if (root == null || root.isBlank()) {
      throw new IllegalStateException("Local file ingestion requires -DingestRootDir");
    }

    Path realRoot = Paths.get(root).toRealPath();
    if (!Files.isDirectory(realRoot)) {
      throw new IllegalStateException("Ingest root directory is not a directory");
    }
    return realRoot;
  }

  /**
   * Returns the configured ingest max file size in bytes, using a megabyte property.
   *
   * @return maximum allowed file size in bytes
   */
  private static long ingestMaxFileBytes() {
    String value = LoadedConstants.INGEST_MAX_FILE_SIZE_MB;
    long maxFileSizeMb;
    try {
      maxFileSizeMb = (value == null || value.isBlank())
              ? DEFAULT_INGEST_MAX_FILE_SIZE_MB
              : Long.parseLong(value.trim());
    } catch (NumberFormatException e) {
      throw new IllegalStateException("ingestMaxFileSizeMb must be a number", e);
    }
    if (maxFileSizeMb <= 0) {
      throw new IllegalStateException("ingestMaxFileSizeMb must be greater than zero");
    }
    return maxFileSizeMb * 1024L * 1024L;
  }

  /**
   * Validates a caller-provided local file path before reading it.
   *
   * @return canonical file path that is inside the configured ingest root
   */
  private static Path validateLocalIngestFile(
          String filePath, Path ingestRoot, long maxFileBytes) throws IOException {
    if (filePath == null || filePath.isBlank()) {
      throw new IllegalArgumentException("File path must not be blank");
    }

    Path path = Paths.get(filePath).toRealPath();
    if (!Files.isRegularFile(path)) {
      throw new IllegalArgumentException("Path is not a regular file");
    }
    if (!path.startsWith(ingestRoot)) {
      throw new IllegalArgumentException("File is outside the configured ingest root");
    }
    validateLocalIngestFileName(path.getFileName().toString());

    long fileSize = Files.size(path);
    if (fileSize > maxFileBytes) {
      throw new IllegalArgumentException("File exceeds max local ingest size");
    }
    return path;
  }

  /**
   * Validates that a local ingest file has an allowed document extension.
   */
  private static void validateLocalIngestFileName(String fileName) {
    String lowerName = fileName.toLowerCase(Locale.ROOT);
    int dot = lowerName.lastIndexOf('.');
    String extension = dot >= 0 ? lowerName.substring(dot + 1) : "";
    if (!LOCAL_INGEST_ALLOWED_EXTENSIONS.contains(extension)) {
      throw new IllegalArgumentException("File extension is not allowed for local ingestion");
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
   * Returns an empty string when the list is empty, meaning no extension filter is applied.
   *
   * @param extensions caller-provided extensions, with or without a leading dot
   * @return SQL condition with bind placeholders and the matching bind values
   */
  static ExtensionFilter buildExtensionFilter(List<String> extensions) {
    if (extensions == null || extensions.isEmpty()) {
      return new ExtensionFilter("", List.of());
    }

    List<String> patterns = extensions.stream()
            .map(EmbeddingTaskManager::normalizeExtensionPattern)
            .toList();
    String conditions = patterns.stream()
            .map(pattern -> "LOWER(object_name) LIKE ?")
            .collect(java.util.stream.Collectors.joining(" OR "));
    return new ExtensionFilter("AND (" + conditions + ")", patterns);
  }

  /**
   * Validates and converts one extension into a case-insensitive SQL LIKE pattern.
   *
   * @param extension extension such as {@code pdf} or {@code .pdf}
   * @return pattern such as {@code %.pdf}
   */
  private static String normalizeExtensionPattern(String extension) {
    String value = extension == null ? "" : extension.trim().toLowerCase(Locale.ROOT);
    if (value.startsWith(".")) {
      value = value.substring(1);
    }
    if (!value.matches(SIMPLE_FILE_EXTENSION)) {
      throw new IllegalArgumentException("Invalid allowedExtensions value");
    }
    return "%." + value;
  }

  /**
   * Binds extension LIKE patterns and returns the next available bind index.
   */
  private static int bindExtensionPatterns(
          PreparedStatement ps, int startIndex, List<String> patterns) throws SQLException {
    int index = startIndex;
    for (String pattern : patterns) {
      ps.setString(index++, pattern);
    }
    return index;
  }

  /**
   * Holds the SQL fragment and bind values for an extension filter.
   */
  record ExtensionFilter(String condition, List<String> patterns) {}

  private static String errorMessage(Exception e) {
    if (e instanceof IllegalArgumentException || e instanceof IllegalStateException) {
      return e.getMessage() != null ? e.getMessage() : e.getClass().getSimpleName();
    }
    return "Embedding task failed";
  }

  private static String displayFileName(String filePath) {
    if (filePath == null || filePath.isBlank()) {
      return "unknown";
    }
    try {
      Path fileName = Paths.get(filePath).getFileName();
      return fileName == null ? "unknown" : fileName.toString();
    } catch (Exception e) {
      return "unknown";
    }
  }

  private static String quoteIdent(String name) {
    return "\"" + name.toUpperCase().replace("\"", "\"\"") + "\"";
  }
}
