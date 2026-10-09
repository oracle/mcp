# OCI Limits MCP Server

## Overview

This MCP server exposes Oracle Cloud Infrastructure Limits APIs through tools mirroring public endpoints.

## MCP client configuration (recommended)

Most users should configure their MCP client to launch the server, rather than starting it manually.

Add a stanza like this to your MCP client config (often called `mcp.json`; example shown is **stdio**):

```json
{
  "mcpServers": {
    "oci-limits": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "oracle.oci-limits-mcp-server"
      ],
      "env": {
        "OCI_CONFIG_PROFILE": "DEFAULT"
      }
    }
  }
}
```

## Tools

| Tool Name | Description | Parameters |
| --- | --- | --- |
| list_services | Returns supported services and a resume token | compartment_id, sort_by='name', sort_order='ASC', limit=None, page=None, subscription_id=None |
| list_limit_definitions | Returns limit definitions and a resume token | compartment_id, service_name=None, name=None, sort_by='name', sort_order='ASC', limit=None, page=None, subscription_id=None |
| list_limit_value | Returns limit values and a resume token | compartment_id, service_name, name, scope_type, availability_domain=None, sort_by='name', sort_order='ASC', limit=None, page=None, subscription_id=None |
| get_resource_availability | Returns usage/availability for a specific limit | service_name, limit_name, compartment_id, availability_domain=None, subscription_id=None, external_location=None |

## Pagination

`list_services`, `list_limit_definitions`, and `list_limit_value` return an object
with `items` (the mapped summaries) and `next_page` (an OCI continuation token,
or `null` when there are no more results). This replaces the previous bare list
response.

With no `page`, a numeric `limit` bounds the total items returned across OCI
pages. With `limit=null` (the tool default), all pages are collected. To resume,
pass the returned `next_page` as `page`, keeping the same filters and sort order;
this fetches only one OCI page, with `limit` controlling its requested size.
Continue until `next_page` is `null`.

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
