# OCI API Deny List Generator

## Overview

The `oci-api-denylist-generator.py` script generates a deny list of OCI CLI commands that can modify the cloud system's configuration. It creates a list of commands to be denied execution by filtering out commands containing actions like "delete", "terminate", "put", "update", "replace", "remove", and "patch".

## Usage

To generate an updated version of the deny list, follow these steps:

1. Sync the `oci-api-mcp-server` environment so its pinned OCI CLI is installed.
2. Navigate to the `scripts` directory.
3. Run the `oci-api-denylist-generator.py` script using Python:
   ```bash
   uv run --project ../src/oci-api-mcp-server python oci-api-denylist-generator.py
   ```
4. The script enumerates the installed OCI CLI's canonical Click command tree, generates a new
   `denylist_<version>` file, and atomically updates the generated files in the `scripts`
   directory for that CLI version.
5. Review the generated diff to confirm every candidate is a mutating operation and that no
   mutating command uses an action outside the configured action set.
6. Copy the reviewed denylist to the [oci-api-mcp-server denylist](../src/oci-api-mcp-server/oracle/oci_api_mcp_server/denylist) and restart the `oci-api-mcp-server`.

## Notes

- The script automatically backs up the existing deny list file if it already exists for the current OCI CLI version.
- Compound action names such as `bulk-delete` are included, while `create-*`, `get-*`,
  `list-*`, and `cancel-*` commands are excluded from automatic classification.
- The action-name classification produces review candidates; it is not a semantic guarantee.
- The generated `denylist` file is used by the AI client to determine which commands to deny execution for.

----
<small>Copyright (c) 2025, Oracle and/or its affiliates. Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.</small>
