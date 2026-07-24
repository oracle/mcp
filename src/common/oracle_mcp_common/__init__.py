"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from .auth import (
    AuthContext,
    AuthType,
    AuthOptions,
    IDCSHttpAuth,
    IDCSHttpAuthContext,
    IDCSHttpAuthOptions,
    build_auth_context,
    build_idcs_http_auth,
    profile_declares_security_token,
    resolve_auth_type,
    resolve_config_file,
    resolve_profile_name,
)

__all__ = [
    "AuthContext",
    "AuthType",
    "AuthOptions",
    "IDCSHttpAuth",
    "IDCSHttpAuthContext",
    "IDCSHttpAuthOptions",
    "build_auth_context",
    "build_idcs_http_auth",
    "profile_declares_security_token",
    "resolve_auth_type",
    "resolve_config_file",
    "resolve_profile_name",
]

__project__ = "oracle_mcp_common"
__version__ = "0.1.1"
