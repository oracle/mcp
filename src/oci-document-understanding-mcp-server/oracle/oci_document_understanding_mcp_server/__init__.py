"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from importlib.metadata import version as distribution_version

__project__ = "oracle.oci-document-understanding-mcp-server"
__version__ = distribution_version(__project__)

__all__ = ["__project__", "__version__"]
