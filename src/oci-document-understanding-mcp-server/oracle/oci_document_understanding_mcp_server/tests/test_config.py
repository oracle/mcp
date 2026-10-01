"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest

from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig


def test_config_defaults_to_oci_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOCUMENT_MCP_MODE", raising=False)
    monkeypatch.delenv("OCI_COMPARTMENT_ID", raising=False)

    config = OciDocumentUnderstandingConfig.from_environment()

    assert config.runtime_mode == "oci"
    assert config.default_compartment_id is None


def test_config_supports_stub_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCUMENT_MCP_MODE", "stub")
    monkeypatch.setenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")

    config = OciDocumentUnderstandingConfig.from_environment()

    assert config.runtime_mode == "stub"
    assert config.default_compartment_id == "ocid1.compartment.oc1..example"


def test_config_rejects_invalid_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCUMENT_MCP_MODE", "bad-value")

    with pytest.raises(ValueError, match="Unsupported"):
        OciDocumentUnderstandingConfig.from_environment()


@pytest.mark.parametrize("mode", ["local", "dev", "prod", "production", "compute", "test", "mock"])
def test_config_rejects_legacy_modes(monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    monkeypatch.setenv("DOCUMENT_MCP_MODE", mode)

    with pytest.raises(ValueError, match="Unsupported"):
        OciDocumentUnderstandingConfig.from_environment()
