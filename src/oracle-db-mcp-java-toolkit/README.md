# Oracle Database MCP Toolkit

## 1. Overview

Oracle Database MCP Toolkit is a Model Context Protocol (MCP) server that lets you:

* Define your own custom tools via a simple YAML configuration file.
* Use built-in tools:
  * Analyze Oracle JDBC thin client logs and RDBMS/SQLNet trace files.
  * Database tools for SQL execution, table management, transactions, performance monitoring and execution plan analysis.
  * Database-powered tools, including vector similarity search (RAG).
  * Admin tools for runtime discovery and configuration: list available tools and live-edit YAML-defined tools with hot reload.
* Deploy locally or remotely - optionally as a container - with support for TLS and OAuth2

![MCP Toolkit Architecture Diagram](./images/MCPToolkitArchitecture.svg)

_Note_: The [Oracle SQLcl MCP Server](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/25.4/sqcug/using-oracle-sqlcl-mcp-server.html) is a fully supported product
with MCP capabilities for the Oracle Database.

---

## 2. Custom Tool Framework — Extending the MCP Server

The MCP server can load both database connection definitions and custom tool definitions from a YAML configuration file.
This provides a flexible and declarative way to extend the server without modifying or rebuilding the codebase.

A YAML file may define:

* **datasources:** — Database configuration info:
  * `url`: This is the JDBC URL used by the MCP server to connect to the database using the JDBC driver.
  * `user`: The username to use for the database connection.
  * `password`: The password to use for the database connection.
  * `host` (optional): The hostname or IP address of the database server.
  * `port` (optional): The port number on which the database server is listening.
  * `database` (optional): The Oracle service name of the database.

* One or more **tools** — The MCP tools:
  * `dataSource` (optional): Defines the data source to be used (defaults to system properties `db.url`, `db.user` and `db.password`).
  * `enabled` (optional): If `false`, disables this custom tool. Omitted/`true` means enabled.
  * `name`: The tool name and title, derived from the YAML key.
  * `description`: A brief description of the tool.
  * `parameters` (optional): A list of the parameters required for the tool. (To fill the statement's placeholders)
  * `statement` The SQL statement to be executed by the tool.

* If you add **parameters**, you can add the following fields:
  * `name`: The name of the tool parameter.
  * `type`: The data type to respect when the LLM fills the parameter.
  * `description`: The description to know what this parameter is about.
  * `required` (optional): Indicates whether the tool parameter is required. (default: false)
  * All the parameter fields are being used to generate an InputSchema.

### DataSource Resolution Logic

When executing a tool, the MCP server determines which datasource to use based on the following rules:

1. If the tool specifies a datasource, that datasource is used.

2. If the tool does not specify a datasource, the server looks for a default datasource:
* First, it checks whether a datasource was provided via system properties (`db.url`, `db.user`, `db.password) (Higher priority).
* If no system property datasource is available, it falls back to the first datasource defined in the YAML file, if present.

3. If no datasource can be resolved and the tool requires one (e.g., SQL-based tools), the server reports a configuration error.

This design ensures that tools always have a predictable datasource while giving you flexibility to choose how connections are provided—either inline in YAML or externally via system
properties and environment variables.

**Example `config.yaml`:**

```yaml
dataSources:
  prod-db:
    url: jdbc:oracle:thin:@prod-host:1521/ORCLPDB1
    user: ${user}
    password: ${password}

tools:
  hotels-by-name:
    dataSource: prod-db
    description: Returns the details of a hotel given its name. The details include the capacity, rating and address.
    parameters:
      - name: name
        type: string
        description: Hotel name to search for.
        required: false
    statement: SELECT * FROM hotels WHERE name LIKE '%' || :name || '%'

# Optional toolsets combining custom tools
toolsets:
  reporting: [hotels-by-name]
  finance:
    tools: [hotels-by-name]
    enabled: false
```

To enable YAML configuration, launch the server with:

```bash
java -DconfigFile=/path/to/config.yaml -jar <mcp-server>.jar
```

Toolsets can be enabled from `-Dtools` alongside individual tools. For example:
- `-Dtools=reporting` enables all tools in the `reporting` toolset
- `-Dtools=reporting,explain` enables your `reporting` set plus the built-in `explain` toolset (see below)
- `-Dtools=*` or omit `-Dtools` to enable everything

Custom tool defaults:
- Custom tools and custom toolsets are enabled by default, even if they are not listed in `-Dtools`.
- Set `enabled: false` on a tool or a toolset to disable it.

Priority/precedence rules (highest to lowest):
1. **Tool-level explicit disable wins:** `tools.<name>.enabled: false` always disables the tool.
2. **Tool-level explicit enable overrides disabled toolsets:** `tools.<name>.enabled: true` enables the tool even if one of its toolsets is disabled.
3. **Disabled toolset affects non-explicit tools:** if a tool is only implied/default-enabled (`enabled` omitted) and belongs to any toolset with `enabled: false`, it stays disabled.
4. **Otherwise default is enabled:** custom tools and custom toolsets are enabled by default.

How to disable a custom toolset (explicit form):

```yaml
toolsets:
  reporting:
    tools: [hotels-by-name, sales-by-region]
    enabled: false
```

Notes:
- The short list form (`reporting: [hotels-by-name, sales-by-region]`) is enabled by default.
- To disable a toolset, use the object form above with `enabled: false`.

Example:

```yaml
tools:
  hotels-by-name:
    # enabled omitted => implicit/default
    statement: SELECT * FROM hotels

  hotels-by-rating:
    enabled: true
    statement: SELECT * FROM hotels

toolsets:
  reporting:
    tools: [hotels-by-name, hotels-by-rating]
    enabled: false
```

Outcome:
- `hotels-by-name` => disabled (implicit tool in disabled toolset)
- `hotels-by-rating` => enabled (explicit `enabled: true`)

> Tip: You can also manage YAML-defined tools at runtime using the `edit-tools` admin tool; see section 3.9.

---

## 3. Built-in Tools

### Built-in Toolsets Overview
The server provides four built-in toolsets that can be enabled via `-Dtools`:

<table>
  <thead>
    <tr>
      <th>Toolset</th>
      <th>Description</th>
      <th>Tools Included</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>mcp-admin</code></td>
      <td>Protected administrative tools</td>
      <td>
        edit-tools, list-credentials
      </td>
    </tr>
    <tr>
      <td><code>log-analyzer</code></td>
      <td>JDBC and RDBMS log analysis</td>
      <td>
        jdbc-analyzer, rdbms-analyzer
      </td>
    </tr>
    <tr>
      <td><code>database-operator</code></td>
      <td>Database operations, transactions, monitoring, and execution plans</td>
      <td>
        read-query, write-query, table, transaction, db-ping,
        db-metrics-range, explain-plan
      </td>
    </tr>
    <tr>
      <td><code>rag</code></td>
      <td>Vector store management, document embedding, and semantic similarity search</td>
      <td>
        vector-model, vector-store, embed, task, oci-storage, similarity-search
      </td>
    </tr>
  </tbody>
</table>

_Note: `list-tools` is a standalone discovery tool. Enabling a toolset enables all tools listed for that toolset._

**Common Configurations:**
- `-Dtools=mcp-admin` - Admin and runtime configuration tools
- `-Dtools=log-analyzer` - Oracle JDBC Log and RDBMS/SQLNet trace file analysis only (no database required)
- `-Dtools=database-operator` - Database operations and SQL execution
- `-Dtools=rag` – Vector store management, document embedding, and semantic similarity search
- `-Dtools=mcp-admin,log-analyzer` - Admin + log analysis
- `-Dtools=*` - All non-protected tools (default if omitted). Protected admin tools require `-Dtools=mcp-admin` or the individual tool name.

### 3.1. Database Operations
These tools provide direct SQL execution capabilities:

- **`read-query`**: Execute SELECT-only queries and return results as JSON.
- **`write-query`**: Execute DML/DDL operations (INSERT, UPDATE, DELETE, CREATE, etc.) with autocommit.

### 3.2. Table Management
A single **`table`** tool covers all table management operations via an `action` parameter:

- **`action=create`**: Create a table using full CREATE TABLE statements
- **`action=drop`**: Drop an existing table by name  (`table` required)
- **`action=list`**: List all tables and synonyms in the current schema
- **`action=describe`**: Get detailed column information for any table (`table` required)

### 3.3. Transaction Management
A single **`transaction`** tool covers all transaction lifecycle operations via an `action` parameter:

- **`action=start`**: Begin a new JDBC transaction and get a transaction ID
- **`action=resume`**: Verify if a transaction ID is still active (`txId` required)
- **`action=commit`**: Commit and close a transaction (`txId` required)
- **`action=rollback`**: Rollback and close a transaction (`txId` required)

### 3.4. Database Monitoring
These tools help monitor database health and performance:

- **`db-ping`**: Connectivity + timings (connect/round-trip) + Database metadata
- **`db-metrics-range`**: Retrieve Oracle performance metrics from V$SYSSTAT

### 3.5. Oracle JDBC Log Analysis

The `jdbc-analyzer` tool covers the Oracle JDBC thin client logs analysis using the `action` parameter, it supports the following values:

* **`action=stats`**: Extracts performance statistics including error counts, sent/received packets and byte counts.
* **`action=queries`**: Retrieves all executed SQL queries with timestamps and execution times.
* **`action=errors`**: Extracts all errors reported by both server and client.
* **`action=connection-events`**: Shows connection open/close events.
* **`action=compare`**: Compares two log files for performance metrics, errors, and network information.
* **`action=list-files`**: List all visible files from a specified directory, which helps the user analyze multiple files with one prompt.

The tool returns results serialized in JSON format.

### 3.6. RDBMS/SQLNet Trace Analysis:

The `rdbms-analyzer` tool operate on RDBMS/SQLNet trace files based on the chosen `action`:

* **`action=rdbms-errors`**: Extracts errors from RDBMS/SQLNet trace files.
* **`action=packet-dumps`**: Extracts packet dumps for a specific connection ID.

Each extracted record includes relevant details/context and is returned serialized in JSON format.

### 3.7. Vector Store Management and Semantic Search (RAG)

These tools provide a full RAG pipeline: model management, vector store creation, document embedding from local files or OCI Object Storage, and semantic similarity search. All embedding operations run in the background and return a task ID immediately.

> **Prerequisite:** An ONNX embedding model must be loaded into your Oracle database before running any embedding tool. Use `vector-model` action=list to verify.

---

* **`vector-model`**: Manage ONNX embedding models loaded in the database.

  - `action=list` — list all loaded models with their names, algorithms, creation dates, and sizes.
  - `action=drop` — remove a model by name.

  **Inputs:**

  * `action` (string, required) — `list` or `drop`
  * `modelName` (string, required for `drop`) — name of the model to remove

  **Returns:** list of models for `list`, or `{ modelName, status: "dropped" }` for `drop`.

---

* **`vector-store`**: Create and list vector store tables.

  - `action=create` — create a new table ready for vector search. Every table gets an `ID` primary key and a `CREATED_AT` timestamp automatically. When metadata is enabled (default), a `METADATA` JSON column and two indexes are created: one on `source_uri` for deduplication and one on `task_id` for cancellation cleanup.
  - `action=list` — list all tables in the current schema that have at least one VECTOR column.

  **Inputs:**

  * `action` (string, required) — `create` or `list`
  * `tableName` (string, required for `create`) — name of the new vector store
  * `textColumn` (string, default: `TEXT`) — column for text chunks
  * `embeddingColumn` (string, default: `EMBEDDING`) — column for vectors
  * `dimensions` (integer, optional) — fix vector size to a specific dimension, or omit for flexible
  * `includeMetadata` (boolean, default: `true`) — add a METADATA column for document tracking and deduplication

  **Returns:** `{ tableName, textColumn, embeddingColumn, dimensions, hasMetadata }` for `create`, or an array of `{ tableName, vectorColumns, rowCount }` for `list`.

---

* **`embed`**: Embed documents into a vector store. All actions run as background jobs and return a `taskId` immediately. Use the `task` tool to monitor progress.

  **Common optional inputs for all actions:**
  * `table` (string, required for `file`, `files`, `object`, `bucket`) — target vector store (use `targetTable` for `action=table`)
  * `textColumn` (string, default: `TEXT`) — text column in the target table
  * `embeddingColumn` (string, default: `EMBEDDING`) — vector column in the target table
  * `modelName` (string, default: `doc_model`) — ONNX embedding model name
  * `chunkParams` (string, default: `{"max": 500, "overlap": 50}`) — chunking parameters (max tokens per chunk, overlap)

  **Actions:**

  - `action=file` — embed a single local file (PDF, Word, Excel, PowerPoint, plain text, and other formats supported by Oracle’s `UTL_TO_TEXT`).
    * `filePath` (string, required) — absolute path to the file

  - `action=files` — embed multiple local files in a single background job.
    * `filePaths` (array, required) — list of absolute file paths; at most 100 files per request

  Local file ingestion requires `-DingestRootDir=/path/to/ingest/root`. Each requested file path is resolved to its real filesystem path and must stay inside that root. Ingested files must be no larger than `ingestMaxFileSizeMb`, whose value is in MB (default: `50`).

  - `action=table` — embed text from an existing Oracle table into a vector store.
    * `sourceTable` (string, required) — table containing the source text
    * `sourceTextColumn` (string, required) — column in the source table holding the text to embed
    * `sourceIdColumn` (string, required) — unique identifier column in the source table (stored in metadata as `source_id`)
    * `targetTable` (string, required) — target vector store table
    * `metadataColumn` (string, default: `METADATA`) — metadata column in the target table

  - `action=object` — embed a single file from OCI Object Storage.
    * `objectUrl` (string) — direct OCI object URL or Pre-Authenticated Request (PAR) URL
    * Or provide `region` + `namespace` + `bucketName` + `objectName` individually
    * `credentialName` (string, optional) — DBMS_CLOUD credential name; omit for public objects

  - `action=bucket` — embed files in an OCI bucket.
    * `bucketUrl` (string) — direct OCI bucket URL or PAR URL
    * Or provide `region` + `namespace` + `bucketName` individually
    * `credentialName` (string, optional) — DBMS_CLOUD credential name; omit for public buckets
    * `prefix` (string, optional) — filter objects by path prefix (e.g. `docs/`)
    * `allowedExtensions` (array, optional) — only embed files with these extensions (e.g. `["pdf", "txt"]`); omit to skip extension filtering
    * `maxObjects` (number or string, optional) — maximum bucket objects to embed. Default is `100`; values above `10000` process at most `10000`.

    Bucket ingestion skips objects larger than `ingestMaxFileSizeMb` (default: `50` MB) before embedding them.

  **Returns:** `{ taskId, status: "PENDING", table, ... }` — use the `task` tool to check progress.

  **Deduplication:** When the target table has a METADATA column, duplicate documents are automatically skipped. The same file, OCI object, or source row is never embedded twice.

  **Metadata written per chunk** (when target table has a METADATA column):

  For `action=file`, `files`, `object`, `bucket`:
  * `task_id` — ID of the embedding task that inserted this chunk (used for cancellation cleanup)
  * `document_id` — UUID shared by all chunks of the same document
  * `source_uri` — file path (`file:///...`) or OCI URL of the source document
  * `chunk_index` — 0-based position of the chunk within the document
  * `total_chunks` — total number of chunks for this document

  For `action=table`:
  * `task_id` — ID of the embedding task that inserted this chunk (used for cancellation cleanup)
  * `source_table` — name of the source table
  * `source_id` — value of the `sourceIdColumn` for the originating row
  * `chunk_index` — 0-based position of the chunk within that row's text
  * `embedded_at` — timestamp of when the embedding was generated

  > Tables created without `includeMetadata` accept inserts but skip deduplication — the same document can be embedded multiple times.

---

* **`task`**: Monitor and control background embedding jobs.

  - `action=status` — get the current status and per-file results for a specific task.
  - `action=list` — list tasks submitted since the server started, newest first, with optional pagination (in-memory only, cleared on restart).
  - `action=cancel` — request cancellation of a PENDING or RUNNING task.

    Embedding task metadata is retained in memory for up to 72 hours after completion, failure, or cancellation. The server keeps at most 10000 task records; if the task store is full, new embedding submissions are rejected until older terminal task records expire.

  **Inputs:**

  * `action` (string, required) — `status`, `list`, or `cancel`
  * `taskId` (string, required for `status` and `cancel`) — task ID returned by the `embed` tool
  * `limit` (integer, optional for `list`) — maximum tasks to return. Default is `100`; values above `1000` return at most `1000`.
  * `offset` (integer, optional for `list`) — number of newest tasks to skip. Default is `0`.

  **Returns:** `status` and `cancel` return `{ taskId, status, table, totalChunksCreated, submittedAt, completedAt, results }` where `status` is one of `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, or `CANCELLED`. `list` returns `{ totalTasks, limit, offset, returned, hasMore, tasks }`. The `results` array contains per-file/source entries and may include cleanup or cancellation entries for cancelled tasks.

  **Cancellation policy:**

  Cancelling a task is best-effort for work that is already running:

  - **Local-file jobs** (`action=file`, `action=files`): the cancel flag is checked between files, and the active insert statement is cancelled when possible. If the target vector store has a `METADATA` column, rows stamped with the task ID are removed before the task is marked `CANCELLED`.
  - **Single-SQL jobs** (`action=object`, `action=bucket`, `action=table`): JDBC `PreparedStatement.cancel()` asks Oracle to stop the active statement. If the statement is stopped before completion, no rows from that statement are committed. If the statement completes before cancellation takes effect, the task may finish as `COMPLETED`.
  - **PENDING tasks** (still in the queue) are cancelled before they start — nothing is written to the database.
  - Calling `cancel` on a task already in a terminal state (`COMPLETED`, `FAILED`, or `CANCELLED`) returns an error.

---

* **`oci-storage`**: Browse OCI Object Storage buckets.

  - `action=list-objects` — list objects in a bucket. Provide `bucketUrl` (direct or PAR URL), or `region` + `namespace` + `bucketName`. Returns 100 objects by default, and at most 10000. Use `prefix` to narrow results or check for a specific object.

  **Inputs:**

  * `action` (string, required) — `list-objects`
  * `bucketUrl` (string) — direct OCI bucket URL or PAR URL (alternative to region/namespace/bucketName)
  * `region`, `namespace`, `bucketName` (string) — required for `list-objects` when `bucketUrl` is not provided
  * `credentialName` (string, optional) — DBMS_CLOUD credential; omit for public buckets
  * `prefix` (string, optional) — filter objects by path prefix
  * `maxResults` (number or string, optional) — maximum objects to return. Default is `100`; values above `10000` return at most `10000`.

  **Returns:** `{ bucketUri, prefix, maxResults, truncated, totalObjects, objects: [{ name, sizeBytes, lastModified }] }`.

---

* **`similarity-search`**: Perform semantic similarity search using Oracle’s vector features (`VECTOR_EMBEDDING`, `VECTOR_DISTANCE`).

  **Inputs:**

  * `question` (string, required): Natural language query.
  * `topK` (integer, optional, default: 5): Number of closest results.
  * `table` (string, default: `profile_oracle`): Table containing text + vector embeddings.
  * `dataColumn` (string, default: `text`): Text/CLOB column.
  * `embeddingColumn` (string, default: `embedding`): Vector column.
  * `modelName` (string, default: `doc_model`): Name of the DB vector model.
  * `textFetchLimit` (integer, default: 4000): Max length of returned text.

  **Returns:**

  * JSON array of similar rows with scores and truncated snippets.

### 3.8. SQL Execution Plan Analysis

* **`explain-plan`**: Generate Oracle execution plans and receive a pre-formatted LLM prompt for tuning and explanation.

  **Modes:**

  * `static` — Uses `EXPLAIN PLAN` (estimated plan; does not run the SQL).
  * `dynamic` — Uses `DBMS_XPLAN.DISPLAY_CURSOR` for the **actual** plan of a cursor.

  **Inputs:**

  * `sql` (required): SQL query to analyze.
  * `mode` (static|dynamic, default: static)
  * `execute` (boolean): Execute SQL to obtain a cursor in dynamic mode.
  * `maxRows` (integer, default: 1): Limit rows fetched during execution.
  * `xplanOptions` (string): Formatting options.

    * Default dynamic: `ALLSTATS LAST +PEEKED_BINDS +OUTLINE +PROJECTION`
    * Default static: `BASIC +OUTLINE +PROJECTION +ALIAS`

  **Returns:**

  * `planText`: DBMS_XPLAN output.
  * `llmPrompt`: A structured prompt for an LLM to explain + tune the plan.

### 3.9. Admin and Runtime Configuration Tools

These tools help you discover what's enabled and manage YAML-defined tools at runtime.
`list-tools` is a standalone discovery tool. Protected administrative tools are part of the `mcp-admin` toolset (enable via `-Dtools=mcp-admin` or include individual tool names).
The `mcp-admin` toolset is not included by default, `-Dtools=*`, or `-Dtools=all`; enable it explicitly with `-Dtools=mcp-admin`.

_Note: The `mcp-admin` toolset is focused on protected runtime configuration and administrative inventory._

#### MCP Admin Tools:

- `list-tools`: List all available tools with their descriptions.
  - Inputs: none
  - Returns: `tools` array with `{ name, title, description }` for built-ins (honoring `-Dtools` filter) and any YAML-defined tools.

- `list-credentials`: List DBMS_CLOUD credentials available in the current schema.
  - Inputs: none
  - Returns: `{ totalCredentials, credentials: [{ credentialName, username, enabled }] }`
  - Requirements and behavior:
    - Must be explicitly enabled with `-Dtools=list-credentials` or `-Dtools=mcp-admin`.
    - When HTTP authentication is enabled, requires OAuth scope `mcp:credentials:read` or `mcp:admin`.
    - To allow any authenticated caller to use `list-credentials` without scope enforcement, set `-DlistCredentials.requireScope=false`.

- `edit-tools`: Create, update, or remove a YAML-defined tool. Changes are auto-reloaded by the server.
  - Inputs (subset; see schema in code):
    - `name` (string, required): Tool name/YAML key
    - `remove` (boolean, optional): If true, delete the tool
    - `description` (string, optional)
    - `enabled` (boolean, optional): `false` disables the tool; omitted/`true` enables it
    - `dataSource` (string, optional): Key from `dataSources:`
    - `statement` (string, optional): SQL (SELECT or DML)
    - `parameters` (array, optional): Items of `{ name, type, description, required }`
  - Requirements and behavior:
    - Must be explicitly enabled with `-Dtools=edit-tools` or `-Dtools=mcp-admin`.
    - Requires `-DconfigFile` to be set to a writable YAML file; otherwise the tool will return an error.
    - When HTTP authentication is enabled, requires OAuth scope `mcp:tools:write` or `mcp:admin`.
    - To allow any authenticated caller to use `edit-tools` without scope enforcement, set `-DeditTools.requireScope=false`.
    - OAuth scope lookup defaults to the `scope` claim in the introspection response. If your authorization server uses a different claim, configure its dot-separated path with `-Doauth.scopeClaimPath=<claim.path>`.
    - Tool names must be safe and cannot collide with built-in tools or toolsets.
    - For `edit-tools` changes, `dataSource` is required, must exist under `dataSources:`, and must be in `admin.editTools.allowedDataSources` when that allowlist is configured.
    - `edit-tools` allows `SELECT` statements by default; additional statement types must be allowed by `admin.editTools.allowedStatementTypes`.
    - Parameters must use supported types and match SQL bind placeholders exactly.
    - On upsert/remove, the YAML is written and the server hot-reloads the configuration shortly after.

  Optional policy for changes made through `edit-tools`:
  ```yaml
  admin:
    editTools:
      enabled: true
      allowedDataSources: [reporting-db]
      allowedStatementTypes: [SELECT]
  ```
  This policy applies only to YAML changes made through `edit-tools`; it is not an allowlist for hand-edited YAML files.
  Hand-edited YAML tools are treated as admin-controlled config. Startup and hot reload perform basic structural validation and skip invalid tools, but they do not enforce `admin.editTools.allowedDataSources` or `admin.editTools.allowedStatementTypes`.

  Example (upsert a tool):
  ```jsonc
  {
    "name": "hotels-by-rating",
    "description": "List hotels with a minimum rating",
    "dataSource": "prod-db",
    "statement": "SELECT * FROM hotels WHERE rating >= :minRating ORDER BY rating DESC",
    "parameters": [
      { "name": "minRating", "type": "number", "description": "Minimum rating", "required": true }
    ]
  }
  ```

  Example (remove a tool):
  ```jsonc
  { "name": "hotels-by-rating", "remove": true }
  ```

---

## 4. Installation

### 4.1. Prerequisites

* **JDK 17+**
* **Maven 3.9+**
* **Credentials** with permissions for your intended operations
* **MCP client** (e.g., Claude Desktop) to call the tools

> The server uses UCP pooling out of the box (initial/min= 1).

### 4.2. Build the MCP server jar

```bash
mvn clean package
```

The created jar can be found in `target/oracle-db-mcp-toolkit-1.0.0.jar`.

### 4.3. Choose a transport mode (stdio vs HTTP)

`oracle-db-mcp-toolkit` supports two transport modes:

* **stdio (default)** – the MCP client spawns the JVM process and talks over stdin/stdout
* **Streamable HTTP** – the MCP server runs as an HTTP service, and clients connect via a URL

#### 4.3.1. Stdio mode (default)

This is the mode used by tools like Claude Desktop, where the client directly launches:

```json
{
  "mcpServers": {
    "oracle-db-mcp-toolkit": {
      "command": "java",
      "args": [
        "-Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service",
        "-Ddb.user=your_user",
        "-Ddb.password=your_password",
        "-Dtools=jdbc-analyzer",
        "-Dojdbc.ext.dir=/path/to/extra-jars",
        "-jar",
        "<path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar"
      ]
    }
  }
}
```

If you don’t set `-Dtransport`, the server runs in stdio mode by default.

#### 4.3.2. Streamable HTTP mode

In streamable HTTP mode, you run the server as a standalone HTTP service and point an MCP client to it.

##### HTTP transport security

HTTP transport requires authentication. Start it with `-Dauth.enabled=true` and configure OAuth2, or use the generated development token described below.

For local development only, an unauthenticated server can be started with `-Dhttp.allowUnauthenticatedForDevelopment=true`. This is intentionally explicit and emits a warning; do not use it for a remotely reachable service.

`http.allowedOriginalHosts` is optional and disabled by default for compatibility with non-browser MCP clients, proxies, and health checks. When configured, it is a comma-separated list of browser-origin host names only (no scheme or port), and the server rejects MCP requests without an `Origin` header and rejects origins outside this allowlist before MCP dispatch. Configure it for browser-accessible deployments that need DNS-rebinding protection:

```shell
-Dhttp.allowedOriginalHosts=mcp.example.com
```

Use a reverse proxy or firewall appropriate for your deployment. `allowedHosts` is a separate CORS setting for OAuth discovery metadata; it does not control MCP request admission.

##### Enabling HTTPS (SSL/TLS)

**WARNING**: Enable https at your own risk. When enabling https pay extra attention to the MCP tools that you enable as they may create a new risk for your database server.

To enable HTTPS (SSL/TLS), specify your certificate keystore path and password using the `-DcertificatePath` and `-DcertificatePassword` options.  
Only PKCS12 (`.p12` or `.pfx`) keystore files are supported.
You can set the HTTPS port with the `-Dhttps.port` option.

Start the server:

```shell
java \
  -Dtransport=http \
  -Dhttps.port=45450 \
  -DcertificatePath=/path/to/your-certificate.p12 \
  -DcertificatePassword=yourPassword \
  -Dauth.enabled=true \
  -Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service \
  -Ddb.user=your_user \
  -Ddb.password=your_password \
  -Dtools=jdbc-analyzer \
  -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```

This exposes the authenticated MCP endpoint at: `https://localhost:45450/mcp`.

##### Using HTTP transport and Cline

Cline supports streamable HTTP directly. Example:

```json
{
  "mcpServers": {
    "oracle-db-mcp-toolkit": {
      "type": "streamableHttp",
      "url": "https://localhost:45450/mcp"
    }
  }
}
```

##### Using HTTP from Claude Desktop

Claude Desktop accepts HTTPS endpoints for remote MCP servers.

```json
{
  "mcpServers": {
    "oracle-db-mcp-toolkit": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://localhost:45450/mcp"
      ]
    }
  }
}
```

### 4.4 HTTP Authentication Configuration

#### 4.4.1. Generated Token (For Development and Testing)

To enable authentication for the HTTP server, set `-Dauth.enabled=true` (default: `false`). HTTP transport refuses to start without authentication unless `-Dhttp.allowUnauthenticatedForDevelopment=true` is explicitly set for local development.
If it's enabled (e.g. set to `true`) the MCP Server will check if there's an environment variable called `ORACLE_DB_TOOLKIT_AUTH_TOKEN` and its value will be used as a token.
If the environment variable is not found, then a random UUID token will be generated once per JVM session. The token would be logged at the `INFO` level.

When connecting to the MCP server, the token needs to be provided in the Authorization header of each request using the `Bearer ` prefix.

#### 4.4.2. OAuth2 Configuration

In order to configure an OAuth2 server, enable `-Dauth.enabled=true` alongside the following system properties:

* `-Dauth.authorizationServer`: The OAuth2 server URL which MUST provide the `/.well-known/oauth-authorization-server`. If it only provides `/.well-known/openid-configuration`, enable `-Dauth.openIdDiscoveryRedirectEnabled=true`.
* `-Dmcp.oauth.scopes`: Optional space- or comma-separated OAuth scopes advertised to MCP clients for end-user login (default: `openid`).
* `-Dmcp.oauth.resourceUrl`: Optional externally visible MCP resource URL advertised in OAuth protected-resource metadata. Set this when the server is behind a proxy or public route whose URL differs from the incoming servlet request URL.
* `-Dauth.openIdDiscoveryRedirectEnabled`: (default: `false`) Creates an `/.well-known/oauth-authorization-server` endpoint that redirects to the authorization server's `/.well-known/openid-configuration` endpoint.
  It works by creating an `/.well-known/oauth-authorization-server` endpoint on the MCP Server that redirects to the OAuth server's `/.well-known/openid-configuration` endpoint.
* `-Dauth.userTokenValidation.mode`: Token validation mode. Use `introspection` (default) to validate bearer tokens by calling the OAuth2 introspection endpoint, or `jwt` to validate JWT access tokens locally with JWKS.
* `-Dauth.userTokenValidation.introspection.endpoint`: The OAuth2 server's introspection endpoint used to validate an access token (The OAuth2 introspection JSON response MUST contain the `active` field, e.g. `{...,"active": false,..}`).
  Which means that whenever the MCP server receives an HTTP request, it sends an HTTP request to the OAuth2 server's introspection endpoint to check the validity of the JWT access token.
* `-Dauth.userTokenValidation.jwt.issuer`: Required when `auth.userTokenValidation.mode=jwt`. Expected JWT `iss` claim.
* `-Dauth.userTokenValidation.jwt.jwksUri`: Required when `auth.userTokenValidation.mode=jwt`. JWKS endpoint used to fetch public signing keys.
* `-Dauth.userTokenValidation.jwt.audience`: Required when `auth.userTokenValidation.mode=jwt`. Expected JWT `aud` claim.
* `-Dauth.userTokenValidation.jwt.jwksCacheSeconds`: Optional JWKS cache duration in seconds when `auth.userTokenValidation.mode=jwt` (default: `600`).
* `-Dauth.userTokenValidation.introspection.clientId`: Client ID used for introspection (e.g. `oracle-db-toolkit`).
* `-Dauth.userTokenValidation.introspection.clientSecret`: Client secret used for introspection.
* `-DallowedHosts`: (default: `*`) The value of `Access-Control-Allow-Origin` header when requesting the `/.well-known/oauth-protected-resource` endpoint (and `/.well-known/oauth-authorization-server` if `-Dauth.openIdDiscoveryRedirectEnabled=true`) of the MCP Server.

##### MCP login scopes vs DeepSec database scopes

The OAuth scopes advertised with `-Dmcp.oauth.scopes` are for the human MCP user's browser login. For most OpenID Connect providers, this should remain `openid` unless your MCP client registration is explicitly allowed to request additional end-user scopes.

Do not put database resource scopes such as `OracleDBDB_ACCESS_SCOPE` in `mcp.oauth.scopes` unless the user-facing OAuth client is allowed to request that scope interactively. Database access-token scopes used for Deep Data Security are configured separately with `-Ddeepsec.databaseToken.scope`.

For more details regarding this MCP and OAuth, please see [MCP specification for authorization](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) (or a newer version if available).

##### Examples

###### Enabling Authentication with OAuth2

```bash
java \
    -Ddb.url=jdbc:oracle:thin:@host:1521/service \
    -Dtransport=http \
    -Dhttps.port=45450 \
    -DcertificatePath=/path/to/your-certificate.p12 \
    -DcertificatePassword=yourPassword \
    -Dauth.enabled=true \
    -Dauth.authorizationServer=http://localhost:8080/realms/mcp \
    -Dmcp.oauth.scopes=openid \
    -Dauth.userTokenValidation.introspection.endpoint=http://localhost:8080/realms/mcp/protocol/openid-connect/token/introspect \
    -Dauth.userTokenValidation.introspection.clientId=oracle-db-toolkit \
    -Dauth.userTokenValidation.introspection.clientSecret=Xj9mPqR2vL5kN8tY3hB7wF4uD6cA1eZ0 \
    -DallowedHosts=http://localhost:6274 \
    -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```

In the above example, we configured OAuth2 with a local KeyCloak server with a realm named `mcp`, and we only allowed a local [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)
running at <http://localhost:6274> to retrieve the data from <http://localhost:45450/.well-known/oauth-protected-resource>

###### Enabling JWT/JWKS Validation

If your authorization server issues JWT access tokens, the MCP server can validate them locally using JWKS instead of calling the introspection endpoint on every request:

```bash
java \
    -Ddb.url=jdbc:oracle:thin:@host:1521/service \
    -Dtransport=http \
    -Dhttps.port=8080 \
    -DcertificatePath=/path/to/your-certificate.p12 \
    -DcertificatePassword=yourPassword \
    -Dauth.enabled=true \
    -Dauth.authorizationServer=https://identity.example.com \
    -Dauth.userTokenValidation.mode=jwt \
    -Dauth.userTokenValidation.jwt.issuer=https://issuer.example.com/ \
    -Dauth.userTokenValidation.jwt.jwksUri=https://identity.example.com/.well-known/jwks.json \
    -Dauth.userTokenValidation.jwt.audience=https://identity.example.com \
    -Dmcp.oauth.scopes=openid \
    -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```

Use introspection instead when your authorization server issues opaque tokens, when central revocation checks are required on every request, or when your provider requires resource servers to call introspection. DeepSec is an exception: it requires the end-user access token to be a signed JWT with `iss` and `sub` claims, even if the toolkit also introspects that JWT.

### 4.5. Oracle Deep Data Security Support

Deep Data Security support lets Oracle Database enforce authorization using the authenticated MCP end user's token. The MCP server still opens database connections with the configured database username and password; DeepSec adds end-user context to those database operations through the Oracle JDBC `EndUserSecurityContextProvider` SPI.

When DeepSec is enabled, the request flow is:

1. The MCP server validates the inbound bearer token from the MCP client.
2. The server obtains a database-scoped DeepSec access token for the application.
3. The server creates an Oracle JDBC `EndUserSecurityContext` from the database access token and the end-user token.
4. OJDBC attaches that context to database operations.
5. Oracle Database activates data roles from the token claims.

Required properties:

* `-Ddeepsec.enabled=true`: Enables DeepSec context propagation. The end-user access token must be a signed JWT containing `iss` and `sub`; opaque tokens are rejected.
* `-Ddeepsec.databaseToken.tokenEndpoint`: OAuth2 token endpoint used to obtain the database-scoped DeepSec token.
* `-Ddeepsec.databaseToken.clientId`: Client ID used to obtain the database-scoped DeepSec token.
* `-Ddeepsec.databaseToken.clientSecret`: Client secret used to obtain the database-scoped DeepSec token.
* `-Ddeepsec.databaseToken.scope`: Database resource scope for the DeepSec/database token, for example `OracleDBDB_ACCESS_SCOPE`.
* `-Doracle.ucp.createConnectionInBorrowThread=true`: Ensures UCP creates a new physical connection in the request thread that is borrowing it, so the current DeepSec context is available during connection creation.

Optional properties:

* `-Ddeepsec.databaseToken.staticValue`: Static database-scoped token for local smoke tests. Prefer `deepsec.databaseToken.tokenEndpoint` plus client credentials for normal use.
* `-Ddb.transactionIdleTimeoutSeconds`: Rolls back an open transaction after this many unused seconds (default: `120`).
* `-Ddb.transactionMaxLifetimeSeconds`: Absolute maximum lifetime for a transaction that spans tool calls (default: `300`).
* `-Ddb.maxTransactionsPerUser`: Maximum concurrent open transactions for one authenticated user (default: `4`).

DeepSec requires a signed JWT end-user access token containing `iss` and `sub` claims. Transactions
that span MCP tool calls are bound to a non-reversible owner identifier derived from those claims.
Every query, resume, commit, and rollback verifies the same owner before touching the connection.
Calls using one transaction are serialized because a JDBC connection cannot be used concurrently.
Expired transactions are automatically rolled back and returned to the connection pool. A refreshed
JWT can resume a transaction when its issuer and subject remain unchanged. Opaque access tokens are
rejected when DeepSec is enabled because Oracle Database must validate the token and read its claims.

Oracle Database activates data roles from group claims in the end-user token. For example, an OCI IAM access-token claim such as:

```json
{
  "group": ["CustomerReaders", "MCPDummyReaders"]
}
```

can activate database roles mapped with clauses such as:

```sql
CREATE DATA ROLE customer_reader
  MAPPED TO 'IAM_OAUTH_GROUP=CustomerReaders';
```

Example:

```bash
java \
    -Ddb.url='jdbc:oracle:thin:@mydb_high?TNS_ADMIN=/path/to/wallet' \
    -Ddb.user=mcp_app_user \
    -Ddb.password='your-db-password' \
    -Doracle.ucp.createConnectionInBorrowThread=true \
    -Dtransport=http \
    -Dhttps.port=8080 \
    -DcertificatePath=/path/to/your-certificate.p12 \
    -DcertificatePassword=yourPassword \
    -Dauth.enabled=true \
    -Dauth.authorizationServer=https://idcs.example.com \
    -Dmcp.oauth.scopes=openid \
    -Dauth.userTokenValidation.introspection.endpoint=https://idcs.example.com/oauth2/v1/introspect \
    -Dauth.userTokenValidation.introspection.clientId=mcp-user-login-client-id \
    -Dauth.userTokenValidation.introspection.clientSecret='mcp-user-login-client-secret' \
    -Ddeepsec.enabled=true \
    -Ddeepsec.databaseToken.tokenEndpoint=https://idcs.example.com/oauth2/v1/token \
    -Ddeepsec.databaseToken.clientId=database-token-client-id \
    -Ddeepsec.databaseToken.clientSecret='database-token-client-secret' \
    -Ddeepsec.databaseToken.scope=OracleDBDB_ACCESS_SCOPE \
    -DconfigFile=/path/to/config.yaml \
    -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```

The user-login scope and the DeepSec database-token scope are intentionally separate:

* `mcp.oauth.scopes=openid` is advertised to MCP clients for browser login.
* `deepsec.databaseToken.scope=OracleDBDB_ACCESS_SCOPE` is used by the MCP server to request the database-scoped token used in the Oracle JDBC end-user security context.

#### DeepSec integration test

The database-backed test is disabled during normal builds. It starts a localhost OAuth callback listener, opens the OCI browser login, uses Authorization Code with PKCE, and keeps the resulting user token only in memory. It then uses the production OJDBC provider SPI with a one-connection UCP pool and verifies `ORA_END_USER_CONTEXT.username`, mapped roles from `v$end_user_data_role`, and a real Oracle transaction resumed across separate simulated requests. The transaction check creates a savepoint, verifies that `DBMS_TRANSACTION.LOCAL_TRANSACTION_ID` remains stable after resumption, and exercises both commit and rollback through the production transaction registry.

The configured `deepsec.it.userLogin.callbackUri` must be registered on the OCI application and its port must be free while Maven runs. The test uses `db.*`, `deepsec.databaseToken.*`, `auth.authorizationServer`, `deepsec.it.userLogin.*`, and `mcp.oauth.resourceUrl`. Do not run the MCP server on the callback port at the same time.

For a one-user smoke test, provide only the expected mapped database roles. The expected username defaults to the access token's `sub` claim and can be overridden with `DEEPSEC_IT_USER_A_USERNAME`:

```bash
export DEEPSEC_IT_ENABLED=true
export DEEPSEC_IT_USER_A_ROLES='CUSTOMER_READER,MCP_DUMMY_READER'

mvn -Ddb.url='jdbc:oracle:thin:@mydb_high?TNS_ADMIN=/path/to/wallet' \
    -Ddb.user=mcp_app_user \
    -Ddb.password='your-db-password' \
    -Dojdbc.ext.dir=/path/to/ojdbc/extensions \
    -Ddeepsec.databaseToken.tokenEndpoint=https://idcs.example.com/oauth2/v1/token \
    -Ddeepsec.databaseToken.clientId=database-token-client-id \
    -Ddeepsec.databaseToken.clientSecret='database-token-client-secret' \
    -Ddeepsec.databaseToken.scope=OracleDBDB_ACCESS_SCOPE \
    -Dauth.authorizationServer=https://idcs.example.com \
    -Ddeepsec.it.userLogin.clientId=user-login-client-id \
    -Ddeepsec.it.userLogin.clientSecret='user-login-client-secret' \
    -Ddeepsec.it.userLogin.callbackUri=http://localhost:8080/auth/callback \
    -Ddeepsec.it.userLogin.scopes='openid OracleDBDB_ACCESS_SCOPE' \
    -Dmcp.oauth.resourceUrl=http://localhost:8080/mcp \
    -Dtest=DeepSecIntegrationTest test
```

The default one-user run also injects a distinct authenticated owner and verifies it is rejected before the held JDBC connection is touched, so a second OCI account is not required to test transaction ownership. For the stronger identity-provider check, set `DEEPSEC_IT_TWO_USERS=true`. The test then opens a second login, verifies the two token subjects differ, executes as A, then B, then A again on a pool limited to one physical connection, and uses the real user B owner for the denial check. OCI may bind the browser session to user A even with `prompt=login`; log out first or open the printed user-B authorization URL in an incognito/separate browser profile. Set `DEEPSEC_IT_USER_B_ROLES` only when that account has mapped roles that should also be asserted. Role names are compared exactly as the database returns them. `DEEPSEC_IT_DATABASE_ACCESS_TOKEN` remains available as an optional override; otherwise the test fetches the application database token through the configured `deepsec.*` provider.

### 4.6. Enabling Authentication without OAuth2

_Note: This mode is used only for development and testing purposes._

```bash
java \
    -Ddb.url=jdbc:oracle:thin:@host:1521/service \
    -Dtransport=http \
    -Dhttps.port=45450 \
    -DcertificatePath=/path/to/your-certificate.p12 \
    -DcertificatePassword=yourPassword \
    -Dauth.enabled=true \
    -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```

After starting the server, a UUID token will be generated and logged at `INFO` level:

```log
...
Nov 25, 2025 12:15:13 PM com.oracle.database.mcptoolkit.oauth.OAuth2Configuration <init>
INFO: Authentication is enabled
Nov 25, 2025 12:15:13 PM com.oracle.database.mcptoolkit.oauth.OAuth2Configuration <init>
WARNING: OAuth2 is not configured
Nov 25, 2025 12:15:13 PM com.oracle.database.mcptoolkit.oauth.TokenGenerator <init>
INFO: Authorization token generated (for testing and development use only): 0dd11948-37a3-470f-911e-4cd8b3d6f69c
...
```

If `ORACLE_DB_TOOLKIT_AUTH_TOKEN` environment variable is set:

```bash
export ORACLE_DB_TOOLKIT_AUTH_TOKEN=Secret_DeV_T0ken
```

Then the server logs will be the following:

```log
Nov 25, 2025 4:10:26 PM com.oracle.database.jdbc.oauth.OAuth2Configuration <init>
INFO: Authentication is enabled
Nov 25, 2025 4:10:26 PM com.oracle.database.jdbc.oauth.OAuth2Configuration <init>
WARNING: OAuth2 is not configured
Nov 25, 2025 4:10:26 PM com.oracle.database.jdbc.oauth.TokenGenerator <init>
INFO: Authorization token generated (for testing and development use only): Secret_DeV_T0ken
```

Ultimately, the token must be included in the http request header (e.g. `Authorization: Bearer 0dd11948-37a3-470f-911e-4cd8b3d6f69c` or `Authorization: Bearer Secret_DeV_T0ken`).

---

## 5. Supported System Properties

<table>
  <thead>
    <tr>
      <th>Property</th>
      <th>Required</th>
      <th>Description</th>
      <th>Example</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>db.url</code></td>
      <td><strong>No*</strong></td>
      <td>JDBC URL for Oracle Database. <em>Required only if any database tools are enabled</em> (not required for log-analyzer–only setups).</td>
      <td><code>jdbc:oracle:thin:@your-host:1521/your-service</code></td>
    </tr>
    <tr>
      <td><code>db.user</code></td>
      <td><strong>No*</strong></td>
      <td>Database username (not required if using token-based auth or centralized config loaded via <code>ojdbc.ext.dir</code>)</td>
      <td><code>ADMIN</code> or <code>your-username</code></td>
    </tr>
    <tr>
      <td><code>db.password</code></td>
      <td><strong>No*</strong></td>
      <td>Database password (not required if using token-based auth or centralized config loaded via <code>ojdbc.ext.dir</code>)</td>
      <td><code>your-secure-password</code></td>
    </tr>
    <tr>
      <td><code>tools</code> (aka <code>-Dtools</code>)</td>
      <td>No</td>
      <td>
        Comma-separated allow-list of tool or toolset names to enable (case-insensitive).<br/>
        You can pass individual tools (e.g. <code>jdbc-analyzer</code>, <code>read-query</code>) or any of the following built-in toolsets:
        <ul>
          <li><code>mcp-admin</code> — protected runtime configuration and administrative inventory tools (edit-tools, list-credentials)</li>
          <li><code>database-operator</code> — database operations, transactions, monitoring, and execution plans (read-query, write-query, table, transaction, db-ping, db-metrics-range, explain-plan).</li>
          <li><code>log-analyzer</code> — all JDBC log and RDBMS/SQLNet analysis tools (jdbc-analyzer and rdbms-analyzer)</li>
          <li><code>rag</code> — vector store management, document embedding, and semantic similarity search (vector-model, vector-store, embed, task, oci-storage, similarity-search)</li>
        </ul>
        You can also define your own YAML <code>toolsets:</code> and reference them here.  
        Use <code>*</code> or <code>all</code> to enable all non-protected tools. If omitted, all non-protected tools are enabled by default.
      </td>
      <td><code>mcp-admin, log-analyzer</code> or <code>reporting</code></td>
    </tr>
    <tr>
      <td><code>ojdbc.ext.dir</code></td>
      <td>No</td>
      <td>
        Directory to load extra jars at runtime (keeps the MCP jar lean).  
        Useful for optional components like <code>oraclepki</code> when using TCPS wallets, token authentication, or centralized driver config.
      </td>
      <td><code>/opt/oracle/ext-jars</code></td>
    </tr>
    <tr>
      <td><code>ingestRootDir</code></td>
      <td>No</td>
      <td>Root directory for local file ingestion with the <code>embed</code> tool. Required only for <code>action=file</code> and <code>action=files</code>. Requested file paths must resolve inside this directory.</td>
      <td><code>/opt/mcp/ingest</code></td>
    </tr>
    <tr>
      <td><code>ingestMaxFileSizeMb</code></td>
      <td>No</td>
      <td>Maximum file size for <code>embed</code> ingestion from local files and OCI bucket objects. The value is in MB. Default is <code>50</code>.</td>
      <td><code>50</code></td>
    </tr>
    <tr>
      <td><code>transport</code></td>
      <td>No</td>
      <td>
        Transport mode for the MCP server. Supported values:
        <code>stdio</code> or <code>http</code>. If omitted, <code>stdio</code> is used.
      </td>
      <td><code>http</code></td>
    </tr>
    <tr>
      <td><code>https.port</code></td>
      <td>No</td>
      <td>
        TCP port used for SSL connection.
      </td>
      <td><code>45451</code></td>
    </tr>
    <tr>
      <td><code>http.allowedOriginalHosts</code></td>
      <td>No</td>
      <td>Optional comma-separated browser-origin host allowlist. When configured, requests without an <code>Origin</code> header or with an untrusted origin are rejected before MCP dispatch. Disabled by default for non-browser client compatibility.</td>
      <td><code>-Dhttp.allowedOriginalHosts=mcp.example.com</code></td>
    </tr>
    <tr>
      <td><code>http.allowUnauthenticatedForDevelopment</code></td>
      <td>No</td>
      <td>Allows unauthenticated HTTP transport for local development only. Defaults to <code>false</code>; enabling it emits a security warning.</td>
      <td><code>-Dhttp.allowUnauthenticatedForDevelopment=true</code></td>
    </tr>
    <tr>
      <td><code>certificatePath</code></td>
      <td>No</td>
      <td>
        Path to SSL certificate keystore (Support PKCS12)
      </td>
      <td><code>/path/to/your/certificate</code></td>
    </tr>
    <tr>
      <td><code>certificatePassword</code></td>
      <td>No</td>
      <td>
        Password of SSL certificate keystore
      </td>
    </tr>
    <tr>
      <td><code>configFile</code></td>
      <td>No</td>
      <td>Path to a YAML file defining <code>datasources</code> and <code>tools</code>. Required if you intend to use the <code>edit-tools</code> admin tool to persist changes.</td>
      <td>/opt/mcp/config.yaml</td>
    </tr>
    <tr>
      <td><code>auth.enabled</code></td>
      <td>No</td>
      <td>Whether HTTP authentication is required or not (default <code>false</code>).<br/>
      All the subsequent OAuth2 system properties are ignored if this property is set to <code>false</code>.</td>
      <td><code>-Dauth.enabled=true</code></td>
    </tr>
    <tr>
      <td><code>auth.authorizationServer</code></td>
      <td>No</td>
      <td>Configure the OAuth2 server URL</td>
      <td><code>-Dauth.authorizationServer=http://localhost:8080/realms/master</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.introspection.endpoint</code></td>
      <td>No</td>
      <td>The OAuth2 server endpoint used to validate and obtain metadata about an access token.</td>
      <td><code>-Dauth.userTokenValidation.introspection.endpoint=http://localhost:8080/realms/mcp/protocol/openid-connect/token/introspect</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.introspection.clientId</code></td>
      <td>No</td>
      <td>The client identifier for registering with the configured OAuth2 server.</td>
      <td><code>-Dauth.userTokenValidation.introspection.clientId=oracle-db-toolkit</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.introspection.clientSecret</code></td>
      <td>No</td>
      <td>The confidential key used to authenticate the client to the configured authorization server during the OAuth2 flow.</td>
      <td><code>-Dauth.userTokenValidation.introspection.clientSecret=Xj9mPqR2vL5kN8tY3hB7wF4uD6cA1eZ0</code></td>
    </tr>
    <tr>
      <td><code>oauth.scopeClaimPath</code></td>
      <td>No</td>
      <td>Dot-separated path in the OAuth2 introspection response that contains scopes. Defaults to <code>scope</code>.</td>
      <td><code>-Doauth.scopeClaimPath=scope</code></td>
    </tr>
    <tr>
      <td><code>editTools.requireScope</code></td>
      <td>No</td>
      <td>Whether <code>edit-tools</code> requires OAuth scope <code>mcp:tools:write</code> or <code>mcp:admin</code> when HTTP authentication is enabled. Defaults to <code>true</code>. Set to <code>false</code> only when any authenticated caller should be allowed to use <code>edit-tools</code>.</td>
      <td><code>-DeditTools.requireScope=false</code></td>
    </tr>
    <tr>
      <td><code>listCredentials.requireScope</code></td>
      <td>No</td>
      <td>Whether <code>list-credentials</code> requires OAuth scope <code>mcp:credentials:read</code> or <code>mcp:admin</code> when HTTP authentication is enabled. Defaults to <code>true</code>. Set to <code>false</code> only when any authenticated caller should be allowed to list credential metadata.</td>
      <td><code>-DlistCredentials.requireScope=false</code></td>
    </tr>
    <tr>
      <td><code>allowedHosts</code></td>
      <td>No</td>
      <td>The <code>Access-Control-Allow-Origin</code> header value when making a request to the MCP Server's <code>/.well-known/oauth-protected-resource</code> endpoint (default <code>*</code> e.g. all hosts are allowed).</td>
      <td><code>-DallowedHosts=http://localhost:6274</code></td>
    </tr>
    <tr>
      <td><code>auth.openIdDiscoveryRedirectEnabled</code></td>
      <td>No</td>
      <td>System property that redirects MCP Server's <code>/.well-known/oauth-authorization-server</code> endpoint to the OAuth server's <code>/.well-known/openid-configuration</code> as a workaround for servers lacking the former (default value is <code>false</code>. If OAuth is not properly configured, then this system property is ignored).</td>
      <td><code>-Dauth.openIdDiscoveryRedirectEnabled=false</code></td>
    </tr>
    <tr>
      <td><code>mcp.oauth.scopes</code></td>
      <td>No</td>
      <td>Space- or comma-separated scopes advertised to MCP clients for end-user login. Keep this separate from DeepSec/database scopes. Defaults to <code>openid</code>.</td>
      <td><code>-Dmcp.oauth.scopes=openid</code></td>
    </tr>
    <tr>
      <td><code>mcp.oauth.resourceUrl</code></td>
      <td>No</td>
      <td>Externally visible MCP endpoint URL advertised in OAuth protected-resource metadata. Useful behind proxies or public routes.</td>
      <td><code>-Dmcp.oauth.resourceUrl=https://example.com/api/mcp</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.mode</code></td>
      <td>No</td>
      <td>Bearer token validation mode: <code>introspection</code> (default) or <code>jwt</code>.</td>
      <td><code>-Dauth.userTokenValidation.mode=jwt</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.jwt.issuer</code></td>
      <td>No</td>
      <td>Expected JWT issuer. Required when <code>auth.userTokenValidation.mode=jwt</code>.</td>
      <td><code>-Dauth.userTokenValidation.jwt.issuer=https://identity.example.com/</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.jwt.jwksUri</code></td>
      <td>No</td>
      <td>JWKS endpoint used to fetch token-signing public keys. Required when <code>auth.userTokenValidation.mode=jwt</code>.</td>
      <td><code>-Dauth.userTokenValidation.jwt.jwksUri=https://identity.example.com/.well-known/jwks.json</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.jwt.audience</code></td>
      <td>No</td>
      <td>Expected JWT audience. Required when <code>auth.userTokenValidation.mode=jwt</code>.</td>
      <td><code>-Dauth.userTokenValidation.jwt.audience=https://identity.example.com</code></td>
    </tr>
    <tr>
      <td><code>auth.userTokenValidation.jwt.jwksCacheSeconds</code></td>
      <td>No</td>
      <td>JWKS cache duration in seconds when <code>auth.userTokenValidation.mode=jwt</code>. Defaults to <code>600</code>.</td>
      <td><code>-Dauth.userTokenValidation.jwt.jwksCacheSeconds=600</code></td>
    </tr>
    <tr>
      <td><code>deepsec.enabled</code></td>
      <td>No</td>
      <td>Enables Oracle Deep Data Security end-user context propagation through OJDBC.</td>
      <td><code>-Ddeepsec.enabled=true</code></td>
    </tr>
    <tr>
      <td><code>deepsec.databaseToken.tokenEndpoint</code></td>
      <td>No</td>
      <td>OAuth2 token endpoint used to obtain the database-scoped token for DeepSec.</td>
      <td><code>-Ddeepsec.databaseToken.tokenEndpoint=https://idcs.example.com/oauth2/v1/token</code></td>
    </tr>
    <tr>
      <td><code>deepsec.databaseToken.clientId</code></td>
      <td>No</td>
      <td>Client ID used by the MCP server to obtain the database-scoped DeepSec token.</td>
      <td><code>-Ddeepsec.databaseToken.clientId=database-token-client-id</code></td>
    </tr>
    <tr>
      <td><code>deepsec.databaseToken.clientSecret</code></td>
      <td>No</td>
      <td>Client secret used by the MCP server to obtain the database-scoped DeepSec token.</td>
      <td><code>-Ddeepsec.databaseToken.clientSecret=database-token-client-secret</code></td>
    </tr>
    <tr>
      <td><code>deepsec.databaseToken.scope</code></td>
      <td>No</td>
      <td>Database resource scope used only for the DeepSec/database token. Do not confuse this with <code>mcp.oauth.scopes</code>.</td>
      <td><code>-Ddeepsec.databaseToken.scope=OracleDBDB_ACCESS_SCOPE</code></td>
    </tr>
    <tr>
      <td><code>deepsec.databaseToken.staticValue</code></td>
      <td>No</td>
      <td>Static database-scoped token for local smoke tests. Prefer <code>deepsec.databaseToken.tokenEndpoint</code> plus client credentials for normal use.</td>
      <td><code>-Ddeepsec.databaseToken.staticValue=...</code></td>
    </tr>
  </tbody>
</table>

<i>* Note:</i> If you don’t set tools, all tools are available by default.

<i>* Conditional requirement:</i> <code>db.url</code> is required **only if** any database tool is enabled via <code>-Dtools</code>.

If you enable **only** the Log Analyzer tools, you can omit <code>db.url</code>.

<i>* Note:</i> If you’re using token-based authentication (e.g., IAM tokens) or a centralized configuration provided via the JARs you place in `-Dojdbc.ext.dir`,
you can omit `db.user` and `db.password`. The driver will pick up credentials and security settings from those extensions.

---

## 6. Docker Image

A `Dockerfile` is included at the root of the project so you can build and run the MCP server as a container.

### 6.1. Build the image

From the project root (where the Dockerfile lives):

```bash
podman build -t oracle-db-mcp-toolkit:1.0.0 .
```

### 6.2. Run the container (HTTP mode example)

This example runs the MCP server over HTTP and HTTPS inside the container and exposes it on port 45450 and 45451 on your host.

```bash
podman run --rm \
  -p 45450:45450 \
  -p 45451:45451 \
  -v /path/to/certificate:/app/certif.p12:ro,z \
  -e JAVA_TOOL_OPTIONS="\
    -Dtransport=http \
    -Dhttps.port=45451 \
    -DcertificatePath=[path/to/certificate] \
    -DcertificatePassword=[password] \
    -Dhttp.allowedOriginalHosts=your-public-hostname \
    -Dauth.enabled=true \
    -Dtools=get-jdbc-stats,get-jdbc-queries \
    -Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service \
    -Ddb.user=your_user \
    -Ddb.password=your_password" \
  oracle-db-mcp-toolkit:1.0.0
```

This exposes the MCP endpoint at: https://[your-ip-address]:45451/mcp

If you plan to use the `edit-tools` admin tool inside the container, mount a writable config file and set `-DconfigFile` accordingly, for example:
- Mount: `-v /absolute/path/config.yaml:/config/config.yaml:Z`
- Set: `-DconfigFile=/config/config.yaml`

You can then configure Cline or Claude Desktop as described in the Using HTTP from Cline / Claude Desktop sections above.

If you need extra JDBC / security jars (e.g. `oraclepki`, wallets, centralized config, or providers that fetch full
database credentials such as username, password, and connection string from a vault secret),
mount them and point `ojdbc.ext.dir` at that directory:

```bash
podman run --rm \
  -p 45450:45450 \
  -p 45451:45451 \
  -v /path/to/ext:/ext:ro \
  -v /path/to/certificate:/app/certif.p12:ro,z \
  -e JAVA_TOOL_OPTIONS="\
    -Dtransport=http \
    -Dhttps.port=45451 \
    -Dhttp.allowedOriginalHosts=your-public-hostname \
    -Dauth.enabled=true \
    -Dtools=get-jdbc-stats,get-jdbc-queries \
    -Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service \
    -Ddb.user=your_user \
    -Ddb.password=your_password \
    -Dojdbc.ext.dir=/ext" \
  oracle-db-mcp-toolkit:1.0.0
```

### 6.3. Using Docker/Podman with stdio

Instead of running the MCP server over HTTP, you can keep using the **stdio** transport
and let your MCP client spawn the container (via **podman run**) instead of spawning java directly.
In this mode, the MCP client talks to the server over stdin/stdout, just like with a local JAR.

#### Example: Claude Desktop using Podman (stdio)

In this configuration, Claude Desktop runs `podman run --rm -i ...à and connects to the server via stdio:

```json
{
  "mcpServers": {
    "oracle-db-mcp-toolkit": {
      "command": "podman",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "/absolute/path/to/ext:/ext:ro",
        "-e",
        "JAVA_TOOL_OPTIONS=-Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service -Ddb.user=your_user -Ddb.password=your_password -Dojdbc.ext.dir=/ext -DconfigFile=/config/config.yaml",
        "oracle-db-mcp-toolkit:1.0.0"
      ]
    }
  }
}
```
