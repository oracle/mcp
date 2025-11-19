# Oracle JDBC Log Analyzer MCP Server

## Overview

The `ojdbc-log-analyzer-mcp-server` provides 8 tools for analyzing Oracle JDBC thin client logs and RDBMS/SQLNet trace files:

### Oracle JDBC Log Analysis:

- **`get-stats`**: Extracts performance statistics including error counts, sent/received packets and byte counts.
- **`get-queries`**: Retrieves all executed SQL queries with timestamps and execution times.
- **`get-errors`**: Extracts all errors reported by both server and client.
- **`get-connections-events`**: Shows connection open/close events.
- **`get-log-files-from-directory`**: Lists all Oracle JDBC log files in a directory.
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
