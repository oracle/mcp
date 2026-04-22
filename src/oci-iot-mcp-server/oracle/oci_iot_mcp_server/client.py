from functools import lru_cache

import oci

from .auth import build_auth_context, resolved_auth_type, resolved_profile_name


@lru_cache(maxsize=None)
def _build_iot_client(profile_name: str, auth_type: str):
    auth_context = build_auth_context(profile_name=profile_name, auth_type=auth_type)
    return oci.iot.IotClient(auth_context.config, signer=auth_context.signer)


def get_iot_client(profile_name: str | None = None, auth_type: str | None = None):
    return _build_iot_client(
        resolved_profile_name(profile_name),
        resolved_auth_type(auth_type),
    )


def clear_iot_client_cache():
    _build_iot_client.cache_clear()
