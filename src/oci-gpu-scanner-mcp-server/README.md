# Lens API MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with the lens API for instance and health check management.

## Overview

This MCP server exposes lens API functionality through a standardized interface, allowing AI assistants to:

- List instances in the lens system
- Manage active health checks
- Submit health check reports
- Monitor health check status

## Features

### Instance Management
- **List Instances**: Retrieve all instances in the system

### Health Check Management
- **Get Latest Health Check**: Retrieve the most recent health check for an instance
- **Create Health Check**: Start a new health check for an instance
- **Submit Health Check Report**: Upload JSON and log reports for health checks
- **Get All Health Checks**: List all health checks for an instance

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LENS_API_BASE_URL` | Base URL of the lens API | `http://localhost:8000` | No |
| `LENS_API_KEY` | Authentication token for the lens API | None | No* |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |

*Required if the lens API requires authentication

### Example Configuration

```bash
export LENS_API_BASE_URL="http://lens-api.example.com"
export LENS_API_KEY="your-api-key-here"
export LOG_LEVEL="DEBUG"
```

## Installation

1. Create a virtual environment:
```bash
python3 -m venv lens-mcp-env
source lens-mcp-env/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
source local.env
```

3. Set environment variables as needed

## Running the MCP Server

#### Running with STDIO

Start the MCP server using STDIO:
```bash
./run_server.sh
```

#### Running with SSE (Server-Sent Events)

Start the MCP server using SSE:
```bash
npx mcp-proxy --port 8001 --shell ./run_server.sh
```

#### Direct Python Execution

Alternatively, run the server directly:
```bash
python server.py
```

#### Testing with MCP Inspector

For development and testing, use the MCP inspector:
```bash
npx @modelcontextprotocol/inspector ./run_server.sh
```

## Available Tools

### list_instances
List all instances in the lens system.

**Parameters:** None

**Example:**
```json
{
  "name": "list_instances",
  "arguments": {}
}
```

### get_latest_health_check
Get the latest active health check for a specific instance.

**Parameters:**
- `instance_id` (string, required): The ID of the instance

**Example:**
```json
{
  "name": "get_latest_health_check",
  "arguments": {
    "instance_id": "ocid1.instance.oc1..."
  }
}
```

### create_health_check
Create a new active health check for a specific instance.

**Parameters:**
- `instance_id` (string, required): The ID of the instance
- `type` (string, optional): Type of health check (["single_node", "multi_node", "advanced" default: "single_node")

**Example:**
```json
{
  "name": "create_health_check",
  "arguments": {
    "instance_id": "ocid1.instance.oc1...",
    "type": "single_node"
  }
}
```

### submit_health_check_report
Submit JSON and log reports for an active health check.

**Parameters:**
- `instance_id` (string, required): The ID of the instance
- `log_report` (string, required): Base64 encoded log file
- `json_report` (string, optional): Base64 encoded JSON report

**Example:**
```json
{
  "name": "submit_health_check_report",
  "arguments": {
    "instance_id": "ocid1.instance.oc1...",
    "log_report": "base64-encoded-log-content",
    "json_report": "base64-encoded-json-content"
  }
}
```

## API Endpoints Mapping

This MCP server maps to the following lens API endpoints:

| MCP Tool | HTTP Method | Endpoint |
|----------|-------------|----------|
| `list_instances` | GET | `/instances/` |
| `get_latest_health_check` | GET | `/instances/{instance_id}/active-health-check/` |
| `create_health_check` | POST | `/instances/{instance_id}/active-health-check/` |
| `submit_health_check_report` | POST | `/instances/{instance_id}/active-health-check/report/` |

## Development

### Project Structure

```
lens/
├── server.py              # Main MCP server
├── config.py              # HTTP client configuration
├── log_setup.py           # Logging configuration
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── tools/
│   ├── tool_definition.py # Tool schema definitions
│   └── tool_handler.py    # Tool implementation handlers
└── logs/                  # Log files (created at runtime)
```

### Logging

The server provides comprehensive logging with:
- Colored console output for development
- File-based logging with timestamps
- Request/response logging for debugging
- Configurable log levels

Logs are stored in the `logs/` directory with timestamps.

### Error Handling

The server includes robust error handling:
- HTTP request/response error handling
- Proper error messages returned to the client
- Comprehensive logging of errors for debugging

## License

This project follows the same license as the parent OCI MCP servers project.
