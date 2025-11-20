# Oracle DB Toolbox MCP Server

## Overview

The `oracle-db-toolbox-mcp-server` provides the capability to build your own custom tools along with 8 tools for analyzing Oracle JDBC thin client logs and RDBMS/SQLNet trace files:

### Oracle JDBC Log Analysis:

- **`get-stats`**: Extracts performance statistics including error counts, sent/received packets and byte counts.
- **`get-queries`**: Retrieves all executed SQL queries with timestamps and execution times.
- **`get-errors`**: Extracts all errors reported by both server and client.
- **`get-connections-events`**: Shows connection open/close events.
- **`list-log-files-from-directory`**: List all visible files from a specified directory, which helps the user analyze multiple files with one prompt.
- **`log-comparison`**: Compares two log files for performance metrics, errors, and network information.

### RDBMS/SQLNet Trace Analysis:

- **`get-rdbms-errors`**: Extracts errors from RDBMS/SQLNet trace files.
- **`get-packet-dumps`**: Extracts packet dumps for a specific connection ID.

## Requirements

Requirements to build the project:

- JDK 17 (or higher)
- Maven 3.9 (or higher)

## How to use

### 1- Build the MCP server jar

```bash
mvn clean install
```

The created jar can be found in `target/ojdbc-log-analyzer-mcp-server-1.0.0.jar`.

### 2- Configuration

Add (or merge) the following JSON to the configuration file to an MCP client (such as Claude or Cline):

```json
{
  "mcpServers": {
    "ojdbc-log-analyzer-mcp-server": {
      "type": "stdio",
      "command": "java",
      "args": [
        "-jar",
        "<path-to-project>/src/ojdbc-log-analyzer-mcp-server/target/ojdbc-log-analyzer-mcp-server-1.0.0.jar"
      ]
    }
  }
}
```

## YAML Configuration Support

The MCP server supports loading database connection and tool definitions from a YAML configuration file.

**Example `config.yaml`:**
```yaml
sources:
  prod-db:
    url: jdbc:oracle:thin:@prod-host:1521/ORCLPDB1
    user: ADMIN
    password: mypassword

tools:
  hotels-by-name:
    source: prod-db
    parameters:
      - name: name
        type: string
        description: Hotel name to search for.
    statement: SELECT * FROM hotels WHERE name LIKE '%' || :name || '%'
```
To enable YAML configuration, launch the server with:
```bash
java -DconfigFile=/path/to/config.yaml -jar <mcp-server>.jar
```