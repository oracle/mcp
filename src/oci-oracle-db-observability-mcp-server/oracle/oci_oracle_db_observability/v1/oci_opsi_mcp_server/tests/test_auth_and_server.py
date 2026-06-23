"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace

from oracle.oci_oracle_db_observability.v1 import auth
from oracle.oci_oracle_db_observability.v1.oci_opsi_mcp_server import server, tools

TEST_LOGGER = logging.getLogger(__name__)


def test_stdio_build_client_uses_security_token_config(monkeypatch, tmp_path) -> None:
    token_file = tmp_path / "security-token"
    token_file.write_text("SECURITY_TOKEN", encoding="utf-8")
    monkeypatch.delenv("ORACLE_MCP_HOST", raising=False)
    monkeypatch.delenv("ORACLE_MCP_PORT", raising=False)
    monkeypatch.setattr(
        auth.oci.config,
        "from_file",
        lambda file_location, profile_name: {
            "region": "us-phoenix-1",
            "tenancy": "ocid1.tenancy.oc1..example",
            "key_file": "/keys/oci.pem",
            "security_token_file": str(token_file),
        },
    )
    monkeypatch.setattr(auth.oci.signer, "load_private_key_from_file", lambda key_file: "private-key")
    monkeypatch.setattr(
        auth.oci.auth.signers,
        "SecurityTokenSigner",
        lambda token, private_key: f"{token}:{private_key}",
    )

    client = auth.build_client(
        lambda config, **kwargs: SimpleNamespace(config=config, kwargs=kwargs),
        project="oracle.oci-opsi-mcp-server",
        version="1.0.0",
        logger=TEST_LOGGER,
    )

    assert client.config["region"] == "us-phoenix-1"
    assert client.config["tenancy"] == "ocid1.tenancy.oc1..example"
    assert client.config["additional_user_agent"] == "oci-opsi/1.0.0"
    assert client.kwargs["signer"] == "SECURITY_TOKEN:private-key"


def test_http_build_client_uses_token_exchange(monkeypatch) -> None:
    monkeypatch.setenv("ORACLE_MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("ORACLE_MCP_PORT", "8888")
    monkeypatch.setenv("OCI_REGION", "us-ashburn-1")
    monkeypatch.setenv("IDCS_DOMAIN", "idcs.example.com")
    monkeypatch.setenv("IDCS_CLIENT_ID", "client-id")
    monkeypatch.setenv("IDCS_CLIENT_SECRET", "client-secret")
    monkeypatch.setattr(auth, "get_access_token", lambda: SimpleNamespace(token="ACCESS_TOKEN"))
    monkeypatch.setattr(
        auth.oci.auth.signers,
        "TokenExchangeSigner",
        lambda token, domain, client_id, client_secret, region: "token-exchange-signer",
    )

    client = auth.build_client(
        lambda config, **kwargs: SimpleNamespace(config=config, kwargs=kwargs),
        project="oracle.oci-opsi-mcp-server",
        version="1.0.0",
        logger=TEST_LOGGER,
    )

    assert client.config["region"] == "us-ashburn-1"
    assert client.config["additional_user_agent"] == "oci-opsi/1.0.0"
    assert client.kwargs["signer"] == "token-exchange-signer"


def test_server_registers_expected_tools() -> None:
    registered = asyncio.run(server.mcp.list_tools(run_middleware=False))

    assert {tool.name for tool in registered} == tools.TOOL_NAMES

    for tool in registered:
        assert tool.annotations == tools.TOOL_ANNOTATIONS[tool.name]
