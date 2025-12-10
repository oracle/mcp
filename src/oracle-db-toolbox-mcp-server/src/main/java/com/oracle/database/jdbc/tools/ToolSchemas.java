package com.oracle.database.jdbc.tools;

public class ToolSchemas {

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
}
