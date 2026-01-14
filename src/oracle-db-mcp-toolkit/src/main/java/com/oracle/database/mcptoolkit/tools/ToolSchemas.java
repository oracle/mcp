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
          "name":        { "type": "string", "description": "Tool name (YAML key). Required for upsert." },
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
}
