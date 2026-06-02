# OCI Python MCP Server

An RPC endpoint for the OCI Python SDK. The agent writes a straight-line SDK
script in Python and sends it to the server. The server parses and tree-walks
that script, never calls `exec` or `eval`, and returns the result of the final
expression.

## Tools

| Tool | Purpose |
| --- | --- |
| `oci_exec(code)` | Run a parsed OCI Python SDK script and return the last line's value. |
| `oci_discover(client?, operation?, service?)` | Discover services, clients, operations, signatures, and docstrings. |

## Example

```python
shape = LaunchInstanceShapeConfigDetails(ocpus=2, memory_in_gbs=16)
details = LaunchInstanceDetails(
    compartment_id="ocid1.compartment...",
    shape="VM.Standard.E4.Flex",
    shape_config=shape,
)
ComputeClient.launch_instance(details)
```

The parser accepts assignments, variables, literals, subscripts on returned
data, OCI model constructors, and `Client.operation(...)` calls. It rejects
imports, loops, conditionals, functions, attribute traversal, and other AST
nodes outside that subset.

State-changing operations are rejected unless `OCI_MCP_ENABLE_MUTATIONS=1` is
set. Read operations are identified by the `list_`, `get_`, and `head_`
prefixes.

## Running

```sh
uvx oracle.oci-python-mcp-server
```

For local development in this repository:

```sh
make test project=oci-python-mcp-server
uv run ruff check src/oci-python-mcp-server
```

Authentication uses OCI instance principals when available, and otherwise falls
back to the default OCI SDK config file.
