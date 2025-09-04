# OpenAPI MCP Server

This server acts as a bridge 🌉, dynamically generating **Model Context Protocol (MCP)** tools from **OpenAPI specifications**. This allows Large Language Models (LLMs) to seamlessly interact with your APIs.

---
## ✨ Features

* ⚡ **Dynamic Tool Generation**: Automatically creates MCP tools from any OpenAPI endpoint for LLM interaction.
* 📡 **Transport Options**: Natively supports `stdio` transport for communication.
* ⚙️ **Flexible Configuration**: Easily configure the server using command-line arguments or environment variables.
* 📚 **OpenAPI & Swagger Support**: Compatible with OpenAPI 3.x and Swagger specs in both JSON and YAML formats.
* 🔑 **Authentication Support**: Handles multiple authentication methods, including Basic, Bearer Token, API Key, and custom headers.

---
## 🚀 Getting Started

### Prerequisites

* **Java 21**: Make sure the JDK is installed and your `JAVA_HOME` environment variable is set correctly.
* **Maven 3.x**: Required for building the project and managing its dependencies.
* **Valid OpenAPI Specification**: You'll need a JSON or YAML file describing the API you want to connect to.

### Installation & Build

1.  **Clone the repository** and navigate to the project directory.
2.  **Build the project** into a runnable JAR file using Maven. This is the only step needed before configuring your client.
    ```bash
    mvn clean package -P release
    ```

---
## 🔧 Configuration

You can configure the server in two primary ways: command-line arguments or environment variables. This configuration is provided to the MCP client, which then uses it to launch the server.

### Environment Variables

The server supports the following environment variables. These can be set within the MCP client's configuration.

| Environment Variable | Description | Example |
| :--- | :--- | :--- |
| `API_BASE_URL` | Base URL of the API. | `https://api.example.com/v1` |
| `API_SPEC` | Path or URL to the OpenAPI specification. | `/configs/openapi.yaml` |
| `AUTH_TYPE` | Authentication type (`BASIC`, `BEARER`, `API_KEY`). | `BEARER` |
| `AUTH_TOKEN` | Token for Bearer authentication. | `eyJhbGciOiJIUzI1NiIsInR5cCI6...` |
| `AUTH_USERNAME` | Username for Basic authentication. | `adminUser` |
| `AUTH_PASSWORD` | Password for Basic authentication. | `P@ssw0rd!` |
| `AUTH_API_KEY` | API key value for `API_KEY` authentication. | `12345-abcdef-67890` |
| `API_API_KEY_NAME`| Name of the API key parameter. | `X-API-KEY` |
| `API_API_KEY_IN` | Location of API key (`header` or `query`). | `header` |
| `AUTH_CUSTOM_HEADERS`| JSON string of custom authentication headers. | `{"X-Tenant-ID": "acme"}` |
| `API_HTTP_CONNECT_TIMEOUT`| Connection timeout in milliseconds. | `5000` |
| `API_HTTP_RESPONSE_TIMEOUT`| Response timeout in milliseconds. | `10000` |

---
## 🔌 Integrating with an MCP Client

The MCP client launches this server as a short-lived process whenever API interaction is needed. Your client configuration must specify the command to execute the .jar file along with its arguments.
#### Example: Client JSON Configuration

Here's how you might configure a client (like VS Code's Cline) to invoke this server, passing the required arguments.

```json
{
  "mcpServers": {
    "my-api-server": {
      "command": "java",
      "args": [
        "-jar",
        "/path/to/your/project/target/openapi-mcp-server-1.0.jar",
        "--api-spec",
        "[https://api.example.com/openapi.json](https://api.example.com/openapi.json)",
        "--api-base-url",
        "[https://api.example.com](https://api.example.com)"
      ],
      "env": {
        "AUTH_TYPE": "BEARER",
        "AUTH_TOKEN": "your-secret-token-here"
      }
    }
  }
}