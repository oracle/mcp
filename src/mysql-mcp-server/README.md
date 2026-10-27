# MySQL MCP Server (mysql_mcp_server.py)

A Python-based MCP (Model Context Protocol) server that provides a suite of tools for managing and interacting with MySQL AI and MySQL HeatWave database resources. This MCP server is not intended for production use but as a proof of concept for exploring models using MCP Servers.

## Overview

`mysql_mcp_server.py` is a FastMCP-based server that provides tools for managing MySQL connections, executing SQL, using MySQL AI or MySQL HeatWave ML/GenAI features, and working with OCI Object Storage. MySQL MCP Server is the recommended server to get started with MySQL HeatWave or MySQL AI and the only server in this repo that supports MySQL AI.

## Features

- **Database Connection Management**
  - Load connection configs from JSON with literal, environment, or OS keyring passwords
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
- Valid database connection file. Set `MYSQL_MCP_CONFIG` to its path, or create `local_config.json` in the package root. Relative paths in `MYSQL_MCP_CONFIG` are resolved from the server process working directory; use an absolute path for MCP clients.
- Valid OCI configuration file (`~/.oci/config`) or environment variables


## OCI Configuration

The server requires a valid OCI config file with proper credentials.
The default location is ~/.oci/config. For instructions on setting up this file,
see the [OCI SDK documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm).


## Supported Database Modes

- `MySQL AI`
- `HeatWave`

## MCP client configuration (recommended)

Most users should configure their MCP client to launch the server, rather than starting it manually.

Add a stanza like this to your MCP client config (often called `mcp.json`; example shown is **stdio**):

```json
{
  "mcpServers": {
    "mysql": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.mysql-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "MYSQL_MCP_CONFIG": "/path/to/your/config.json"
      }
    }
  }
}
```

Example with `TENANCY_ID_OVERRIDE`:

```json
{
  "mcpServers": {
    "mysql": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.mysql-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT",
        "MYSQL_MCP_CONFIG": "/path/to/your/config.json",
        "TENANCY_ID_OVERRIDE": "ocid1.tenancy.oc1..deadbeef"
      }
    }
  }
}
```

## Environment Variables

The server supports the following environment variables:

- `MYSQL_MCP_CONFIG`: Path to the database connection JSON file
- Variables named by `password_env`: Passwords inherited by the server process
- `PROFILE_NAME`: OCI configuration profile name (default: "DEFAULT")
- `TENANCY_ID_OVERRIDE`: Overrides the tenancy ID from the config file

## Connection configuration

At startup, the server loads the file named by `MYSQL_MCP_CONFIG`, or `local_config.json` in the package root when that variable is unset. It does not search for other files or fall back when the selected file is missing.

Each `server_infos` entry requires `host`, `user`, `database`, `port`, and exactly one password source. Other connection keys are rejected.

| Password source | Example field | Behavior |
| --- | --- | --- |
| Literal password | `"password": "example-password"` | Uses the string in the connection file. Existing configurations remain supported without deprecation, including empty literal passwords. |
| Environment reference | `"password_env": "MYSQL_APP_PASSWORD"` | Reads a non-empty password from the named environment variable in the server process. The reference must match `[A-Za-z_][A-Za-z0-9_]*`. |
| OS keyring reference | `"password_keyring": {"service": "mysql-mcp-app", "username": "appuser"}` | Reads a non-empty password from the selected OS credential store. Both reference values must be non-empty strings. |

For example, a connection file with an environment reference contains no password value:

```json
{
  "server_infos": {
    "app": {
      "host": "localhost",
      "user": "appuser",
      "password_env": "MYSQL_APP_PASSWORD",
      "database": "appdb",
      "port": 3306
    }
  }
}
```

Provision `MYSQL_APP_PASSWORD` through the runtime environment or a secret manager before the MCP client launches the server. Environment references do not encrypt secrets at rest. Do not move the password into an MCP client's `env` JSON, a checked-in `.env` file, or a shell command saved in history. The MCP client configuration above needs only the connection file path; the server must inherit the password variable from its launcher.

### OS keyring setup

Provision the credential on the MCP host, under the account that runs the server, using the same Python environment and selected backend as the server. From this package directory, enter the password at the prompt:

```sh
uv run python -m keyring set mysql-mcp-app appuser
```

Replace `password_env` in the example connection with:

```json
"password_keyring": {
  "service": "mysql-mcp-app",
  "username": "appuser"
}
```

The keyring username is an explicit lookup key; it is not inferred from the database `user` field. The server supports macOS Keychain, Windows Credential Locker, Secret Service (including libsecret), and KWallet. It rejects chained, null, plaintext, and third-party backends. If automatic selection chooses a chain, configure the intended supported backend explicitly, for example with `PYTHON_KEYRING_BACKEND=keyring.backends.macOS.Keyring` on macOS. Use the same setting when provisioning and launching the server.

Headless hosts need a working, unlocked credential store for the runtime account. On Linux, install and start the appropriate secret-store daemon and give the server access to the same D-Bus session. Installing the Python `keyring` package alone does not create or unlock that store. Follow the [keyring headless Linux setup guide](https://keyring.readthedocs.io/en/stable/#using-keyring-on-headless-linux-systems) for Secret Service prerequisites. Service accounts and remote MCP hosts do not automatically share the interactive user's credential store.

### Migration and failures

Existing literal `password` entries need no changes. To migrate a connection, provision its environment variable or keyring entry, then replace `password` with `password_env` or `password_keyring`. Never retain both fields. [example_config.json](example_config.json) shows all three alternatives with synthetic values.

Passwords are resolved once during startup, and only connector-supported settings plus the resolved `password` reach MySQL Connector/Python. Restart the MCP server after rotating a password or changing its source. Conflicting sources, unset or empty environment values, missing keyring entries, and unavailable, locked, or unsupported stores produce configuration errors without falling back to another source. The server remains available over STDIO; `list_all_connections` reports the configuration error until the configuration is fixed and the server restarts. Password values are not included in configuration errors or connection summaries.

### Optional SSH tunnel

The optional `bastion` block keeps the existing SSH tunnel settings. Required keys are `bastion_host`, `bastion_username`, `private_key_path`, and `db_host`. Optional keys default to `bastion_port: 22`, `db_port: 3306`, `local_bind_host: "127.0.0.1"`, and `local_bind_port: 3306`. Other bastion keys are rejected.

For example, a connection through an existing tunnel can use:

```json
{
  "server_infos": {
    "remote_via_bastion": {
      "host": "127.0.0.1",
      "user": "dbuser",
      "password_env": "MYSQL_REMOTE_PASSWORD",
      "database": "appdb",
      "port": 3306
    }
  },
  "bastion": {
    "bastion_host": "bastion.example.com",
    "bastion_username": "ubuntu",
    "private_key_path": "<absolute-path-to-private-key>",
    "db_host": "db.example.com",
    "db_port": 3306
  }
}
```

## Usage

The server runs using stdio transport and can be started by running:

```bash
uv run oracle.mysql_mcp_server
```

## Development tests

MySQL is excluded from Moon. From this package directory, install the locked test dependencies and run the offline suite:

```sh
uv sync --locked --group dev
uv run --locked pytest
```

The default pytest configuration measures branch coverage across the production package and fails below 90%. Offline tests use synthetic configuration and mocked external services; they do not read the user's database or OCI configuration.

Live database and OCI tests are skipped by default. Run them only against disposable resources by explicitly setting `MYSQL_MCP_RUN_LIVE_TESTS=1` and `MYSQL_MCP_CONFIG` to a dedicated test configuration. These tests can create and drop database objects, ingest files, and invoke ML and object-storage operations. Real credential-store and authenticated database checks are separate from the mocked offline suite.

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
- MySQL passwords can use literal JSON values, environment references, or supported OS credential stores. Protect connection files containing literal passwords with appropriate file permissions.

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
