/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

import com.fasterxml.jackson.databind.json.JsonMapper;
import com.oracle.database.mcptoolkit.ServerConfig;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.spec.McpSchema;

import java.nio.file.Paths;
import java.sql.*;
import java.util.*;

import static com.oracle.database.mcptoolkit.Utils.*;
import static com.oracle.database.mcptoolkit.tools.ToolSchemas.*;

/**
 * RAG (Retrieval-Augmented Generation) tools.
 *
 * <p>The available tools are:</p>
 * <ul>
 *   <li><strong>similarity-search</strong>: Semantic vector similarity search.</li>
 *   <li><strong>vector-store</strong>: Create or list vector store tables (action=create, list).</li>
 *   <li><strong>vector-model</strong>: List or drop ONNX embedding models (action=list, drop).</li>
 *   <li><strong>embed</strong>: Embed documents from local files, Oracle tables, or OCI Object Storage
 *       (action=file, action=files, table, object, bucket). All actions are asynchronous and return a taskId.</li>
 *   <li><strong>task</strong>: Track background embedding tasks (action=status, list).</li>
 * </ul>
 */
public class RagTools {

  private static final String DEFAULT_VECTOR_TABLE            = "profile_oracle";
  private static final String DEFAULT_VECTOR_DATA_COLUMN      = "text";
  private static final String DEFAULT_VECTOR_EMBEDDING_COLUMN = "embedding";
  private static final String DEFAULT_VECTOR_MODEL_NAME       = "doc_model";
  private static final int    DEFAULT_VECTOR_TEXT_FETCH_LIMIT = 4000;
  private static final String DEFAULT_CHUNK_PARAMS            = "{\"max\": 500, \"overlap\": 50}";

  private RagTools() {}

  /**
   * Returns a list of all RAG tool specifications based on the provided server configuration.
   * <p>
   * The returned list includes tool specifications for RAG applications, such as similarity search
   * using vector embeddings. The tools are filtered based on the configuration settings.
   *
   * @param config the server configuration to use for determining which tools to include
   * @return a list of tool specifications for RAG tools
   */
  public static List<McpServerFeatures.SyncToolSpecification> getTools(ServerConfig config) {
    List<McpServerFeatures.SyncToolSpecification> tools = new ArrayList<>();
    tools.add(getSimilaritySearchTool(config));
    tools.add(getVectorStoreTool(config));
    tools.add(getVectorModelTool(config));
    tools.add(getEmbedTool(config));
    tools.add(getTaskTool());
    tools.addAll(ObjectStorageRagTools.getTools(config));
    return tools;
  }

  /**
   * Returns a tool specification for the {@code similarity-search} tool.
   * <p>
   * This tool allows users to perform similarity searches using vector embeddings.
   * The tool's behavior is configured based on the provided server configuration.
   * <p>
   * The tool accepts the following input arguments:
   * <ul>
   *   <li>{@code question}: the natural-language query text (required, non-blank)</li>
   *   <li>{@code topK}: the maximum number of rows to return (optional, default=5, clamped to [1, 100])</li>
   *   <li>{@code table}: the table name containing text + embedding columns (optional, default="profile_oracle")</li>
   *   <li>{@code dataColumn}: the column holding the text/CLOB to return (optional, default="text")</li>
   *   <li>{@code embeddingColumn}: the vector column used by the similarity function (optional, default="embedding")</li>
   *   <li>{@code modelName}: the database vector model used to embed the question (optional, default="doc_model")</li>
   *   <li>{@code textFetchLimit}: the substring length to return from the text column (optional, default=4000)</li>
   * </ul>
   * <p>
   * The tool returns a list of text snippets ranked by similarity, along with a structured content map containing the results.
   *
   * @param config the server configuration to use for determining the tool's behavior
   * @return a tool specification for the {@code similarity-search} tool
   */
  public static McpServerFeatures.SyncToolSpecification getSimilaritySearchTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("similarity-search")
         .title("Similarity Search")
         .description("Semantic vector similarity over a table with (text, embedding) columns")
         .inputSchema(SIMILARITY_SEARCH)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection c = openConnection(config, null)) {
          Map<String, Object> arguments = callReq.arguments();
          String question = String.valueOf(arguments.get("question"));
          if (question == null || question.isBlank()) {
            return new McpSchema.CallToolResult("Question must be non-blank", true);
          }
          int topK;
          try {
            topK = Integer.parseInt(String.valueOf(arguments.getOrDefault("topK", 5)));
          } catch (NumberFormatException e) {
            topK = 5;
          }
          topK = Math.max(1, Math.min(100, topK));

          String table = getOrDefault(arguments.get("table"), DEFAULT_VECTOR_TABLE);
          String dataColumn = getOrDefault(arguments.get("dataColumn"), DEFAULT_VECTOR_DATA_COLUMN);
          String embeddingColumn = getOrDefault(arguments.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
          String modelName = getOrDefault(arguments.get("modelName"), DEFAULT_VECTOR_MODEL_NAME);

          int textFetchLimit = DEFAULT_VECTOR_TEXT_FETCH_LIMIT;
          Object limitArg = arguments.get("textFetchLimit");
          if (limitArg != null) {
            try {
              textFetchLimit = Math.max(1, Integer.parseInt(String.valueOf(limitArg)));
            }
            catch (NumberFormatException ignored) {}
          }

          List<String> results = runSimilaritySearch(
                  c, table, dataColumn, embeddingColumn, modelName, textFetchLimit, question, topK);

          return McpSchema.CallToolResult.builder()
                  .structuredContent(Map.of("rows", results))
                  .addTextContent(new JsonMapper().writeValueAsString(results))
                  .build();
        }
      }))
    .build();
  }

  /**
   * Returns a tool specification for {@code vector-store}.
   * <p>
   * action=create — create a new vector store table.<br>
   * action=list   — list all existing vector stores.
   *
   * @param config server configuration
   * @return tool specification
   */
  public static McpServerFeatures.SyncToolSpecification getVectorStoreTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("vector-store")
         .title("Vector Store")
         .description("Manage vector stores. action=create (needs tableName), list (no args).")
         .inputSchema(VECTOR_STORE)
         .build())
      .callHandler((exchange, callReq) -> {
        String action = String.valueOf(callReq.arguments().getOrDefault("action", ""));
        return switch (action) {
          case "create" -> tryCall(() -> {
            try (Connection c = openConnection(config, null)) {
              Map<String, Object> args = callReq.arguments();
              String  tableName       = String.valueOf(args.get("tableName"));
              String  textColumn      = getOrDefault(args.get("textColumn"),      DEFAULT_VECTOR_DATA_COLUMN);
              String  embeddingColumn = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
              Integer dimensions      = parseIntegerOrNull(args.get("dimensions"));
              boolean includeMetadata = !Boolean.FALSE.equals(args.get("includeMetadata"));

              createVectorStore(c, tableName, textColumn, embeddingColumn, dimensions, includeMetadata);

              String dimInfo = (dimensions == null) ? "flexible (*)" : String.valueOf(dimensions);
              return McpSchema.CallToolResult.builder()
                      .structuredContent(Map.of(
                              "tableName",       tableName,
                              "textColumn",      textColumn,
                              "embeddingColumn", embeddingColumn,
                              "dimensions",      dimInfo,
                              "hasMetadata",     includeMetadata))
                      .addTextContent("Vector store '" + tableName + "' created with " + dimInfo + " dimensions")
                      .build();
            }
          });
          case "list" -> tryCall(() -> {
            try (Connection c = openConnection(config, null)) {
              List<Map<String, Object>> stores = listVectorStores(c);
              return McpSchema.CallToolResult.builder()
                      .structuredContent(Map.of("vectorStores", stores))
                      .addTextContent(new JsonMapper().writeValueAsString(stores))
                      .build();
            }
          });
          default -> new McpSchema.CallToolResult(
                  "Unknown action '" + action + "'. Must be one of: create, list", true);
        };
      })
    .build();
  }

  /**
   * Returns a tool specification for {@code vector-model}.
   * <p>
   * action=list — list all ONNX embedding models.<br>
   * action=drop — drop a model by name.
   *
   * @param config server configuration
   * @return tool specification
   */
  public static McpServerFeatures.SyncToolSpecification getVectorModelTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("vector-model")
         .title("Vector Model")
         .description("Manage ONNX embedding models. action=list (no args), drop (needs modelName).")
         .inputSchema(VECTOR_MODEL)
         .build())
      .callHandler((exchange, callReq) -> {
        String action = String.valueOf(callReq.arguments().getOrDefault("action", ""));
        return switch (action) {
          case "list" -> tryCall(() -> {
            try (Connection c = openConnection(config, null)) {
              List<Map<String, Object>> models = listVectorModels(c);
              return McpSchema.CallToolResult.builder()
                      .structuredContent(Map.of("models", models))
                      .addTextContent(new JsonMapper().writeValueAsString(models))
                      .build();
            }
          });
          case "drop" -> tryCall(() -> {
            try (Connection c = openConnection(config, null)) {
              String modelName = String.valueOf(callReq.arguments().get("modelName"));
              dropVectorModel(c, modelName);
              return McpSchema.CallToolResult.builder()
                      .structuredContent(Map.of("modelName", modelName, "status", "dropped"))
                      .addTextContent("Model '" + modelName + "' has been dropped successfully.")
                      .build();
            }
          });
          default -> new McpSchema.CallToolResult(
                  "Unknown action '" + action + "'. Must be one of: list, drop", true);
        };
      })
    .build();
  }

  /**
   * Returns a tool specification for {@code embed}.
   * <p>
   * All actions run in the background via {@link EmbeddingTaskManager} and return a task ID immediately.
   * OCI actions (object, bucket) delegate URI construction to {@link ObjectStorageRagTools}.
   *
   * @param config server configuration
   * @return tool specification
   */
  public static McpServerFeatures.SyncToolSpecification getEmbedTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("embed")
         .title("Embed")
         .description("Embed documents into a vector store. "
                 + "action=file (single local file, needs filePath), "
                 + "action=files (batch of local files, needs filePaths array), "
                 + "action=table (from an existing Oracle table), "
                 + "action=object (single OCI Object Storage file), "
                 + "action=bucket (all files in an OCI bucket). "
                 + "All actions run in the background — returns a taskId immediately. "
                 + "Show the taskId to the user and wait for them to ask for a status check.")
         .inputSchema(EMBED)
         .build())
      .callHandler((exchange, callReq) -> {
        String action = String.valueOf(callReq.arguments().getOrDefault("action", ""));
        return switch (action) {
          case "file" -> tryCall(() -> {
            Map<String, Object> args = callReq.arguments();
            String table           = String.valueOf(args.get("table"));
            String textColumn      = getOrDefault(args.get("textColumn"),      DEFAULT_VECTOR_DATA_COLUMN);
            String embeddingColumn = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
            String modelName       = getOrDefault(args.get("modelName"),       DEFAULT_VECTOR_MODEL_NAME);
            String chunkParams     = getOrDefault(args.get("chunkParams"),     DEFAULT_CHUNK_PARAMS);

            Object rawFilePath = args.get("filePath");
            if (rawFilePath == null) {
              return new McpSchema.CallToolResult("Provide filePath (single file path)", true);
            }
            List<String> filePaths = List.of(rawFilePath.toString());

            String taskId = EmbeddingTaskManager.getInstance().submitLocalFiles(
                    config, table, filePaths, textColumn, embeddingColumn, modelName, chunkParams);

            LinkedHashMap<String, Object> result = new LinkedHashMap<>();
            result.put("taskId",     taskId);
            result.put("status",     "PENDING");
            result.put("totalFiles", filePaths.size());
            result.put("table",      table);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          case "files" -> tryCall(() -> {
            Map<String, Object> args = callReq.arguments();
            String table           = String.valueOf(args.get("table"));
            String textColumn      = getOrDefault(args.get("textColumn"),      DEFAULT_VECTOR_DATA_COLUMN);
            String embeddingColumn = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
            String modelName       = getOrDefault(args.get("modelName"),       DEFAULT_VECTOR_MODEL_NAME);
            String chunkParams     = getOrDefault(args.get("chunkParams"),     DEFAULT_CHUNK_PARAMS);

            Object rawFilePaths = args.get("filePaths");
            if (!(rawFilePaths instanceof List<?>)) {
              return new McpSchema.CallToolResult("Provide filePaths (array of file paths)", true);
            }
            List<String> filePaths = ((List<?>) rawFilePaths).stream().map(Object::toString).toList();
            if (filePaths.isEmpty()) {
              return new McpSchema.CallToolResult("filePaths must not be empty", true);
            }

            String taskId = EmbeddingTaskManager.getInstance().submitLocalFiles(
                    config, table, filePaths, textColumn, embeddingColumn, modelName, chunkParams);

            LinkedHashMap<String, Object> result = new LinkedHashMap<>();
            result.put("taskId",     taskId);
            result.put("status",     "PENDING");
            result.put("totalFiles", filePaths.size());
            result.put("table",      table);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          case "table" -> tryCall(() -> {
            Map<String, Object> args = callReq.arguments();
            String sourceTable   = String.valueOf(args.get("sourceTable"));
            String sourceTextCol = String.valueOf(args.get("sourceTextColumn"));
            String sourceIdCol   = String.valueOf(args.get("sourceIdColumn"));
            String targetTable   = String.valueOf(args.get("targetTable"));
            String textCol       = getOrDefault(args.get("textColumn"),      DEFAULT_VECTOR_DATA_COLUMN);
            String embeddingCol  = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
            String metadataCol   = getOrDefault(args.get("metadataColumn"),  "METADATA");
            String modelName     = getOrDefault(args.get("modelName"),       DEFAULT_VECTOR_MODEL_NAME);
            String chunkParams   = getOrDefault(args.get("chunkParams"),     DEFAULT_CHUNK_PARAMS);

            String taskId = EmbeddingTaskManager.getInstance().submitTableEmbedding(
                    config, sourceTable, sourceTextCol, sourceIdCol,
                    targetTable, textCol, embeddingCol, metadataCol, modelName, chunkParams);

            LinkedHashMap<String, Object> result = new LinkedHashMap<>();
            result.put("taskId",      taskId);
            result.put("status",      "PENDING");
            result.put("sourceTable", sourceTable);
            result.put("targetTable", targetTable);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          case "object" -> tryCall(() -> {
            Map<String, Object> args = callReq.arguments();
            String credentialName  = ObjectStorageRagTools.nullableCredential(args.get("credentialName"));
            String table           = String.valueOf(args.get("table"));
            String textColumn      = getOrDefault(args.get("textColumn"),      DEFAULT_VECTOR_DATA_COLUMN);
            String embeddingColumn = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
            String modelName       = getOrDefault(args.get("modelName"),       DEFAULT_VECTOR_MODEL_NAME);
            String chunkParams     = getOrDefault(args.get("chunkParams"),     DEFAULT_CHUNK_PARAMS);

            // objectUrl (direct or PAR) takes priority over individual components
            String rawObjectUrl = getOrDefault(args.get("objectUrl"), null);
            String objectUri = (rawObjectUrl != null) ? rawObjectUrl
                    : ObjectStorageRagTools.buildObjectUri(
                            String.valueOf(args.get("region")),
                            String.valueOf(args.get("namespace")),
                            String.valueOf(args.get("bucketName")),
                            String.valueOf(args.get("objectName")));

            String taskId = EmbeddingTaskManager.getInstance().submitSingleFile(
                    config, table, credentialName, objectUri,
                    textColumn, embeddingColumn, modelName, chunkParams);

            Map<String, Object> result = Map.of(
                    "taskId",    taskId,
                    "status",    "PENDING",
                    "objectUri", objectUri,
                    "table",     table);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          case "bucket" -> tryCall(() -> {
            Map<String, Object> args = callReq.arguments();
            String credentialName  = ObjectStorageRagTools.nullableCredential(args.get("credentialName"));
            String prefix          = getOrDefault(args.get("prefix"), "");
            String table           = String.valueOf(args.get("table"));
            String textColumn      = getOrDefault(args.get("textColumn"),      DEFAULT_VECTOR_DATA_COLUMN);
            String embeddingColumn = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
            String modelName       = getOrDefault(args.get("modelName"),       DEFAULT_VECTOR_MODEL_NAME);
            String chunkParams     = getOrDefault(args.get("chunkParams"),     DEFAULT_CHUNK_PARAMS);
            @SuppressWarnings("unchecked")
            List<String> allowedExtensions = args.get("allowedExtensions") instanceof List<?>
                    ? ((List<?>) args.get("allowedExtensions")).stream().map(Object::toString).toList()
                    : List.of();

            // bucketUrl (direct or PAR) takes priority over individual components
            String rawBucketUrl = getOrDefault(args.get("bucketUrl"), null);
            String bucketUri = (rawBucketUrl != null) ? rawBucketUrl
                    : ObjectStorageRagTools.buildBucketUri(
                            String.valueOf(args.get("region")),
                            String.valueOf(args.get("namespace")),
                            String.valueOf(args.get("bucketName")));

            String taskId = EmbeddingTaskManager.getInstance().submitBucket(
                    config, table, credentialName, bucketUri, prefix, allowedExtensions,
                    textColumn, embeddingColumn, modelName, chunkParams);

            LinkedHashMap<String, Object> result = new LinkedHashMap<>();
            result.put("taskId",    taskId);
            result.put("status",    "PENDING");
            result.put("bucketUri", bucketUri);
            result.put("prefix",    prefix);
            if (!allowedExtensions.isEmpty()) result.put("allowedExtensions", allowedExtensions);
            result.put("table",     table);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });

          default -> new McpSchema.CallToolResult(
                  "Unknown action '" + action + "'. Must be one of: file, files, table, object, bucket", true);
        };
      })
    .build();
  }

  /**
   * Returns a tool specification for {@code task}.
   * <p>
   * action=status — get status and progress of a specific background task.<br>
   * action=list   — list all background tasks in this server session.
   *
   * @return tool specification (no server config needed)
   */
  public static McpServerFeatures.SyncToolSpecification getTaskTool() {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("task")
         .title("Task")
         .description("Track background embedding tasks. action=status (needs taskId), list (no args).")
         .inputSchema(TASK)
         .build())
      .callHandler((exchange, callReq) -> {
        String action = String.valueOf(callReq.arguments().getOrDefault("action", ""));
        return switch (action) {
          case "status" -> tryCall(() -> {
            String taskId = String.valueOf(callReq.arguments().get("taskId"));
            EmbeddingTaskManager.EmbeddingTask task = EmbeddingTaskManager.getInstance().getTask(taskId);
            if (task == null) {
              return new McpSchema.CallToolResult("Task not found: " + taskId, true);
            }
            Map<String, Object> result = EmbeddingTaskManager.taskToMap(task);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });
          case "list" -> tryCall(() -> {
            List<Map<String, Object>> taskList = EmbeddingTaskManager.getInstance().getAllTasks()
                    .stream()
                    .sorted((a, b) -> b.submittedAt.compareTo(a.submittedAt))
                    .map(EmbeddingTaskManager::taskToMap)
                    .collect(java.util.stream.Collectors.toList());

            LinkedHashMap<String, Object> result = new LinkedHashMap<>();
            result.put("totalTasks", taskList.size());
            result.put("tasks",      taskList);
            return McpSchema.CallToolResult.builder()
                    .structuredContent(result)
                    .addTextContent(new JsonMapper().writeValueAsString(result))
                    .build();
          });
          default -> new McpSchema.CallToolResult(
                  "Unknown action '" + action + "'. Must be one of: status, list", true);
        };
      })
    .build();
  }

  /**
   * Executes a vector similarity search against the configured table.
   *
   * <p>Uses the columns/table/model declared in {@link ServerConfig} and returns the
   * text fragments of the top matches.</p>
   *
   * @param c an open JDBC connection
   * @param table table name containing text + embedding columns
   * @param dataColumn column holding the text/CLOB to return
   * @param embeddingColumn vector column used by the similarity function
   * @param modelName database vector model used to embed the question
   * @param textFetchLimit substring length to return from the text column
   * @param question natural-language query text
   * @param topK maximum number of rows to return (clamped by caller)
   * @return list of text snippets ranked by similarity
   * @throws java.sql.SQLException if the SQL execution fails
   */
  private static List<String> runSimilaritySearch(Connection c,
                                                  String table,
                                                  String dataColumn,
                                                  String embeddingColumn,
                                                  String modelName,
                                                  int textFetchLimit,
                                                  String question,
                                                  int topK) throws SQLException {
    String sql = String.format(
        SqlQueries.SIMILARITY_SEARCH_QUERY,
        quoteIdent(dataColumn.toUpperCase()), textFetchLimit, quoteIdent(table.toUpperCase()), quoteIdent(embeddingColumn.toUpperCase()), modelName
    );

    List<String> result = new ArrayList<>();
    try (PreparedStatement ps = c.prepareStatement(sql)) {
      ps.setString(1, question);
      ps.setInt(2, topK);
      try (ResultSet rs = ps.executeQuery()) {
        while (rs.next()) {
          result.add(rs.getString("text"));
        }
      }
    }
    return result;
  }

  /**
   * Retrieves all tables that contain vector embeddings.
   *
   * @param c database connection
   * @return list of vector stores with their columns and row counts
   * @throws SQLException if the query fails
   */
  private static List<Map<String, Object>> listVectorStores(Connection c) throws SQLException {
    Map<String, Map<String, Object>> storeMap = new LinkedHashMap<>();

    try (PreparedStatement ps = c.prepareStatement(SqlQueries.LIST_VECTOR_STORES_QUERY);
         ResultSet rs = ps.executeQuery()) {
      while (rs.next()) {
        String tableName = rs.getString("table_name");
        Map<String, Object> store = storeMap.computeIfAbsent(tableName, k -> {
          Map<String, Object> s = new LinkedHashMap<>();
          s.put("tableName",     tableName);
          s.put("vectorColumns", new ArrayList<String>());
          try {
            s.put("rowCount", rs.getLong("num_rows"));
          } catch (SQLException e) {
            throw new RuntimeException(e);
          }
          return s;
        });

        @SuppressWarnings("unchecked")
        List<String> cols = (List<String>) store.get("vectorColumns");
        cols.add(rs.getString("column_name"));
      }
    }

    return new ArrayList<>(storeMap.values());
  }

  /**
   * Retrieves all embedding models loaded in the database.
   *
   * @param c database connection
   * @return list of models with names, types, and sizes
   * @throws SQLException if the query fails
   */
  private static List<Map<String, Object>> listVectorModels(Connection c) throws SQLException {
    List<Map<String, Object>> results = new ArrayList<>();

    try (PreparedStatement ps = c.prepareStatement(SqlQueries.LIST_VECTOR_MODELS_QUERY);
         ResultSet rs = ps.executeQuery()) {
      while (rs.next()) {
        Map<String, Object> model = new LinkedHashMap<>();
        model.put("name",      rs.getString("model_name"));
        model.put("function",  rs.getString("mining_function"));
        model.put("algorithm", rs.getString("algorithm"));
        model.put("created",   rs.getTimestamp("creation_date"));
        model.put("size",      rs.getLong("model_size"));
        results.add(model);
      }
    }
    return results;
  }

  /**
   * Drops an ONNX embedding model from the database.
   *
   * @param c open JDBC connection
   * @param modelName name of the model to drop
   * @throws SQLException if the operation fails or the model doesn't exist
   */
  private static void dropVectorModel(Connection c, String modelName) throws SQLException {
    try (CallableStatement cs = c.prepareCall(SqlQueries.DROP_VECTOR_MODEL_QUERY)) {
      cs.setString(1, modelName);
      cs.execute();
    }
  }

  /**
   * Create a new vector store table.
   * <p>
   * Always includes an ID primary key and timestamp. When metadata is enabled,
   * also creates an index to accelerate duplicate file detection.
   *
   * @param c database connection
   * @param tableName name of the table to create
   * @param textColumn column for storing text chunks
   * @param embeddingColumn column for storing vectors
   * @param dimensions fixed vector size, or null for flexible
   * @param includeMetadata whether to enable document tracking and deduplication
   * @throws SQLException if table creation fails
   */
  private static void createVectorStore(
          Connection c, String tableName, String textColumn, String embeddingColumn,
          Integer dimensions, boolean includeMetadata) throws SQLException {

    StringBuilder sql = new StringBuilder("CREATE TABLE ");
    sql.append(quoteIdent(tableName.toUpperCase())).append(" (");

    sql.append("ID VARCHAR2(36) DEFAULT SYS_GUID() PRIMARY KEY, ");
    sql.append("CREATED_AT TIMESTAMP DEFAULT SYSTIMESTAMP, ");

    if (includeMetadata) {
      sql.append("METADATA JSON, ");
    }

    sql.append(quoteIdent(textColumn.toUpperCase())).append(" CLOB, ");

    if (dimensions == null) {
      sql.append(quoteIdent(embeddingColumn.toUpperCase())).append(" VECTOR(*, FLOAT32) NOT NULL");
    } else {
      sql.append(quoteIdent(embeddingColumn.toUpperCase())).append(" VECTOR(").append(dimensions).append(", FLOAT32) NOT NULL");
    }

    sql.append(")");

    try (Statement st = c.createStatement()) {
      st.executeUpdate(sql.toString());

      if (includeMetadata) {
        String indexSql = String.format(
                "CREATE INDEX %s ON %s (JSON_VALUE(METADATA, '$.source_uri'))",
                quoteIdent((tableName + "_SOURCE_IDX").toUpperCase()),
                quoteIdent(tableName.toUpperCase())
        );
        st.executeUpdate(indexSql);
      }
    }
  }

  /**
   * Processes and inserts a document into a vector store.
   *
   * @param c database connection
   * @param table target vector store
   * @param textColumn where to store text
   * @param embeddingColumn where to store vectors
   * @param modelName which embedding model to use
   * @param fileBytes raw file content
   * @param fullPath file path (used for deduplication)
   * @param chunkParams how to split the document
   * @return number of chunks inserted, or 0 if no text could be extracted from the file
   * @throws SQLException if insertion fails
   */
  static int insertFileWithNativeChunking(
          Connection c, String table, String textColumn, String embeddingColumn,
          String modelName, byte[] fileBytes, String fullPath,
          String chunkParams) throws SQLException {

    Blob fileBlob = c.createBlob();
    fileBlob.setBytes(1, fileBytes);

    String embeddingParams = buildEmbeddingParams(modelName);

    boolean withMetadata = hasMetadataColumn(c, table);

    if (withMetadata) {
      String sql = String.format(
              SqlQueries.INSERT_FILE_WITH_EMBEDDING_QUERY,
              quoteIdent(table.toUpperCase()),
              quoteIdent(textColumn.toUpperCase()),
              quoteIdent(embeddingColumn.toUpperCase()),
              quoteIdent(table.toUpperCase())
      );

      String documentId = UUID.randomUUID().toString();
      String sourceUri  = Paths.get(fullPath).toUri().toString(); // file:///path/to/file

      try (PreparedStatement ps = c.prepareStatement(sql)) {
        ps.setString(1, documentId);
        ps.setString(2, sourceUri);
        ps.setBlob(3, fileBlob);
        ps.setString(4, chunkParams);
        ps.setString(5, embeddingParams);
        ps.setString(6, sourceUri);
        return ps.executeUpdate();
      }

    } else {
      String sql = String.format(
              SqlQueries.INSERT_FILE_WITHOUT_METADATA_QUERY,
              quoteIdent(table.toUpperCase()),
              quoteIdent(textColumn.toUpperCase()),
              quoteIdent(embeddingColumn.toUpperCase())
      );

      try (PreparedStatement ps = c.prepareStatement(sql)) {
        ps.setBlob(1, fileBlob);
        ps.setString(2, chunkParams);
        ps.setString(3, embeddingParams);
        return ps.executeUpdate();
      }
    }
  }

  /**
   * Checks whether a table has a METADATA column.
   *
   * @param c database connection
   * @param table table name to inspect
   * @return {@code true} if the METADATA column exists
   * @throws SQLException if the query fails
   */
  static boolean hasMetadataColumn(Connection c, String table) throws SQLException {
    try (PreparedStatement ps = c.prepareStatement(SqlQueries.CHECK_METADATA_COLUMN_QUERY)) {
      ps.setString(1, table.toUpperCase());
      try (ResultSet rs = ps.executeQuery()) {
        return rs.next() && rs.getInt(1) > 0;
      }
    }
  }

  /**
   * Checks whether a file's source URI already exists in a vector store's METADATA column.
   *
   * @param c database connection
   * @param table target vector store table
   * @param sourceUri file URI to look up (e.g. {@code file:///path/to/file} or an OCI URL)
   * @return {@code true} if the file has already been embedded
   * @throws SQLException if the query fails
   */
  static boolean fileExistsInVectorStore(Connection c, String table, String sourceUri) throws SQLException {
    String sql = String.format(SqlQueries.CHECK_FILE_EXISTS_IN_STORE_QUERY, quoteIdent(table.toUpperCase()));
    try (PreparedStatement ps = c.prepareStatement(sql)) {
      ps.setString(1, sourceUri);
      try (ResultSet rs = ps.executeQuery()) {
        return rs.next() && rs.getInt(1) > 0;
      }
    }
  }

  /**
   * Builds the embedding parameters JSON required by {@code DBMS_VECTOR.UTL_TO_EMBEDDINGS}.
   *
   * @param modelName name of the ONNX embedding model loaded in the database
   * @return JSON string with provider and model fields
   */
  static String buildEmbeddingParams(String modelName) {
    return String.format("{\"provider\": \"database\", \"model\": \"%s\"}", modelName);
  }

  /**
   * Parse integer or return null if missing or invalid.
   */
  private static Integer parseIntegerOrNull(Object value) {
    if (value == null) return null;
    try {
      return Integer.parseInt(String.valueOf(value));
    } catch (Exception e) {
      return null;
    }
  }
}