"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from unittest.mock import MagicMock

import pytest
from oracle_mcp_common import AuthContext, AuthType

from oracle.oci_speech_mcp_server.utils import clients


@pytest.mark.parametrize("auth_type", list(AuthType))
@pytest.mark.parametrize("with_signer", [False, True])
def test_all_auth_paths_apply_exact_user_agent(monkeypatch, auth_type, with_signer):
    signer = object() if with_signer else None
    context = AuthContext(
        auth_type=auth_type,
        config={"region": "eu-frankfurt-1", "log_requests": True},
        signer=signer,
        tenancy_id="tenancy",
        region="eu-frankfurt-1",
        profile_name=None,
    )
    build = MagicMock(return_value=context)
    monkeypatch.setattr(clients, "build_auth_context", build)

    constructors = []
    for owner, name in (
        (clients.oci.ai_speech, "AIServiceSpeechClient"),
        (clients.oci.object_storage, "ObjectStorageClient"),
        (clients.oci.ons, "NotificationControlPlaneClient"),
        (clients.oci.ons, "NotificationDataPlaneClient"),
        (clients.oci.events, "EventsClient"),
    ):
        constructor = MagicMock(side_effect=lambda *args, **kwargs: object())
        monkeypatch.setattr(owner, name, constructor)
        constructors.append(constructor)

    bundle = clients.get_clients()
    assert bundle is clients.get_clients()
    build.assert_called_once_with()
    assert constructors[0].call_count == 2
    for constructor in constructors:
        for call in constructor.call_args_list:
            config = call.args[0]
            assert config["additional_user_agent"] == "oci-speech-mcp/1.0.0"
            assert config["log_requests"] is False
            if signer is None:
                assert "signer" not in call.kwargs
            else:
                assert call.kwargs["signer"] is signer

    speech_config = constructors[0].call_args_list[0].args[0]
    tts_config = constructors[0].call_args_list[1].args[0]
    assert speech_config["region"] == "eu-frankfurt-1"
    assert tts_config["region"] == "us-phoenix-1"


def test_client_helpers_and_reset(monkeypatch):
    assert clients.USER_AGENT_NAME == "oci-speech-mcp"
    assert clients._safe_config({"region": "a"}, region="b")["region"] == "b"
    assert "signer" not in clients._client_kwargs(None)
    assert clients._client_kwargs("signer")["signer"] == "signer"
    clients._clients = "cached"
    clients.reset_clients()
    assert clients._clients is None
