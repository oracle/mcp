# OpenAPI MCP Server

## Overview

This project is a server that dynamically generates MCP (Model Context Protocol) tools from OpenAPI specifications, enabling Large Language Models (LLMs) to interact seamlessly with APIs via the Model Context Protocol.
## Features

* Dynamic Tool Generation: Automatically creates MCP tools from OpenAPI endpoints for LLM interaction.
* Transport Options: Supports stdio transport
* Flexible Configuration: Easily configure through environment variables or CLI arguments.
* OpenAPI & Swagger Support: Compatible with OpenAPI 3.x and Swagger specs in JSON or YAML.
* Authentication Support: Multiple methods including Basic, Bearer Token, API Key, and custom.

## Prerequisites

- **Java 21**  
  Make sure the JDK is installed and `JAVA_HOME` is set correctly.

- **Maven 3.x**  
  Required for building the project and managing dependencies.

- **Valid OpenAPI specifications**  
  JSON or YAML files describing the APIs you want to generate MCP tools for.

- **Authentication configuration (optional)**  
  Environment variables or configuration files for API authentication (e.g., API Key, Bearer Token, Basic Auth, or custom methods).

## Installation

1. **Clone this repository**
2. **Navigate to the project directory**
3. **Build the project using Maven**
```bash
maven clean package -P release
```
4. **Run the jar with arguments**
```bash
java -jar target/openapi-mcp-server-1.0.jar --api-spec https://api.example.com/openapi.json --api-base-url https://api.example.com
```

## MCP Server Configuration
Installation is dependent on the MCP Client being used, it usually consists of adding the MCP Server invocation in a json config file, for example with Claude UI on windows it looks like this:

```json
{
  "mcpServers": {
    "cpq-server": {
      "command": "java",
      "args": [
        "-jar",
        "/Users/johnwick/Documents/Projects/mcp/src/openapi-mcp-server/target/openapi-mcp-server-1.0.jar",
        "--api-spec",
        "https://api.example.com/openapi.json",
         "--api-base-url",
        "https://api.example.com"
      ],
      "env": {}
    }
  }
}
```

## Environment Variables

The server supports the following environment variables:

| Environment Variable        | Description                                           |
|-----------------------------|-------------------------------------------------------|
| `API_BASE_URL`              | Base URL of the API                                   |
| `API_SPEC`                  | Path to the OpenAPI specification (JSON or YAML)     |
| `AUTH_TYPE`                 | Authentication type (`BASIC`, `BEARER`, `API_KEY`, or custom) |
| `AUTH_TOKEN`                | Token for Bearer authentication                      |
| `AUTH_USERNAME`             | Username for Basic authentication                    |
| `AUTH_PASSWORD`             | Password for Basic authentication                    |
| `AUTH_API_KEY`              | API key value for `API_KEY` authentication          |
| `API_API_KEY_NAME`          | Name of the API key for header or query placement    |
| `API_API_KEY_IN`            | Location of API key (`header` or `query`)            |
| `AUTH_CUSTOM_HEADERS`       | JSON string representing custom authentication headers |
| `API_HTTP_CONNECT_TIMEOUT`  | Connection timeout in milliseconds                   |
| `API_HTTP_RESPONSE_TIMEOUT` | Response timeout in milliseconds                     |
| `API_HTTP_VERSION`          | HTTP version to use (`HTTP_1_1` or `HTTP_2`)         |
| `API_HTTP_REDIRECT`         | Redirect policy (`NORMAL`, `NEVER`, `ALWAYS`)       |
| `API_HTTP_PROXY_HOST`       | Hostname of HTTP proxy server                        |
| `API_HTTP_PROXY_PORT`       | Port of HTTP proxy server                             |
