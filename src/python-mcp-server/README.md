# oracle.python-mcp-server

Python code execution MCP server that runs arbitrary Python code inside a WebAssembly (WASM) sandbox.

The sandbox provides complete isolation: no host filesystem access, no network access, and a fuel-based instruction budget to prevent runaway execution. The Python standard library is available inside the sandbox.

## Running the Server

### STDIO (default)

```bash
uv run oracle.python-mcp-server
```

### HTTP

```bash
ORACLE_MCP_HOST=0.0.0.0 ORACLE_MCP_PORT=8080 uv run oracle.python-mcp-server
```

## First Run

The first run downloads CPython 3.13 WASM (~30 MB zip) from GitHub and extracts it to `~/.cache/python-sandbox-mcp/`. Override the binary path with:

```bash
PYTHON_WASM_PATH=/path/to/python.wasm uv run oracle.python-mcp-server
```

## Tools

| Tool | Description |
|------|-------------|
| `run_python` | Execute Python code in the WASM sandbox, returns stdout, stderr, exit_code, timed_out |
| `run_python_with_input` | Same as run_python but also accepts stdin data |

## Sandbox Properties

- Python stdlib available via `/lib` mount (read-only)
- No other host filesystem access
- No network access
- Fuel-based timeout: each WASM instruction consumes 1 fuel unit

## Security

This server executes arbitrary code. The WASM sandbox ensures that executed code cannot access the host filesystem (beyond the read-only stdlib), make network calls, or run indefinitely. However, operators should review their deployment environment and apply additional controls as appropriate.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
