"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os

from fastmcp.server.auth.providers.oci import OCIProvider

# ---------- AUTH PROVIDER ----------

class CustomOCIProvider(OCIProvider):

    def _prepare_scopes_for_token_exchange(self, scopes: list[str]) -> list[str]:
        return []

def get_auth_provider():

    return CustomOCIProvider(
        config_url=os.getenv("OCI_CONFIG_URL"),
        client_id=os.getenv("OCI_MCP_CLIENT_ID"),
        client_secret=os.getenv("OCI_MCP_CLIENT_SECRET"),
        base_url="http://localhost:8000",
        redirect_path="/mcp/auth/callback",
        required_scopes=["openid", "get_approles", "approles"],
    )