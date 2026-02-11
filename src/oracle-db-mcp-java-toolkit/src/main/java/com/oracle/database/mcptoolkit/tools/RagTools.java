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
    tools.add(getCreateVectorStoreTool(config));
    tools.add(getInsertFileWithEmbeddingTool(config));
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
   * List all vector stores (tables with VECTOR columns).
   */
  public static McpServerFeatures.SyncToolSpecification getListVectorStoresTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("list-vector-stores")
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
   * List all vector embedding models.
   */
  public static McpServerFeatures.SyncToolSpecification getListVectorModelsTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("list-vector-models")
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
   * Create a new vector store table.
   */
  public static McpServerFeatures.SyncToolSpecification getCreateVectorStoreTool(ServerConfig config) {
    return McpServerFeatures.SyncToolSpecification.builder()
      .tool(McpSchema.Tool.builder()
         .name("create-vector-store")
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
   * List all vector stores (tables with VECTOR columns).
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
   * List all vector embedding models.
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
   * Create a new vector store table.
   * <p>
   * - ID and CREATED_AT are always present — every table needs a PK and insert timestamp.
   * - EMBEDDING is NOT NULL — a row without a vector has no purpose.
   * - When metadata is enabled, a functional index on source_file is created automatically
   *   to make the NOT EXISTS deduplication check fast.
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
   * Insert a file using Oracle's native extraction pipeline in a single atomic SQL statement.
   * Returns the number of chunks inserted (0 means file already existed — dedup fired).
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