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

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static com.oracle.database.mcptoolkit.Utils.*;
import static com.oracle.database.mcptoolkit.tools.ToolSchemas.*;

/**
 * RAG (Retrieval-Augmented Generation) tools.
 * <p>
 * Provides vector-based semantic search capabilities including similarity search,
 * vector store management, and document insertion with automatic chunking.
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
    tools.add(getListVectorStoresTool(config));
    tools.add(getListVectorModelsTool(config));
    tools.add(getDropVectorModelTool(config));
    tools.add(getCreateVectorStoreTool(config));
    tools.add(getInsertFileWithEmbeddingTool(config));
    tools.add(getEmbedFromTableTool(config));
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
   * Lists all tables configured for vector search.
   *
   * @param config server configuration
   * @return tool specification for {@code list-vector-stores}
   */
  public static McpServerFeatures.SyncToolSpecification getListVectorStoresTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("list-vector-stores")
         .title("List Vector Stores")
         .description("Lists all vector stores in a database.")
         .inputSchema(LIST_VECTOR_STORES)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection c = openConnection(config, null)) {
          List<Map<String, Object>> stores = listVectorStores(c);
          return McpSchema.CallToolResult.builder()
                  .structuredContent(Map.of("vectorStores", stores))
                  .addTextContent(new JsonMapper().writeValueAsString(stores))
                  .build();
        }
      }))
    .build();
  }

  /**
   * Lists all AI embedding models available in the database.
   *
   * @param config server configuration
   * @return tool specification for {@code list-vector-models}
   */
  public static McpServerFeatures.SyncToolSpecification getListVectorModelsTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("list-vector-models")
         .title("List Vector Models")
         .description("Lists all AI vector embedding models available in the Oracle Database")
         .inputSchema(LIST_VECTOR_MODELS)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection c = openConnection(config, null)) {
          List<Map<String, Object>> models = listVectorModels(c);
          return McpSchema.CallToolResult.builder()
                  .structuredContent(Map.of("models", models))
                  .addTextContent(new JsonMapper().writeValueAsString(models))
                  .build();
        }
      }))
    .build();
  }

  /**
   * Drops an ONNX embedding model from the Oracle schema.
   *
   * @param config server configuration
   * @return tool specification for {@code drop-vector-model}
   */
  public static McpServerFeatures.SyncToolSpecification getDropVectorModelTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("drop-vector-model")
         .title("Drop Vector Model")
         .description("Drop an ONNX embedding model from the Oracle Database")
         .inputSchema(DROP_VECTOR_MODEL)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection c = openConnection(config, null)) {
          Map<String, Object> args = callReq.arguments();
          String modelName = String.valueOf(args.get("modelName"));

          dropVectorModel(c, modelName);

          return McpSchema.CallToolResult.builder()
                  .structuredContent(Map.of(
                          "modelName", modelName,
                          "status", "dropped"
                  ))
                  .addTextContent("Model '" + modelName + "' has been dropped successfully.")
                  .build();
        }
      }))
    .build();
  }

  /**
   * Creates a new vector store table.
   *
   * @param config server configuration
   * @return tool specification for {@code create-vector-store}
   */
  public static McpServerFeatures.SyncToolSpecification getCreateVectorStoreTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("create-vector-store")
         .title("Create Vector Store")
         .description("Create a new vector store table with text and embedding columns")
         .inputSchema(CREATE_VECTOR_STORE)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection c = openConnection(config, null)) {
          Map<String, Object> args = callReq.arguments();

          String  tableName = String.valueOf(args.get("tableName"));
          String  textColumn = getOrDefault(args.get("textColumn"), DEFAULT_VECTOR_DATA_COLUMN);
          String  embeddingColumn = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
          Integer dimensions = parseIntegerOrNull(args.get("dimensions"));
          boolean includeMetadata = !Boolean.FALSE.equals(args.get("includeMetadata"));

          createVectorStore(c, tableName, textColumn, embeddingColumn, dimensions, includeMetadata);

          String dimInfo = (dimensions == null) ? "flexible (*)" : String.valueOf(dimensions);
          return McpSchema.CallToolResult.builder()
                  .structuredContent(Map.of(
                          "tableName",       tableName,
                          "textColumn",      textColumn,
                          "embeddingColumn", embeddingColumn,
                          "dimensions",      dimInfo,
                          "hasMetadata",     includeMetadata
                  ))
                  .addTextContent("Vector store '" + tableName + "' created successfully with " + dimInfo + " dimensions")
                  .build();
        }
      }))
    .build();
  }

  /**
   * Insert file with automatic extraction, chunking, and embedding.
   *
   * @param config server configuration
   * @return tool specification for {@code insert-file-with-embedding}
   */
  public static McpServerFeatures.SyncToolSpecification getInsertFileWithEmbeddingTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("insert-file-with-embedding")
         .title("Insert File With Embedding")
         .description("Insert file content (PDF, DOCX, TXT, etc.) using Oracle's native extraction. Automatically chunks and embeds.")
         .inputSchema(INSERT_FILE_WITH_EMBEDDING)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection c = openConnection(config, null)) {
          Map<String, Object> args = callReq.arguments();

          String table = String.valueOf(args.get("table"));
          String filePath = String.valueOf(args.get("filePath"));
          String textColumn = getOrDefault(args.get("textColumn"), DEFAULT_VECTOR_DATA_COLUMN);
          String embeddingColumn = getOrDefault(args.get("embeddingColumn"), DEFAULT_VECTOR_EMBEDDING_COLUMN);
          String modelName = getOrDefault(args.get("modelName"), DEFAULT_VECTOR_MODEL_NAME);
          String chunkParams = getOrDefault(args.get("chunkParams"), DEFAULT_CHUNK_PARAMS);

          Path path = Paths.get(filePath);
          if (!Files.exists(path)) {
            return new McpSchema.CallToolResult("File not found: " + filePath, true);
          }

          byte[] fileBytes = Files.readAllBytes(path);

          // The absolute path — stored in metadata and used for deduplication
          String fullPath = path.toAbsolutePath().toString();

          int chunksInserted = insertFileWithNativeChunking(
                                  c,
                                  table,
                                  textColumn,
                                  embeddingColumn,
                                  modelName,
                                  fileBytes,
                                  fullPath,
                                  chunkParams);

                // chunksInserted == 0 means file was already present
                if (chunksInserted == 0) {
                  return McpSchema.CallToolResult.builder()
                    .structuredContent(Map.of(
                            "table",         table,
                            "sourceFile",    fullPath,
                            "chunksCreated", 0,
                            "status",        "skipped",
                            "reason",        "File already exists in vector store"
                    ))
                    .addTextContent("File '" + fullPath + "' already exists in '" + table + "'. Skipping to avoid duplicates.")
          .build();
      }

      return McpSchema.CallToolResult.builder()
        .structuredContent(Map.of(
                "table",         table,
                "sourceFile",    fullPath,
                "chunksCreated", chunksInserted,
                "status",        "success"
        ))
              .addTextContent("Successfully processed '" + fullPath + "' and inserted " + chunksInserted + " chunks with embeddings")
              .build();
        }
      }))
    .build();
  }

  /**
   * Generates vector embeddings from text in an existing Oracle table and inserts
   * them into a target vector store.
   *
   * <p>The tool inspects the target table at runtime to determine whether a
   * {@code METADATA} column is present, and automatically selects the appropriate
   * INSERT pipeline:</p>
   * <ul>
   *   <li><strong>With metadata</strong>: each chunk row includes a JSON object
   *       containing {@code source_table}, {@code source_id}, {@code chunk_index},
   *       and {@code embedded_at}, allowing full traceability back to the origin row.</li>
   *   <li><strong>Without metadata</strong>: only the text chunk and vector embedding
   *       are inserted, with no additional tracking.</li>
   * </ul>
   *
   * @param config the server configuration used to open the database connection
   * @return a tool specification for the {@code embed-from-table} tool
   */
  public static McpServerFeatures.SyncToolSpecification getEmbedFromTableTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("embed-from-table")
         .title("Embed From Table")
         .description("Generate vector embeddings from text in an existing Oracle table and insert them into a vector store.")
         .inputSchema(ToolSchemas.EMBED_FROM_TABLE)
         .build())
      .callHandler((exchange, callReq) -> tryCall(() -> {
        try (Connection conn = openConnection(config, null)) {
          Map<String, Object> args = callReq.arguments();

          String sourceTable   = String.valueOf(args.get("sourceTable"));
          String sourceTextCol = String.valueOf(args.get("sourceTextColumn"));
          String sourceIdCol   = String.valueOf(args.get("sourceIdColumn"));
          String targetTable   = String.valueOf(args.get("targetTable"));
          String textCol       = getOrDefault(args.get("textColumn"),      "TEXT");
          String embeddingCol  = getOrDefault(args.get("embeddingColumn"), "EMBEDDING");
          String metadataCol   = getOrDefault(args.get("metadataColumn"),  "METADATA");
          String modelName     = getOrDefault(args.get("modelName"),       DEFAULT_VECTOR_MODEL_NAME);
          String chunkParams   = getOrDefault(args.get("chunkParams"),     DEFAULT_CHUNK_PARAMS);
          String embedParams   = "{\"provider\": \"database\", \"model\": \"" + modelName + "\"}";

          boolean withMetadata = hasMetadataColumn(conn, targetTable);

          String sql;
          if (withMetadata) {
            sql = String.format(SqlQueries.INSERT_EMBEDDINGS_FROM_TABLE,
                    targetTable,
                    textCol, embeddingCol, metadataCol,
                    sourceIdCol,
                    sourceIdCol,
                    sourceTable,
                    sourceTextCol
            );
          } else {
            sql = String.format(SqlQueries.INSERT_EMBEDDINGS_FROM_TABLE_NO_METADATA,
                    targetTable,
                    textCol, embeddingCol,
                    sourceTable,
                    sourceTextCol
            );
          }

          try (PreparedStatement stmt = conn.prepareStatement(sql)) {
            if (withMetadata) {
              stmt.setString(1, sourceTable);
              stmt.setString(2, chunkParams);
              stmt.setString(3, embedParams);
            } else {
              stmt.setString(1, chunkParams);
              stmt.setString(2, embedParams);
            }

            int inserted = stmt.executeUpdate();

            return McpSchema.CallToolResult.builder()
                    .structuredContent(Map.of(
                            "status",           "ok",
                            "rowsInserted",     inserted,
                            "source",           sourceTable,
                            "target",           targetTable,
                            "metadataTracking", withMetadata
                    ))
                    .addTextContent("Successfully embedded " + inserted + " chunks from "
                            + sourceTable + " into " + targetTable
                            + (withMetadata ? " (with metadata)" : " (no metadata column)") + ".")
                    .build();
          }
        }
      }))
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
        quoteIdent(dataColumn), textFetchLimit, quoteIdent(table), embeddingColumn, modelName
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
    Map<String, Map<String, Object>> storeMap = new java.util.LinkedHashMap<>();

    try (PreparedStatement ps = c.prepareStatement(SqlQueries.LIST_VECTOR_STORES_QUERY);
         ResultSet rs = ps.executeQuery()) {
      while (rs.next()) {
        String tableName = rs.getString("table_name");
        Map<String, Object> store = storeMap.computeIfAbsent(tableName, k -> {
          Map<String, Object> s = new java.util.LinkedHashMap<>();
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
        Map<String, Object> model = new java.util.LinkedHashMap<>();
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
    sql.append(quoteIdent(tableName)).append(" (");

    // Always present
    sql.append("ID VARCHAR2(36) DEFAULT SYS_GUID() PRIMARY KEY, ");
    sql.append("CREATED_AT TIMESTAMP DEFAULT SYSTIMESTAMP, ");

    if (includeMetadata) {
      sql.append("METADATA JSON, ");
    }

    sql.append(quoteIdent(textColumn)).append(" CLOB, ");

    if (dimensions == null) {
      sql.append(quoteIdent(embeddingColumn)).append(" VECTOR(*, FLOAT32) NOT NULL");
    } else {
      sql.append(quoteIdent(embeddingColumn)).append(" VECTOR(").append(dimensions).append(", FLOAT32) NOT NULL");
    }

    sql.append(")");

    try (Statement st = c.createStatement()) {
      st.executeUpdate(sql.toString());

      if (includeMetadata) {
        String indexSql = String.format(
                "CREATE INDEX %s ON %s (JSON_VALUE(METADATA, '$.source_file'))",
                quoteIdent(tableName + "_SOURCE_IDX"),
                quoteIdent(tableName)
        );
        st.executeUpdate(indexSql);
      }
    }
  }

  /**
   * Processes and inserts a document into a vector store.
   * <p>
   * Automatically extracts text, splits into chunks, generates embeddings, and stores
   * everything. For tables with metadata, prevents duplicate insertions of the same file.
   *
   * @param c database connection
   * @param table target vector store
   * @param textColumn where to store text
   * @param embeddingColumn where to store vectors
   * @param modelName which embedding model to use
   * @param fileBytes raw file content
   * @param fullPath file path (used for deduplication)
   * @param chunkParams how to split the document
   * @return number of chunks inserted (0 if file already exists)
   * @throws SQLException if insertion fails
   */
  private static int insertFileWithNativeChunking(
          Connection c, String table, String textColumn, String embeddingColumn,
          String modelName, byte[] fileBytes, String fullPath,
          String chunkParams) throws SQLException {

    Blob fileBlob = c.createBlob();
    fileBlob.setBytes(1, fileBytes);

    String embeddingParams = String.format(
            "{\"provider\": \"database\", \"model\": \"%s\"}", modelName);

    boolean withMetadata = hasMetadataColumn(c, table);

    if (withMetadata) {
      // Single atomic INSERT: extraction + chunking + embedding + metadata + dedup
      String sql = String.format(
              SqlQueries.INSERT_FILE_WITH_EMBEDDING_QUERY,
              quoteIdent(table),
              quoteIdent(textColumn),
              quoteIdent(embeddingColumn),
              quoteIdent(table)
      );

      String documentId = UUID.randomUUID().toString();

      try (PreparedStatement ps = c.prepareStatement(sql)) {
        ps.setString(1, documentId);
        ps.setString(2, fullPath);
        ps.setBlob(3, fileBlob);
        ps.setString(4, chunkParams);
        ps.setString(5, embeddingParams);
        ps.setString(6, fullPath);
        return ps.executeUpdate();
      }

    } else {
      String sql = String.format(
              SqlQueries.INSERT_FILE_WITHOUT_METADATA_QUERY,
              quoteIdent(table),
              quoteIdent(textColumn),
              quoteIdent(embeddingColumn)
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
   * Check if a table has a METADATA column.
   * Used to decide which INSERT query to use (with or without metadata/dedup).
   */
  private static boolean hasMetadataColumn(Connection c, String table) throws SQLException {
    try (PreparedStatement ps = c.prepareStatement(SqlQueries.CHECK_METADATA_COLUMN_QUERY)) {
      ps.setString(1, table.toUpperCase());
      try (ResultSet rs = ps.executeQuery()) {
        return rs.next() && rs.getInt(1) > 0;
      }
    }
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