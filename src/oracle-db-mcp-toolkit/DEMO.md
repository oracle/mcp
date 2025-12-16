# Oracle Database MCP Toolkit Demo

## 1.Overview

To test the capabilities of the Oracle Database MCP Toolkit, a demo instance of the MCP server is made available via
<https://mcptoolkit.orcl.dev:45453/mcp> with the following tools activated:

JDBC log analysis tools:

- **`get-jdbc-stats`**: Extracts performance statistics including error counts, sent/received packets and byte counts.
- **`get-jdbc-queries`**: Retrieves all executed SQL queries with timestamps and execution times.
- **`get-jdbc-errors`**: Extracts all errors reported by both server and client.
- **`get-jdbc-connections-events`**: Shows connection open/close events.
- **`list-log-files-from-directory`**: List all visible files from a specified directory, which helps the user analyze multiple files with one prompt.
- **`jdbc-log-comparison`**: Compares two log files for performance metrics, errors, and network information.

RDBMS/SQLNet trace analysis Tools:

- **`get-rdbms-errors`**: Extracts errors from RDBMS/SQLNet trace files.
- **`get-rdbms-packet-dumps`**: Extracts packet dumps for a specific connection ID.

Custom tools (created using YAML configuration file):

- **`hotels-by-name`**: Return the details of a hotel given its name. The details include the capacity, rating and address.
This tool is created using the following YAML configuration file: 

```yaml
dataSources:
  dev-db:
    url: ${db_url}
    user: ${user}
    password: ${password}

tools:
  hotels-by-name:
    dataSource: dev-db
    description: Return the details of a hotel given its name. The details include the capacity, rating and address.
    parameters:
      - name: name
        type: string
        description: Hotel name to search for.
    statement: SELECT * FROM hotels WHERE name LIKE '%' || :name || '%'
```

Where `${db_url}`, `${user}` and `${password}`are environment variables.

## 2. Requirements

An MCP Client that support Streamable HTTP transport mode is needed, such as MCP Inspector, Cline or Claude Desktop.

**Note**: If you're using Claude Desktop, you also need [mcp-remote](https://www.npmjs.com/package/mcp-remote).

## 3. Setup

The deployed instance uses `streamableHttp` transport protocol and a runtime generated `Authorization` token.

Use the following token `3e297077-f01e-4045-a9d0-2a71e97e6dfa`.

### MCP Inspector

To use MCP Inspector as an MCP client, specify `streamableHttp`as transport type,  `https://mcptoolkit.orcl.dev:45453/mcp` as the URL, _Via Proxy_ as Connection Type,
for Authentication, add a `Authorization` custom header with `Bearer 3e297077-f01e-4045-a9d0-2a71e97e6dfa` as value.
the final configuration should look as shown below:

<img src="https://objectstorage.eu-amsterdam-1.oraclecloud.com/n/axumz0amlzwj/b/oracle-db-toolkit-mcp-demo/o/mcp-Inspector-1.png" height="500px" width="auto" alt="MCP Inspector config screenshot">

After checking the configuration, click the *Connect* button, and the available tools will be shown in the main section:

<img src="https://objectstorage.eu-amsterdam-1.oraclecloud.com/n/axumz0amlzwj/b/oracle-db-toolkit-mcp-demo/o/mcp-Inspector-2.png" height="500px" width="auto" alt="MCP Inspector tools screenshot">

_Note :_ The filePath should be provided as a URL.

### Cline

Add or merge this configuration into `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "Oracle Database MCP Toolkit (Demo)": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "type": "streamableHttp",
      "url": "https://mcptoolkit.orcl.dev:45453/mcp",
      "headers": {
        "Authorization": "Bearer 3e297077-f01e-4045-a9d0-2a71e97e6dfa"
      }
    }
  }
}
```

After saving the configuration file, the available tools will be shown in the *Configure* Tab of *MCP Servers* settings:

<img src="https://objectstorage.eu-amsterdam-1.oraclecloud.com/n/axumz0amlzwj/b/oracle-db-toolkit-mcp-demo/o/cline-1.png" height="500px" width="auto" alt="Cline tools screenshot">

Here's an example of a prompt that trigger the `get-jdbc-queries` tool:

<img src="https://objectstorage.eu-amsterdam-1.oraclecloud.com/n/axumz0amlzwj/b/oracle-db-toolkit-mcp-demo/o/cline-2.png" height="500px" width="auto" alt="Cline prompt example screenshot">

### Claude Desktop

In order to connect the MCP server and also to provide the `Authorization` token to Claude Desktop, The [mcp-remote](https://www.npmjs.com/package/mcp-remote) is used to properly configure.
Below is an example of `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "Oracle Database MCP Toolkit (Demo)": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://mcptoolkit.orcl.dev:45453/mcp",
        "--header",
        "Authorization:${DEMO_TOKEN}"
      ],
      "env": {
        "DEMO_TOKEN": "Bearer 3e297077-f01e-4045-a9d0-2a71e97e6dfa"
      }
    }
  }
}
```

Upon saving the configuration file an opening Claude Desktop, you'll be to see the tools in the *Connectors* section:

<img src="https://objectstorage.eu-amsterdam-1.oraclecloud.com/n/axumz0amlzwj/b/oracle-db-toolkit-mcp-demo/o/claude-1.png" height="500px" width="auto" alt="Claude Desktop tools screenshot">

Here's the result of the same prompt used to know what queries were executed :

<img src="https://objectstorage.eu-amsterdam-1.oraclecloud.com/n/axumz0amlzwj/b/oracle-db-toolkit-mcp-demo/o/claude-2.png" height="500px" width="auto" alt="Claude Desktop prompt example screenshot">