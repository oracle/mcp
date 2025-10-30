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

Follow these instructions to get started as quickly as possible. Once finished, look [here](#local-development) to set up your local development environment if you wish to [contribute](#contributing) changes.

1. Install `uv` from [here](https://docs.astral.sh/uv/getting-started/installation/)
2. Install python with `uv python install 3.13`
3. If you are using OCI servers, configure your [OCI authentication](#authentication)
4. Add desired servers to your [MCP client configuration](#client-configuration)

Below is an example MCP client configuration for a typical python server

*(For Node.js/Java/other servers, follow respective instructions in that server’s README)*

For macOS/Linux:
```
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "command": "uvx",
      "args": [
        "oracle.oci-api-mcp-server@latest"
      ],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

## Authentication

For OCI MCP servers, you'll need to install and authenticate using the OCI CLI.

1. Install the [OCI CLI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)
2. Configure your OCI CLI profile
```bash
oci session authenticate --region=<region> --tenancy-name=<tenancy_name>
```
where:
`<region>` is the region you would like to authenticate in (e.g. `us-phoenix-1`)
`<tenancy_name>` is the name of your OCI tenancy

Some MCP servers may not work with token-based authentication alone. See more about API key-based authentication [here](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm).

All actions are performed with the permissions of the configured OCI CLI profile. We advise least-privilege IAM setup, secure credential management, safe network practices, secure logging, and warn against exposing secrets.

Remember to refresh the session once it expires with:
```bash
oci session authenticate --profile-name <profile_name> --region <region> --auth security_token
```

`<profile_name>` is the profile that you set up in the steps above. You can view a list of your profiles by running `cat ~/.oci/config` on macOS/Linux if you forget which profile you have set up.

## Client configuration

Each MCP server exposes endpoints that your client can connect to. To enable this connection, just add the relevant server to your MCP client’s configuration file. You can find the list of servers under the `src` folder.

Refer to the sections below for client-specific configuration instructions.

### Cline

<details>
<summary>Setup</summary>

Before continuing, make sure you have already followed the steps above in the [Quick start](#quick-start) section.

1. If using Visual Studio Code, install the [Cline VS Code Extension](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) (or equivalent extension for your preferred IDE). 
2. Once installed, click the extension to open it.
3. Click the **MCP Servers** button near the top of the the extension's panel.
4. Select the **Installed** tab.
5. Click **Configure MCP Servers** to open the `cline_mcp_settings.json` file.
6. In the `cline_mcp_settings.json` file, add your desired MCP servers in the `mcpServers` object. Below is an example for for the generic OCI API MCP server. Make sure to save the file after editing. `<profile_name>` is the profile that you set up during the [authentication](#authentication) steps.

For macOS/Linux:
```json
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.oci-api-mcp-server@latest"
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

Before continuing, make sure you have already followed the steps above in the [Quick start](#quick-start) section.

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
      "command": "uvx",
      "args": [
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

`<profile_name>` is the profile that you set up during the [authentication](#authentication) steps.

For Windows - **TODO**

2. In your **Cursor Settings**, check your **Installed Servers** under the **MCP** tab to ensure that your `.cursor/mcp.json` was properly configured.

</details>

### MCPHost

<details>
<summary>Setup</summary>

Before continuing, make sure you have already followed the steps above in the [Quick start](#quick-start) section.

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
8. Create an mcphost configuration file (e.g. `~/.mcphost.json`). Check [here](https://github.com/mark3labs/mcphost?tab=readme-ov-file#mcp-servers) for more info.
9. Add your desired server to the `mcpServers` object. Below is an example for for the compute OCI MCP server. Make sure to save the file after editing.

For macOS/Linux:
```json
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "type": "stdio",
      "command": "uvx",
      "args": [
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

`<profile_name>` is the profile that you set up during the [authentication](#authentication) steps.

For Windows - **TODO**

10. Start `mcphost` with `OCI_CONFIG_PROFILE=<profile> mcphost -m ollama:<model> --config <config-path>`
    1.  `<model>` is the model you chose above
    2.  `<profile>` is the name of the OCI CLI profile that you set up above
    3.  `<config-path>` is the path to the mcphost configuration json file that you made above

</details>

## Local development

This section will help you set up your environment to prepare it for local development if you wish to [contribute](#contributing) changes.

1. Set up python virtual environment and install dev requirements
    ```sh
    uv venv --python 3.13 --seed
    source .venv/bin/activate        # On Windows: .venv\Scripts\activate
    pip install -r requirements-dev.txt
    ```

2.  Locally build and install servers within the virtual environment
    ```sh
    make build
    make install
    ```

3. Add desired servers to your MCP client configuration, but run them using the locally installed server package instead

Below is an example MCP client configuration for a typical python server using the local server package

*(For Node.js/Java/other servers, follow respective instructions in that server’s README)*

For macOS/Linux:
```
{
  "mcpServers": {
    "oracle-oci-api-mcp-server": {
      "command": "uv",
      "args": [
        "run",
        "oracle.oci-api-mcp-server"
      ],
      "env": {
        "VIRTUAL_ENV": "<path to your cloned repo>/mcp/.venv",
        "FASTMCP_LOG_LEVEL": "ERROR"
      }
    }
  }
}
```

where `<path to your cloned repo>` is the absolute path to wherever you cloned this repo that will help point to the venv created above (e.g. `/Users/myuser/dev/mcp/.venv`)

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
