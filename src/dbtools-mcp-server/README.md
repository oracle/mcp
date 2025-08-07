# DBTools MCP Server (dbtools-mcp-server.py)

A Python-based MCP (Model Context Protocol) server that provides a suite of tools for managing and interacting with Oracle Cloud Infrastructure (OCI) database resources. This MCP server is not intented to be used in production environment but as a proof of concept for exploring models using MCP Servers.

## Overview

dbtools-mcp-server.py is a FastMCP-based server that provides various tools for managing OCI database resources, including autonomous databases, database tools connections, and SQL execution capabilities.

## Features

- **Compartment Management**
  - List all compartments
  - Get compartment by name

- **Database Operations**
  - List autonomous databases in specific compartments
  - List all databases across the tenancy
  - Execute SQL scripts on database connections
  - Get table information for Oracle and MySQL databases
  - List tables in a database

- **Database Tools Connection Management**
  - List all database connections
  - Get connection details by name
  - Execute SQL through database tools connections

- **Report Management**
  - Bootstrap report definitions table
  - Create, execute, get, delete, and list reports
  - Find matching reports using vector similarity search
  - Create and populate vector columns for RAG integration

- **Additional Features**
  - MySQL HeatWave chat integration

## Prerequisites

- Python 3.x
- fastmcp (installed automatically via requirements.txt)
- OCI SDK (installed via requirements.txt)
- Valid OCI configuration file with credentials

## Installation

1. Clone this repository.
2. Install required dependencies using pip:
   ```
   pip install -r requirements.txt
   ```
   This will install `oci`, `requests`, `fastmcp`, and all other dependencies.
3. Set up your OCI config file at ~/.oci/config

## OCI Configuration

The server requires a valid OCI config file with proper credentials. 
The default location is ~/.oci/config. For instructions on setting up this file, 
see the [OCI SDK documentation](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm).

## Required Python Packages

- oci
- requests
- fastmcp

## Supported Database Types

The get_table_info tool supports the following database types:
- Oracle Database
- MySQL (including HeatWave)

## MCP Server Configuration
Installation is dependent on the MCP Client being used, it usually consists of adding the MCP Server invocation in a json config file, for example with Claude UI on windows it looks like this:
```
{
  "mcpServers": {
    "dbtools": {
      "command": "C:\\Python\\python.exe",
      "args": [
        "C:\\Users\\user1\\mcp\\src\\dbtools-mcp-server\\dbtools-mcp-server.py"
      ]
    }
  }
}
```



Example with TENANCY_ID_OVERRIDE:
```
{
  "mcpServers": {
    "dbtools": {
      "command": "C:\\Python\\python.exe",
      "args": [
        "C:\\Users\\user1\\dbtools-mcp-server\\dbtools-mcp-server.py"
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
- `MODEL_NAME`: Name of the embedding model (default: "MINILM_L12_V2"). Note: May need to be prefixed with "ADMIN." depending on the database user (e.g., "ADMIN.MINILM_L12_V2").
- `MODEL_EMBEDDING_DIMENSION`: Dimension of the vector embeddings (default: 384)

## Usage

The server runs using stdio transport and can be started by running:

```
python dbtools-mcp-server.py
```

## API Tools

1. `list_all_compartments()`: Lists all compartments in the tenancy
2. `get_compartment_by_name_tool(name)`: Retrieves compartment details by name
3. `list_autonomous_databases(compartment_name)`: Lists databases in a specific compartment
4. `list_all_databases()`: Lists all databases across the tenancy
5. `list_dbtools_connection_tool(compartment_name)`: Lists database tools connections in a compartment
6. `list_all_connections()`: Lists all database connections across all compartments
7. `get_dbtools_connection_by_name_tool(display_name)`: Gets connection details by name
8. `execute_sql_tool(dbtools_connection_display_name, sql_script)`: Executes SQL on a database connection
9. `get_table_info(dbtools_connection_display_name, table_name)`: Retrieves table information
10. `list_tables(dbtools_connection_display_name)`: Lists all tables in a database connection
11. `ask_heatwave_chat_tool(dbtools_connection_display_name, question)`: Interacts with MySQL HeatWave chat
12. `bootstrap_reports(dbtools_connection_display_name)`: Ensures report_definitions table exists
13. `create_report(dbtools_connection_display_name, name, sql_query, description=None, bind_parameters=None)`: Creates a new report definition
14. `execute_report(dbtools_connection_display_name, report_name, bind_values=None)`: Executes a report with optional bind values
15. `get_report(dbtools_connection_display_name, report_name)`: Retrieves a report definition by name
16. `delete_report(dbtools_connection_display_name, report_name)`: Deletes a report definition by name
17. `list_reports(dbtools_connection_display_name)`: Lists all reports for a connection
18. `find_matching_reports(dbtools_connection_display_name, search_text, limit=5)`: Finds similar reports using vector similarity search
19. `ragify_column(dbtools_connection_display_name, table_name, column_names, vector_column_name)`: Creates and populates a vector column for RAG integration

## Security

The server uses OCI's built-in authentication and authorization mechanisms, including:
- OCI config file-based authentication
- Signer-based authentication for specific endpoints

## Example Prompts

Here are example prompts you can use to interact with the MCP server, note that depending on the model being used you might need to be more specific, for example: "list all employees using myConnection1 dbtools connection".

### 1. Creating and Managing Tables

```
"Create an employee table in the HR database with columns for ID, name, email, and salary"
"Show me all tables in the finance database"
"Add a department column to the employee table"
"Delete the test_table from my database"
```

### 2. Querying Data

```
"What's the average salary of employees by department?"
"Show me all employees hired in the last 6 months"
"List the top 5 departments by headcount"
"Get all projects with status 'In Progress'"
```

### 3. Database Administration

```
"List all databases in my tenancy"
"Show me the databases in the production compartment"
"Get all database connections"
"What tables exist in the marketing database?"
```

### 4. Using HeatWave Chat

```
"Ask HeatWave: Which products have the highest profit margin?"
"Ask HeatWave: Summarize our sales performance by region"
"Ask HeatWave: What's the trend in customer acquisitions?"
```

### 5. Compartment Management

```
"Show me all compartments"
"List databases in the development compartment"
"Get details of the production compartment"
```

Note: Replace placeholder names (like "HR database", "production compartment") with your actual database tools connection and compartment names when using these prompts.
