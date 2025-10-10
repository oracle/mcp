# Oracle MCP Server Repository

Repository containing reference implementations of MCP (Model Context Protocol) servers for managing and interacting with Oracle products. Each MCP server under `src/` may be written in a different programming language, demonstrating MCP’s language-agnostic approach.

## What is MCP?

The Model Context Protocol (MCP) enables standardized, language-agnostic machine-to-machine workflows across data, models, and cloud resources. MCP servers implement specific tool suites, exposing them to MCP-compatible clients.

## Project Scope

- **Proof-of-concept/Reference implementations:**  
  This repository is not intended for production use; servers are provided as reference and for exploration, prototyping, and learning.

- **Polyglot architecture:**  
  Each `src/<server-name>/` directory represents a distinct MCP server, and these may use Python, Node.js, Java, or other languages.

## Prerequisites

- Supported OS: Linux, macOS, or Windows (varies by server; check server README)
- Git (for cloning this repository)
- Internet access (for downloading dependencies)
- *Cloud access*: Some servers require Oracle Cloud Infrastructure (OCI) credentials and configuration ([OCI docs](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm))

**Note:**  
Each MCP server has its own specific requirements (e.g., language runtime version, libraries).  
Always see the respective `src/<server>/README.md` for detailed setup instructions.

## Quick Start

1. **Clone this repository:**
    ```sh
    git clone https://github.com/oracle/mcp.git
    cd mcp
    ```

2. **List available MCP servers:**
    ```sh
    ls src/
    ```

3. **Read the appropriate server's README for setup instructions:**
    ```sh
    cat src/<server-name>/README.md
    ```
    - Example: For the Python-based DBTools MCP server:
      ```
      cd src/dbtools-mcp-server/
      cat README.md
      ```

4. **Typical Python Server Setup Example:**
    ```sh
    python3 -m venv venv
    source venv/bin/activate        # On Windows: venv\Scripts\activate
    pip install -r requirements-dev.txt
    ```
    *(For Node.js/Java/other servers, follow respective instructions in that server’s README)*

5. **Build and Install servers in the current virtual environment**
    ```sh
    make build
    make install
    ```

## Authentication

For OCI MCP servers, you'll need to install and authenticate using the OCI CLI.

1. Install the [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)
2. Configure your OCI CLI profile
```bash
oci session authenticate --region=<region> --tenancy-name=<tenancy_name>
```
where:
<region> is the region you would like to authenticate in (e.g. `us-phoenix-1`)
<tenancy_name> is the name of your OCI tenancy

All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

Remember to refresh the session once it expires with:
```bash
oci session authenticate --profile-name <profile_name> --region <region> --auth security_token
```

## Client configuration

Each MCP server exposes endpoints that your client can connect to. To enable this connection, just add the relevant server to your MCP client’s configuration file. You can find the list of servers under the `src` folder.

Refer to the sections below for client-specific configuration instructions.

### Cline

<details>
<summary>Setup</summary>

Before continuing, make sure you have already followed the steps above in the [Getting Started](#getting-started) section.

1. If using Visual Studio Code, install the [Cline VS Code Extension](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) (or equivalent extension for your preferred IDE). 
2. Once installed, click the extension to open it.
3. Click the **MCP Servers** button near the top of the the extension's panel.
4. Select the **Installed** tab.
5. Click **Configure MCP Servers** to open the `cline_mcp_settings.json` file.
6. In the `cline_mcp_settings.json` file, add your desired MCP servers in the `mcpServers` object. Below is an example for for the compute OCI MCP server. Make sure to save the file after editing.

For macOS/Linux
```json
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "oracle.oci-api-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "<profile_name>",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

For Windows - **TODO**

7. Once installed, you should see a list of your **MCP Servers** under the **Installed** tab. They will have a green toggle that shows that they are enabled.
8. Click **Done** when finished.

</details>

### Cursor

<details>
<summary>Setup</summary>

Before continuing, make sure you have already followed the steps above in the [Getting Started](#getting-started) section.

1. You can place MCP configurations in two locations, depending on your use case:

**Project Configuration**: For tools specific to a project, create a `.cursor/mcp.json` file in your project directory. This allows you to define MCP servers that are only available within that specific project.

**Global Configuration**: For tools that you want to use across all projects, create a `~/.cursor/mcp.json` file in your home directory. This makes MCP servers available in all your Cursor workspaces.

**`.cursor/mcp.json`**

For macOS/Linux:

```json
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "oracle.oci-api-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "<profile_name>",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

For Windows - **TODO**

2. In your **Cursor Settings**, check your **Installed Servers** under the **MCP** tab to ensure that your `.cursor/mcp.json` was properly configured.

</details>

### MCPHost

<details>
<summary>Setup</summary>

Before continuing, make sure you have already followed the steps above in the [Getting Started](#getting-started) section.

1. Download [Ollama](https://ollama.com/download)
2. Start the Ollama server

For macOS: If installed via the official installer, `ollama start`. If installed via homebrew, `brew services start ollama`

For Windows: If installed via the official installer, the server is typically configured to start automatically in the background and on system boot. 

For Linux: `sudo systemctl start ollama`

3. Verify the ollama server has started with `curl http://localhost:11434`. A successful response will typically be "Ollama is running".
4. Fetch the large language model, where `<model>` is the name of your desired model (e.g. `qwen2.5`), with `ollama pull <model>`. For more options, check Ollama's list of [models that support tool calling](https://ollama.com/search?c=tools).
5. Install `go` from [here](https://go.dev/doc/install)
6. Install `mcphost` with `go install github.com/mark3labs/mcphost@latest`
7. Add go's bin to your PATH with `export PATH=$PATH:~/go/bin`
8. Create an mcphost configuration file (e.g. `./mcphost.json`)
9. Add your desired server to the `mcpServers` object. Below is an example for for the compute OCI MCP server. Make sure to save the file after editing.

For macOS/Linux

```json
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "oracle.oci-api-mcp-server"
      ],
      "env": {
        "VIRTUAL_ENV": "<path to your cloned repo>/oci-mcp/.venv",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

For Windows - **TODO**

10. Start `mcphost` with `OCI_CONFIG_PROFILE=<profile> mcphost -m ollama:<model> --config <config-path>`
    1.  `<model>` is the model you chose above
    2.  `<profile>` is the name of the OCI CLI profile that you set up above
    3.  `<config-path>` is the path to the mcphost configuration json file that you made above

</details>

## Directory Structure

```
.
├── src/
│   ├── dbtools-mcp-server/     # MCP server (Python example)
│   ├── another-mcp-server/     # (Possible Node.js, Java, or other implementation)
│   └── ...
├── LICENSE.txt
├── README.md
├── CONTRIBUTING.md
└── SECURITY.md
```
Each server subdirectory includes its own `README.md` with language/runtime details, installation, and usage.

## Testing

### Testing with a Local Development MCP Server

You can modify the settings of your MCP client to run your local server. Open your client json settings file and
update it as needed. For instance:

```json
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "oracle.oci-api-mcp-server"
      ],
      "env": {
        "VIRTUAL_ENV": "<path to your cloned repo>/oci-mcp/.venv",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

where `<absolute path to your server code>` is the absolute path to the server code, for instance
`/Users/myuser/dev/oci-mcp/src/oci-identity-mcp-server/oracle/oci_identity_mcp_server`.

### Inspector

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction)
provides [Inspector](https://github.com/modelcontextprotocol/inspector) which is a developer tool for testing and
debugging MCP servers. More information on Inspector can be found in
the [documentation](https://modelcontextprotocol.io/docs/tools/inspector).

The Inspector runs directly through npx without requiring installation. For instance, to inspect your locally developed
server, you can run:

```
npx @modelcontextprotocol/inspector \
  uv \
  --directory <absolute path to your server code> \
  run \
  server.py
```

Inspector will run your server on localhost (for instance: http://127.0.0.1:6274) which should automatically open the
tool for debugging and development.


## Contributing

This project welcomes contributions from the community. Before submitting a pull 
request, please [review our contribution guide](./CONTRIBUTING.md).

## Security

Please consult the [security guide](./SECURITY.md) for our responsible security
vulnerability disclosure process.

## License
<!-- The correct copyright notice format for both documentation and software
    is "Copyright (c) [year,] year Oracle and/or its affiliates."
    You must include the year the content was first released (on any platform) and
    the most recent year in which it was revised. -->

Copyright (c) 2025 Oracle and/or its affiliates.
 
Released under the Universal Permissive License v1.0 as shown at  
<https://oss.oracle.com/licenses/upl/>.

## Third-Party APIs

Developers choosing to distribute a binary implementation of this project are responsible for obtaining and providing all required licenses and copyright notices for the third-party code used in order to ensure compliance with their respective open source licenses.

## Disclaimer

Users are responsible for their local environment and credential safety. Different language model selections may yield different results and performance.
