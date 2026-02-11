/*
 ** Oracle Database MCP Toolkit version 1.0.0
 **
 ** Copyright (c) 2025 Oracle and/or its affiliates.
 ** Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/
 */

package com.oracle.database.mcptoolkit.tools;

/**
 * The ToolSchemas class provides a collection of JSON schemas for various tool-related operations.
 * These schemas define the structure and constraints of the input data for different tools.
 */
public class ToolSchemas {

  /**
   * JSON schema for SQL-only operations.
   * <p>
   * This schema requires a "sql" property and optionally accepts a "txId" property.
   */
  static final String SQL_ONLY = """
      {
        "type":"object",
        "properties": {
          "sql": {
            "type": "string"
            },
          "txId": {
            "type": "string",
            "description": "Optional active transaction id"
            }
          },
          "required":["sql"]
      }""";

  /**
   * JSON schema for DROP/DESCRIBE table operations.
   */
  static final String DROP_OR_DESCRIBE_TABLE = """
      {
        "type":"object",
        "properties":
          {
            "table":
              {
              "type":"string"
              }},
          "required":["table"]
     }""";

  /**
   * JSON schema for transaction ID operations.
   */
  static final String TX_ID = """
      {
        "type":"object",
        "properties":
          {"txId":
            {"type":"string"}},
            "required":["txId"]
      }""";

  /**
   * JSON schema for file path operations.
   * <p>
   * This schema requires a "filePath" property, which should be an absolute path or a URL to an Oracle JDBC log file.
   */
  static final String FILE_PATH_SCHEMA = """
            {
              "type": "object",
              "properties": {
                "filePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the Oracle JDBC log file."
                }
              },
              "required": ["filePath"]
            }
            """;

  /**
   * JSON schema for file comparison operations.
   * <p>
   * This schema requires "filePath" and "secondFilePath" properties, which should be absolute paths or URLs to Oracle JDBC log files.
   */
  static final String FILE_COMPARISON_SCHEMA = """
            {
              "type": "object",
              "properties": {
                "filePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the 1st Oracle JDBC log file"
                },
                "secondFilePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the 2nd Oracle JDBC log file"
                }
              },
              "required": ["filePath", "secondFilePath"]
            }
            """;

  /**
   * JSON schema for RDBMS tools operations.
   * <p>
   * This schema requires "filePath" and "connectionId" properties, where "filePath" is an absolute path or a URL to an RDBMS/SQLNet trace file, and "connectionId" is a connection ID string.
   */
  static final String RDBMS_TOOLS_SCHEMA = """
            {
              "type": "object",
              "properties": {
                "filePath": {
                  "type": "string",
                  "description": "Absolute path or an URL to the RDBMS/SQLNet trace file"
                },
                "connectionId": {
                  "type": "string",
                  "description": "Connection ID string"
                }
              },
              "required": ["filePath", "connectionId"]
            }
            """;

  /**
   * JSON schema for similarity search operations.
   * <p>
   * This schema requires a "question" property and optionally accepts several other properties to customize the search.
   */
  static final String SIMILARITY_SEARCH = """
    {
      "type": "object",
      "properties": {
        "question": {
          "type": "string",
          "description": "Natural-language query text"
        },
        "topK": {
          "type": "integer",
          "description": "Number of rows to return",
          "default": 5
        },
        "table": {
          "type": "string",
          "description": "Override: table name"
          },
        "dataColumn": {
           "type": "string",
           "description": "Override: text/CLOB column"
          },
        "embeddingColumn": {
          "type": "string",
          "description": "Override: embedding column"
          },
        "modelName": {
           "type": "string",
           "description": "Override: vector model name"
        },
        "textFetchLimit": {
           "type": "integer",
           "description": "Override: substring length (CLOB)" }
      },
      "required": ["question"]
    }""";

  /**
   * JSON schema for explain plan operations.
   * <p>
   * This schema requires a "sql" property and optionally accepts several other properties to customize the plan.
   */
  static final String EXPLAIN_PLAN = """
    {
      "type": "object",
      "properties": {
        "sql":        { "type": "string", "description": "SQL to plan" },
        "mode":       { "type": "string", "enum": ["static","dynamic"], "description": "static=EXPLAIN PLAN, dynamic=DISPLAY_CURSOR" },
        "maxRows":    { "type": "integer", "minimum": 1, "description": "When executing SELECT in dynamic mode, cap rows fetched" },
        "execute":    { "type": "boolean", "description": "If true, actually run the SQL to collect runtime stats (A-Rows). Default: SELECT=true, DML/DDL=false" },
        "xplanOptions": {
          "type": "string",
          "description": "Override DBMS_XPLAN options, e.g. 'ALLSTATS LAST +PEEKED_BINDS +OUTLINE +PROJECTION'"
        }
      },
      "required": ["sql"]
    }""";

  /**
   * JSON schema for admin tools that take no input.
   */
  static final String NO_INPUT_SCHEMA = """
      {
        "type": "object",
        "properties": {}
      }
      """;

  /**
   * JSON schema for editing or adding a dynamic tool in the YAML config.
   * The operation is an upsert keyed by the tool name. Only provided fields are updated.
   */
  static final String EDIT_TOOL_SCHEMA = """
      {
        "type": "object",
        "properties": {
          "name":        { "type": "string", "description": "Tool name (YAML key). Required for upsert or delete." },
          "remove":      { "type": "boolean", "description": "If true, remove this tool from the YAML config. Other fields are ignored." },
          "description": { "type": "string", "description": "Human-friendly description of the tool" },
          "dataSource":  { "type": "string", "description": "Reference key from dataSources to use for this tool" },
          "statement":   { "type": "string", "description": "SQL statement to execute (SELECT or DML)" },
          "parameters":  {
            "type": "array",
            "description": "Optional parameter list for the tool",
            "items": {
              "type": "object",
              "properties": {
                "name":        { "type": "string",  "description": "Parameter name" },
                "type":        { "type": "string",  "description": "JSON schema type (e.g., string, number, integer, boolean)" },
                "description": { "type": "string",  "description": "Parameter description" },
                "required":    { "type": "boolean", "description": "Whether this parameter is required" }
              },
              "required": ["name", "type"]
            }
          }
        },
        "required": ["name"]
      }
      """;

  /**
   * JSON schema for listing vector stores.
   */
  static final String LIST_VECTOR_STORES = """
    {
      "type": "object",
      "properties": {}
    }""";

  /**
   * JSON schema for listing vector models.
   */
  static final String LIST_VECTOR_MODELS = """
    {
      "type": "object",
      "properties": {}
    }""";

  /**
   * JSON schema for Creating Vector Store.
   * <p>
   * This schema requires a "tableName" property and optionally accepts column names,
   * vector dimensions, and a flag to include metadata tracking.
   */
  static final String CREATE_VECTOR_STORE = """
  {
    "type": "object",
    "properties": {
      "tableName": {
        "type": "string",
        "description": "Name of the vector store table to create"
      },
      "textColumn": {
        "type": "string",
        "description": "Name for text/CLOB column (default: text)"
      },
      "embeddingColumn": {
        "type": "string",
        "description": "Name for vector embedding column (default: EMBEDDING)"
      },
      "dimensions": {
        "type": "integer",
        "description": "Vector dimensions (optional). If not specified, allows flexible dimensions"
      },
      "includeMetadata": {
        "type": "boolean",
        "description": "Include ID and metadata columns (default: true)"
      }
    },
    "required": ["tableName"]
  }""";

  /**
   * JSON schema for inserting file with embedding.
   */
  static final String INSERT_FILE_WITH_EMBEDDING = """
    {
      "type": "object",
      "properties": {
        "table": {
          "type": "string",
          "description": "Target vector store table name"
        },
        "filePath": {
          "type": "string",
          "description": "Path to file (PDF, DOC, JSON, etc.)"
        },
        "textColumn": {
          "type": "string",
          "description": "Text column name (default: text)"
        },
        "embeddingColumn": {
          "type": "string",
          "description": "Embedding column name (default: EMBEDDING)"
        },
        "modelName": {
          "type": "string",
          "description": "Vector model name (default: doc_model)"
        },
        "metadata": {
          "type": "string",
          "description": "Optional JSON metadata"
        },
        "chunkParams": {
          "type": "string",
          "description": "JSON chunking params (default: {\\\"max\\\": 500, \\\"overlap\\\": 50})"
        }
      },
      "required": ["table", "filePath"]
    }""";

}
