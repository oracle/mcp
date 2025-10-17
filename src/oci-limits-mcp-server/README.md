# OCI Limits MCP Server

## Overview

This MCP server exposes Oracle Cloud Infrastructure Limits APIs through tools mirroring public endpoints.

## Running the Server

To run the server:
```sh
uv run oracle.oci-limits-mcp-server
```

## Tools

| Tool Name | Description | Parameters |
| --- | --- | --- |
| list_services | Returns supported services | compartment_id, sort_by='name', sort_order='ASC', limit=100, page=None, subscription_id=None |
| list_limit_definitions | Returns limit definitions | compartment_id, service_name=None, name=None, sort_by='name', sort_order='ASC', limit=100, page=None, subscription_id=None |
| list_limit_values | Returns limit values | compartment_id, service_name, scope_type=None, availability_domain=None, name=None, sort_by='name', sort_order='ASC', limit=100, page=None, subscription_id=None, external_location=None |
| get_resource_availability | Returns usage/availability for a specific limit | service_name, limit_name, compartment_id, availability_domain=None, subscription_id=None, external_location=None |

## Authentication

Follows the same pattern as other OCI MCP servers:
- Reads OCI config from ~/.oci/config
- Uses security token authentication
- Adds custom user agent header

## Notes

- For AD-scoped limits, `availability_domain` is required.
- Tools return dicts aligned with Swagger models.

## License

Copyright (c) 2025 Oracle and/or its affiliates.
Released under the Universal Permissive License v1.0.

## Third-Party APIs

Developers distributing binary implementations must obtain and provide required third-party licenses and copyright notices.

## Disclaimer

Users are responsible for local environment and credential safety. Different language models may yield different results.
