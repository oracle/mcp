"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OciDocumentUnderstandingConfig(BaseModel):
    """Runtime configuration for OCI provider setup."""

    model_config = ConfigDict(frozen=True)

    runtime_mode: Literal["oci", "stub"] = Field(..., description="Provider mode: OCI SDK or deterministic stub.")
    default_compartment_id: str | None = Field(None, description="Default compartment OCID for OCI Document Understanding calls.")

    @staticmethod
    def from_environment() -> "OciDocumentUnderstandingConfig":
        """Builds provider configuration from environment variables."""
        runtime_mode = _normalize_mode(_env("DOCUMENT_MCP_MODE", "oci"))
        return OciDocumentUnderstandingConfig(
            runtime_mode=runtime_mode,
            default_compartment_id=_env("OCI_COMPARTMENT_ID", None),
        )


def _env(name: str, default: str | None) -> str | None:
    """Reads an environment variable and falls back when absent or blank."""
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


def _normalize_mode(value: str | None) -> str:
    """Parses the supported provider modes."""
    normalized = (value or "oci").strip().lower()
    if normalized == "stub":
        return "stub"
    if normalized == "oci":
        return "oci"
    raise ValueError(f"Unsupported DOCUMENT_MCP_MODE: {value}")
