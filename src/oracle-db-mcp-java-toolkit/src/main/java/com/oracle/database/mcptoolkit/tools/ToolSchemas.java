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
   * JSON schema for the consolidated transaction tool.
   */
  static final String TRANSACTION = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["start", "resume", "commit", "rollback"],
          "description": "start=Begin a new JDBC transaction (returns txId). resume=Verify a txId is still active. commit=Commit and close a transaction. rollback=Rollback and close a transaction."
        },
        "txId": {
          "type": "string",
          "description": "Required for resume, commit, and rollback actions."
        }
      },
      "required": ["action"]
    }""";

  /**
   * JSON schema for the consolidated table management tool.
   */
  static final String TABLE_MANAGEMENT = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["create", "drop", "list", "describe"],
          "description": "create=Create a table from a full CREATE TABLE statement. drop=Drop a table by name. list=List all tables and synonyms in the current schema. describe=Get detailed column info for a specific table."
        },
        "sql": {
          "type": "string",
          "description": "Full CREATE TABLE statement. Required for action=create."
        },
        "table": {
          "type": "string",
          "description": "Table name. Required for action=drop and action=describe."
        },
        "txId": {
          "type": "string",
          "description": "Optional active transaction ID. Applies to action=create."
        }
      },
      "required": ["action"]
    }""";

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

  static final String JDBC_ANALYZER_SCHEMA = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["stats", "queries", "errors", "connection-events", "list-files", "compare"],
          "description": "Operation to perform on JDBC logs."
        },
        "filePath": {
          "type": "string",
          "description": "Absolute path or URL to an Oracle JDBC thin log file."
        },
        "secondFilePath": {
          "type": "string",
          "description": "Absolute path or URL to the second Oracle JDBC thin log file (compare only)."
        },
        "directoryPath": {
          "type": "string",
          "description": "Absolute path to a directory containing log files (list-files only)."
        }
      },
      "required": ["action"],
      "oneOf": [
        { "properties": { "action": { "const": "compare" } }, "required": ["filePath", "secondFilePath"] },
        { "properties": { "action": { "const": "list-files" } }, "required": ["directoryPath"] },
        { "properties": { "action": { "const": "stats" } }, "required": ["filePath"] },
        { "properties": { "action": { "const": "queries" } }, "required": ["filePath"] },
        { "properties": { "action": { "const": "errors" } }, "required": ["filePath"] },
        { "properties": { "action": { "const": "connection-events" } }, "required": ["filePath"] }
      ]
    }
    """;

  static final String RDBMS_ANALYZER_SCHEMA = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["errors", "packet-dumps"],
          "description": "Operation to perform on an RDBMS/SQLNet trace file."
        },
        "filePath": {
          "type": "string",
          "description": "Absolute path or URL to the RDBMS/SQLNet trace file."
        },
        "connectionId": {
          "type": "string",
          "description": "Connection ID string (required for packet-dumps)."
        }
      },
      "required": ["action", "filePath"],
      "oneOf": [
        { "properties": { "action": { "const": "packet-dumps" } }, "required": ["connectionId"] },
        { "properties": { "action": { "const": "errors" } } }
      ]
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

}
