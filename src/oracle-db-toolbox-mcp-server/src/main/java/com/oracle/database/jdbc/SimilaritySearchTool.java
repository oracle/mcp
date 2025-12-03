package com.oracle.database.jdbc;

import com.fasterxml.jackson.databind.json.JsonMapper;
import io.modelcontextprotocol.server.McpServerFeatures;
import io.modelcontextprotocol.spec.McpSchema;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

import static com.oracle.database.jdbc.Utils.openConnection;
import static com.oracle.database.jdbc.Utils.tryCall;
import static com.oracle.database.jdbc.Utils.getOrDefault;

public class SimilaritySearchTool {

  private static final Pattern SAFE_IDENT = Pattern.compile("[A-Za-z0-9_$.#]+");

  private static final String DEFAULT_VECTOR_TABLE            = "profile_oracle";
  private static final String DEFAULT_VECTOR_DATA_COLUMN      = "text";
  private static final String DEFAULT_VECTOR_EMBEDDING_COLUMN = "embedding";
  private static final String DEFAULT_VECTOR_MODEL_NAME       = "doc_model";
  private static final int    DEFAULT_VECTOR_TEXT_FETCH_LIMIT = 4000;
  private static final String SIMILARITY_SEARCH = """
    SELECT dbms_lob.substr(%s, %s, 1) AS text
    FROM %s
    ORDER BY VECTOR_DISTANCE(%s,
             TO_VECTOR(VECTOR_EMBEDDING(%s USING ? AS data)))
    FETCH FIRST ? ROWS ONLY
  """;

  static McpServerFeatures.SyncToolSpecification getSymilaritySearchTool(ServerConfig config) {

        return McpServerFeatures.SyncToolSpecification.builder()
            .tool(McpSchema.Tool.builder()
                .name("similarity_search")
                .title("Similarity Search")
                .description("Semantic vector similarity over a table with (text, embedding) columns")
                .inputSchema(ToolSchemas.SIMILARITY_SEARCH)
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
        SIMILARITY_SEARCH,
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
   * Escapes and quotes a potentially unsafe identifier for SQL use.
   *
   * @param ident identifier to quote
   * @return a quoted or validated identifier
   */
  static String quoteIdent(String ident) {
    if (ident == null) throw new IllegalArgumentException("identifier is null");
    String s = ident.trim();
    if (!SAFE_IDENT.matcher(s).matches()) {
      return "\"" + s.replace("\"", "\"\"") + "\"";
    }
    return s;
  }

}
