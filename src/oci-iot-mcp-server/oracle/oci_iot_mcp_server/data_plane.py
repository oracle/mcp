import base64
import hashlib
import json
from datetime import timedelta

import httpx

from .errors import error_result
from .tool_models import DataApiTokenModel, success_result

ORDS_API_DATE = "20250531"
_DATA_API_TOKEN_CACHE: dict[tuple[str, ...], DataApiTokenModel] = {}


class DataApiTokenError(RuntimeError):
    def __init__(self, *, code: str, message: str, retry_hint: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.retry_hint = retry_hint
        self.details = details or {}


def _data_api_token_cache_key(*, domain_context: dict, env: dict) -> tuple[str, ...]:
    secret_fingerprint = hashlib.sha256(
        f"{env['OCI_IOT_ORDS_CLIENT_SECRET']}:{env['OCI_IOT_ORDS_PASSWORD']}".encode()
    ).hexdigest()
    return (
        domain_context["domain_group_short_id"],
        domain_context["domain_short_id"],
        domain_context.get("db_allowed_identity_domain_host") or "",
        env["OCI_IOT_ORDS_CLIENT_ID"],
        env["OCI_IOT_ORDS_USERNAME"],
        secret_fingerprint,
    )


def clear_data_api_token_cache() -> None:
    _DATA_API_TOKEN_CACHE.clear()


def get_cached_data_api_token(*, domain_context: dict, env: dict, now) -> DataApiTokenModel:
    current_time = now()
    cache_key = _data_api_token_cache_key(domain_context=domain_context, env=env)
    cached_token = _DATA_API_TOKEN_CACHE.get(cache_key)
    if cached_token is not None and cached_token.expires_at > current_time:
        return cached_token

    token = mint_data_api_token(
        domain_context=domain_context,
        env=env,
        now=lambda: current_time,
    )
    _DATA_API_TOKEN_CACHE[cache_key] = token
    return token


def build_ords_base_url(domain_context: dict) -> str:
    return f"https://{domain_context['data_host']}/ords/{domain_context['domain_short_id']}/{ORDS_API_DATE}"


def build_twin_filter(digital_twin_instance_id: str) -> dict:
    return {"$and": [{"digital_twin_instance_id": digital_twin_instance_id}]}


def encode_q(filter_payload: dict) -> str:
    return json.dumps(filter_payload, separators=(",", ":"))


def require_token_credentials(env: dict) -> dict:
    required = [
        "OCI_IOT_ORDS_CLIENT_ID",
        "OCI_IOT_ORDS_CLIENT_SECRET",
        "OCI_IOT_ORDS_USERNAME",
        "OCI_IOT_ORDS_PASSWORD",
    ]
    missing = [name for name in required if not env.get(name)]
    if missing:
        return error_result(
            code="missing_token_credentials",
            message="Missing one or more OCI IoT ORDS credential environment variables.",
            retry_hint="Set the missing OCI_IOT_ORDS_* environment variables and retry.",
            details={"missing": missing},
        )

    return success_result({"present": required, "missing": []})


def mint_data_api_token(*, domain_context: dict, env: dict, now) -> DataApiTokenModel:
    identity_domain_host = domain_context.get("db_allowed_identity_domain_host")
    if not identity_domain_host:
        raise DataApiTokenError(
            code="missing_ords_configuration",
            message="IoT domain is not configured for ORDS token minting.",
            retry_hint="Configure ORDS data access for the IoT domain and retry.",
            details={"missing": ["db_allowed_identity_domain_host"]},
        )

    scope = (
        f"/{domain_context['domain_group_short_id']}/iot/"
        f"{domain_context['domain_short_id']}"
    )
    auth = base64.b64encode(
        f"{env['OCI_IOT_ORDS_CLIENT_ID']}:{env['OCI_IOT_ORDS_CLIENT_SECRET']}".encode()
    ).decode()

    try:
        response = httpx.post(
            f"https://{identity_domain_host}/oauth2/v1/token",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "password",
                "username": env["OCI_IOT_ORDS_USERNAME"],
                "password": env["OCI_IOT_ORDS_PASSWORD"],
                "scope": scope,
            },
            timeout=30.0,
        )
        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            raise_for_status()
        payload = response.json()
        access_token = payload["access_token"]
        token_type = payload["token_type"]
        expires_in = payload["expires_in"]
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        raise DataApiTokenError(
            code="data_plane_error",
            message="Failed to mint an IoT Data API bearer token.",
            retry_hint="Verify the ORDS credentials and domain access, then retry.",
            details={"status_code": status_code},
        ) from exc
    except httpx.RequestError as exc:
        raise DataApiTokenError(
            code="data_plane_error",
            message="Failed to mint an IoT Data API bearer token.",
            retry_hint="Verify the ORDS credentials and domain access, then retry.",
            details={"reason": str(exc)},
        ) from exc
    except (KeyError, TypeError, ValueError) as exc:
        raise DataApiTokenError(
            code="data_plane_error",
            message="IoT Data API token endpoint returned an invalid response.",
            retry_hint="Verify the ORDS credentials and domain access, then retry.",
            details={"reason": str(exc)},
        ) from exc

    minted_at = now()
    return DataApiTokenModel(
        access_token=access_token,
        token_type=token_type,
        expires_in=expires_in,
        expires_at=minted_at + timedelta(seconds=expires_in),
    )


def _get_json(*, url: str, token: str, params: dict) -> dict:
    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def get_collection_record(*, base_url: str, path: str, token: str, record_id: str) -> dict:
    return _get_json(url=f"{base_url}{path}/{record_id}", token=token, params={})


def list_collection_records(
    *,
    base_url: str,
    path: str,
    token: str,
    params: dict,
    target_count: int,
) -> list[dict]:
    records = []
    offset = 0
    scanned = 0
    while len(records) < target_count and scanned < 500:
        page = _get_json(
            url=f"{base_url}{path}",
            token=token,
            params={**params, "limit": min(100, target_count), "offset": offset},
        )
        items = page.get("items", [])
        if not items:
            break
        records.extend(items)
        offset += len(items)
        scanned += len(items)

    return records[:target_count]


def get_raw_command_record(*, base_url: str, token: str, request_id: str) -> dict:
    return get_collection_record(
        base_url=base_url,
        path="/rawCommandData",
        token=token,
        record_id=request_id,
    )


def list_raw_command_records(
    *,
    base_url: str,
    token: str,
    digital_twin_instance_id: str,
    target_count: int,
) -> list[dict]:
    return list_collection_records(
        base_url=base_url,
        path="/rawCommandData",
        token=token,
        params={"q": encode_q(build_twin_filter(digital_twin_instance_id))},
        target_count=target_count,
    )


def list_snapshot_records(
    *,
    base_url: str,
    token: str,
    digital_twin_instance_id: str,
    target_count: int,
) -> list[dict]:
    return list_collection_records(
        base_url=base_url,
        path="/snapshotData",
        token=token,
        params={"q": encode_q(build_twin_filter(digital_twin_instance_id))},
        target_count=target_count,
    )


def list_historized_records(
    *,
    base_url: str,
    token: str,
    digital_twin_instance_id: str,
    target_count: int,
) -> list[dict]:
    return list_collection_records(
        base_url=base_url,
        path="/historizedData",
        token=token,
        params={"q": encode_q(build_twin_filter(digital_twin_instance_id))},
        target_count=target_count,
    )


def list_rejected_data_records(
    *,
    base_url: str,
    token: str,
    digital_twin_instance_id: str,
    target_count: int,
) -> list[dict]:
    return list_collection_records(
        base_url=base_url,
        path="/rejectedData",
        token=token,
        params={"q": encode_q(build_twin_filter(digital_twin_instance_id))},
        target_count=target_count,
    )
