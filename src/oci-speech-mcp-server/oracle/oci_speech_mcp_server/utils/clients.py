"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at
https://oss.oracle.com/licenses/upl.
"""

from dataclasses import dataclass
from threading import Lock
from typing import Any

import oci
from oracle_mcp_common import build_auth_context

from .. import __project__, __version__

TTS_REGION = "us-phoenix-1"
USER_AGENT_NAME = __project__.split("oracle.", 1)[1].removesuffix("-server")
ADDITIONAL_USER_AGENT = f"{USER_AGENT_NAME}/{__version__}"


@dataclass(frozen=True)
class Clients:
    speech: Any
    speech_tts: Any
    object_storage: Any
    notifications: Any
    subscriptions: Any
    events: Any


_clients: Clients | None = None
_clients_lock = Lock()


def _client_kwargs(signer: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"retry_strategy": oci.retry.DEFAULT_RETRY_STRATEGY}
    if signer is not None:
        kwargs["signer"] = signer
    return kwargs


def _safe_config(config: dict[str, Any], *, region: str | None = None) -> dict[str, Any]:
    result = {
        **config,
        "additional_user_agent": ADDITIONAL_USER_AGENT,
        "log_requests": False,
    }
    if region is not None:
        result["region"] = region
    return result


def get_clients() -> Clients:
    """Build and cache process-wide stdio clients from one auth context."""
    global _clients
    if _clients is not None:
        return _clients
    with _clients_lock:
        if _clients is not None:
            return _clients
        context = build_auth_context()
        config = _safe_config(context.config)
        tts_config = _safe_config(context.config, region=TTS_REGION)
        kwargs = _client_kwargs(context.signer)
        _clients = Clients(
            speech=oci.ai_speech.AIServiceSpeechClient(config, **kwargs),
            speech_tts=oci.ai_speech.AIServiceSpeechClient(tts_config, **kwargs),
            object_storage=oci.object_storage.ObjectStorageClient(config, **kwargs),
            notifications=oci.ons.NotificationControlPlaneClient(config, **kwargs),
            subscriptions=oci.ons.NotificationDataPlaneClient(config, **kwargs),
            events=oci.events.EventsClient(config, **kwargs),
        )
        return _clients


def reset_clients() -> None:
    """Clear cached clients. Intended for tests and controlled reconfiguration."""
    global _clients
    with _clients_lock:
        _clients = None
