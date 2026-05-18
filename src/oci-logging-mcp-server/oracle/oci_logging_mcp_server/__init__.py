"""
Copyright (c) 2025-2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from importlib.metadata import PackageNotFoundError, version

__project__ = "oracle.oci-logging-mcp-server"
try:
    __version__ = version(__project__)
except PackageNotFoundError:
    __version__ = "0.0.0"
