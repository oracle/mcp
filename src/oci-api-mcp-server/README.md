# OCI API MCP Server

## Overview
This server provides tools to run OCI CLI commands to interact with the OCI services.
It includes resources and tools to help with OCI command execution and provide helpful information.

## Running the server
```sh
uv run oracle.oci-api-mcp-server
```
## Tools and Resources
| Tool/Resource Name | Description |
| --- | --- |
| get_oci_command_help | Returns helpful instructions for running an OCI CLI command. Only provide the command after 'oci', do not include the string 'oci' in your command. |
| run_oci_command | Runs an OCI CLI command. This tool allows you to run OCI CLI commands on the user's behalf. Only provide the command after 'oci', do not include the string 'oci' in your command. |
| get_oci_commands (Resource) | Returns helpful information on various OCI services and related commands. |

<span style="font-size: small;">Copyright (c) 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.</span>
