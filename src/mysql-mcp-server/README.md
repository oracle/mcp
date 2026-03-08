# MySQL MCP Server (mysql_mcp_server.py)

A Python-based MCP (Model Context Protocol) server that provides a suite of tools for managing and interacting with MySQL AI and MySQL HeatWave database resources. This MCP server is not intended for production use but as a proof of concept for exploring models using MCP Servers.

## Overview

`mysql_mcp_server.py` is a FastMCP-based server that provides tools for managing MySQL connections, executing SQL, using MySQL AI or MySQL HeatWave ML/GenAI features, and working with OCI Object Storage. MySQL MCP Server is the recommended server to get started with MySQL HeatWave or MySQL AI and the only server in this repo that supports MySQL AI.

## Features

- **Database Connection Management**
  - Load connection configs from JSON or environment variables
  - List all configured database connections
  - Validate connectivity and resolve provider mode (MySQL AI vs. MySQL HeatWave)

- **Database Operations**
  - Execute SQL queries

- **MySQL AI and MySQL HeatWave ML and GenAI Tools**
  - `ml_generate`: Text generation with GenAI
  - `ragify_column`: Create/populate vector columns for embeddings
  - `ask_ml_rag`: Retrieval-augmented generation from vector stores
  - `ask_ml_rag_vector_store`: Retrieve segments from the default vector store (skip_generate)
  - `ask_ml_rag_innodb`: Retrieve segments from InnoDB tables using specified segment and embedding columns
  - `heatwave_ask_help`: Answers questions about how to use HeatWave ML
  - `ask_nl_sql`: Convert natural language questions into SQL queries and execute them automatically
  - `retrieve_relevant_schema_information`: Retrieve relevant schemas and tables (DDL) for a natural language question

- **Vector Store Management**
  - List files in `secure_file_priv` (local mode)
  - Load documents into vector stores from local file system
  - Load documents from OCI Object Storage into vector stores

- **OCI Object Store Tools**
  - List all compartments
  - Get compartment by name
  - List buckets in a compartment
  - List objects in a bucket

## Prerequisites
- Valid database connection file. Resolution order:
  1) Path specified by environment variable `MYSQL_MCP_CONFIG` (absolute or relative to this module)
  2) `local_config.json` (default)
- Valid OCI configuration file (`~/.oci/config`) or environment variables


## OCI Configuration

The server requires a valid OCI config file with proper credentials.
The default location is ~/.oci/config. For instructions on setting up this file,
see the [OCI SDK documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm).


## Supported Database Modes

- `MySQL AI`
- `HeatWave`

## MCP Server Configuration

Installation is dependent on the MCP Client being used, it usually consists of adding the MCP Server invocation in a json config file, for example with Claude UI on Windows it looks like this:
```json
{
  "mcpServers": {
    "mysqltools": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\mysql-mcp-server",
        "run",
        "oracle.mysql_mcp_server"
      ]
    }
  }
}
```
**Note**: On Windows you may have to provide the suffix *.exe* to "oracle.mysql_mcp_server".



Example with TENANCY_ID_OVERRIDE::
```json
{
  "mcpServers": {
    "mysqltools": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\ABSOLUTE\\PATH\\TO\\PARENT\\FOLDER\\mysql-mcp-server",
        "run",
        "oracle.mysql_mcp_server"
      ],
      "env": {
        "TENANCY_ID_OVERRIDE": "ocid1.tenancy.oc1..deadbeef"
      }
    }
  }
}
```

## Environment Variables

The server supports the following environment variables:

- `PROFILE_NAME`: OCI configuration profile name (default: "DEFAULT")
- `TENANCY_ID_OVERRIDE`: Overrides the tenancy ID from the config file

## Configuration (utils.fill_config_defaults and utils.load_mysql_config)

The server loads and validates connection configuration using two helpers in utils.py.

- utils.load_mysql_config:
  - Search order (first existing file wins):
    1) Path from env `MYSQL_MCP_CONFIG` (if set). If relative, also tries `<module_dir>/<value>`.
    2) `<module_dir>/local_config.json` (default when env not set)
    3) `<module_dir>/config.json`
    4) `<cwd>/config.json`
  - Returns a validated dict after passing the loaded JSON through fill_config_defaults.

- utils.fill_config_defaults:
  - Validates the schema and applies defaults for the optional bastion section.
  - Expected JSON shape:
    {
      "server_infos": {
        "<connection_id>": {
          "host": "<hostname or IP>",
          "user": "<username>",
          "password": "<password>",
          "database": "<default_schema>",
          "port": 3306
        }
      },
      "bastion": {                         // optional; for SSH tunneling
        "bastion_host": "<host>",
        "bastion_username": "<user>",
        "private_key_path": "<path to private key>",
        "db_host": "<remote DB host>",
        "db_port": 3306,                   // default 3306
        "bastion_port": 22,                // default 22
        "local_bind_host": "127.0.0.1",    // default 127.0.0.1
        "local_bind_port": 3306            // default 3306
      }
    }
  - Required server entry keys are exactly: {"host","user","password","database","port"}.
  - If a bastion block is present, only the allowed keys above are permitted; defaults are applied when omitted.

Example minimal config (local file):
{
  "server_infos": {
    "local_server": {
      "host": "localhost",
      "user": "root",
      "password": "",
      "database": "mysql_mcp",
      "port": 3306
    }
  }
}

Example with bastion:
{
  "server_infos": {
    "remote_via_bastion": {
      "host": "127.0.0.1",
      "user": "dbuser",
      "password": "secret",
      "database": "appdb",
      "port": 3306
    }
  },
  "bastion": {
    "bastion_host": "bastion.example.com",
    "bastion_username": "ubuntu",
    "private_key_path": "/home/user/.ssh/id_rsa",
    "db_host": "mysql.internal",
    "db_port": 3306
    // optional keys (with defaults if omitted): bastion_port, local_bind_host, local_bind_port
  }
}

Note:
- Set `MYSQL_MCP_CONFIG` to point at a specific JSON file if you don't want to use `local_config.json`.
- The defaults and schema enforcement are performed at startup; invalid or incomplete entries raise clear exceptions.

## Usage

The server runs using stdio transport and can be started by running:

```bash
uv run oracle.mysql_mcp_server
```

## API Tools

1. `list_all_connections()`: List configured database connections and modes
2. `execute_sql_tool_by_connection_id(connection_id, sql_script, params)`: Execute SQL on a database connection
3. `ml_generate(connection_id, question)`: Generate text
4. `ragify_column(connection_id, table_name, input_column_name, embedding_column_name)`: Embed text into a VECTOR column
5. `list_vector_store_files_local(connection_id)`: List available files in `secure_file_priv`
6. `load_vector_store_local(connection_id, file_path)`: Load documents from local filesystem
7. `load_vector_store_oci(connection_id, namespace, bucket_name, document_prefix)`: Load documents from OCI Object Storage
8. `ask_ml_rag_vector_store(connection_id, question, context_size)`: RAG query on default vector store
9. `ask_ml_rag_innodb(connection_id, question, segment_col, embedding_col, context_size)`: RAG query restricted to InnoDB tables
10. `heatwave_ask_help(connection_id, question)`: Ask natural language questions about MySQL HeatWave AutoML via NL2ML
11. `list_all_compartments()`: List OCI compartments
12. `object_storage_list_buckets(compartment_name | compartment_id)`: List buckets in a compartment
13. `object_storage_list_objects(namespace, bucket_name)`: List objects in a bucket
14. `ask_nl_sql(connection_id, question)`: Convert natural language questions into SQL queries and execute them automatically

## Security

- Uses OCI’s config-based authentication
- MySQL connection parameters may be stored in JSON config or environment variables

## Example Prompts

Here are example prompts you can use to interact with the MCP server, note that depending on the model being used you might need to be more specific, for example: "list all employees using myConnection1 mysql connection".

### 1. Database Operations

```
"List all configured database connections"
"Execute 'SELECT * FROM employees' on my connection"
"Add embeddings for 'body' column into 'embedding' column in docs table"
```

### 2. MySQL AI/MySQL HeatWave

```
"Generate a summary of error logs"
"Ask ml_rag: Show me refund policy from the vector store"
"What is the average delay incurred by flights?"
```

### 3. Object Storage

```
"List all compartments in my tenancy"
"Show all buckets in the development compartment"
"List objects in my 'docs-bucket'"
```

### 4. Vector Store

```
"Load all documents with prefix 'manuals/' into schema hr, table product_docs"
"List local files for vector store ingestion"
```

---

## Appendix: Feature Compatibility and Common Questions

### Q&A Reference

**Q: Is the repo for both HeatWave and MySQL AI?**
A: Yes. This repository supports both MySQL HeatWave and MySQL AI.

**Q: What happened to call_nl2ml for HeatWave? Does one need to use the dbtools server for that?**
A: The `heatwave_ask_help` (NL2ML) tool works only for HeatWave (not for MySQL AI connections). It provides clear, useful error messages if used with an unsupported connection. The dbtools MCP server is not required.

**Q: Do all tools work with both MySQL HeatWave and MySQL AI, with only the connection differing?**
A: No. Not all tools are universally supported. Some are exclusive to MySQL HeatWave (OCI), while others are only for MySQL AI. Refer to the specific tool answers in this appendix.

**Q: What happens if you try to use `list_vector_store_files_local` with a HeatWave connection?**
A: The `list_vector_store_files_local` tool does not function with HeatWave connections. If called on a MySQL HeatWave connection, it  will fail gracefully with an error message. When working with MySQL HeatWave, use `load_vector_store_oci` to load documents from object store instead.

**Q: Can `load_vector_store_oci` be used with MySQL AI (e.g., to load files from OCI Object Store into the InnoDB vector store)?**
A: No. The `load_vector_store_oci` tool only works with MySQL HeatWave (OCI) connections. If called on a MySQL AI connection, it will fail gracefully with an error message. When working with MySQL AI, use `load_vector_store_local` to load documents from the local file system instead.

**Q: Will `ragify_column` work with both HeatWave and MySQL AI?**
A: Yes. The `ragify_column` tool is fully supported on both MySQL AI and MySQL HeatWave connections. Its operation and results are the same on both platforms.

**Q: Where does `ask_ml_rag_innodb` execute its vector processing? For example, does it always run solely in MySQL Database Service (MDS), or will the table be loaded into HeatWave and the vector computations performed on the HeatWave cluster?**
A: On MySQL HeatWave (OCI) connections, `ask_ml_rag_innodb` loads the relevant InnoDB table into the HeatWave cluster, and all vector search and processing are executed on the HeatWave cluster for maximum performance. On MySQL AI connections, the processing takes place within the database service instance itself (not a distributed cluster).

**Q: Is the `.oci/config` always needed, or only when (a) listing Compartments/Object Store or (b) loading files from the Object Store?**
A: The OCI config file is required only for features that interact with Oracle Cloud Infrastructure—such as listing compartments, accessing Object Store, or loading files from Object Store. All other functionality can be used without `.oci/config`.

**Q: Will the MCP server work with MySQL AI if there is no OCI config present? Will it support a purely on-premises user?**
A: Yes. The MCP server supports MySQL AI connections without requiring an OCI config file, making it suitable for on-premises environments. For MySQL HeatWave (OCI) connections, any features not dependent on cloud resources will also continue to work if the OCI config is absent. Cloud-dependent requests (such as for OCI Object Store or Compartments) will fail gracefully if attempted without an OCI config.

---
