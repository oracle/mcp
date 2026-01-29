# Oracle Database MCP Toolkit Demo

## 1.Overview

This document demonstrates how to try the Oracle Database MCP Toolkit by running your own instance of the MCP server.

The demo focuses on the following tools:

JDBC log analysis tools:

- **`get-jdbc-stats`**: Extracts performance statistics including error counts, sent/received packets and byte counts.
- **`get-jdbc-queries`**: Retrieves all executed SQL queries with timestamps and execution times.
- **`get-jdbc-errors`**: Extracts all errors reported by both server and client.
- **`jdbc-log-comparison`**: Compares two log files for performance metrics, errors, and network information.

RDBMS/SQLNet trace analysis tools:

- **`get-rdbms-errors`**: Extracts errors from RDBMS/SQLNet trace files.
- **`get-rdbms-packet-dumps`**: Extracts packet dumps for a specific connection ID.

Custom tools (via YAML configuration):

- **`hotels-by-name`**: Returns the details of a hotel given its name. The details include the capacity, rating and address.
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
    description: Returns the details of a hotel given its name. The details include the capacity, rating and address.
    parameters:
      - name: name
        type: string
        description: Hotel name to search for.
    statement: SELECT * FROM hotels WHERE name LIKE '%' || :name || '%'
```

Where `${db_url}`, `${user}` and `${password}` are environment variables.

## 2. Requirements

- An MCP client that supports the Streamable HTTP transport (e.g., MCP Inspector, Cline, Claude Desktop). Stdio is also
  supported by the server; see the README for details.
- A running MCP Toolkit server.

**Note**: If you're using Claude Desktop, you also need [mcp-remote](https://www.npmjs.com/package/mcp-remote).

## 3. Start a local MCP Toolkit server (HTTP example)

You can run the server over HTTPS with authentication enabled. The token can be supplied via the
`ORACLE_DB_TOOLKIT_AUTH_TOKEN` environment variable or, if not set, it will be generated and printed to the logs (see README §4.4).

Example:

```bash
java \
  -Dtransport=http \
  -Dhttps.port=45450 \
  -DcertificatePath=/path/to/your-certificate.p12 \
  -DcertificatePassword=yourPassword \
  -DenableAuthentication=true \
  -Dtools=get-jdbc-stats,get-jdbc-queries,get-jdbc-errors,jdbc-log-comparison,get-rdbms-errors,get-rdbms-packet-dumps \
  -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```

This exposes the MCP endpoint at: `https://localhost:45450/mcp`.

When connecting from a client, include the token in the `Authorization` header as `Bearer YOUR_TOKEN`.

For additional deployment modes (including stdio and Docker/Podman) and OAuth2 configuration, see the project README.

### Run in a container (Podman)

The repository contains a Dockerfile you can use to build and run the server in a container.

1) Build the image (from the repo root):

```bash
podman build -t oracle-db-mcp-toolkit:1.0.0 .
```

2) Run the container with HTTPS and token auth (adjust paths and secrets for your environment):

```bash
podman run --name with_token_auth -d \
  -p 45453:45453 \
  -v /home/opc/jetty.p12:/app/jetty.p12:ro,z \
  -v /home/opc/custom_tools/custom_tools.yaml:/app/custom_tools.yaml:ro,z \
  -e JAVA_TOOL_OPTIONS="-Dtransport=http -Dhttps.port=45453 -DcertificatePath=/app/jetty.p12 -DcertificatePassword=CERTIF_PASSWORD -DenableAuthentication=true -Dtools=mcp-admin,log-analyzer,rag -DconfigFile=/app/custom_tools.yaml" \
  -e ORACLE_DB_TOOLKIT_AUTH_TOKEN="3e297077-f01e-4045-a9d0-2a71e97e6dfa" \
  oracle-db-mcp-toolkit:1.0.0
```

After the container starts, the MCP endpoint is available at:

  https://localhost:45453/mcp

Notes:

- The :z volume flag is commonly required on SELinux-enabled hosts (Podman). It is harmless elsewhere.
- For Docker, you can use the same command but omit :z on volume mounts.

## 4. Connect your MCP client

### MCP Inspector

Configure MCP Inspector with:

- Transport: `streamableHttp`
- URL: `https://localhost:45450/mcp`
- Connection Type: Via Proxy
- Authentication: Add a custom header `Authorization: Bearer YOUR_TOKEN`

After saving, click Connect and the available tools will be listed.

_Note:_ For log analysis tools, provide `filePath` values as URLs where applicable.

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
      "url": "https://localhost:45450/mcp",
      "headers": { "Authorization": "Bearer YOUR_TOKEN" }
    }
  }
}
```

After saving, the tools will appear in the MCP Servers settings. You can then invoke tools like `get-jdbc-queries` by prompt.

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
        "https://localhost:45450/mcp",
        "--header",
        "Authorization:${DEMO_TOKEN}"
      ],
      "env": { "DEMO_TOKEN": "Bearer YOUR_TOKEN" }
    }
  }
}
```

Upon saving, open Claude Desktop and you should see the tools in the Connectors section.