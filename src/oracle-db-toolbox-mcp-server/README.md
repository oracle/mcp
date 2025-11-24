# Oracle DB Toolbox MCP Server

## Overview

`oracle-db-toolbox-mcp-server` is a Model Context Protocol (MCP) server that lets you: 
  * Use 8 built-in tools to analyze Oracle JDBC thin client logs and RDBMS/SQLNet trace files.
  * Define your own custom tools via a simple YAML configuration file (optional).

## Built-in Tools

### Oracle JDBC Log Analysis:

These tools operate on Oracle JDBC thin client logs:

- **`get-stats`**: Extracts performance statistics including error counts, sent/received packets and byte counts.
- **`get-queries`**: Retrieves all executed SQL queries with timestamps and execution times.
- **`get-errors`**: Extracts all errors reported by both server and client.
- **`get-connections-events`**: Shows connection open/close events.
- **`list-log-files-from-directory`**: List all visible files from a specified directory, which helps the user analyze multiple files with one prompt.
- **`log-comparison`**: Compares two log files for performance metrics, errors, and network information.

### RDBMS/SQLNet Trace Analysis:

These tools operate on RDBMS/SQLNet trace files:

- **`get-rdbms-errors`**: Extracts errors from RDBMS/SQLNet trace files.
- **`get-packet-dumps`**: Extracts packet dumps for a specific connection ID.

## Prerequisites

- **Java 17+** (JDK)
- **Credentials** with permissions for your intended operations
- **MCP client** (e.g., Claude Desktop) to call the tools

### Build the MCP server jar

```bash
mvn clean install
```

The created jar can be found in `target/oracle-db-toolbox-mcp-server-1.0.0.jar`.

### Transport modes (stdio vs HTTP)

`oracle-db-toolbox-mcp-server` supports two transport modes:

- **Stdio (default)** – the MCP client spawns the JVM process and talks over stdin/stdout
- **HTTP (streamable)** – the MCP server runs as an HTTP service, and clients connect via a URL

#### Stdio mode (default)

This is the mode used by tools like Claude Desktop, where the client directly launches:

```jsonc
{
  "mcpServers": {
    "oracle-db-toolbox-mcp-server": {
      "command": "java",
      "args": [
        "-Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service",
        "-Ddb.user=your_user",
        "-Ddb.password=your_password"
        "-Dtools=get-stats,get-queries",
        "-Dojdbc.ext.dir=/path/to/extra-jars",
        "-jar",
        "<path-to-jar>/oracle-db-toolbox-mcp-server-1.0.0.jar"
      ]
    }
  }
}
```
If you don’t set `-Dtransport`, the server runs in stdio mode by default.

#### HTTP mode

In HTTP mode, you run the server as a standalone HTTP service and point an MCP client to it.

Start the server:

```shell
java \
  -Dtransport=http \
  -Dhttp.port=45450 \
  -Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service \
  -Ddb.user=your_user \
  -Ddb.password=your_password \
  -Dtools=get-stats,get-queries \
  -jar <path-to-jar>/oracle-db-toolbox-mcp-server-1.0.0.jar
```
This exposes the MCP endpoint at: `http://localhost:45450/mcp`.

### Using HTTP from Cline
Cline supports streamable HTTP directly. Example:

```json
{
  "mcpServers": {
    "oracle-db-toolbox-mcp-server": {
      "type": "streamableHttp",
      "url": "http://localhost:45450/mcp"
    }
  }
}
```

### Using HTTP from Claude Desktop
Claude Desktop accepts HTTPS endpoints for remote MCP servers.
If your MCP server is only available over plain HTTP (e.g. http://localhost:45450/mcp),
you can use the `mcp-remote` workaround:

```json
{
  "mcpServers": {
    "oracle-db-toolbox-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:45450/mcp"
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

### Supported System Properties
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
        Comma-separated allow-list of tool names to enable.  
        Use <code>*</code> or <code>all</code> to enable everything.  
        If omitted, all tools are enabled by default.
      </td>
      <td><code>get-stats,get-queries</code></td>
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
      <td><code>transport</code></td>
      <td>No</td>
      <td>
        Transport mode for the MCP server. Supported values:
        <code>stdio</code> or <code>http</code>. If omitted, <code>stdio</code> is used.
      </td>
      <td><code>http</code></td>
    </tr>
    <tr>
      <td><code>http.port</code></td>
      <td>No</td>
      <td>
        TCP port used when <code>-Dtransport=http</code> is set.
      </td>
      <td><code>45450</code></td>
    </tr>
    <tr>
      <td><code>configFile</code></td>
      <td>No</td>
      <td>Path to a YAML file defining `sources` and `tools`.</td>
      <td>/opt/mcp/config.yaml</td>
    </tr>
  </tbody>
</table>

<i>* Note:</i> If you don’t set tools, all tools are available by default.

<i>* Conditional requirement:</i> <code>db.url</code> is required **only if** any database tool is enabled via <code>-Dtools</code>.

If you enable **only** the Log Analyzer tools, you can omit <code>db.url</code>.

<i>* Note:</i> If you’re using token-based authentication (e.g., IAM tokens) or a centralized configuration provided via the JARs you place in `-Dojdbc.ext.dir`,
you can omit `db.user` and `db.password`. The driver will pick up credentials and security settings from those extensions.
