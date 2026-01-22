"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest


def test_models_module_optional():
    """If a models.py is introduced later, these tests will start running.
    Currently this server has no models module, so we skip gracefully.
    """
    pytest.importorskip(
        "oracle.oci_usage_mcp_server.models",
        reason="No models.py present in oci-usage-mcp-server",
    )
