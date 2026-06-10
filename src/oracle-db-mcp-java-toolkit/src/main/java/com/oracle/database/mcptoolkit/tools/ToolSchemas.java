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
          "enabled":     { "type": "boolean", "description": "Optional switch. true/omitted = enabled, false = disabled." },
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
   * JSON schema for vector store management (create, list).
   */
  static final String VECTOR_STORE = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["create", "list"],
          "description": "create=Create a new vector store (needs tableName). list=List all existing vector stores."
        },
        "tableName": {
          "type": "string",
          "description": "Table name to create. Required for action=create."
        },
        "textColumn": {
          "type": "string",
          "description": "Text/CLOB column name (default: TEXT)."
        },
        "embeddingColumn": {
          "type": "string",
          "description": "Vector embedding column name (default: EMBEDDING)."
        },
        "dimensions": {
           "type": "integer",
           "description": "Fixed vector dimensions. Omit for flexible size."
        },
        "includeMetadata": {
           "type": "boolean",
           "description": "Add METADATA column for tracking and dedup (default: true)."
        }
      },
      "required": ["action"]
    }""";

  /**
   * JSON schema for vector model management (list, drop).
   */
  static final String VECTOR_MODEL = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["list", "drop"],
          "description": "list=List all ONNX embedding models. drop=Drop a model by name (needs modelName)."
        },
        "modelName": {
          "type": "string",
          "description": "Model name to drop. Required for action=drop."
        }
      },
      "required": ["action"]
    }""";

  /**
   * JSON schema for embedding documents into a vector store.
   * All actions run in the background and return a taskId immediately.
   */
  static final String EMBED = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["file", "files", "table", "object", "bucket"],
          "description": "file=Single local file (needs filePath, table). files=Multiple local files (needs filePaths array, table). table=From existing Oracle table (needs sourceTable, sourceTextColumn, sourceIdColumn, targetTable). object=Single OCI file (use objectUrl for a direct or PAR URL, or provide region+namespace+bucketName+objectName+table). bucket=Entire OCI bucket (use bucketUrl for a direct or PAR URL, or provide region+namespace+bucketName+table). PAR URLs are self-authenticating — credentialName is ignored."
        },
        "table": {
          "type": "string",
          "description": "Target vector store. Required for actions: file, files, object, bucket."
        },
        "textColumn": {
          "type": "string",
          "description": "Text column name (default: TEXT)."
        },
        "embeddingColumn": {
           "type": "string",
           "description": "Embedding column name (default: EMBEDDING)."
        },
        "modelName": {
          "type": "string",
          "description": "Vector model name (default: doc_model)."
        },
        "chunkParams": {
          "type": "string",
          "description": "JSON chunking params (default: {\\\"max\\\": 500, \\\"overlap\\\": 50})."
        },
        "filePath": {
          "type": "string",
          "description": "Single local file path. Required for action=file."
        },
        "filePaths": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "List of local file paths. Required for action=files."
        },
        "sourceTable": {
          "type": "string",
          "description": "Source table containing text. Required for action=table."
        },
        "sourceTextColumn": {
          "type": "string",
          "description": "Text column in source table. Required for action=table."
        },
        "sourceIdColumn": {
          "type": "string",
          "description": "ID column in source table. Required for action=table."
        },
        "targetTable": {
          "type": "string",
          "description": "Target vector store. Required for action=table."
        },
        "metadataColumn": {
          "type": "string",
          "description": "Metadata column in target (default: METADATA). For action=table." },
        "credentialName": {
          "type":
          "string", "description": "DBMS_CLOUD credential name. Omit for public buckets. For action=object/bucket." 
        },
        "region": {
          "type": "string",
          "description": "OCI region (e.g. us-ashburn-1). Required for action=object/bucket."
        },
        "namespace": {
          "type": "string",
          "description": "OCI namespace. Required for action=object/bucket."
        },
        "bucketName": {
          "type": "string",
          "description": "OCI bucket name. Required for action=object/bucket."
        },
        "objectName": {
          "type": "string",
          "description": "Object path in the bucket. Required for action=object when objectUrl is not provided."
        },
        "prefix": {
          "type": "string",
          "description": "Optional prefix filter (e.g. docs/). For action=bucket."
        },
        "allowedExtensions": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Optional file extension filter (e.g. pdf, txt, docx). For action=bucket. If omitted, no extension filter is applied."
        },
        "maxObjects": {
          "description": "Maximum bucket objects to embed for action=bucket. Default is 100. Values above 10000 process at most 10000 objects."
        },
        "objectUrl": {
          "type": "string",
          "description": "Direct OCI URL or Pre-Authenticated Request (PAR) URL for a single object. For action=object. Alternative to region/namespace/bucketName/objectName. PAR URLs do not require credentialName."
        },
        "bucketUrl": {
          "type": "string",
          "description": "Direct OCI bucket URL or Pre-Authenticated Request (PAR) bucket URL. For action=bucket. Alternative to region/namespace/bucketName. PAR URLs do not require credentialName." }
      },
      "required": ["action"]
    }""";

  /**
   * JSON schema for background embedding task management (status, list).
   */
  static final String TASK = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["status", "list", "cancel"],
          "description": "status=Get status of a specific task (needs taskId). list=List all embedding tasks submitted since the server started. cancel=Request cancellation of a PENDING or RUNNING task (needs taskId). Cleanup of committed local-file rows requires task metadata."
        },
        "taskId": {
          "type": "string",
          "description": "Task ID returned by the embed tool. Required for action=status and action=cancel." }
      },
      "required": ["action"]
    }""";

  /**
   * JSON schema for OCI Object Storage utilities.
   */
  static final String OCI_STORAGE = """
    {
      "type": "object",
      "properties": {
        "action": {
          "type": "string",
          "enum": ["list-objects"],
          "description": "list-objects=List objects in an OCI bucket (default 100, capped at 10000; use bucketUrl for a direct or PAR URL, or provide region+namespace+bucketName). Use prefix to narrow results."
        },
        "credentialName": {
          "type": "string",
          "description": "DB credential name. Omit for public buckets. For action=list-objects."
        },
        "region": {
          "type": "string",
          "description": "OCI region (e.g. eu-amsterdam-1). Required for action=list-objects."
        },
        "namespace": {
          "type": "string",
          "description": "OCI Object Storage namespace. Required for action=list-objects."
        },
        "bucketName": {
          "type": "string",
          "description": "OCI bucket name. Required for action=list-objects." 
         },
        "prefix": {
          "type": "string",
          "description": "Optional prefix filter (e.g. docs/). For action=list-objects."
        },
        "maxResults": {
          "description": "Maximum objects to return for action=list-objects. Default is 100. Values above 10000 return at most 10000 objects."
        },
        "bucketUrl": {
          "type": "string",
          "description": "Direct OCI bucket URL or Pre-Authenticated Request (PAR) bucket URL. For action=list-objects. Alternative to region/namespace/bucketName. PAR URLs do not require credentialName." 
        }
      },
      "required": ["action"]
    }""";

}
