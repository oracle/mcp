from datetime import UTC, datetime

import pytest

import oracle.oci_iot_mcp_server.data_plane as data_plane
from oracle.oci_iot_mcp_server.data_plane import (
    DataApiTokenError,
    build_ords_base_url,
    build_twin_filter,
    clear_data_api_token_cache,
    encode_q,
    get_cached_data_api_token,
    list_collection_records,
    mint_data_api_token,
    require_token_credentials,
)


def test_build_ords_base_url_uses_domain_group_host_and_domain_short_id():
    result = build_ords_base_url(
        {
            "data_host": "xyz987.data.iot.us-phoenix-1.oci.oraclecloud.com",
            "domain_short_id": "abc123",
        }
    )

    assert result == "https://xyz987.data.iot.us-phoenix-1.oci.oraclecloud.com/ords/abc123/20250531"


def test_mint_data_api_token_uses_password_grant_and_scope(monkeypatch):
    observed = {}

    class FakeResponse:
        def raise_for_status(self):
            observed["raise_for_status_called"] = True

        def json(self):
            return {"access_token": "token-123", "token_type": "Bearer", "expires_in": 3600}

    def fake_post(*args, **kwargs):
        observed["url"] = args[0]
        observed["headers"] = kwargs["headers"]
        observed["data"] = kwargs["data"]
        return FakeResponse()

    monkeypatch.setattr(data_plane.httpx, "post", fake_post)

    context = {
        "domain_short_id": "abc123",
        "domain_group_short_id": "xyz987",
        "db_allowed_identity_domain_host": "id.example.com",
    }

    result = mint_data_api_token(
        domain_context=context,
        env={
            "OCI_IOT_ORDS_CLIENT_ID": "client-id",
            "OCI_IOT_ORDS_CLIENT_SECRET": "client-secret",
            "OCI_IOT_ORDS_USERNAME": "iot.user@example.com",
            "OCI_IOT_ORDS_PASSWORD": "secret-password",
        },
        now=lambda: datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC),
    )

    assert result.access_token == "token-123"
    assert result.expires_at.isoformat() == "2026-03-26T13:00:00+00:00"
    assert observed["raise_for_status_called"] is True
    assert observed["url"] == "https://id.example.com/oauth2/v1/token"
    assert observed["data"]["scope"] == "/xyz987/iot/abc123"
    assert build_twin_filter("ocid1.digitaltwininstance.oc1..aaaa") == {
        "$and": [{"digital_twin_instance_id": "ocid1.digitaltwininstance.oc1..aaaa"}]
    }
    assert encode_q(build_twin_filter("ocid1.digitaltwininstance.oc1..aaaa")) == (
        '{"$and":[{"digital_twin_instance_id":"ocid1.digitaltwininstance.oc1..aaaa"}]}'
    )


def test_mint_data_api_token_requires_identity_domain_host():
    with pytest.raises(DataApiTokenError) as excinfo:
        mint_data_api_token(
            domain_context={
                "domain_short_id": "abc123",
                "domain_group_short_id": "xyz987",
            },
            env={
                "OCI_IOT_ORDS_CLIENT_ID": "client-id",
                "OCI_IOT_ORDS_CLIENT_SECRET": "client-secret",
                "OCI_IOT_ORDS_USERNAME": "iot.user@example.com",
                "OCI_IOT_ORDS_PASSWORD": "secret-password",
            },
            now=lambda: datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC),
        )

    assert excinfo.value.code == "missing_ords_configuration"
    assert excinfo.value.details["missing"] == ["db_allowed_identity_domain_host"]


def test_get_cached_data_api_token_reuses_unexpired_token(monkeypatch):
    clear_data_api_token_cache()
    observed = {"calls": 0}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            observed["calls"] += 1
            return {
                "access_token": f"token-{observed['calls']}",
                "token_type": "Bearer",
                "expires_in": 3600,
            }

    monkeypatch.setattr(data_plane.httpx, "post", lambda *args, **kwargs: FakeResponse())

    context = {
        "domain_short_id": "abc123",
        "domain_group_short_id": "xyz987",
        "db_allowed_identity_domain_host": "id.example.com",
    }
    env = {
        "OCI_IOT_ORDS_CLIENT_ID": "client-id",
        "OCI_IOT_ORDS_CLIENT_SECRET": "client-secret",
        "OCI_IOT_ORDS_USERNAME": "iot.user@example.com",
        "OCI_IOT_ORDS_PASSWORD": "secret-password",
    }

    try:
        token1 = get_cached_data_api_token(
            domain_context=context,
            env=env,
            now=lambda: datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC),
        )
        token2 = get_cached_data_api_token(
            domain_context=context,
            env=env,
            now=lambda: datetime(2026, 3, 26, 12, 5, 0, tzinfo=UTC),
        )
    finally:
        clear_data_api_token_cache()

    assert token1.access_token == "token-1"
    assert token2.access_token == "token-1"
    assert observed["calls"] == 1


def test_get_cached_data_api_token_refreshes_after_expiry(monkeypatch):
    clear_data_api_token_cache()
    observed = {"calls": 0}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            observed["calls"] += 1
            return {
                "access_token": f"token-{observed['calls']}",
                "token_type": "Bearer",
                "expires_in": 60,
            }

    monkeypatch.setattr(data_plane.httpx, "post", lambda *args, **kwargs: FakeResponse())

    context = {
        "domain_short_id": "abc123",
        "domain_group_short_id": "xyz987",
        "db_allowed_identity_domain_host": "id.example.com",
    }
    env = {
        "OCI_IOT_ORDS_CLIENT_ID": "client-id",
        "OCI_IOT_ORDS_CLIENT_SECRET": "client-secret",
        "OCI_IOT_ORDS_USERNAME": "iot.user@example.com",
        "OCI_IOT_ORDS_PASSWORD": "secret-password",
    }

    try:
        token1 = get_cached_data_api_token(
            domain_context=context,
            env=env,
            now=lambda: datetime(2026, 3, 26, 12, 0, 0, tzinfo=UTC),
        )
        token2 = get_cached_data_api_token(
            domain_context=context,
            env=env,
            now=lambda: datetime(2026, 3, 26, 12, 1, 1, tzinfo=UTC),
        )
    finally:
        clear_data_api_token_cache()

    assert token1.access_token == "token-1"
    assert token2.access_token == "token-2"
    assert observed["calls"] == 2


def test_require_token_credentials_returns_structured_error_for_missing_env():
    result = require_token_credentials({"OCI_IOT_ORDS_CLIENT_ID": "client-id"})

    assert result["ok"] is False
    assert result["error"]["code"] == "missing_token_credentials"
    assert result["error"]["details"]["missing"] == [
        "OCI_IOT_ORDS_CLIENT_SECRET",
        "OCI_IOT_ORDS_USERNAME",
        "OCI_IOT_ORDS_PASSWORD",
    ]


def test_require_token_credentials_returns_sanitized_success_payload():
    result = require_token_credentials(
        {
            "OCI_IOT_ORDS_CLIENT_ID": "client-id",
            "OCI_IOT_ORDS_CLIENT_SECRET": "client-secret",
            "OCI_IOT_ORDS_USERNAME": "iot.user@example.com",
            "OCI_IOT_ORDS_PASSWORD": "secret-password",
        }
    )

    assert result == {
        "ok": True,
        "data": {
            "present": [
                "OCI_IOT_ORDS_CLIENT_ID",
                "OCI_IOT_ORDS_CLIENT_SECRET",
                "OCI_IOT_ORDS_USERNAME",
                "OCI_IOT_ORDS_PASSWORD",
            ],
            "missing": [],
        },
    }


def test_list_collection_records_uses_limit_offset_until_target_count(monkeypatch):
    observed_params = []
    pages = iter(
        [
            {"items": [{"id": "1"}, {"id": "2"}]},
            {"items": [{"id": "3"}]},
        ]
    )

    monkeypatch.setattr(
        data_plane,
        "_get_json",
        lambda **kwargs: observed_params.append(kwargs["params"]) or next(pages),
    )

    records = list_collection_records(
        base_url="https://xyz987.data.iot.us-phoenix-1.oci.oraclecloud.com/ords/abc123/20250531",
        path="/rawCommandData",
        token="token-123",
        params={"q": '{"$and":[{"digital_twin_instance_id":"ocid1.digitaltwininstance.oc1..aaaa"}]}'},
        target_count=3,
    )

    assert [record["id"] for record in records] == ["1", "2", "3"]
    assert observed_params == [
        {
            "q": '{"$and":[{"digital_twin_instance_id":"ocid1.digitaltwininstance.oc1..aaaa"}]}',
            "limit": 3,
            "offset": 0,
        },
        {
            "q": '{"$and":[{"digital_twin_instance_id":"ocid1.digitaltwininstance.oc1..aaaa"}]}',
            "limit": 3,
            "offset": 2,
        },
    ]


def test_get_json_sends_bearer_token_and_raises_for_status(monkeypatch):
    observed = {}

    class FakeResponse:
        def raise_for_status(self):
            observed["raise_for_status_called"] = True

        def json(self):
            return {"items": []}

    def fake_get(url, *, headers, params, timeout):
        observed["url"] = url
        observed["headers"] = headers
        observed["params"] = params
        observed["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(data_plane.httpx, "get", fake_get)

    payload = data_plane._get_json(
        url="https://example.com/data",
        token="token-123",
        params={"limit": 1},
    )

    assert payload == {"items": []}
    assert observed == {
        "url": "https://example.com/data",
        "headers": {"Authorization": "Bearer token-123"},
        "params": {"limit": 1},
        "timeout": 30.0,
        "raise_for_status_called": True,
    }


def test_get_collection_record_builds_record_url(monkeypatch):
    observed = {}

    monkeypatch.setattr(
        data_plane,
        "_get_json",
        lambda **kwargs: observed.update(kwargs) or {"id": "rc-1"},
    )

    result = data_plane.get_collection_record(
        base_url="https://example.com/base",
        path="/rawCommandData",
        token="token-123",
        record_id="rc-1",
    )

    assert result == {"id": "rc-1"}
    assert observed == {
        "url": "https://example.com/base/rawCommandData/rc-1",
        "token": "token-123",
        "params": {},
    }


def test_list_collection_records_stops_when_page_is_empty(monkeypatch):
    observed_params = []
    pages = iter([{"items": [{"id": "1"}]}, {"items": []}])

    monkeypatch.setattr(
        data_plane,
        "_get_json",
        lambda **kwargs: observed_params.append(kwargs["params"]) or next(pages),
    )

    result = list_collection_records(
        base_url="https://example.com/base",
        path="/snapshotData",
        token="token-123",
        params={},
        target_count=4,
    )

    assert result == [{"id": "1"}]
    assert observed_params == [
        {"limit": 4, "offset": 0},
        {"limit": 4, "offset": 1},
    ]


def test_collection_wrappers_use_expected_paths_and_filters(monkeypatch):
    observed_get = {}
    observed_list = []

    monkeypatch.setattr(
        data_plane,
        "get_collection_record",
        lambda **kwargs: observed_get.update(kwargs) or {"id": kwargs["record_id"]},
    )
    monkeypatch.setattr(
        data_plane,
        "list_collection_records",
        lambda **kwargs: observed_list.append(kwargs) or [{"id": kwargs["path"]}],
    )

    detail = data_plane.get_raw_command_record(
        base_url="https://example.com/base",
        token="token-123",
        request_id="rc-1",
    )
    raw = data_plane.list_raw_command_records(
        base_url="https://example.com/base",
        token="token-123",
        digital_twin_instance_id="twin-1",
        target_count=5,
    )
    snapshot = data_plane.list_snapshot_records(
        base_url="https://example.com/base",
        token="token-123",
        digital_twin_instance_id="twin-1",
        target_count=5,
    )
    historized = data_plane.list_historized_records(
        base_url="https://example.com/base",
        token="token-123",
        digital_twin_instance_id="twin-1",
        target_count=5,
    )
    rejected = data_plane.list_rejected_data_records(
        base_url="https://example.com/base",
        token="token-123",
        digital_twin_instance_id="twin-1",
        target_count=5,
    )

    assert detail == {"id": "rc-1"}
    assert observed_get == {
        "base_url": "https://example.com/base",
        "path": "/rawCommandData",
        "token": "token-123",
        "record_id": "rc-1",
    }
    assert raw == [{"id": "/rawCommandData"}]
    assert snapshot == [{"id": "/snapshotData"}]
    assert historized == [{"id": "/historizedData"}]
    assert rejected == [{"id": "/rejectedData"}]
    assert [entry["path"] for entry in observed_list] == [
        "/rawCommandData",
        "/snapshotData",
        "/historizedData",
        "/rejectedData",
    ]
    assert all(entry["params"]["q"] == encode_q(build_twin_filter("twin-1")) for entry in observed_list)
