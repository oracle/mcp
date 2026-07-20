"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

import pytest

from oracle.oci_document_understanding_mcp_server.oci.config import OciDocumentUnderstandingConfig


def test_config_defaults_to_local_session_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DOCUMENT_MCP_MODE", raising=False)
    monkeypatch.delenv("OCI_AUTH_MODE", raising=False)
    monkeypatch.delenv("OCI_COMPARTMENT_ID", raising=False)
    monkeypatch.delenv("OCI_CONFIG_PROFILE", raising=False)

    config = OciDocumentUnderstandingConfig.from_environment()

    assert config.runtime_mode == "local"
    assert config.auth_mode == "session-token"
    assert config.region == "us-ashburn-1"
    assert config.default_compartment_id is None
    assert config.profile == "DEFAULT"


def test_config_supports_stub_mode_and_config_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOCUMENT_MCP_MODE", "test")
    monkeypatch.delenv("OCI_AUTH_MODE", raising=False)
    monkeypatch.setenv("OCI_REGION", "us-phoenix-1")
    monkeypatch.setenv("OCI_COMPARTMENT_ID", "ocid1.compartment.oc1..example")
    monkeypatch.setenv("OCI_CONFIG_PROFILE", "MYPROFILE")

    config = OciDocumentUnderstandingConfig.from_environment()

    assert config.runtime_mode == "stub"
    assert config.auth_mode == "none"
    assert config.region == "us-phoenix-1"
    assert config.default_compartment_id == "ocid1.compartment.oc1..example"
    assert config.profile == "MYPROFILE"


@pytest.mark.parametrize("name", ["DOCUMENT_MCP_MODE", "OCI_AUTH_MODE"])
def test_config_rejects_invalid_modes(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    monkeypatch.setenv(name, "bad-value")

    with pytest.raises(ValueError, match="Unsupported"):
        OciDocumentUnderstandingConfig.from_environment()


@pytest.mark.parametrize(
    ("mode", "expected_auth"),
    [
        ("production", "instance-principal"),
        ("compute", "instance-principal"),
        ("development", "session-token"),
    ],
)
def test_config_runtime_mode_aliases_set_default_auth(monkeypatch: pytest.MonkeyPatch, mode: str, expected_auth: str) -> None:
    monkeypatch.setenv("DOCUMENT_MCP_MODE", mode)
    monkeypatch.delenv("OCI_AUTH_MODE", raising=False)

    config = OciDocumentUnderstandingConfig.from_environment()

    assert config.auth_mode == expected_auth


@pytest.mark.parametrize(
    ("auth", "expected"),
    [
        ("config-file", "api-key"),
        ("prod", "instance-principal"),
        ("stub", "none"),
    ],
)
def test_config_auth_aliases(monkeypatch: pytest.MonkeyPatch, auth: str, expected: str) -> None:
    monkeypatch.setenv("DOCUMENT_MCP_MODE", "local")
    monkeypatch.setenv("OCI_AUTH_MODE", auth)

    config = OciDocumentUnderstandingConfig.from_environment()

    assert config.auth_mode == expected
