"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from oracle.oci_speech_mcp_server.tools import (
    customization as customization_tools,
    notifications as extras_tools,
    transcription as transcription_tools,
    tts as tts_tools,
)
from oracle.oci_speech_mcp_server.utils import clients


def response(data=None, *, headers=None, status=200):
    return SimpleNamespace(
        data=data,
        headers=headers or {"opc-request-id": "request-1", "etag": "etag-1"},
        status=status,
    )


@pytest.fixture
def mock_clients(monkeypatch):
    bundle = SimpleNamespace(
        speech=MagicMock(),
        speech_tts=MagicMock(),
        object_storage=MagicMock(),
        notifications=MagicMock(),
        subscriptions=MagicMock(),
        events=MagicMock(),
    )
    for module in (
        transcription_tools,
        customization_tools,
        tts_tools,
        extras_tools,
    ):
        monkeypatch.setattr(module, "get_clients", lambda: bundle)
    return bundle


@pytest.fixture(autouse=True)
def clean_client_cache():
    clients.reset_clients()
    yield
    clients.reset_clients()
