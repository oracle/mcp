# MySQL MCP Server (mysql_mcp_server.py)

A Python-based MCP (Model Context Protocol) server that provides a suite of tools for managing and interacting with MySQL AI and MySQL HeatWave database resources. This MCP server is not intended for production use but as a proof of concept for exploring models using MCP Servers.

## Overview

`mysql_mcp_server.py` is a FastMCP-based server that provides tools for managing MySQL connections, executing SQL, using MySQL AI ML/AI features, and working with OCI Object Storage.

## Features

- **Database Connection Management**
  - Load connection configs from JSON or environment variables
  - List all configured database connections
  - Validate connectivity and resolve provider mode (MySQL AI vs. OCI)

- **Database Operations**
  - Execute SQL queries

- **MySQL AI ML and AI Tools**
  - `ml_generate`: Text generation with MySQL AI GenAI
  - `ragify_column`: Create/populate vector columns for embeddings
  - `ask_ml_rag`: Retrieval-augmented generation from vector stores

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

- Python 3.x
- `fastmcp`
- `oci` SDK
- `mysql-connector-python` SDK
- Valid database connection file. Resolution order:
  1) Path specified by environment variable `MYSQL_MCP_CONFIG` (absolute or relative to this module)
  2) `src/mysql-mcp-server/local_config.json` (default)
- Valid OCI configuration file (`~/.oci/config`) or environment variables

## Installation

1. Clone this repository.
2. Install required dependencies using pip:
   ```
   pip install -r requirements.txt
   ```
   This will install `oci`, `fastmcp`, `mysql-connector-python`, and all other dependencies.
3. Set up your OCI config file at ~/.oci/config

## OCI Configuration

The server requires a valid OCI config file with proper credentials.
The default location is ~/.oci/config. For instructions on setting up this file,
see the [OCI SDK documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm).

## Required Python Packages

- `oci`
- `requests`
- `fastmcp`
- `mysql-connector-python`

## Supported Database Modes

- **MYSQL_AI** (local MySQL AI AI mode)
- **OCI** (Oracle Cloud Infrastructure-managed databases)

## MCP Server Configuration

Installation is dependent on the MCP Client being used, it usually consists of adding the MCP Server invocation in a json config file, for example with Claude UI on windows it looks like this:
```json
{
  "mcpServers": {
    "mysqltools": {
      "command": "C:\\Python\\python.exe",
      "args": [
        "C:\\Users\\user1\\mysql-mcp-server\\mysql_mcp_server.py"
      ]
    }
  }
}
```



Example with TENANCY_ID_OVERRIDE::
```json
{
  "mcpServers": {
    "mysqltools": {
      "command": "C:\\Python\\python.exe",
      "args": [
        "C:\\Users\\user1\\mysql-mcp-server\\mysql_mcp_server.py"
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
python mysql_mcp_server.py
```

## API Tools

1. `list_all_connections()`: List configured database connections and modes
2. `execute_sql_tool_by_connection_id(connection_id, sql, params)`: Execute SQL on a database connection
3. `ml_generate(connection_id, question)`: Generate text via MySQL AI ML
4. `ragify_column(connection_id, table, input_col, embedding_col)`: Embed text into a VECTOR column
5. `list_vector_store_files_local(connection_id)`: List available files in `secure_file_priv`
6. `load_vector_store_local(connection_id, file_path)`: Load documents from local filesystem
7. `load_vector_store_oci(connection_id, namespace, bucket, prefix, schema, table)`: Load documents from OCI Object Storage
8. `ask_ml_rag_vector_store(connection_id, question)`: RAG query on default vector store
9. `ask_ml_rag_innodb(connection_id, question, segment_col, embedding_col)`: RAG query restricted to InnoDB tables
10. `list_all_compartments()`: List OCI compartments
11. `object_storage_list_buckets(compartment_name | compartment_id)`: List buckets in a compartment
12. `object_storage_list_objects(namespace, bucket_name)`: List objects in a bucket

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

### 2. MySQL AI AI

```
"Generate a summary of error logs using MySQL AI ML"
"Ask ml_rag: Show me refund policy from the vector store"
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
