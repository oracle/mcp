# Oracle Database MCP Toolkit

## 1. Overview

Oracle Database MCP Toolkit is a Model Context Protocol (MCP) server that lets you:
* Define your own custom tools via a simple YAML configuration file.
* Use built-in tools:
  * Analyze Oracle JDBC thin client logs and RDBMS/SQLNet trace files.
  * **database-powered tools**, including **vector similarity search** and **SQL execution plan analysis**.
* Deploy locally or remotely - optionally as a container - with support for TLS and OAuth2

![MCP Toolkit Architecture Diagram](./images/MCPToolkitArchitectureDiagram.svg)

---

## 2. Custom Tool Framework — Extending the MCP Server
The MCP server can load both database connection definitions and custom tool definitions from a YAML configuration file.
This provides a flexible and declarative way to extend the server without modifying or rebuilding the codebase.

A YAML file may define:

* **datasources:** — Database configuration info:
  * `url`: This the JDBC URL used by the MCP server to connect to the database using the JDBC driver.
  * `user`: The username to use for the database connection.
  * `password`: The password to use for the database connection.
  * `host` (optional): The hostname or IP address of the database server.
  * `port` (optional): The port number on which the database server is listening.
  * `database` (optional): The Oracle service name of the database.

* One or more **tools** — The MCP tools:
  * `dataSource` (optional): Defines the data source to be used (defaults to system properties `db.url`, `db.user` and `db.password`).
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

* First, it checks whether a datasource was provided via system properties (db.url, db.user, db.password) (Higher priority).

* If no system property datasource is available, it falls back to the first datasource defined in the YAML file, if present.

3. If no datasource can be resolved and the tool requires one (e.g., SQL-based tools), the server reports a configuration error.

This design ensures that tools always have a predictable datasource while giving you flexibility to choose how connections are provided—either inline in YAML or externally via system properties and environment variables.

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
```
To enable YAML configuration, launch the server with:
```bash
java -DconfigFile=/path/to/config.yaml -jar <mcp-server>.jar
```

---

## 3. Built-in Tools

### 3.1. Oracle JDBC Log Analysis:

These tools operate on Oracle JDBC thin client logs:

- **`get-jdbc-stats`**: Extracts performance statistics including error counts, sent/received packets and byte counts.
- **`get-jdbc-queries`**: Retrieves all executed SQL queries with timestamps and execution times.
- **`get-jdbc-errors`**: Extracts all errors reported by both server and client.
- **`get-jdbc-connection-events`**: Shows connection open/close events.
- **`list-log-files-from-directory`**: List all visible files from a specified directory, which helps the user analyze multiple files with one prompt.
- **`jdbc-log-comparison`**: Compares two log files for performance metrics, errors, and network information.

### 3.2. RDBMS/SQLNet Trace Analysis:

These tools operate on RDBMS/SQLNet trace files:

- **`get-rdbms-errors`**: Extracts errors from RDBMS/SQLNet trace files.
- **`get-rdbms-packet-dumps`**: Extracts packet dumps for a specific connection ID.

### 3.3. Vector Similarity Search

* **`similarity_search`**: Perform semantic similarity search using Oracle’s vector features (`VECTOR_EMBEDDING`, `VECTOR_DISTANCE`).

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

### 3.4. SQL Execution Plan Analysis

* **`explain_plan`**: Generate Oracle execution plans and receive a pre-formatted LLM prompt for tuning and explanation.

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

---

## 4. Installation

### 4.1. Prerequisites
- **Java 17+** (JDK)
- **Credentials** with permissions for your intended operations
- **MCP client** (e.g., Claude Desktop) to call the tools

> The server uses UCP pooling out of the box (initial/min= 1).

### 4.2. Build the MCP server jar

```bash
mvn clean install
```

The created jar can be found in `target/oracle-db-mcp-toolkit-1.0.0.jar`.

### 4.3. Choose a transport mode (stdio vs HTTP)

`oracle-db-mcp-toolkit` supports two transport modes:

- **Stdio (default)** – the MCP client spawns the JVM process and talks over stdin/stdout
- **HTTP (streamable)** – the MCP server runs as an HTTP service, and clients connect via a URL

#### 4.3.1. Stdio mode (default)

This is the mode used by tools like Claude Desktop, where the client directly launches:

```jsonc
{
  "mcpServers": {
    "oracle-db-mcp-toolkit": {
      "command": "java",
      "args": [
        "-Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service",
        "-Ddb.user=your_user",
        "-Ddb.password=your_password"
        "-Dtools=get-jdbc-stats,get-jdbc-queries",
        "-Dojdbc.ext.dir=/path/to/extra-jars",
        "-jar",
        "<path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar"
      ]
    }
  }
}
```
If you don’t set `-Dtransport`, the server runs in stdio mode by default.

#### 4.3.2. HTTP mode

In HTTP mode, you run the server as a standalone HTTP service and point an MCP client to it.

Start the server:

```shell
java \
  -Dtransport=http \
  -Dhttp.port=45450 \
  -Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service \
  -Ddb.user=your_user \
  -Ddb.password=your_password \
  -Dtools=get-jdbc-stats,get-jdbc-queries \
  -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```
This exposes the MCP endpoint at: `http://localhost:45450/mcp`.

### 4.4. Enabling HTTPS (SSL/TLS)
To enable HTTPS (SSL/TLS), specify your certificate keystore path and password using the `-DcertificatePath` and `-DcertificatePassword` options.  
Only PKCS12 (`.p12` or `.pfx`) keystore files are supported.
You can set the HTTPS port with the `-Dhttps.port` option.
##### Example
```shell
-DcertificatePath=/path/to/your-certificate.p12 -DcertificatePassword=yourPassword -Dhttps.port=443
```
### 4.5. Using HTTP transport and Cline
Cline supports streamable HTTP directly. Example:

```json
{
  "mcpServers": {
    "oracle-db-mcp-toolkit": {
      "type": "streamableHttp",
      "url": "http://localhost:45450/mcp"
    }
  }
}
```

### 4.6. Using HTTP from Claude Desktop
Claude Desktop accepts HTTPS endpoints for remote MCP servers.
If your MCP server is only available over plain HTTP (e.g. http://localhost:45450/mcp),
you can use the `mcp-remote` workaround:

```json
{
  "mcpServers": {
    "oracle-db-mcp-toolkit": {
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

### 4.7. HTTP Authentication Configuration

#### 4.7.1. Generated Token (For Development and Testing)

To enable authentication for the HTTP server, you must set the `-DenableAuthentication` system property to `true` (default value is `false`).
If it's enabled (e.g. set to `true`) the MCP Server will check if there's an environment variable called `ORACLE_DB_TOOLKIT_AUTH_TOKEN` and its value will be used as a token.
If the environment variable is not found, then a random UUID token will be generated once per JVM session. The token would be logged at the `INFO` level.

When connecting to the MCP server, the token needs to be provided in the Authorization header of each request using the `Bearer ` prefix.

#### 4.7.2. OAuth2 Configuration

In order to configure an OAuth2 server, the `-DenableAuthentication` should be enabled alongside the following system properties:

- `-DauthServer`: The OAuth2 server URL which MUST provide the `/.well-known/oauth-authorization-server`. But if the authorization server only provides the `/.well-known/openid-configuration` you can enable `-DredirectOAuthToOpenID`.
- `-DredirectOAuthToOpenID`: (default: `false`) This system property is used to as a workaround to support OAuth servers that provide `/.well-known/openid-configuration` and not `/.well-known/oauth-authorization-server`.
  It works by creating an `/.well-known/oauth-authorization-server` endpoint on the MCP Server that redirects to the OAuth server's `/.well-known/openid-configuration` endpoint.
- `-DintrospectionEndpoint`: The OAuth2 server's introspection endpoint used to validate an access token (The OAuth2 introspection JSON response MUST contain the `active` field, e.g. `{...,"active": false,..}`).
- `-DclientId`: Client ID (e.g. `oracle-db-toolkit`)
- `-DclientSecret`: Client Secret (e.g. `Xj9mPqR2vL5kN8tY3hB7wF4uD6cA1eZ0`)
- `-DallowedHosts`: (default: `*`) The value of `Access-Control-Allow-Origin` header when requesting the `/.well-known/oauth-protected-resource` endpoint (and `/.well-known/oauth-authorization-server` if `-DredirectOAuthToOpenID` is set to `true`) of the MCP Server.

For more details regarding this MCP and OAuth, please see [MCP specification for authorization](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) (or a newer version if available).

##### Examples

###### Enabling Authentication with OAuth2

```bash
java \
    -Ddb.url=jdbc:oracle:thin:@host:1521/service \
    -Dtransport=http \
    -Dhttp.port=45450 \
    -DenableAuthentication=true \
    -DauthServer=http://localhost:8080/realms/mcp \
    -DintrospectionEndpoint=http://localhost:8080/realms/mcp/protocol/openid-connect/token/introspect \
    -DclientId=oracle-db-toolkit \
    -DclientSecret=Xj9mPqR2vL5kN8tY3hB7wF4uD6cA1eZ0 \
    -DallowedHosts=http://localhost:6274 \
    -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```

In the above example, we configured OAuth2 with a local KeyCloak server with a realm named `mcp`, and we only allowed a local [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector)
running at <http://localhost:6274> to retrieve the data from <http://localhost:45450/.well-known/oauth-protected-resource>


##### Enabling Authentication without OAuth2

_Note: This mode is used only for development and testing purposes._

```bash
java \
    -Ddb.url=jdbc:oracle:thin:@host:1521/service \
    -Dtransport=http \
    -Dhttp.port=45450 \
    -DenableAuthentication=true \
    -jar <path-to-jar>/oracle-db-mcp-toolkit-1.0.0.jar
```
After starting the server, a UUID token will be generated and logged at <code>INFO</code> level:

```log
Nov 25, 2025 3:30:46 PM com.oracle.database.jdbc.oauth.OAuth2Configuration <init>
INFO: Authentication is enabled
Nov 25, 2025 3:30:46 PM com.oracle.database.jdbc.oauth.OAuth2Configuration <init>
WARNING: OAuth2 is not configured
Nov 25, 2025 3:30:46 PM com.oracle.database.jdbc.oauth.TokenGenerator <init>
INFO: Authorization token generated (for testing and development use only): 0dd11948-37a3-470f-911e-4cd8b3d6f69c
Nov 25, 2025 3:30:46 PM com.oracle.database.jdbc.OracleDatabaseMCPToolkit startHttpServer
INFO: [oracle-db-mcp-toolkit] HTTP transport started on http://localhost:45450 (endpoint: http://localhost:45450/mcp)
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
        Comma-separated allow-list of tool names to enable.  
        Use <code>*</code> or <code>all</code> to enable everything.  
        If omitted, all tools are enabled by default.
      </td>
      <td><code>get-jdbc-stats,get-jdbc-queries</code></td>
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
      <td><code>https.port</code></td>
      <td>No</td>
      <td>
        TCP port used for SSL connection.
      </td>
      <td><code>45451</code></td>
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
      <td>Path to a YAML file defining <code>datasources</code> and <code>tools</code>.</td>
      <td>/opt/mcp/config.yaml</td>
    </tr>
    <tr>
      <td><code>enableAuthentication</code></td>
      <td>No</td>
      <td>Whether HTTP authentication is required or not (default <code>false</code>).<br/>
      All the subsequent OAuth2 system properties are ignored if this property is set to <code>false</code>.</td>
      <td><code>-DenableAuthentication=true</code></td>
    </tr>
    <tr>
      <td><code>authServer</code></td>
      <td>No</td>
      <td>Configure the OAuth2 server URL</td>
      <td><code>-DauthServer=http://localhost:8080/realms/master</code></td>
    </tr>
    <tr>
      <td><code>introspectionEndpoint</code></td>
      <td>No</td>
      <td>The OAuth2 server endpoint used to validate and obtain metadata about an access token.</td>
      <td><code>-DintrospectionEndpoint=http://localhost:8080/realms/mcp/protocol/openid-connect/token/introspect</code></td>
    </tr>
    <tr>
      <td><code>clientId</code></td>
      <td>No</td>
      <td>The client identifier for registering with the configured OAuth2 server.</td>
      <td><code>-DclientId=oracle-db-toolkit</code></td>
    </tr>
    <tr>
      <td><code>clientSecret</code></td>
      <td>No</td>
      <td>The confidential key used to authenticate the client to the configured authorization server during the OAuth2 flow.</td>
      <td><code>-DclientSecret=Xj9mPqR2vL5kN8tY3hB7wF4uD6cA1eZ0</code></td>
    </tr>
    <tr>
      <td><code>allowedHosts</code></td>
      <td>No</td>
      <td>The <code>Access-Control-Allow-Origin</code> header value when making a request to the MCP Server's <code>/.well-known/oauth-protected-resource</code> endpoint (default <code>*</code> e.g. all hosts are allowed).</td>
      <td><code>-DallowedHosts=http://localhost:6274</code></td>
    </tr>
    <tr>
      <td><code>redirectOAuthToOpenID</code></td>
      <td>No</td>
      <td>System property that redirects MCP Server's <code>/.well-known/oauth-authorization-server</code> endpoint to the OAuth server's <code>/.well-known/openid-configuration</code> as a workaround for servers lacking the former (default value is <code>false</code>. If OAuth is not properly configured, then this system property is ignored).</td>
      <td><code>-DredirectOAuthToOpenID=false</code></td>
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
    -Dhttp.port=45450 \
    -Dhttps.port=45451 \
    -DcertificatePath=[path/to/certificate] \
    -DcertificatePassword=[password] \
    -Dtools=get-jdbc-stats,get-jdbc-queries \
    -Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service \
    -Ddb.user=your_user \
    -Ddb.password=your_password" \
  oracle-db-mcp-toolkit:1.0.0
```
This exposes the MCP endpoint at: http://[your-ip-address]:45450/mcp or https://[your-ip-address]:45451/mcp

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
    -Dhttp.port=45450 \
    -Dhttps.port=45451 \
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
In this configuration, Claude Desktop runs `podman run --rm -i ... and connects to the server via stdio:

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
        "JAVA_TOOL_OPTIONS=-Dtools=get-jdbc-stats,get-jdbc-queries -Ddb.url=jdbc:oracle:thin:@your-host:1521/your-service -Ddb.user=your_user -Ddb.password=your_password -Dojdbc.ext.dir=/ext -DconfigFile=/config/config.yaml",
        "oracle-db-mcp-toolkit:1.0.0"
      ]
    }
  }
}
```
