# MCP Server Best Practices

This document lays out the best practices for an individual MCP server. You may use `oci-compute-mcp-server` as an example.

## Typical MCP Server Structure

```
mcp-server-name/
├── LICENSE.txt             # License information
├── pyproject.toml          # Project configuration
├── CHANGELOG.md            # The CHANGELOG for the server.
├── README.md               # Project description, setup instructions
├── uv.lock                 # Dependency lockfile
└── oracle/                 # Source code directory
    ├── __init__.py         # Package initialization
    └── mcp_server_name/    # Server package, notice the underscores
        ├── __init__.py     # Package version and metadata
        ├── models.py       # Pydantic models
        ├── server.py       # Server implementation
        ├── consts.py       # Constants definition
        ├── ...             # Additional modules
        └── tests/          # Test directory
```

## Code Organization

1. **Separation of Concerns**:
   - `models.py`: Define data models and validation logic
   - `server.py`: Implement MCP server, tools, and resources
   - `consts.py`: Define constants used across the server
   - Additional modules for specific functionality (e.g., API clients)

2. **Keep modules focused and limited to a single responsibility**

3. **Use clear and consistent naming conventions**

### Entry Points

MCP servers should follow these guidelines for application entry points:

1. **Single Entry Point**: Define the main entry point only in `server.py`
   - Do not create a separate `main.py` file
   - This maintains clarity about how the application starts

2. **Main Function**: Implement a `main()` function in `server.py` that:
   - Handles command-line arguments
   - Sets up environment and logging
   - Initializes the MCP server

Example:

```python
def main():
    """Run the MCP server with CLI argument support."""
    mcp.run()


if __name__ == '__main__':
    main()
```

3. **Package Entry Point**: Configure the entry point in `pyproject.toml`:

```toml
[project.scripts]
"oracle.mcp-server-name" = "oracle.mcp_server_name.server:main"
```

## License and Copyright Headers

Include license headers at the top of each source file:

```python
"""
Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""
```

## Type Definitions

### General Rules

1. Make all models Pydantic; this ensures serializability. You may refer to the OCI python SDK for reference to most OCI models.
2. Define Literals for constrained values.
3. Add comprehensive descriptions to each field.

Pydantic model example for [NetworkSecurityGroup](src/oci-networking-mcp-server/oracle/oci_networking_mcp_server/models.py)

```python
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

class NetworkSecurityGroup(BaseModel):
    """
    Pydantic model mirroring the fields of oci.core.models.NetworkSecurityGroup.
    """

    compartment_id: Optional[str] = Field(
        None,
        description="The OCID of the compartment containing the network security group.",
    )
    defined_tags: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Defined tags for this resource. Each key is predefined and scoped to a namespace.",
    )
    display_name: Optional[str] = Field(
        None, description="A user-friendly name. Does not have to be unique."
    )
    freeform_tags: Optional[Dict[str, str]] = Field(
        None, description="Free-form tags for this resource as simple key/value pairs."
    )
    id: Optional[str] = Field(
        None, description="The OCID of the network security group."
    )
    lifecycle_state: Optional[
        Literal[
            "PROVISIONING",
            "AVAILABLE",
            "TERMINATING",
            "TERMINATED",
            "UNKNOWN_ENUM_VALUE",
        ]
    ] = Field(None, description="The network security group's current state.")
    time_created: Optional[datetime] = Field(
        None,
        description="The date and time the network security group was created (RFC3339).",
    )
    vcn_id: Optional[str] = Field(
        None, description="The OCID of the VCN the network security group belongs to."
    )
```

The pydantic model above was generated using Cline by providing it a prompt similar to this:
```
Can you create a pydantic model of oci.core.models.NetworkSecurityGroup and put it inside of the oracle/oci_networking_mcp_server/models.py file, and name it NetworkSecurityGroup? Can you also make a function that maps an oci.core.models.NetworkSecurityGroup instance to an oracle.oci_networking_mcp_server.model.NetworkSecurityGroup instance? Do the same for all of the nested types within the model as well

Use file oracle/oci_compute_mcp_server/models.py as an example of how to do this
```

## Function Parameters with Pydantic Field

MCP tool functions should use spread parameters with Pydantic's `Field` for detailed descriptions:

Here is an example for [list_instances](src/oci-compute-mcp-server/oracle/oci_compute_mcp_server/server.py)

```python
@mcp.tool(description="List Instances in a given compartment")
def list_instances(
    compartment_id: str = Field(..., description="The OCID of the compartment"),
    limit: Optional[int] = Field(
        None,
        description="The maximum amount of instances to return. If None, there is no limit.",
        ge=1,
    ),
    lifecycle_state: Optional[
        Literal[
            "MOVING",
            "PROVISIONING",
            "RUNNING",
            "STARTING",
            "STOPPING",
            "STOPPED",
            "CREATING_IMAGE",
            "TERMINATING",
            "TERMINATED",
        ]
    ] = Field(None, description="The lifecycle state of the instance to filter on"),
) -> list[Instance]:
    instances: list[Instance] = []

    try:
        client = get_compute_client()

        response: oci.response.Response = None
        has_next_page = True
        next_page: str = None

        while has_next_page and (limit is None or len(instances) < limit):
            kwargs = {
                "compartment_id": compartment_id,
                "page": next_page,
                "limit": limit,
            }

            if lifecycle_state is not None:
                kwargs["lifecycle_state"] = lifecycle_state

            response = client.list_instances(**kwargs)
            has_next_page = response.has_next_page
            next_page = response.next_page if hasattr(response, "next_page") else None

            data: list[oci.core.models.Instance] = response.data
            for d in data:
                instance = map_instance(d)
                instances.append(instance)

        logger.info(f"Found {len(instances)} Instances")
        return instances

    except Exception as e:
        logger.error(f"Error in list_instances tool: {str(e)}")
        raise e
```

### Field Guidelines

1. **Required parameters**: Use `...` as the default value to indicate a parameter is required
2. **Optional parameters**: Provide sensible defaults and mark as `Optional` in the type hint
3. **Descriptions**: Write clear, informative descriptions for each parameter
4. **Validation**: Use Field constraints like `ge`, `le`, `min_length`, `max_length`
5. **Literals**: Use `Literal` for parameters with a fixed set of valid values
