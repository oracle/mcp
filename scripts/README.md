# OCI API Deny List Generator

## Overview

The `oci-api-denylist-generator.py` script generates a deny list of OCI CLI commands that can modify the cloud system's configuration. It creates a list of commands to be denied execution by filtering out commands containing actions like "delete", "terminate", "put", "update", "replace", "remove", and "patch".

## Usage

To generate an updated version of the deny list, follow these steps:

1. Ensure you have the OCI CLI installed and configured on your system.
2. Navigate to the `scripts` directory.
3. Run the `oci-api-denylist-generator.py` script using Python:
   ```bash
   python oci-api-denylist-generator.py
   ```
4. The script will generate a new `denylist_<version>` file and update the `denylist` file with the latest deny list based on the current OCI CLI version.
5. To use the newly generated deny list, copy the denylist to the [oci-api-mcp-server denylist](../src/oci-api-mcp-server/oracle/oci_api_mcp_server/denylist) and restart the `oci-api-mcp-server`.

## Notes

- The script automatically backs up the existing deny list file if it already exists for the current OCI CLI version.
- The deny list includes commands that can potentially change the configuration of the cloud system.
- The generated `denylist` file is used by the AI client to determine which commands to deny execution for.

----
<small>Copyright (c) 2025, Oracle and/or its affiliates. Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.</small>
