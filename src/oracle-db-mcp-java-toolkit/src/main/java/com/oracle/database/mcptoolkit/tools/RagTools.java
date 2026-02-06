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

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static com.oracle.database.mcptoolkit.Utils.*;
import static com.oracle.database.mcptoolkit.tools.ToolSchemas.SIMILARITY_SEARCH;

/**
 * RAG (Retrieval-Augmented Generation) tools.
 * <p>
 * This class provides tools for RAG applications, including similarity search
 * using vector embeddings.
 */
public class RagTools {

  private static final String DEFAULT_VECTOR_TABLE            = "profile_oracle";
  private static final String DEFAULT_VECTOR_DATA_COLUMN      = "text";
  private static final String DEFAULT_VECTOR_EMBEDDING_COLUMN = "embedding";
  private static final String DEFAULT_VECTOR_MODEL_NAME       = "doc_model";
  private static final int    DEFAULT_VECTOR_TEXT_FETCH_LIMIT = 4000;

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

}
