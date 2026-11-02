"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import importlib


def test_server_module_imports() -> None:
    module = importlib.import_module("oracle.oci_vision_mcp_server.server")

    assert module.mcp.name == "oracle.oci-vision-mcp-server"
