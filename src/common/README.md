# oracle-mcp-common

Shared utilities for Oracle MCP servers. This package provides helpers and decorators that can be reused across the various OCI MCP server implementations.

## Usage

Install the package in editable mode from the repository root:

```bash
pip install -e src/common
```

Then import helpers as needed, for example:

```python
from oracle.mcp_common.helpers import with_oci_client
```
