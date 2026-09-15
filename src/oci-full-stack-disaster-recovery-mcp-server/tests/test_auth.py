"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.

Tests for OCI FSDR client authentication helpers.
"""

from __future__ import annotations

from oracle.oci_fsdr_mcp_server import __project__, __version__, auth


EXPECTED_ADDITIONAL_USER_AGENT = (
    f"{__project__.split('oracle.', 1)[1].split('-server', 1)[0]}/{__version__}"
)


def test_get_dr_client_caches_per_profile(monkeypatch):
    auth._client_cache.clear()
    created = []

    def fake_make_client(profile):
        client = object()
        created.append((profile, client))
        return client

    monkeypatch.setattr(auth, "_make_client", fake_make_client)

    first = auth.get_dr_client("FSDR_REGION1")
    second = auth.get_dr_client("FSDR_REGION1")
    third = auth.get_dr_client("FSDR_REGION2")

    assert first is second
    assert third is not first
    assert [profile for profile, _ in created] == ["FSDR_REGION1", "FSDR_REGION2"]


def test_make_client_selects_auth_strategy(monkeypatch):
    calls = []

    monkeypatch.setattr(auth, "_make_security_token_client", lambda p: calls.append(("token", p)) or "token-client")
    monkeypatch.setattr(auth, "_make_api_key_client", lambda p: calls.append(("api", p)) or "api-client")

    monkeypatch.setattr(auth, "DEFAULT_OCI_AUTH_TYPE", "security_token")
    assert auth._make_client("token-profile") == "token-client"

    monkeypatch.setattr(auth, "DEFAULT_OCI_AUTH_TYPE", "api_key")
    assert auth._make_client("api-profile") == "api-client"
    assert calls == [("token", "token-profile"), ("api", "api-profile")]


def test_make_api_key_client_loads_and_validates_config(monkeypatch):
    config = {"profile": "loaded"}
    calls = []

    monkeypatch.setattr(
        auth.oci.config,
        "from_file",
        lambda file_location, profile_name: calls.append(("from_file", file_location, profile_name)) or config,
    )
    monkeypatch.setattr(
        auth.oci.config,
        "validate_config",
        lambda loaded_config: calls.append(("validate", loaded_config.copy())),
    )

    class FakeDisasterRecoveryClient:
        def __init__(self, loaded_config, signer=None):
            calls.append(("client", loaded_config.copy(), signer))

    monkeypatch.setattr(
        auth.oci.disaster_recovery,
        "DisasterRecoveryClient",
        FakeDisasterRecoveryClient,
    )

    client = auth._make_api_key_client("FSDR_REGION1")

    assert isinstance(client, FakeDisasterRecoveryClient)
    assert calls == [
        ("from_file", auth.DEFAULT_OCI_CONFIG_FILE, "FSDR_REGION1"),
        ("validate", {"profile": "loaded"}),
        (
            "client",
            {
                "profile": "loaded",
                "additional_user_agent": EXPECTED_ADDITIONAL_USER_AGENT,
            },
            None,
        ),
    ]


def test_make_security_token_client_uses_token_signer(monkeypatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text(" security-token \n", encoding="utf-8")
    key_file = tmp_path / "oci_api_key.pem"
    key_file.write_text("private-key", encoding="utf-8")
    calls = []

    monkeypatch.setattr(
        auth.oci.config,
        "from_file",
        lambda file_location, profile_name: {
            "security_token_file": str(token_file),
            "key_file": str(key_file),
        },
    )

    class FakeSecurityTokenSigner:
        def __init__(self, token, private_key_file_location):
            calls.append(("signer", token, private_key_file_location))

    class FakeDisasterRecoveryClient:
        def __init__(self, config, signer):
            calls.append(("client", config, signer))

    monkeypatch.setattr(auth.oci.auth.signers, "SecurityTokenSigner", FakeSecurityTokenSigner)
    monkeypatch.setattr(
        auth.oci.disaster_recovery,
        "DisasterRecoveryClient",
        FakeDisasterRecoveryClient,
    )

    client = auth._make_security_token_client("FSDR_REGION1")

    assert isinstance(client, FakeDisasterRecoveryClient)
    assert calls[0] == ("signer", "security-token", str(key_file))
    assert calls[1][0] == "client"
    assert calls[1][1] == {"additional_user_agent": EXPECTED_ADDITIONAL_USER_AGENT}
    assert isinstance(calls[1][2], FakeSecurityTokenSigner)
